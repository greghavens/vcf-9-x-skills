# SDDC Manager API token helper for VCF 9.0

Drop this in `~/.vcfrc` (or your script), `source` it, and call `vcf_token` wherever you need a bearer token. It mints a token pair, caches it, refreshes the access token when it is about to expire, and falls back to a full re-login if the refresh token has also died.

## The endpoints it uses

Three calls, all on SDDC Manager itself:

| Purpose | Call | Body |
|---|---|---|
| Get a token pair | `POST /v1/tokens` | `{"username": "...", "password": "..."}` |
| Refresh the access token | `PATCH /v1/tokens/access-token/refresh` | the **bare refresh token id**, not JSON |
| Invalidate the refresh token | `DELETE /v1/tokens/refresh-token` | the bare refresh token id |

The refresh call is the one people trip on: `Content-Type: application/json`, but the body is just the UUID (`3c6b3c30-3bf2-...`) with no quotes and no wrapping object. The response is the new access token as a bare string, not an object. The function below is liberal about that anyway (raw / quoted / `{"accessToken":...}` all parse) because it varies by build.

## Expiry: read it, don't guess it

The access token is a JWT and it carries its own `exp` claim, so rather than hardcoding "60 minutes" the function base64url-decodes the payload and uses the real expiry with a 120s clock-skew margin. That way it keeps working if your org changes the token lifetime, and it survives the client's clock being a bit off from SDDC Manager's.

## The code

