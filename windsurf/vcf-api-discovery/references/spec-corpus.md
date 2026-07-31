# Spec corpus — the primary lookup route

**Use this first.** Before fetching any documentation page, answer the question from the OpenAPI
specifications themselves. They are the only source that is both complete and version-exact.

**Start at §3.** A pre-extracted operation inventory for both versions **is bundled with this
skill** at `references/spec-inventory/`, and `scripts/find_operation.py` reads it by default from
any working directory. For the common question — *does this operation exist in this version, and
what is its method and path* — **you do not need to clone anything**. Clone the repository (§1)
when you need what the inventory deliberately does not carry: request/response schemas, parameter
details, enums, examples.

---

## 1. The repository and its git tags — the authoritative fallback

```
https://github.com/vmware/vcf-api-specs
```

"API specifications for the VMware VCF products." Specs live under `/specifications`, organized by
component; `/scripts` holds example build scripts for generating language bindings.

**The repository carries git tags per VCF release.** Two are relevant:

| Tag | VCF version | Tag commit date |
|---|---|---|
| `9.0.0.0` | VCF 9.0 | 2025-06-18 |
| `9.1.0.0` | VCF 9.1 | 2026-05-13 |

**This is the single most important fact in this file.** A version-scoped API question ("does this
endpoint exist in 9.0?", "what changed in 9.1?") is answered against the matching tag — not
against `main`, and not from a doc page that may or may not be version-pinned. The bundled
inventory (§3) is itself extracted from these two tags, which is why it can answer the
existence-and-path question without a clone.

Clone when you need **schema-level detail** the inventory does not carry — a request body, an
enum, a parameter list, a response shape — or when you need a product/version the extraction did
not capture:

```bash
git clone https://github.com/vmware/vcf-api-specs /tmp/vcf-api-specs
git -C /tmp/vcf-api-specs checkout 9.1.0.0      # or 9.0.0.0

# Or, for a second worktree so both versions are on disk at once:
git -C /tmp/vcf-api-specs worktree add /tmp/vcf-specs-90 9.0.0.0
```

`main` is *not* a version. Never answer "is X in 9.0" from an untagged checkout, and never answer it
from the 9.1 tag on the assumption that the surface is stable — it is not (see §4).

**Second channel (same content, no tags):** the developer-portal ZIP at
`https://developer.broadcom.com/sdks/vcf-api-specification/latest` — 9.1 artifact
`vcf-api-specs-9.1.0.0-25372366.zip` (~39 MB), covering eight products. Use the ZIP only when git is
unavailable; the tagged repo is strictly better because it gives you both versions and a diff.
(A 9.0-equivalent ZIP filename was not verified during research — only `latest` = 9.1 was retrieved.)

---

## 2. Per-product spec map — both versions

Base paths and operation counts below are machine-extracted from the two tags. Counts are
*spec operations* (method + path pairs), not doc pages.

### VCF 9.1 (tag `9.1.0.0`) — 14 specs, 11,590 operations

| Product key | Spec file (under repo root) | OpenAPI | Base path | Ops |
|---|---|---|---|---|
| `sddc-manager` | `specifications/sddc-manager/sddc-manager-openapi.json` | 3.0.1 | `http://localhost:80` | 423 |
| `vcf-installer` | `specifications/vcf-installer/vcf-installer-openapi.json` | 3.0.1 | `http://localhost:80` | 57 |
| `vcf-operations` | `specifications/vcf-operations/vcf-operations-openapi.json` | 3.0.1 | `/suite-api` | 504 |
| `log-management` | `specifications/vcf-operations/log-management-openapi.json` | 3.0.1 | `http://localhost:8787` | 23 |
| `vcf-operations-for-networks` | `specifications/vcf-operations/vcf-operations-for-networks-openapi.yaml` | 3.0.1 | `/api/ni` | 636 |
| `realtime-metrics` | `specifications/vcf-operations/realtime-metrics/realtime-metrics-openapi.yaml` | 3.0.2 | `http://localhost:8080/` | 4 |
| `fleet-lcm` | `specifications/fleet-lcm/fleet-lcm-openapi.yaml` | 3.0.4 | `https://vcf.broadcom.com/fleet-lcm` | 51 |
| `sddc-lcm` | `specifications/sddc-lcm/sddc-lcm-openapi.yaml` | 3.0.4 | `https://vcf.broadcom.com/sddc-lcm` | 26 |
| `vsphere-automation` | `specifications/vsphere/openapi/automation/vcenter.yaml` | 3.0.3 | `https://{host}/api` | 1367 |
| `vsphere-vi-json` | `specifications/vsphere/openapi/vi-json/vi-json.yaml` | 3.0.0 | `https://{vcenter-host}/sdk/vim25/{release}` | 2243 |
| `vsan-data-protection` | `specifications/vsan-data-protection/vsan-data-protection-openapi.yaml` | 3.0.3 | `https://{host}/api` | 65 |
| `nsx-policy` | `specifications/nsx/openapi-2.0/nsx_policy_api.yaml` | **2.0** | `/policy/api/v1` | 3729 |
| `nsx-manager` | `specifications/nsx/openapi-2.0/nsx_api.yaml` | **2.0** | `/api/v1` | 1453 |
| `nsx-global-policy` | `specifications/nsx/openapi-2.0/nsx_global_policy_api.yaml` | **2.0** | `/global-manager/api/v1` | 1009 |

### VCF 9.0 (tag `9.0.0.0`) — 8 specs, 5,083 operations

| Product key | Spec file (under repo root) | OpenAPI | Base path | Ops |
|---|---|---|---|---|
| `sddc-manager` | `specifications/sddc-manager/sddc-manager-openapi.json` | 3.0.1 | `http://localhost:80` | 375 |
| `vcf-installer` | `specifications/vcf-installer/vcf-installer-openapi.json` | 3.0.1 | `http://localhost:80` | 52 |
| `vcf-operations` | `specifications/vcf-operations/vcf-operations-openapi.json` | 3.0.1 | `/suite-api` | 370 |
| `vcf-operations-for-logs` | `specifications/vcf-operations/vcf-operations-for-logs-openapi.json` | 3.0.1 | `/api/v2` | 136 |
| `vcf-operations-for-networks` | `specifications/vcf-operations/vcf-operations-for-networks-openapi.yaml` | 3.0.1 | `/api/ni` | 632 |
| `vsphere-automation` | `specifications/vsphere/openapi/automation/vcenter.yaml` | 3.0.3 | `https://{host}/api` | 1275 |
| `vsphere-vi-json` | `specifications/vsphere/openapi/vi-json/vi-json.yaml` | 3.0.0 | `https://{vcenter-host}/sdk/vim25/{release}` | 2195 |
| `vsan-data-protection` | `specifications/vsan-data-protection/vsan-data-protection-openapi.yaml` | 3.0.3 | `https://{host}/api` | 48 |

**Base paths are what the spec declares, not necessarily what you call.** `http://localhost:80`
(SDDC Manager, VCF Installer) and `http://localhost:8787` (Log Management) are on-appliance loopback
defaults; substitute the appliance FQDN and HTTPS. `/suite-api`, `/api/ni`, `/policy/api/v1`,
`/api/v1` and `/global-manager/api/v1` are true path prefixes to append to the appliance URL.

**Legacy WSDL also lives here** for EAM, PBM, SMS, VIM (incl. vSAN), SSO client and VSLM under
`specifications/vsphere/wsdl/` in both tags. It is not in the extracted inventory — grep the WSDL/XSD
directly if a question is about a SOAP managed object.

---

## 3. The bundled inventory (start here)

The repo is large and the vSphere/NSX YAML files are megabytes. A machine-extracted operation
inventory for **both versions** is **bundled with this skill** — roughly 5 MB, already on disk,
no clone and no network required:

```
vcf-api-discovery/
    scripts/find_operation.py        # searches the inventory below by default
    references/spec-inventory/
        index.json                   # per-version, per-product: spec_file, openapi, base_path, ops, tags, security schemes
        SUMMARY.md                   # the two tables above, condensed
        DELTA-9.0-to-9.1.md          # added / removed / newly-deprecated per product
        9.0__<product>.ops.json      # 8 files  — {meta, operations[]}
        9.1__<product>.ops.json      # 14 files — {meta, operations[]}
```

That is 22 `*.ops.json` files covering all 16,673 operations across both tags. Each entry in
`operations[]` has `method`, `path`, `operationId`, `summary`, `tags`, `deprecated`. `meta`
repeats the product's `index.json` record, so every hit is traceable back to a spec file, an
OpenAPI version and a base path.

`find_operation.py` resolves `references/spec-inventory/` **relative to its own location**, so it
works unchanged from any working directory — you do not need to `cd` into the skill, and you do
not need to pass `--inventory` unless you are pointing it at a regenerated copy elsewhere.

### What the bundled inventory can and cannot answer

| It answers | It does not answer |
|---|---|
| *Does this operation exist at 9.0 / 9.1?* | *What fields does the request body take?* |
| *What is its method and path?* | *What are the valid enum values?* |
| *What is its `operationId`, `summary`, tags?* | *What query/path parameters does it accept, and which are required?* |
| *Is it marked `deprecated` in that version's spec?* | *What is the response shape?* |
| *Which product, spec file and base path does it belong to?* | *What does the auth flow actually look like end to end?* |
| *What was added / removed / newly deprecated between the tags?* | — |

**The extraction carries operations only — not schemas.** `components.schemas` /
`definitions`, `requestBody` contents, parameter objects and examples are **not** in these files.
The moment a question moves from *"does it exist and where"* to *"what goes in the body"*, the
inventory has nothing for you and the answer must come from the spec file itself at the matching
git tag (§1) — `meta.spec_file` in the hit tells you exactly which file to open. Never infer a
payload shape from an `operationId` or a `summary`.

**Search it with the bundled script, not with grep:**

```bash
python3 scripts/find_operation.py --version 9.1 "edge cluster"
python3 scripts/find_operation.py --version 9.0 --product sddc-manager --method POST upgrade
python3 scripts/find_operation.py --both-versions "depot"
python3 scripts/find_operation.py --list-products          # products, counts, base paths
```

Other flags: `--any` / `--regex` / `--case-sensitive` for match behaviour, `--no-deprecated` to hide
operations the spec marks deprecated (they are shown with a `[DEPRECATED]` tag by default),
`--limit N`, `--json`, `--inventory DIR`.

The script requires `--version` on purpose. Silently searching both versions is how a 9.1-only
endpoint ends up in a 9.0 answer.

If the inventory directory has been moved or deleted, regenerate it by cloning both tags and
walking the spec files (the script prints the exact instructions on failure), then point the script
at the result with `--inventory DIR`.

### Worked example — what the diff catches that prose does not

`DELTA-9.0-to-9.1.md` is not a convenience; it surfaces changes no release note mentioned. The
clearest case in this corpus:

> **`vsphere-automation` removed exactly nine operations between the two tags, and all nine are the
> `/hvc/*` Hybrid Linked Mode tree:** `GET|POST /hvc/links`, `GET|DELETE /hvc/links/{link}`,
> `POST /hvc/links/{link}?action=delete`, `GET|PUT /hvc/management/administrators`, and
> `POST /hvc/management/administrators?action=add|remove` (operationIds
> `Vcenter.Hvc.Links_*` and `Vcenter.Hvc.Management.Administrators_*`).

An entire capability was withdrawn. The product grew overall — 1275 → 1367 operations, 101 added —
so a headline count comparison hides it completely, and no "what's new" page enumerates removals.
Only a per-operation set difference between the two tags surfaces it. Of the seven products present
at both tags, only two remove anything at all (`vsphere-automation`: 9; `vcf-operations-for-networks`:
1) — so the removals section of the delta file is short enough to read in full every time, and worth
doing before you answer any "did this change in 9.1?" question. The lifecycle consequence is written
up in `../../vcf-lifecycle-upgrade/references/deltas.md`.

---

## 4. Products with no spec at 9.0 — read this before answering a 9.0 question

Seven product keys are **absent from the 9.0.0.0 tag** and present only at 9.1.0.0:

| Product | 9.1 ops | Why absent at 9.0 |
|---|---|---|
| `nsx-policy` | 3729 | NSX specs were not published in the 9.0 tag of this repo |
| `nsx-manager` | 1453 | same |
| `nsx-global-policy` | 1009 | same |
| `fleet-lcm` | 51 | service introduced/split out in 9.1 |
| `sddc-lcm` | 26 | service introduced/split out in 9.1 |
| `realtime-metrics` | 4 | new in 9.1 |
| `log-management` | 23 | new in 9.1 (replaces `vcf-operations-for-logs`) |

And one goes the other way: **`vcf-operations-for-logs` (136 ops, `/api/v2`) exists only at 9.0** and
is gone at 9.1, where `log-management` (`http://localhost:8787`) takes its place. These are different
specs with different base paths — do not treat a `for-logs` endpoint as valid on 9.1.

### What the absences mean for evidence quality

The three NSX absences are the ones that will bite. **NSX absolutely has a REST API in VCF 9.0** —
the 9.0 product documentation and the version-pinned 9.0.0 API reference both describe it in detail.
What is missing is the *spec file in this repo at that tag*. So:

- **Never say "NSX has no such API in 9.0" on the basis of a corpus miss.** The corpus simply has no
  NSX data at 9.0. The correct phrasing is: *"the 9.0 spec tag does not ship NSX specs; verified in
  the 9.1 spec and in the 9.0.0 NSX API reference."*
- For NSX at 9.0, downgrade the evidence route: pull the spec **from a running 9.0 NSX Manager**
  (`GET /api/v1/spec/openapi/nsx_policy_api.json` — see `live-discovery.md`), or use the
  version-pinned portal reference at
  `https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/`.
- For `fleet-lcm`, `sddc-lcm`, `realtime-metrics` and `log-management` the absence is *meaningful* —
  these services did not exist as separate APIs at 9.0, and the corresponding functionality lived in
  SDDC Manager or in `vcf-operations-for-logs`. Here a corpus miss is real evidence, but say why.

**General rule:** a miss in an *absent* product is "no evidence"; a miss in a *present* product is
"evidence of absence". Always state which of the two you are reporting.

---

## 5. The OpenAPI-version gotcha: NSX is 2.0, everything else is 3.0

Verbatim from the repository documentation:

> "NSX are OpenAPI 2.0 based unlike other VCF components which are based on OpenAPI 3.0."

Consequences, all of which change how you work with the file:

| | NSX (`nsx-policy`, `nsx-manager`, `nsx-global-policy`) | Everything else |
|---|---|---|
| Spec version | Swagger / OpenAPI **2.0** | OpenAPI **3.0.0 – 3.0.4** |
| Server/base URL key | `basePath` (+ `host`, `schemes`) | `servers[].url` |
| Request body | a parameter with `in: body` | top-level `requestBody` |
| Schema container | `definitions` | `components.schemas` |
| Content negotiation | `consumes` / `produces` at op or root | `content: {<media-type>: …}` per body/response |
| `$ref` targets | `#/definitions/Foo` | `#/components/schemas/Foo` |

Practical effects:

- **Code generation:** tell `openapi-generator` which spec version applies per component. A pipeline
  that assumes 3.0 across the board silently mis-generates the NSX clients (missing bodies, wrong
  base URL).
- **Validation/lint tooling:** 3.0-only validators reject the NSX files as invalid rather than as
  2.0. That rejection is not a defect in the spec.
- **Ad-hoc parsing:** any script that reads `servers[0].url` gets `None` for NSX; read `basePath`.
  The bundled inventory already normalizes this — `base_path` in `index.json` is correct for both
  flavours, which is another reason to query the inventory rather than the raw YAML.
- **Conversion:** if a uniform 3.0 corpus is needed, convert the NSX files (e.g. `swagger2openapi`)
  and note in the answer that the converted artifact is derived, not shipped.

Also note the NSX file layout is itself a signal: they sit under `specifications/nsx/openapi-2.0/`,
i.e. upstream has versioned the directory by spec flavour, leaving room for a future `openapi-3.0/`.

---

## 6. Suggested lookup order

1. `scripts/find_operation.py --version <v> <keyword>` against the extracted inventory.
2. If a hit needs schema detail (request body, enums, response shape): open the spec file named in
   `meta.spec_file` at the matching git tag.
3. If the product is absent at the requested version (§4): go to `live-discovery.md` (ask the
   appliance) or `doc-portal.md` (version-pinned reference), and label the evidence accordingly.
4. Cross-check version-sensitive claims against `DELTA-9.0-to-9.1.md` — it lists what was added,
   removed and newly deprecated per product, which is usually the real answer to "did this change?"
