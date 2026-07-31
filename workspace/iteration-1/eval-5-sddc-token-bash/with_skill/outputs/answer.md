# SDDC Manager API token helper for VCF 9.0 (bash)

Here's the function. Two things worth knowing before the code:

**The refresh chain is two-tier, not one.** SDDC Manager 9.0 hands you an *access token* (JWT,
1 hour) plus a *refresh token* (UUID, 24 hours). Refreshing uses the refresh token; once
that 24-hour window closes, nothing can be refreshed and you have to log in again with the
password. So "refreshes it when it expires" needs both paths, and the function has both.

**Your self-signed cert doesn't have to mean `-k`.** Because the cert is self-signed, the leaf
*is* its own issuer — so you can hand that one file to `curl --cacert` and get real verification
against exactly that certificate, with no CA infrastructure and no trust-store surgery. That's
one command to set up, and it's meaningfully better than `-k` here: SDDC Manager holds the
credentials for your whole estate, so a client that accepts any certificate on that hostname is
a different risk class from one talking to a test API. `SDDC_INSECURE=1` is still there if you
want it while prototyping — just make it a decision rather than a default.

## Setup

```bash
# 1. Pin the appliance's self-signed certificate (once)
mkdir -p ~/.vcf && chmod 700 ~/.vcf
openssl s_client -connect sfo-vcf01.rainpole.io:443 -servername sfo-vcf01.rainpole.io \
  </dev/null 2>/dev/null | openssl x509 -outform pem > ~/.vcf/sddc-manager.pem

# 2. Check the fingerprint against what the SDDC Manager console shows, out of band.
#    Grabbing a cert over the same untrusted channel you're trying to secure proves nothing
#    on its own — this comparison is what makes the pin worth anything.
openssl x509 -in ~/.vcf/sddc-manager.pem -noout -fingerprint -sha256 -subject -dates
```

Connect by **FQDN, not IP** — the cert is issued to the FQDN, so an IP fails hostname
verification even with the pin in place.

## The script

Save as `sddc-token.sh` and `source` it.