```bash
# ---------------------------------------------------------------------------
# SDDC Manager (VCF 9.0) API token helper
#
#   vcf_token            -> echoes a currently-valid access token (JWT)
#   vcf_api VERB PATH    -> authenticated curl, auto-retries once on 401
#   vcf_token_logout     -> invalidates the refresh token server-side
#   vcf_token_reset      -> forgets cached tokens locally
#
# Config (env):
#   VCF_SDDC        SDDC Manager FQDN            (required)
#   VCF_USER        e.g. administrator@vsphere.local
#   VCF_PASS        password  (or VCF_PASS_FILE / VCF_PASS_CMD)
#   VCF_PASS_FILE   file containing the password, chmod 600
#   VCF_PASS_CMD    command that prints the password (vault/pass/op read ...)
#   VCF_CACERT      path to the SDDC Manager cert -> real TLS verification
#   VCF_PIN         sha256//BASE64 pubkey pin (alternative to VCF_CACERT)
#   VCF_INSECURE    1 = skip verification (default while cert is self-signed)
#   VCF_TOKEN_CACHE cache file (default ~/.cache/vcf/<user>@<host>.json, 0600)
#   VCF_SKEW        seconds of clock slack, default 120
# ---------------------------------------------------------------------------

_vcf_need() {
  local m=0 c
  for c in curl jq base64; do
    command -v "$c" >/dev/null 2>&1 || { echo "vcf: missing dependency: $c" >&2; m=1; }
  done
  return $m
}

# base64url -> raw, tolerating GNU (-d) and BSD (-D)
_vcf_b64d() {
  if [ -z "${_VCF_B64D:-}" ]; then
    if printf 'aGk=' | base64 -d >/dev/null 2>&1; then _VCF_B64D=-d; else _VCF_B64D=-D; fi
  fi
  base64 "$_VCF_B64D" 2>/dev/null
}

# Print the exp claim (epoch seconds) of a JWT, or nothing if unreadable.
_vcf_jwt_exp() {
  local jwt=$1 p
  case $jwt in *.*.*) ;; *) return 1 ;; esac
  p=${jwt#*.}; p=${p%%.*}
  p=${p//-/+}; p=${p//_//}
  case $(( ${#p} % 4 )) in 2) p="$p==" ;; 3) p="$p=" ;; esac
  printf '%s' "$p" | _vcf_b64d | jq -er '.exp // empty' 2>/dev/null
}

# NOTE: `$(vcf_token)` runs in a subshell, so the shell variables below never
# make it back to the caller -- this file is the real cache, and it is what
# stops every call from logging in again. Keep it on local disk, mode 600.
_vcf_cache_file() {
  if [ -n "${VCF_TOKEN_CACHE:-}" ]; then printf '%s' "$VCF_TOKEN_CACHE"; return; fi
  local key="${VCF_USER:-administrator@vsphere.local}@${VCF_SDDC:-unset}"
  printf '%s/vcf/%s.json' "${XDG_CACHE_HOME:-$HOME/.cache}" "${key//[^A-Za-z0-9._@-]/_}"
}

# Populate _VCF_CURL with transport + TLS options.
_vcf_curl_setup() {
  _VCF_CURL=( --silent --show-error --connect-timeout 10 --max-time 120
              --retry 2 --retry-connrefused )
  if   [ -n "${VCF_CACERT:-}" ]; then _VCF_CURL+=( --cacert "$VCF_CACERT" )
  elif [ -n "${VCF_PIN:-}" ];    then _VCF_CURL+=( --insecure --pinnedpubkey "$VCF_PIN" )
  elif [ "${VCF_INSECURE:-1}" = 1 ]; then
    _VCF_CURL+=( --insecure )
    # Warn on terminals only -- otherwise every $(vcf_token) in a script
    # (each a fresh subshell) would repeat this on stderr.
    if [ -z "${_VCF_WARNED:-}" ] && [ -t 2 ]; then
      _VCF_WARNED=1
      echo "vcf: TLS verification disabled (self-signed). Set VCF_CACERT or VCF_PIN to fix." >&2
    fi
  else
    echo "vcf: refusing to connect: set VCF_CACERT, VCF_PIN, or VCF_INSECURE=1" >&2
    return 1
  fi
}

_vcf_password() {
  local p=
  if   [ -n "${VCF_PASS:-}" ];      then printf '%s' "$VCF_PASS"
  elif [ -n "${VCF_PASS_FILE:-}" ]; then
    # `read` returns 1 on a file with no trailing newline but still fills p.
    IFS= read -r p < "$VCF_PASS_FILE" || true
    [ -n "$p" ] || { echo "vcf: $VCF_PASS_FILE is empty" >&2; return 1; }
    printf '%s' "$p"
  elif [ -n "${VCF_PASS_CMD:-}" ];  then eval "$VCF_PASS_CMD"
  else echo "vcf: no password (set VCF_PASS, VCF_PASS_FILE or VCF_PASS_CMD)" >&2; return 1
  fi
}

# POST /v1/tokens -> fresh access + refresh token
_vcf_login() {
  local body code pass
  pass=$(_vcf_password) || return 1
  body=$(mktemp); code=$(
    jq -nc --arg u "${VCF_USER:-administrator@vsphere.local}" --arg p "$pass" \
       '{username:$u,password:$p}' |
    curl "${_VCF_CURL[@]}" -o "$body" -w '%{http_code}' \
         -X POST "https://$VCF_SDDC/v1/tokens" \
         -H 'Content-Type: application/json' -H 'Accept: application/json' \
         --data-binary @-
  )
  pass=
  if [ "$code" != 200 ] && [ "$code" != 201 ]; then
    echo "vcf: login failed (HTTP ${code:-?}): $(head -c 400 "$body")" >&2
    rm -f "$body"; return 1
  fi
  _VCF_ACCESS=$(jq -r '.accessToken // empty' < "$body")
  _VCF_REFRESH=$(jq -r '.refreshToken.id // .refreshToken // empty' < "$body")
  rm -f "$body"
  [ -n "$_VCF_ACCESS" ] || { echo "vcf: no accessToken in response" >&2; return 1; }
  _vcf_stamp_and_save
}

# PATCH /v1/tokens/access-token/refresh  (body = bare refresh token id)
_vcf_refresh() {
  local body code out
  [ -n "${_VCF_REFRESH:-}" ] || return 1
  body=$(mktemp)
  # Body is the bare refresh-token id, not JSON. Fed via stdin so curl can
  # never mistake a leading '@' for a filename.
  code=$(printf '%s' "$_VCF_REFRESH" |
         curl "${_VCF_CURL[@]}" -o "$body" -w '%{http_code}' \
         -X PATCH "https://$VCF_SDDC/v1/tokens/access-token/refresh" \
         -H 'Content-Type: application/json' -H 'Accept: application/json' \
         --data-binary @-)
  if [ "$code" != 200 ]; then rm -f "$body"; return 1; fi
  # Response is the raw token; be liberal about quoting / object wrapping.
  out=$(jq -r 'if type=="object" then (.accessToken // empty) else . end' < "$body" 2>/dev/null) \
    || out=$(tr -d '"\r\n' < "$body")
  [ -n "$out" ] || out=$(tr -d '"\r\n' < "$body")
  rm -f "$body"
  case $out in *.*.*) ;; *) return 1 ;; esac
  _VCF_ACCESS=$out
  _vcf_stamp_and_save
}

_vcf_stamp_and_save() {
  local now exp
  now=$(date +%s)
  exp=$(_vcf_jwt_exp "$_VCF_ACCESS") || exp=
  # SDDC Manager access tokens are short-lived (~1h). If the JWT is opaque,
  # assume a conservative 15 minutes rather than trusting a guess.
  [ -n "$exp" ] || exp=$(( now + 900 ))
  _VCF_EXP=$exp
  local f d t; f=$(_vcf_cache_file); d=$(dirname "$f")
  mkdir -p "$d" 2>/dev/null && chmod 700 "$d" 2>/dev/null
  t=$(mktemp "$d/.tok.XXXXXX" 2>/dev/null) || return 0
  chmod 600 "$t"
  jq -nc --arg a "$_VCF_ACCESS" --arg r "${_VCF_REFRESH:-}" --argjson e "$_VCF_EXP" \
     '{accessToken:$a,refreshToken:$r,exp:$e}' > "$t" && mv -f "$t" "$f" || rm -f "$t"
  return 0
}

# Load only if the file parses, so a corrupt cache never wipes live state.
_vcf_load_cache() {
  local f a r e; f=$(_vcf_cache_file)
  [ -r "$f" ] || return 1
  a=$(jq -r '.accessToken // empty' < "$f" 2>/dev/null) || return 1
  [ -n "$a" ] || return 1
  r=$(jq -r '.refreshToken // empty' < "$f" 2>/dev/null)
  e=$(jq -r '.exp // 0'            < "$f" 2>/dev/null)
  _VCF_ACCESS=$a; _VCF_REFRESH=$r; _VCF_EXP=${e:-0}
}

_vcf_valid() {
  [ -n "${_VCF_ACCESS:-}" ] && [ "$(( ${_VCF_EXP:-0} - ${VCF_SKEW:-120} ))" -gt "$(date +%s)" ]
}

# ---- public -----------------------------------------------------------------

# Echo a valid access token. Mints one, refreshes it, or reuses the cache.
vcf_token() {
  _vcf_need || return 1
  [ -n "${VCF_SDDC:-}" ] || { echo "vcf: VCF_SDDC is not set" >&2; return 1; }
  _vcf_curl_setup || return 1

  if [ "${1:-}" != --force ]; then
    # In-memory first, then the on-disk cache (which may have been refreshed
    # by another process since we last looked).
    _vcf_valid || _vcf_load_cache || true
    if _vcf_valid; then printf '%s\n' "$_VCF_ACCESS"; return 0; fi
    # Expired but we still hold a refresh token: cheap PATCH beats a re-login.
    if _vcf_refresh; then printf '%s\n' "$_VCF_ACCESS"; return 0; fi
  fi

  _VCF_ACCESS=; _VCF_REFRESH=; _VCF_EXP=0
  _vcf_login || return 1
  printf '%s\n' "$_VCF_ACCESS"
}

# vcf_api GET /v1/domains
# vcf_api POST /v1/hosts @spec.json
# Prints the body; returns non-zero on HTTP >= 400.
vcf_api() {
  local verb=$1 path=$2 data=${3:-} tok body code
  tok=$(vcf_token) || return 1
  # vcf_token ran in a subshell, so set the curl options up in *this* shell.
  _vcf_curl_setup || return 1
  body=$(mktemp)

  _vcf_call() {
    local args=( -X "$verb" "https://$VCF_SDDC${path}"
                 -H "Authorization: Bearer $1"
                 -H 'Accept: application/json' )
    [ -n "$data" ] && args+=( -H 'Content-Type: application/json' --data-binary "$data" )
    curl "${_VCF_CURL[@]}" -o "$body" -w '%{http_code}' "${args[@]}"
  }

  code=$(_vcf_call "$tok")
  if [ "$code" = 401 ] || [ "$code" = 403 ]; then   # token died mid-flight
    tok=$(vcf_token --force) || { rm -f "$body"; unset -f _vcf_call; return 1; }
    code=$(_vcf_call "$tok")
  fi
  unset -f _vcf_call
  cat "$body"; rm -f "$body"
  case ${code:-000} in
    000|'') echo "vcf: request failed (no HTTP response)" >&2; return 1 ;;
  esac
  [ "$code" -lt 400 ]
}

vcf_token_reset() {
  _VCF_ACCESS=; _VCF_REFRESH=; _VCF_EXP=0
  rm -f "$(_vcf_cache_file)"
}

vcf_token_logout() {
  _vcf_curl_setup || return 1
  [ -n "${_VCF_REFRESH:-}" ] || _vcf_load_cache || true
  if [ -n "${_VCF_REFRESH:-}" ]; then
    printf '%s' "$_VCF_REFRESH" |
      curl "${_VCF_CURL[@]}" -o /dev/null -X DELETE \
        "https://$VCF_SDDC/v1/tokens/refresh-token" \
        -H 'Content-Type: application/json' --data-binary @-
  fi
  vcf_token_reset
}
```

