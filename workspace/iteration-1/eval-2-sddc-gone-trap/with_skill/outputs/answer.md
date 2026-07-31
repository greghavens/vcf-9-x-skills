# Short answer: no, on both counts

Two things in that question need correcting before the rest of the answer is any use, because
everything downstream inherits the error.

**1. There is no product called "VCF Fleet Manager."** It does not appear anywhere in the 9.1
documentation, and it never existed as a product name. What you are half-remembering is the 9.0
component **VCF Operations fleet management** — a standalone appliance with its own BOM row
(`9.0.0.0`, build `24695816`). That appliance *was* eliminated in 9.1, which is probably where the
confusion started:

> "The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by
> fleet lifecycle" — 9.1 What's New, VCF Operations

> "completely replaces the standalone Fleet Management Appliance introduced in version 9.0. It is
> replaced with two new services — Fleet Lifecycle and SDDC Lifecycle — which run natively within
> VCF Management Services." — Broadcom KB 440630

So the thing that disappeared in 9.1 is the **fleet management appliance**, not SDDC Manager. The
9.1 nouns you want are **fleet lifecycle** and **SDDC lifecycle**, two services running inside
**VCF Management Services**, fronted by the VCF Operations UI and API. "Fleet Management" survives
only as a documentation section heading and a UI feature grouping.

**2. SDDC Manager was not removed in 9.1. Only its UI is deprecated.** This is the one that will
actually cost you if you architect around it:

- It is in the 9.1 BOM, merged with VCF Installer into a single row:
  `VCF Installer/SDDC Manager 9.1.0.0 (25371088)`.
- Its documented 9.1 role is unchanged in substance: lifecycle management for ESX, vCenter, HCX and
  NSX; workload-domain deployment; vCenter import; vSAN stretched-cluster configuration.
- It **drives the first half of the 9.0.x → 9.1 upgrade itself**, up to and including its own
  self-upgrade.
- Its scale went *up*: 5000 hosts per VCF instance (2x over 9.0) and 256 simultaneous cluster
  upgrades.

What is actually deprecated, precisely:

> "The SDDC Manager UI is being deprecated and will be removed in a future release. After your
> upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management activities."

That sentence scopes the deprecation to the **UI**. No 9.1 page states the SDDC Manager **API** is
deprecated — and the machine-computed diff of the published OpenAPI specs (git tags `9.0.0.0` and
`9.1.0.0` of `github.com/vmware/vcf-api-specs`) says the opposite:

| Product | 9.0 ops | 9.1 ops | added | removed | newly deprecated |
|---|---|---|---|---|---|
| `sddc-manager` | 375 | **423** | 48 | **0** | 21 |

Zero operations removed. Forty-eight added. If you write SDDC Manager out of your 9.1 design, you
are designing around an API that is not only still present but larger than it was.

---

## What to call for lifecycle management in 9.1

There are now **three** API surfaces, and which one you call depends on *what you are managing*.
They are separate services with separate base paths, separate auth, and separate task namespaces.

| What you are doing | Call |
|---|---|
| Lifecycle of the **management components** (identity broker, VCF Operations, Ops for networks, real-time metrics, Salt master/RaaS, VCF Automation, telemetry, SDDC lifecycle, software depot, log management, VCF services runtime) | **fleet lifecycle** — `/fleet-lcm` (51 ops) |
| Install / update / patch **within a single VCF instance** | **SDDC lifecycle** — `/sddc-lcm` (26 ops) |
| Workload-domain deployment, vCenter import, vSAN stretched clusters, and LCM of **ESX, vCenter, HCX, NSX** | **SDDC Manager** — `/v1` (423 ops) |
| Binary/image store behind all of the above | **software depot** (new BOM component, `9.1.0.0` build `25371105`) |
| The UI for all of it | **VCF Operations** |

The anchoring statement from the 9.1 docs: *"VCF Operations now uses the fleet lifecycle, SDDC
lifecycle, and software depot components to orchestrate lifecycle operations on both fleet and
instance-level components."*

Both `fleet-lcm` and `sddc-lcm` are genuinely new — neither exists at the `9.0.0.0` spec tag. That
version split is the real architectural change, and it is the useful thing to take away from
whatever you read that produced "Fleet Manager."

### The core new workflow — fleet lifecycle upgrade plans

All spec-confirmed at 9.1. Canonical order is **validate → create → configure → precheck → apply →
poll**:

```
POST /fleet-lcm/v1/upgrade-plans/validations          validate before creating
POST /fleet-lcm/v1/upgrade-plans                      create a plan
GET  /fleet-lcm/v1/upgrade-plans/{planId}
GET  /fleet-lcm/v1/upgrade-plans/{planId}/bundles     bundles the plan needs
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=configure
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=apply
```

Supporting calls you will want alongside it:

```
GET  /fleet-lcm/v1/release-versions
GET  /fleet-lcm/v1/release-versions/target-versions
POST /fleet-lcm/v1/depot-metadata?action=sync
GET  /fleet-lcm/v1/health
GET|PATCH|POST /fleet-lcm/v1/components/{componentId}
GET|PATCH|POST /fleet-lcm/v1/sddc-lcms          register/refresh instance-level LCM
POST /fleet-lcm/v1/system                       fleet lifecycle self-upgrade
```

SDDC lifecycle has **no upgrade-plan resource** — planning lives on fleet lifecycle, which registers
and refreshes SDDC LCM instances via `/fleet-lcm/v1/sddc-lcms`. What `/sddc-lcm` gives you is the
instance-level component and depot surface:

```
GET|POST /sddc-lcm/v1/components        GET|PATCH|POST /sddc-lcm/v1/components/{componentId}
POST /sddc-lcm/v1/depot                 set the depot for this instance
POST /sddc-lcm/v1/depot/components      resolve components against it
GET  /sddc-lcm/v1/health
POST /sddc-lcm/v1/nodes                 PATCH /sddc-lcm/v1/nodes/{nodeId}/config
```

### SDDC Manager calls that are still correct in 9.1

Everything you already use for bundles, depot settings, manifests, releases, compatibility
matrices, personalities, repository images, upgradables, upgrades and tasks still resolves. Notable
9.1 *additions* on SDDC Manager:

```
GET  /v1/upgradables/domains/{domainId}/upgrade-sequences
GET  /v1/upgradables/domains/{domainId}/vcenter-sizing-infos
GET  /v1/upgradables/domains/{domainId}/vcenter-upgrade-mechanisms     RDU is the default
GET  /v1/version-drift
GET  /v1/system/settings/depot/machine-details
POST /v1/system/check-sets/{runId}/exports  (+ GET .../exports, .../exports/data)   CSV export
POST /v1/vcf-management-components/resources-calculation
POST /v1/vcf-management-components/passwords
POST /v1/vcf-management-components/vcfops-discovery
POST /v1/clusters/{clusterId}/remediations  (+ GET .../remediations/{remediationId})
GET|POST|DELETE /v1/domains/{domainId}/hcx-managers[...]
```

### Prechecks moved — this is the trap inside the trap

The SDDC Manager upgrade-precheck pair is **now deprecated in 9.1** (spec-confirmed; it was not
deprecated in 9.0):

```
POST /v1/upgrades/{upgradeId}/prechecks                    DEPRECATED in 9.1
GET  /v1/upgrades/{upgradeId}/prechecks/{precheckId}       DEPRECATED in 9.1
```

They still exist and still resolve — nothing was removed — but new automation should target
`POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck`. SDDC Manager's `check-sets` family
survives, is *not* deprecated, and gained the CSV export operations above. Note the prose summary of
the "21 deprecated APIs" mentions edge clusters, domain overlays and DNS/NTP but omits the upgrade
prechecks, even though they are two of the 21 — trust the spec here.

### Task polling: three namespaces, and they don't cross

```
SDDC Manager:     GET /v1/tasks   GET /v1/tasks/{id}   PATCH /v1/tasks/{id}   DELETE /v1/tasks/{id}
fleet lifecycle:  GET /fleet-lcm/v1/tasks/{taskId}   POST /fleet-lcm/v1/tasks/{taskId}?action=cancel|retry
SDDC lifecycle:   GET /sddc-lcm/v1/tasks/{taskId}    POST /sddc-lcm/v1/tasks/{taskId}?action=cancel|retry
```

A task ID from one service is not resolvable on another. Poll the service that started the work —
polling the wrong one returns nothing and reads exactly like a stalled upgrade. Note also that the
LCM services use `?action=` query verbs for cancel/retry while SDDC Manager uses `DELETE`/`PATCH` on
the task resource.

### Auth: three surfaces, three credentials, no shared tokens

| Surface | Base | Scheme | How to get it |
|---|---|---|---|
| SDDC Manager | `https://<sddc-manager-fqdn>/v1` | `Authorization: Bearer <accessToken>` | `POST /v1/tokens`; refresh via `PATCH /v1/tokens/access-token/refresh`; access token 1 h, refresh 24 h. **Unchanged from 9.0.** |
| VCF Operations | `https://<vcfops-fqdn>/suite-api` | `Authorization: OpsToken <token>` | `POST /suite-api/api/auth/token/acquire`. 9.1 also accepts an identity-broker Bearer token and adds `POST .../token/exchange`. |
| fleet lifecycle / SDDC lifecycle | `https://<host>/fleet-lcm`, `/sddc-lcm` | `fleet-lcm`: basic **or** Bearer JWT. `sddc-lcm`: Bearer JWT only. | **See the warning below.** |