```bash
# shellcheck shell=bash
# ---------------------------------------------------------------------------
# SDDC Manager API token helper — VMware Cloud Foundation 9.0
#
# Endpoints (all confirmed present in the SDDC Manager OpenAPI spec at git tag
# 9.0.0.0 of github.com/vmware/vcf-api-specs — unchanged at 9.1.0.0):
#   POST   /v1/tokens                         createToken            -> 201 TokenPair
#   PATCH  /v1/tokens/access-token/refresh    refreshAccessToken     -> 200 string (JWT)
#   DELETE /v1/tokens/refresh-token           invalidateRefreshToken -> 204
# Access token lifetime 1 h, refresh token lifetime 24 h.
# Subsequent calls use:  Authorization: Bearer <accessToken>
#
# Usage:  . ./sddc-token.sh
#         sddc_api GET /v1/domains
# ---------------------------------------------------------------------------

# ---- configuration --------------------------------------------------------
: "${SDDC_MANAGER:=sfo-vcf01.rainpole.io}"    # FQDN, not IP — the cert is issued to the FQDN
: "${SDDC_USER:=administrator@vsphere.local}"
: "${SDDC_PASSWORD:=}"                        # empty => prompt on /dev/tty
: "${SDDC_CA_BUNDLE:=$HOME/.vcf/sddc-manager.pem}"   # pinned self-signed cert (see notes)
: "${SDDC_INSECURE:=0}"                       # 1 = skip TLS verification (last resort)
: "${SDDC_SKEW:=60}"                          # renew this many seconds before expiry

# Token cache. It has to live in a file, not a shell variable: callers write
# $(sddc_token), which runs the function in a subshell, so any in-memory state
# would be discarded and every call would re-authenticate.
: "${SDDC_TOKEN_CACHE:=${XDG_RUNTIME_DIR:-/tmp}/sddc-token-$(id -u)-${SDDC_MANAGER//[^A-Za-z0-9._-]/_}}"

_sddc_code=""; _sddc_body=""
_sddc_at=""; _sddc_at_exp=0; _sddc_rt=""; _sddc_rt_exp=0

# ---- internals ------------------------------------------------------------

_sddc_cache_load() {
  _sddc_at=""; _sddc_at_exp=0; _sddc_rt=""; _sddc_rt_exp=0
  [ -f "$SDDC_TOKEN_CACHE" ] || return 0
  # refuse a cache file we do not own (shared /tmp)
  [ -O "$SDDC_TOKEN_CACHE" ] || { echo "sddc: $SDDC_TOKEN_CACHE not owned by us, ignoring" >&2; return 0; }
  local k v
  while IFS='=' read -r k v; do
    case "$k" in
      at) _sddc_at=$v ;; at_exp) _sddc_at_exp=$v ;;
      rt) _sddc_rt=$v ;; rt_exp) _sddc_rt_exp=$v ;;
    esac
  done < "$SDDC_TOKEN_CACHE"
  return 0
}

_sddc_cache_save() {
  local old; old=$(umask); umask 077
  printf 'at=%s\nat_exp=%s\nrt=%s\nrt_exp=%s\n' \
    "$_sddc_at" "$_sddc_at_exp" "$_sddc_rt" "$_sddc_rt_exp" > "$SDDC_TOKEN_CACHE"
  umask "$old"
}

# _sddc_http METHOD URL [curl args...] -> sets _sddc_code, _sddc_body
_sddc_http() {
  local method=$1 url=$2; shift 2
  local -a opts=(--silent --show-error --request "$method" --write-out $'\n%{http_code}')
  if [ -r "$SDDC_CA_BUNDLE" ]; then
    opts+=(--cacert "$SDDC_CA_BUNDLE")
  elif [ "$SDDC_INSECURE" = "1" ]; then
    opts+=(--insecure)
  fi
  local raw
  raw=$(curl "${opts[@]}" "$@" "$url") || { _sddc_code="000"; _sddc_body=""; return 1; }
  _sddc_code=${raw##*$'\n'}
  _sddc_body=${raw%$'\n'*}
  return 0
}

# _sddc_json_str JSON JQ_PATH   (jq when available, sed fallback otherwise)
_sddc_json_str() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$1" | jq -r "$2 // empty" 2>/dev/null
    return
  fi
  case "$2" in
    .accessToken)
      printf '%s' "$1" | sed -n 's/.*"accessToken"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' ;;
    .refreshToken.id)
      printf '%s' "$1" | sed -n 's/.*"refreshToken"[[:space:]]*:[[:space:]]*{[^}]*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' ;;
  esac
}

# read the real exp claim from the JWT instead of assuming 3600 s
_sddc_jwt_exp() {
  local p=${1#*.}; p=${p%%.*}
  case $(( ${#p} % 4 )) in 2) p="${p}==";; 3) p="${p}=";; 1) return 1;; esac
  local json exp
  json=$(printf '%s' "$p" | tr '_-' '/+' | base64 -d 2>/dev/null) || return 1
  exp=$(printf '%s' "$json" | sed -n 's/.*"exp"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p')
  [ -n "$exp" ] || return 1
  printf '%s' "$exp"
}

_sddc_set_access() {   # $1 = raw JWT
  _sddc_at=$1
  _sddc_at_exp=$(_sddc_jwt_exp "$1" 2>/dev/null) || _sddc_at_exp=""
  [ -n "$_sddc_at_exp" ] || _sddc_at_exp=$(( $(date +%s) + 3600 ))   # documented 1 h
}

# POST /v1/tokens
_sddc_login() {
  if [ -z "$SDDC_PASSWORD" ]; then
    if [ -r /dev/tty ]; then
      read -r -s -p "Password for ${SDDC_USER} at ${SDDC_MANAGER}: " SDDC_PASSWORD < /dev/tty
      echo >&2
    else
      echo "sddc: no SDDC_PASSWORD set and no tty to prompt on" >&2; return 1
    fi
  fi
  # JSON-escape backslashes and double quotes
  local esc=${SDDC_PASSWORD//\\/\\\\}; esc=${esc//\"/\\\"}
  local usr=${SDDC_USER//\\/\\\\};     usr=${usr//\"/\\\"}

  # credentials go in over stdin, so they never appear in ps output
  _sddc_http POST "https://${SDDC_MANAGER}/v1/tokens" \
    --header 'Content-Type: application/json' --header 'Accept: application/json' \
    --data @- <<EOF
{"username":"${usr}","password":"${esc}"}
EOF

  case "$_sddc_code" in
    200|201) : ;;
    000) echo "sddc: cannot reach https://${SDDC_MANAGER} — network or TLS failure." >&2
         echo "     If this is the self-signed cert, see SDDC_CA_BUNDLE." >&2; return 1 ;;
    401|403) echo "sddc: credentials rejected (HTTP $_sddc_code): $_sddc_body" >&2; return 1 ;;
    *) echo "sddc: POST /v1/tokens failed (HTTP $_sddc_code): $_sddc_body" >&2; return 1 ;;
  esac

  local at rt
  at=$(_sddc_json_str "$_sddc_body" .accessToken)
  rt=$(_sddc_json_str "$_sddc_body" .refreshToken.id)
  [ -n "$at" ] || { echo "sddc: no accessToken in response: $_sddc_body" >&2; return 1; }

  _sddc_set_access "$at"
  _sddc_rt=$rt
  _sddc_rt_exp=$(( $(date +%s) + 86400 ))   # refresh token lives 24 h
  _sddc_cache_save
}

# PATCH /v1/tokens/access-token/refresh
_sddc_refresh() {
  [ -n "$_sddc_rt" ] || return 1

  # The spec types the body as a JSON string. Broadcom's reference sends the
  # bare UUID; a strict JSON parser wants it quoted. Try bare, retry quoted.
  _sddc_http PATCH "https://${SDDC_MANAGER}/v1/tokens/access-token/refresh" \
    --header 'Content-Type: application/json' --header 'Accept: application/json' \
    --data "$_sddc_rt"
  if [ "$_sddc_code" = "400" ]; then
    _sddc_http PATCH "https://${SDDC_MANAGER}/v1/tokens/access-token/refresh" \
      --header 'Content-Type: application/json' --header 'Accept: application/json' \
      --data "\"$_sddc_rt\""
  fi

  if [ "$_sddc_code" != "200" ]; then
    # 404 = unknown/expired refresh token, 401 = revoked -> force a full login
    _sddc_rt=""; _sddc_rt_exp=0; _sddc_cache_save
    return 1
  fi

  # body is the raw JWT; some builds wrap it in JSON quotes
  local jwt=$_sddc_body
  jwt=${jwt#\"}; jwt=${jwt%\"}
  jwt=$(printf '%s' "$jwt" | tr -d '[:space:]')
  case "$jwt" in
    *.*.*) _sddc_set_access "$jwt"; _sddc_cache_save; return 0 ;;
    *) _sddc_rt=""; _sddc_rt_exp=0; _sddc_cache_save; return 1 ;;
  esac
}

# ---- public API -----------------------------------------------------------

# sddc_token — print a currently valid access token, refreshing or re-logging
# in as needed. Cheap and safe to call before every request.
sddc_token() {
  _sddc_cache_load
  local now; now=$(date +%s)

  if [ -n "$_sddc_at" ] && [ "$now" -lt $(( _sddc_at_exp - SDDC_SKEW )) ]; then
    printf '%s\n' "$_sddc_at"; return 0
  fi
  if [ -n "$_sddc_rt" ] && [ "$now" -lt $(( _sddc_rt_exp - SDDC_SKEW )) ]; then
    if _sddc_refresh; then printf '%s\n' "$_sddc_at"; return 0; fi
  fi
  _sddc_login || return 1
  printf '%s\n' "$_sddc_at"
}

# sddc_api METHOD PATH [curl args...] — authenticated call, one retry on 401
#   sddc_api GET /v1/domains
#   sddc_api GET /v1/system/appliance-info      # returns the VCF version
#   sddc_api POST /v1/foo --header 'Content-Type: application/json' --data @body.json
sddc_api() {
  local method=$1 path=$2; shift 2
  local tok
  tok=$(sddc_token) || return 1

  _sddc_http "$method" "https://${SDDC_MANAGER}${path}" \
    --header "Authorization: Bearer ${tok}" --header 'Accept: application/json' "$@"

  if [ "$_sddc_code" = "401" ]; then
    _sddc_cache_load; _sddc_at_exp=0; _sddc_cache_save   # mark stale, force renewal
    tok=$(sddc_token) || return 1
    _sddc_http "$method" "https://${SDDC_MANAGER}${path}" \
      --header "Authorization: Bearer ${tok}" --header 'Accept: application/json' "$@"
  fi

  [ -n "$_sddc_body" ] && printf '%s\n' "$_sddc_body"
  case "$_sddc_code" in 2*) return 0 ;; *) return 1 ;; esac
}

# sddc_logout — DELETE /v1/tokens/refresh-token and clear the cache
sddc_logout() {
  _sddc_cache_load
  if [ -n "$_sddc_rt" ]; then
    _sddc_http DELETE "https://${SDDC_MANAGER}/v1/tokens/refresh-token" \
      --header 'Content-Type: application/json' --data "$_sddc_rt"
    if [ "$_sddc_code" = "400" ]; then
      _sddc_http DELETE "https://${SDDC_MANAGER}/v1/tokens/refresh-token" \
        --header 'Content-Type: application/json' --data "\"$_sddc_rt\""
    fi
  fi
  rm -f "$SDDC_TOKEN_CACHE"
  _sddc_at=""; _sddc_at_exp=0; _sddc_rt=""; _sddc_rt_exp=0
  unset SDDC_PASSWORD
}
```