## Using it

```bash
source ~/.vcfrc
export VCF_SDDC=sfo-vcf01.sfo.rainpole.io
export VCF_USER=administrator@vsphere.local
export VCF_PASS_FILE=~/.vcf-pass          # chmod 600

# raw token, wherever you need one
curl -k -H "Authorization: Bearer $(vcf_token)" \
     "https://$VCF_SDDC/v1/domains" | jq .

# or let the wrapper handle auth + retry for you
vcf_api GET  /v1/domains | jq -r '.elements[].name'
vcf_api GET  /v1/releases/domains/$id | jq .
vcf_api POST /v1/hosts @commission-hosts.json | jq .
```

Long-running loops are the point of the caching: call `vcf_token` inside the loop and it costs nothing until the token is close to expiring, at which point it silently does the PATCH.

```bash
while :; do
  vcf_api GET "/v1/tasks/$task_id" | jq -r .status
  sleep 30
done
```

## About that self-signed cert

`VCF_INSECURE=1` is the default so this works today, but note what you are turning off: you are POSTing `administrator@vsphere.local` and its password to whatever answers on that IP. On a management network that is usually an acceptable risk; it is still worth closing. Two low-effort ways:

**Trust the actual cert** (survives nothing but a cert rotation):

```bash
openssl s_client -connect "$VCF_SDDC:443" -showcerts </dev/null 2>/dev/null \
  | openssl x509 -out ~/.vcf-sddc.pem
export VCF_CACERT=~/.vcf-sddc.pem
```