**SDDC Manager is excluded from VCF SSO** — do not present an identity-broker (VIDB) token to it.
That is constant across 9.0 and 9.1.

---

## Three things to close before you build against this

**1. fleet-lcm / sddc-lcm token acquisition is not documented — UNVERIFIED, and it is blocking.**
The specs declare which schemes are *accepted*, but neither spec contains a token-issuing operation:
there is no `/fleet-lcm/v1/tokens`, no `/sddc-lcm/v1/tokens`, and zero operations whose path
contains `token`, `auth` or `login` in either inventory. Where the JWT comes from — identity broker,
VCF Operations, or a local appliance account — is not established by any source I have. The 9.0
fleet-management Basic-auth pattern (`admin@local:<password>` base64, KB 409715) authenticated an
appliance that no longer exists in 9.1, so do not assume it carries forward. Establish and test this
credential path against a real 9.1 system before you depend on it. Discovering it at the
`?action=apply` step, mid-upgrade, is the worst possible time.

**2. The role required for lifecycle write operations is not documented — UNVERIFIED.** No source I
have names SDDC Manager role names at all, and since SDDC Manager is outside VCF SSO the 9.1
built-in roles (VCF Administrator, VCF Viewer, SDDC Administrator, SDDC Viewer) do not govern it —
that mapping covers vCenter, NSX, VCF Operations, VCF Automation, HCX and Orchestrator only. Do not
assume a token that can read `GET /v1/upgradables` can also submit `POST /v1/upgrades`, and do not
invent a role name for a service-account request. Confirm against Broadcom's role docs or
empirically on a non-production instance.

**3. OAuth clients do not survive the vIDM → identity broker migration.** Verbatim: *"OAuth clients
are not migrated automatically. You must manually regenerate the client and secret using identity
broker and configure accordingly."* Local accounts, local-account MFA and AD MFA are not supported
by the migration either. This is the prerequisite most likely to be missed, because it breaks
automation *after* the change window closes, when nobody is looking for it. Inventory every OAuth
client and every script holding a secret before you migrate.

Also worth knowing if you have automation in the blast radius: the **entire `/hvc/*` Hybrid Linked
Mode tree (9 operations) was removed** from vCenter between 9.0 and 9.1 — the largest hard API
breakage in the delta, and the only meaningful removal anywhere. Whether existing HLM links keep
working after upgrade, and what replaces them, is not documented anywhere I can see. If you use HLM,
resolve that before upgrading.

---

## If you are heading toward a 9.0 → 9.1 upgrade

The structural fact worth internalising, which also settles the SDDC Manager question for good: the
upgrade **pivots at order 6**. SDDC Manager drives orders 0–6 (identity-broker network transition,
VCF Operations + cloud proxy, then its own self-upgrade). VCF Operations drives orders 6–23 (deploy
VCF Management Services + License Server, licence transfer, identity broker, VCF Automation, then
NSX / vCenter / ESX / vSAN / Tools). A product that is "gone" does not drive the first half of its
own successor's upgrade.

A few gates that catch people:

- **Every workload domain must be at VCF 5.2 or later** before the 9.1 upgrade. Below 5.2, go to 5.2
  first. Supported sources overall are VCF 5.2.x or 9.0.x.
- **VCF Operations and SDDC Manager must both already be at 9.1** before VCF Management Services can
  be deployed.
- **A License server is new and required** in 9.1 — licences moved out of VCF Operations, and there
  is an explicit licence-transfer step in the sequence.
- **NSX Edge clusters are now upgraded at the end** of the domain upgrade. If you carry a 9.0-era
  mental model, correct it.

One caveat on sourcing: orders 2–5 and 9–23 are collapsed into ranges in the published upgrade
guide, so the exact intra-range ordering is not verified. The shape of the sequence is solid; don't
let anyone fabricate the individual steps inside those ranges.

---

## Sourcing note

All of this traces to Broadcom documentation and to the published VCF OpenAPI specifications
(captured 2026-07-31); none of it has been executed against a live VCF deployment. The operation
counts and deprecation flags above are machine-computed from the `9.0.0.0` and `9.1.0.0` git tags of
`github.com/vmware/vcf-api-specs` and I re-verified them directly while writing this: `fleet-lcm` 51
ops, `sddc-lcm` 26 ops, `sddc-manager` 375 → 423. Items marked UNVERIFIED are genuine gaps, not
hedging — treat them as work to do, and validate any upgrade sequence against Broadcom's docs for
your exact build before anyone runs it.

One last thing to expect: a 9.1 techdocs page still describes the SDDC Manager API as "~280 REST
interfaces" and labels it "SDDC Manager (fleet management)". Both the count and that parenthetical
are stale. The count is 423, and that label is very likely the original source of the "Fleet
Manager" idea. Don't let it pull you back in.