## Using it

```bash
export SDDC_MANAGER=sfo-vcf01.rainpole.io
export SDDC_USER=administrator@vsphere.local
. ./sddc-token.sh

sddc_api GET /v1/domains
sddc_api GET /v1/system/appliance-info      # confirms you really are on 9.0

# or just the raw token, for your own curl calls
curl --cacert ~/.vcf/sddc-manager.pem \
     -H "Authorization: Bearer $(sddc_token)" \
     "https://$SDDC_MANAGER/v1/hosts"

sddc_logout    # invalidates the refresh token server-side
```

## Design notes

**The cache is a file, not a variable — and that's the one non-obvious thing in here.** The
natural way to call this is `$(sddc_token)`, which runs the function in a *subshell*. Any token
cached in a shell variable dies with that subshell, so the "cache" would never hit and you'd
issue a fresh `POST /v1/tokens` on every single call. A mode-0600 file under `$XDG_RUNTIME_DIR`
(tmpfs, cleared at logout) fixes that, and as a bonus the token survives across separate script
invocations. If you'd rather nothing touched disk, drop the cache functions and have
`sddc_token` assign to a global instead of printing — but then every caller must use
`sddc_token && ... "$SDDC_TOKEN"`, never `$(sddc_token)`.

Other choices:

- **Expiry comes from the JWT's own `exp` claim**, decoded from the token, with the documented
  1 hour only as a fallback. Beats hardcoding an assumption about the appliance's clock.