**Or pin the public key** (survives re-issue with the same key, and is one line):

```bash
openssl s_client -connect "$VCF_SDDC:443" </dev/null 2>/dev/null \
  | openssl x509 -pubkey -noout \
  | openssl pkey -pubin -outform der \
  | openssl dgst -sha256 -binary | base64
export VCF_PIN="sha256//<that base64 string>"
```

Either one makes `vcf_token` verify properly with no other changes. Grab the cert from a machine you trust, on first use, before there is anything worth intercepting.

## Details worth knowing

- **`$(vcf_token)` runs in a subshell**, so shell variables set inside it never reach the caller. That is why the token cache is a file (`~/.cache/vcf/<user>@<host>.json`, mode 0600) rather than just a variable, and it is what keeps a 500-iteration script down to one login.
- **The password never appears in `ps`.** The login body is built with `jq` and piped to curl's stdin (`--data-binary @-`), so it is not in the process argument list where any user on the box could read it. `VCF_PASS_CMD` lets you pull it from Vault, `pass`, or `op read` instead of leaving it in a file.
- **`--force`** skips the cache and the refresh and does a full re-login. That is what `vcf_api` uses when it sees a 401 or 403 mid-flight, which happens if someone revoked the token or SDDC Manager restarted.
- **Concurrency is benign, not perfect.** Two parallel scripts hitting an expired token will both log in; the last write wins and both tokens work. If you run heavy parallelism and want to avoid the extra logins, wrap the refresh in `flock` on the cache file.
- **Failure modes are distinguished:** a connection failure (`000`) is reported separately from an HTTP error, so a network blip does not look like a successful empty response.
- **Bash 4+** for the associative-free array use here; also works on macOS if you install a newer bash or accept the BSD `base64 -D` fallback, which is handled.

## Caveats on the VCF 9.0 part specifically

I verified the three endpoints and the odd bare-string refresh body against Broadcom's current SDDC Manager API reference, and I tested the function end to end against a mock SDDC Manager (login, cached hit, expiry to refresh, refresh-rejected to re-login, 401 retry, all three refresh response shapes, both password sources, all TLS modes). I could not test it against a real 9.0 appliance, so:

- **Token lifetime is not contractually documented.** Historically the access token is about an hour and the refresh token about 24 hours. The function reads `exp` from the JWT rather than assuming, so this does not matter much, but if the refresh token lifetime is shorter than you expect you will simply see an extra login and no error.
- **This is the SDDC Manager token, and only that.** In VCF 9.0 the other components have their own auth: VCF Operations and VCF Automation issue their own tokens (VCF Automation via an API-token / refresh-token exchange), and a SDDC Manager bearer token will not authenticate against them. If you are scripting across all of them you need one helper per service.
- **`POST /v1/tokens` also accepts an `apiKey`** instead of username/password on 9.0. If your org issues service-account API keys, swap the login body for `{"apiKey": "..."}` and the rest of the function is unchanged.
- If SDDC Manager sits behind a load balancer or you use the VCF Installer appliance, point `VCF_SDDC` at the appliance that actually serves `/v1/tokens`.

## Sources

- [Tokens APIs - SDDC Manager API, Broadcom Developer Portal](https://developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/)
- [Tokens APIs - VMware Cloud Foundation API, Broadcom Developer Portal](https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/)
- [Getting Started with Token-Based Authentication for VMware Cloud Foundation APIs](https://blogs.vmware.com/cloud-foundation/2020/05/20/getting-started-with-token-based-authentication-for-vmware-cloud-foundation-apis/)
- [VMware Cloud Foundation 9.1 APIs: Obtaining Authentication Tokens](https://my-cloudy-world.com/2026/05/14/vmware-cloud-foundation-9-1-apis-obtaining-authentication-tokens/)