- **Both failure modes are handled.** Access token stale → `PATCH .../refresh`. Refresh token
  rejected (404/401) or past 24 h → full `POST /v1/tokens`. A 401 that arrives mid-request gets
  one transparent retry, because a token can expire between the check and the call.
- **The refresh body is sent bare, then quoted on a 400.** The 9.0 spec types that body as a
  JSON string under `application/json`, but a bare UUID isn't strictly valid JSON — Broadcom's
  reference sends it bare and it works on the builds it was written against. Rather than bet on
  one, the function tries bare and retries quoted. Same for the logout call.
- **Credentials go to curl over stdin**, so they never show up in `ps`. Quotes and backslashes
  in the password are JSON-escaped.
- **`jq` is used when present**, with a `sed` fallback so this runs on a bare jump host.

## Three VCF 9.0 specifics that trip people up

1. **There is no fleet-wide SSO token in 9.0, and SDDC Manager wouldn't accept one anyway.**
   SSO-issued, role-scoped API tokens (Fleet Management → Identity & Access → API Clients) are a
   **9.1** feature — the 9.0 `vcf-operations` spec has zero `/api/fleet-management/iam/**`
   operations against 70 in 9.1. And separately, SDDC Manager and ESX are excluded from VCF SSO
   in *both* versions, so `POST /v1/tokens` stays the way in regardless. If you've been reading a
   9.1 walkthrough for a long-lived service-account token, it doesn't apply here.
2. **24 hours is the real ceiling on unattended running.** After that the refresh token is dead
   and only the password gets you a new pair. For a long-running daemon, either keep the
   credential available from a secret store, or re-run login on a schedule. There are no
   fleet-level token TTL controls in 9.0 to extend this — those are 9.1 IAM settings.
3. **This is SDDC-Manager-only.** Each VCF product has its own flow and its own header: vCenter
   uses `vmware-api-session-id`, NSX uses a `JSESSIONID` cookie *plus* an `x-xsrf-token` header
   (30-minute default), VCF Operations uses `Authorization: OpsToken <token>` (6 hours). A Bearer
   token from SDDC Manager opens exactly one door.

## Provenance

The three token endpoints, their request/response schemas (`TokenCreationSpec` →
`TokenPair`/`RefreshToken`) and the JSON-string refresh body were read from the SDDC Manager
OpenAPI spec at **git tag `9.0.0.0`** of `github.com/vmware/vcf-api-specs`, not from a doc page —
so they're version-exact for 9.0. All three are unchanged at `9.1.0.0`, so this survives the
upgrade. The 1 h / 24 h lifetimes and the `Authorization: Bearer` header are from Broadcom's
9.0 developer reference; note the 9.0 spec declares no `securitySchemes` at all, so the header
is prose-sourced rather than machine-confirmed (correct, just not spec-verifiable).

I ran the script end to end against a mock SDDC Manager with a self-signed cert — login,
subshell cache hit, expiry-driven refresh including the bare→quoted 400 retry, mid-flight 401
retry, refresh-token rejection falling back to full login, cross-process cache reuse, logout,
bad-password handling, and TLS verification actually failing when the cert isn't trusted. It is
clean under `shellcheck`. It has **not** been run against a real VCF 9.0 appliance, so treat the
bare-vs-quoted refresh body as the one thing to watch on first contact.
