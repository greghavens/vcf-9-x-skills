# vSphere inventory and VM lifecycle — VCF 9.1

**Applies to:** vCenter **9.1.0.0** (build 25370922) and ESX **9.1.0.0** (build 25370933),
the versions in the VCF 9.1 Bill of Materials.
**Do not apply this file to VCF 9.0.** Use `../9.0/inventory-and-vms.md` for 9.0 and
`../deltas.md` for the change list.

> **The hypervisor is called ESX in 9.1, not ESXi.** The BOM row is **"ESX"** and the 9.1
> vSphere what's-new page uses "ESX" throughout, not "ESXi". A formal "renamed from ESXi"
> statement was still not found in either doc set — `UNVERIFIED` — but the product name in
> 9.1 is unambiguous.

## Provenance of everything below

| Tag | Meaning |
|---|---|
| **[SPEC]** | The exact `method + path` was found in `research/spec-inventory/9.1__vsphere-automation.ops.json` — machine-extracted from `specifications/vsphere/openapi/automation/vcenter.yaml` at git tag `9.1.0.0` of `github.com/vmware/vcf-api-specs` (`info.version: 9.1.0.0`, `servers[0].url: https://{host}/api`, 1,367 operations). Schema and description quotes come from that same file. Strongest evidence available. |
| **[DOC]** | Verified only from version-pinned Broadcom prose (VCF 9.1 programming guide, 9.1 release notes, 9.1 product support notes). |
| **[INFERRED]** | Neither — a shape or convention, not a verified fact. Confirm before relying on it. |
| **`UNVERIFIED`** | The research could not establish it. Do not fill the gap by guessing. |

**Both 9.0 and 9.1 have a full machine-readable spec.** Unlike the NSX skill, there is no
evidence asymmetry to warn about here. A `[SPEC]` tag in this file is evidence about **9.1**;
the 9.0 file carries its own, independently extracted.

---

## Contents

- [Provenance](#provenance-of-everything-below)
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — reachable vCenter on 443, `/api` base path](#p1--you-can-reach-vcenter-on-443-and-you-are-using-the-api-base-path)
  - [P2 — **the federated-login gate (inherited from 9.0)**](#p2--your-credential-can-actually-create-a-session-the-90-gate-still-applies)
  - [P3 — a live session token](#p3--you-hold-a-live-session-token-and-send-it-on-every-call)
  - [P4 — the right per-object privileges](#p4--you-hold-the-right-privileges-on-the-right-objects)
  - [P5 — placement targets already exist](#p5--the-placement-targets-already-exist-resource-pool-folder-datastore-network)
  - [P6 — identifiers resolved, not constructed](#p6--you-resolved-identifiers-rather-than-constructing-them)
  - [P7 — list truncation understood](#p7--you-know-the-list-operations-truncate)
  - [P8 — power state matches the operation](#p8--the-vms-power-state-matches-the-operation-you-are-about-to-run)
- [Base path and API surfaces](#base-path-and-api-surfaces) — `/api`, deprecated `/rest`, VI-JSON
- [Session](#session) — **`/api/session`, not `/api/cis/session`**
- [Tasks and the `vmw-task=true` convention](#tasks-and-the-vmw-tasktrue-convention)
- [Inventory traversal](#inventory-traversal) — resolution order, endpoints, filters, enums
- [VM lifecycle](#vm-lifecycle) — create, clone, instant clone, relocate, register, delete
- [VM power](#vm-power)
- [VM reconfigure](#vm-reconfigure)
- [**Worked example** — clone a VM from a template](#worked-example--clone-a-vm-from-a-template-in-inventory) (Steps 0–7 + [failure decode](#failure-decode-for-this-sequence))
- [**What 9.1 adds and removes in this scope**](#what-91-adds-and-removes-in-this-scope) — incl. the **`/hvc/*` Hybrid Linked Mode removal**
- [Out of scope — where to route instead](#out-of-scope--where-to-route-instead)
- [What is unverified for 9.1](#what-is-unverified-for-91)

---

## Prerequisites

Everything here must be true **before** you issue any inventory or VM call. Each item
carries four elements — if one is missing the item is incomplete:

1. **What must be true.**
2. **How to verify it** — a concrete, *non-destructive* check. Never verify a privilege by
   performing the production change it guards.
3. **Which version it applies to** — every item applies to **vCenter 9.1.0.0** unless said
   otherwise.
4. **Whether it exists in 9.0** — stated as a "9.0 difference" line on every item.

### P1 — You can reach vCenter on 443, and you are using the `/api` base path

- **Must be true:** an `https://<vcenter>` endpoint on port **443**, its certificate chain
  in your trust store, and every request under **`/api`**. Verbatim from the VCF 9.1
  programming guide: *"All existing and non-deprecated HTTP operations of the VMware Cloud
  Foundation API are available on port 443 and the `/api` base path."* **[DOC]** The spec
  agrees: `servers[0].url` is `https://{host}/api`. **[SPEC]**
- **`/rest` is deprecated and incomplete.** *"The APIs released up to vSphere version 7.0.2
  are also available on the deprecated `/rest` base path"*, and *"the `/api` base path will
  remain the only active base path when the `/rest` base path is removed in a future
  vSphere release."* **[DOC]** Consequence: **every operation introduced after vSphere
  7.0.2 is `/api`-only.** A `/rest` client does not fail cleanly — the old half of it keeps
  working while new calls 404.
- **A separate subset lives on port 5480** (appliance configuration and lifecycle). **[DOC]**
  Not used by anything in this file.
- **Verify:** `curl -sS -o /dev/null -w '%{http_code}\n' -u '<user>' https://<vcenter>/api/session -X POST`
  without `-k`. A TLS error is a trust-store problem, not an endpoint problem. A 401 means
  you reached the right place — go to P2.
- **9.0 difference:** none. The 9.0 programming guide carries the identical wording and the
  9.0 spec declares the same `servers[0].url`. `/rest` was already deprecated at 9.0 and is
  still not removed at 9.1.

### P2 — Your credential can actually create a session (the 9.0 gate still applies)

- **Must be true:** the identity you are authenticating with is acceptable to a vCenter
  that **blocks non-federated username/password logins**. This was introduced in 9.0 and
  carries forward. Verbatim from the VCF **9.0** product support notes, under removals:
  *"Blocked non-federated username/password logins to vCenter: vCenter 9.0 blocks logins
  with just a user name and password, which might sometimes allow bypassing the federated
  provider domain."* **[DOC]**
- **Evidence caveat, stated plainly.** The **9.1** product support notes do **not** restate
  this. A removal in 9.0 does not un-remove itself in 9.1, so the working assumption is that
  the gate still applies — but the *only* verbatim source for it is a 9.0-pinned page.
  If a change record needs a 9.1 citation for this, there isn't one; say so.
- **Why it is a prerequisite and not a footnote:** on a federated deployment, a plain local
  credential returns 401 from `POST /api/session` — the same response as a wrong password,
  a locked account, or a typo in the username. Teams lose hours to this because the error
  surface gives them nothing to distinguish it.
- **The spec's own signal.** The 9.1 spec declares three security schemes **[SPEC]**:
  | Scheme | Type | Notes |
  |---|---|---|
  | `basic_auth` | `http` / `basic` | The scheme declared on `POST /session`. |
  | `api_key_auth` | `apiKey`, header **`vmware-api-session-id`** | Declared on every other operation. |
  | `federated_identity_auth` | `http` / `bearer` | Description, verbatim: *"If your vCenter Server is federated with an external identity provider, please see: VMware Identity Broker - vCenter Server Workflows."* |
  The presence of `federated_identity_auth` is the spec-level trace of the same fact.
- **Verify — before writing any client.** Establish the identity source first, then probe:
  `POST https://<vcenter>/api/session` with HTTP Basic. **201** and a token means you are
  through. **401** with a credential you are confident in means the gate, not the password —
  route to `vcf-foundation` for the federated flow. Do not brute-force variations of the
  username; each attempt counts against lockout policy.
- **Also removed at 9.0, same page, same blast radius [DOC]:** Integrated Windows
  Authentication (IWA), SSPI, smart card and RSA SecurID. A client that relied on one of
  those has been dead since 9.0, not degraded.
- **9.1 adds OAuth 2.0 token support** to vCenter, per the 9.1 release notes **[DOC]** —
  and VCF PowerCLI 9.1 gains OAuth authentication cmdlet support. Read that as the
  *supported route around* the gate, not as its removal.
  **Careful with what the spec shows, though:** `POST /api/vcenter/authentication/token`
  (`Vcenter.Authentication.Token_issue`, RFC 8693 token exchange) is present at **both**
  the 9.0 and 9.1 tags, and its own description says *"This operation was added in vSphere
  API 7.0.2.0."* **[SPEC]** So the 9.1 "OAuth 2.0 token support" claim is about product
  capability, **not** a new endpoint — do not tell anyone the token endpoint is new in 9.1.
  See `../deltas.md`.
- **9.0 difference:** the gate originates in 9.0 and the verbatim statement is on the
  9.0-pinned page. What is genuinely new at 9.1 is the OAuth 2.0 support above, plus
  `POST /api/vcenter/registered-tokens` (`Vcenter.RegisteredTokens_create`, **9.1-only**
  **[SPEC]**) for the overflow/expanded access-token pairing — see the 9.1 additions
  section below. Credential acquisition itself remains `vcf-foundation`'s scope.

### P3 — You hold a live session token and send it on every call

- **Must be true:** the `vmware-api-session-id` header on every request after
  `POST /api/session`. The spec declares `api_key_auth` (apiKey, header
  `vmware-api-session-id`) as the security scheme on essentially every operation in this
  file. **[SPEC]**
- **Verify:** `GET /api/session` **[SPEC — `Cis.Session_get`]** returns 200 and a
  `Cis.Session.Info` body for a valid token, 401 for a missing or dead one. The spec notes
  a side effect: *"A side effect of invoking this operation may be a change to the
  session's last accessed time."* — so it is also a keepalive. Use it as your liveness
  probe rather than a real inventory call.
- **Session idle timeout is not stated in the spec** and no 9.0 page retrieved gives a
  number. `UNVERIFIED`. Build the client to re-authenticate on 401 rather than to a
  presumed lifetime.
- **9.0 difference:** none. Identical three operations, identical header.

### P4 — You hold the right privileges, on the right objects

- **Must be true:** vSphere privileges are **per-object**, and the spec names them per
  operation. Holding one does not imply the others. Verbatim from the 9.0 spec **[SPEC]**:

  | Operation | Privileges required, per the spec's own description |
  |---|---|
  | `Vcenter.VM_create` | `VirtualMachine.Inventory.Create` on the **folder**; `Resource.AssignVMToPool` on the **resource pool**; `Datastore.AllocateSpace` on the **datastore**; `Network.Assign` on the **network** |
  | `Vcenter.VM_clone` | `VirtualMachine.Provisioning.Clone` on the **source VM**; `VirtualMachine.Inventory.CreateFromExisting` on the target **folder**; `Resource.AssignVMToPool` on the target **resource pool**; `Datastore.AllocateSpace` on the target **datastore(s)** |
  | `Vcenter.VM_instantClone` | `VirtualMachine.Provisioning.Clone` **and** `VirtualMachine.Inventory.CreateFromExisting` on the source; `VirtualMachine.Interact.PowerOn` on the target folder |
  | `Vcenter.VM_delete` | `VirtualMachine.Inventory.Delete` on the **VM** |
  | `Vcenter.VM_relocate` | `Resource.ColdMigrate` on the **VM**; `Resource.AssignVMToPool` on the target **resource pool** |
  | `Vcenter.VM_register` | `VirtualMachine.Inventory.Register` on the folder; `System.Read` on the datastore |
  | `Vcenter.VM_unregister` | `VirtualMachine.Inventory.Unregister` on the VM |
  | `Vcenter.Vm.Power_start` / `_stop` / `_suspend` / `_reset` | `VirtualMachine.Interact.PowerOn` / `.PowerOff` / `.Suspend` / `.Reset` on the VM |
  | `Vcenter.ResourcePool_create` | `Resource.CreatePool` on the **parent** resource pool |

- **Verify — read, do not test by writing.**
  - `GET /api/vcenter/authorization/privileges` **[SPEC — `Vcenter.Authorization.Privileges_list`]**
    and `GET /api/vcenter/authorization/privileges/{privilege}` **[SPEC — `..._get`]** enumerate
    what exists.
  - `GET /api/vcenter/authorization/roles` / `GET .../roles/{role}` **[SPEC —
    `Vcenter.Authorization.Roles_list` / `_get`]** show what a role grants.
  - `POST /api/vcenter/authorization/permissions?action=list` **[SPEC —
    `Vcenter.Authorization.Permissions_list`]** — *"Queries the authorization permissions in
    the vCenter Server matching given criteria"*, added in vSphere API 9.0.0.0. This is the
    direct answer to "does this principal hold that privilege on that object".
  - For a live trace of what a call actually checked:
    `POST /api/vcenter/authorization/privilege-checks?action=list` **[SPEC —
    `Vcenter.Authorization.PrivilegeChecks_list`]** and
    `GET /api/vcenter/authorization/privilege-checks/latest` **[SPEC — `...Latest_get`]**.
    Both require the `Sessions.CollectPrivilegeChecks` privilege themselves.
  - **Do not verify write privilege by attempting the production write.** If you want a
    live probe, do it against a throwaway object — a scratch resource pool you then delete —
    never against the target VM.
- **9.0 difference:** none that matters. The privilege strings and the whole
  `/vcenter/authorization` operation set are identical at both tags (18 operations each),
  and **no operation in this file's scope was newly deprecated at 9.1** — of the 28 newly
  deprecated operations in the 9.1 spec, all 28 are under `/vcenter/namespace-management`,
  `/vcenter/namespaces` or `/appliance/health`. **[SPEC]**

### P5 — The placement targets already exist (resource pool, folder, datastore, network)

- **Must be true:** `Vcenter.VM_create` accepts a `placement` object and **creates none of
  its targets for you**. Before the create you need:
  - a **resource pool** (or a standalone **host**, or a **cluster** — see the placement rules
    below),
  - a **folder** of type `VIRTUAL_MACHINE`,
  - a **datastore** with space,
  - a **network** for each vNIC.
- **The placement rules are spec-stated and easy to get wrong.** From
  `Vcenter.VM.ClonePlacementSpec` **[SPEC]**, verbatim: *"If host and resource_pool are both
  specified, resource_pool must belong to host. If host and cluster are both specified,
  host must be a member of cluster."* And: *"if resource_pool is set, and the target is a
  DRS cluster, a host will be picked by DRS. if resource_pool is set, and the target is a
  cluster without DRS, InvalidArgument will be thrown."* A non-DRS cluster therefore
  **requires** an explicit `host`.
- **`Vcenter.VM.CloneSpec.placement` is optional**, and omitting it inherits the source VM's
  placement: *"If this property is missing or `null`, the system will use the values from
  the source virtual machine."* That is convenient and it is also how a clone silently
  lands on the wrong datastore. Be explicit.
- **Verify:** one `GET` per target, capturing the returned identifier —
  `GET /api/vcenter/resource-pool?names=<n>`, `GET /api/vcenter/folder?type=VIRTUAL_MACHINE&names=<n>`,
  `GET /api/vcenter/datastore?names=<n>`, `GET /api/vcenter/network?names=<n>`. A zero-length
  array is the failure; treat it as fatal before the create rather than after.
- **9.0 difference:** none. `Vcenter.VM.CreateSpec`, `Vcenter.VM.PlacementSpec`,
  `Vcenter.VM.CloneSpec` and `Vcenter.VM.ClonePlacementSpec` have byte-identical property
  sets and required lists at both tags.

### P6 — You resolved identifiers rather than constructing them

- **Must be true:** every `folder`, `resource_pool`, `datastore`, `host`, `cluster`,
  `network`, `vm` value is a vCenter managed-object identifier — `group-v42`, `resgroup-8`,
  `datastore-15`, `vm-101` — not a display name and not a path. The spec states the resource
  type for each field, e.g. *"the property must be an identifier for the resource type:
  `ResourcePool`"*. **[SPEC]** There is no name-based form of these fields.
- **Verify:** resolve by list-with-name-filter and read the identifier out of the response.
  Fail closed on an empty result. The worked example does exactly this.
- **9.0 difference:** none.

### P7 — You know the list operations truncate

- **Must be true:** every inventory list caps its result and says so only in prose. From the
  spec's own operation descriptions **[SPEC]**:

  | Operation | Cap, verbatim from the spec |
  |---|---|
  | `Vcenter.VM_list` | *"at most **4000** visible (subject to permission checks) virtual machines"* |
  | `Vcenter.Host_list` | *"at most **2500** visible … hosts"* |
  | `Vcenter.Datastore_list` | *"at most **2500** visible … datastores"* |
  | `Vcenter.Datacenter_list` | *"at most **1000** visible … datacenters"* |
  | `Vcenter.Cluster_list` | *"at most **1000** visible … clusters"* |
  | `Vcenter.Folder_list` | *"at most **1000** visible … folders"* |
  | `Vcenter.Network_list` | *"at most **1000** visible … networks"* |
  | `Vcenter.ResourcePool_list` | *"at most **1000** visible … resource pools"* |

- **There is no pagination cursor on these operations** — no `page_size`, no
  `next_token`, no `cursor` parameter is declared. **[SPEC]** Truncation is therefore
  *silent*: a 200 with a short array, indistinguishable from a small estate. The
  `Vapi.Std.Errors.UnableToAllocateResource` error is declared on these operations for the
  over-limit case, but the spec does not commit to raising it in preference to truncating.
  **[INFERRED — behavior on exceeding the cap is not pinned down by the spec; treat both
  outcomes as possible.]**
- **Verify / mitigate:** always filter. Narrow by `datacenters`, `clusters`, `folders` or
  `names` so the result cannot approach the cap, and iterate over containers rather than
  querying the root. If you genuinely need a full-estate VM inventory above 4,000, that is a
  VI-JSON `PropertyCollector` job, not an `/api` job.
- **9.0 difference:** the caps are identical at both tags — 9.1 did not raise them.
- **The 9.1 Query API does not help you here yet.** The 9.1 release notes announce a
  **Query API** delivering *"a fast, flexible, and scalable way to retrieve vSphere
  inventory data"* with server-side filtering, pagination and entity counting **[DOC]**.
  **No such path exists in the 9.1 ops inventory** — there is no `/vcenter/query`, no
  `/query`, and the only `/vcenter/inventory/*` operations are the two `*_find` calls that
  are also in 9.0. Its paths, verbs and payloads are `UNVERIFIED`. Do not emit a Query API
  call from a guessed path; if a customer needs it, resolve it from the appliance's own
  spec first. See `../deltas.md`.

### P8 — The VM's power state matches the operation you are about to run

- **Must be true:** several operations are state-gated, and the spec says so in the error
  descriptions **[SPEC]**:
  - `DELETE /api/vcenter/vm/{vm}` → **400 `Vapi.Std.Errors.NotAllowedInCurrentState`**
    *"if the virtual machine is running (powered on)"*. Delete needs a powered-off VM.
  - `Vcenter.Vm.Power_start` — *"Powers on a powered-off or suspended virtual machine."*
  - `Vcenter.Vm.Power_stop` — *"Powers off a powered-on or suspended virtual machine."*
  - `Vcenter.Vm.Power_suspend` — *"Suspends a powered-on virtual machine."*
  - `Vcenter.Vm.Power_reset` — *"Resets a powered-on virtual machine."*
- **Verify:** `GET /api/vcenter/vm/{vm}/power` **[SPEC — `Vcenter.Vm.Power_get`]**. The
  `Vcenter.Vm.Power.State` enum is exactly `POWERED_OFF`, `POWERED_ON`, `SUSPENDED`. **[SPEC]**
- **9.0 difference:** none.

---

## Base path and API surfaces

| Surface | Base | Spec / evidence | When to use it |
|---|---|---|---|
| **vSphere Automation (this file)** | `https://{host}/api` | `9.1__vsphere-automation.ops.json`, **1,367 ops** **[SPEC]** | Default for everything here. |
| Legacy REST | `https://{host}/rest` | **[DOC]** — deprecated; only operations released up to **vSphere 7.0.2** | Never, for new work. Recognize it in inherited scripts. |
| **VI-JSON** | `https://{host}/sdk/vim25/{release}` | `9.1__vsphere-vi-json.ops.json`, **2,243 ops**, spec `9.1.0.0`, security scheme `Session` = header `vmware-api-session-id` **[SPEC]** | Only when `/api` has no equivalent — `PropertyCollector` bulk retrieval, vApp operations, `VirtualMachine` reconfigure fields `/api/vcenter/vm/{vm}/hardware` does not expose. |
| Appliance subset | port **5480** | **[DOC]** | vCenter appliance config/lifecycle. Not this file. |

**VI-JSON path shape** `[DOC, corroborated by the spec's `base_path`]`:
`/sdk/vim25/{release}/{managedObjectType}/{moId}/{operation}`, e.g.
`GET /sdk/vim25/9.1.0.0/VirtualMachine/vm-495/config`,
`POST /sdk/vim25/9.1.0.0/SessionManager/{moId}/Login`. Its login is `SessionManager.Login`,
**not** `POST /api/session` — different surface, different login operation, same header name
for the resulting token.

Keep the focus on `/api`. VI-JSON is bigger, older-shaped, and its payloads are the full
vim25 structures; reaching for it by default trades a 20-line request for a 200-line one.

---

## Session

Three operations, both versions, all **[SPEC — `9.1__vsphere-automation.ops.json`]**:

| Verb | Path | operationId | Response |
|---|---|---|---|
| POST | `/api/session` | `Cis.Session_create` | **201** — `type: string, format: password` (the token) |
| GET | `/api/session` | `Cis.Session_get` | **200** — `Cis.Session.Info` |
| DELETE | `/api/session` | `Cis.Session_delete` | — |

> ### Path conflict: `/api/session` vs `/api/cis/session` — resolved in favour of the spec
>
> The research dossier records the session endpoint as `POST /api/cis/session`, read off
> the Broadcom developer portal. **The specification does not contain that path.** In
> `vcenter.yaml` at tag `9.0.0.0` the three operations are declared at **`/session`**,
> under `servers[0].url = https://{host}/api`, which composes to **`https://<vcenter>/api/session`**.
> `Cis.Session` is the OpenAPI **tag** on those operations — a grouping label, not a path
> segment. The same is true at the `9.1.0.0` tag.
>
> **Use `/api/session`.** If a client built on the portal's rendering works against a live
> appliance, that would mean vCenter accepts both spellings — plausible, but not something
> this file can assert. `UNVERIFIED` whether `/api/cis/session` also resolves.

`POST /api/session` declares `security: [basic_auth]` **[SPEC]** — HTTP Basic, i.e.
`Authorization: Basic base64(user:password)`. This resolves the dossier's open question
about the request-side auth header; the dossier could not retrieve the walkthrough page,
but the spec states the scheme directly.

Verbatim from the spec description of `Cis.Session_create` **[SPEC]**: *"Creates a session
with the API. This is the equivalent of login. This operation exchanges user credentials
supplied in the security context for a session token that is to be used for authenticating
subsequent calls. To authenticate subsequent calls clients are expected to include the
session token. For REST API calls the HTTP `vmware-api-session-id` header field should be
used for this."*

The 401 description on `Session_create` is worth reading when you are debugging a
token-based login **[SPEC]** — it lists the preconditions for SAML: *"the supplied token is
delegate-able · the time of client and server system are synchronized · the token supplied
is valid · if bearer tokens are used check that system configuration allows the API
endpoint to accept such tokens."* Clock skew is on that list for a reason.

**Federated identity and token exchange are `vcf-foundation`'s job.** For completeness, the
RFC 8693 token-exchange endpoint exists here too:
`POST /api/vcenter/authentication/token` **[SPEC — `Vcenter.Authentication.Token_issue`]**,
`Content-Type: application/x-www-form-urlencoded`, spec description: *"Provides a token
endpoint as defined in RFC 6749. Supported grant types:
`urn:ietf:params:oauth:grant-type:token-exchange`… This operation was added in vSphere API
7.0.2.0."* Note that "added in 7.0.2.0" — it is **not** new in 9.x. Do not re-derive the
federation flow here.

---

## Tasks and the `vmw-task=true` convention

Some operations exist twice: a synchronous form, and a `?…&vmw-task=true` form that returns
**202** and defers the work. **151 operations** carry the `vmw-task=true` suffix in the 9.1
spec. **[SPEC]**

| Verb | Path | operationId |
|---|---|---|
| GET | `/api/cis/tasks/{task}` | `Cis.Tasks_get` |
| POST | `/api/cis/tasks?action=list` | `Cis.Tasks_list` |
| POST | `/api/cis/tasks/{task}?action=cancel` | `Cis.Tasks_cancel` |

All **[SPEC]**. `Cis.Tasks_get` takes an optional `spec` query parameter
(`Cis.Tasks.GetSpec`); with it absent the spec says *"only the data described in
`Cis.Task.Info` will be returned and the result of the operation will be return[ed]"*.

**`Cis.Task.Status` enum, verbatim [SPEC]:** `PENDING`, `RUNNING`, `BLOCKED`, `SUCCEEDED`,
`FAILED`. Poll until `SUCCEEDED` or `FAILED`; `BLOCKED` is not terminal — it usually means
the task is waiting on a question or a lock, and it can move to `RUNNING` on its own.

`Cis.Task.Info` requires `cancelable`, `description`, `operation`, `service`, `status`, and
optionally carries `progress` and `result`. Note the spec's warning on `result` **[SPEC]**:
*"If an operation reports partial results before it completes, this property could be set
before the … status has the value SUCCEEDED. The value could change as the operation
progresses."* **Do not read `result` until `status` is `SUCCEEDED`.**

> **One spec-text ambiguity, flagged rather than papered over.** The `202` response on the
> `$Task` variants is `type: string`, but the *description* is copied verbatim from the
> synchronous variant — on `Vcenter.VM_clone$Task` it reads *"ID of newly-created virtual
> machine"*, not "task identifier". Across the whole 9.1 spec there are 151 `202`
> descriptions, 63 of them just *"Success!"*, and **not one mentions a task**. So the spec **declares** the async variant
> and the `Cis.Tasks` polling surface, but does **not** textually confirm that the 202 body
> is the value you pass to `GET /api/cis/tasks/{task}`. That pairing is the documented
> purpose of `vmw-task=true` and is what every client does — but it is **[INFERRED]** from
> the spec, not stated by it. If your poller depends on it, confirm against the appliance
> on first run, and handle a body that turns out to be a VM id by falling back to
> `POST /api/cis/tasks?action=list`.

**Rule of thumb.** Use the `$Task` form for anything that moves data — clone, relocate, OVF
deploy, EVC mode set. Use the synchronous form for create, power, and reconfigure, which
return directly and cheaply.

---

## Inventory traversal

### Resolution order

Work outside in. Each step's output is the next step's filter, and doing it out of order
means re-querying:

1. **Datacenter** — `GET /api/vcenter/datacenter?names=<dc>`
2. **Cluster** or **host** — `GET /api/vcenter/cluster?datacenters=<dc-id>&names=<cluster>`
   or `GET /api/vcenter/host?clusters=<cluster-id>`
3. **Resource pool** — `GET /api/vcenter/resource-pool?clusters=<cluster-id>&names=<pool>`
4. **Folder** — `GET /api/vcenter/folder?type=VIRTUAL_MACHINE&datacenters=<dc-id>&names=<folder>`
5. **Datastore** — `GET /api/vcenter/datastore?datacenters=<dc-id>&names=<ds>`
6. **Network** — `GET /api/vcenter/network?datacenters=<dc-id>&names=<pg>`

### Endpoints

All **[SPEC — `9.1__vsphere-automation.ops.json`]**. Paths shown relative to `/api`.

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/vcenter/datacenter` | `Vcenter.Datacenter_list` | |
| POST | `/vcenter/datacenter` | `Vcenter.Datacenter_create` | Body `Vcenter.Datacenter.CreateSpec`: `name` (**required**), `folder`. |
| GET | `/vcenter/datacenter/{datacenter}` | `Vcenter.Datacenter_get` | |
| DELETE | `/vcenter/datacenter/{datacenter}` | `Vcenter.Datacenter_delete` | *"Delete an empty datacenter from the vCenter Server"*. Takes a `force` query parameter. **Destructive.** |
| GET | `/vcenter/cluster` | `Vcenter.Cluster_list` | Filters: `clusters`, `names`, `folders`, `datacenters`. |
| GET | `/vcenter/cluster/{cluster}` | `Vcenter.Cluster_get` | |
| GET | `/vcenter/cluster/{cluster}/evc-mode` | `Vcenter.Cluster.EvcMode_get` | |
| PUT | `/vcenter/cluster/{cluster}/evc-mode?vmw-task=true` | `Vcenter.Cluster.EvcMode_set$Task` | Task form only. |
| POST | `/vcenter/cluster/{cluster}/evc-mode?action=check-set&vmw-task=true` | `Vcenter.Cluster.EvcMode_checkSet$Task` | Dry run before the set. |
| POST | `/vcenter/cluster/{cluster}/evc-mode?action=check-add-host-evc&vmw-task=true` | `Vcenter.Cluster.EvcMode_checkAddHostEvc$Task` | |
| GET | `/vcenter/host` | `Vcenter.Host_list` | Filters: `hosts`, `names`, `folders`, `datacenters`, `clusters`, `connection_states`, `host_uuids`, plus a `filter` object form. |
| POST | `/vcenter/host` | `Vcenter.Host_create` | Body `Vcenter.Host.CreateSpec`, required: `hostname`, `user_name`, `password`, `thumbprint_verification`; optional `port`, `folder`, `thumbprint`, `ssl_certificate`, `force_add`. |
| DELETE | `/vcenter/host/{host}` | `Vcenter.Host_delete` | **Destructive.** |
| POST | `/vcenter/host/{host}?action=connect` | `Vcenter.Host_connect` | |
| POST | `/vcenter/host/{host}?action=disconnect` | `Vcenter.Host_disconnect` | **Disruptive** — vCenter loses management of the host's VMs. |
| GET | `/vcenter/host/{host}/entropy/external-pool` | `Vcenter.Host.Entropy.ExternalPool_get` | |
| POST | `/vcenter/host/{host}/entropy/external-pool?action=add` | `Vcenter.Host.Entropy.ExternalPool_add` | |
| GET | `/vcenter/datastore` | `Vcenter.Datastore_list` | Filters: `datastores`, `names`, `types`, `folders`, `datacenters`. |
| GET | `/vcenter/datastore/{datastore}` | `Vcenter.Datastore_get` | |
| GET | `/vcenter/datastore/{datastore}/default-policy` | `Vcenter.Datastore.DefaultPolicy_get` | |
| GET | `/vcenter/inventory/datastore` | `Vcenter.Inventory.Datastore_find` | Reverse lookup — resolve datastore identifiers to inventory info. |
| GET | `/vcenter/network` | `Vcenter.Network_list` | Filters: `networks`, `names`, `types`, `folders`, `datacenters`. **There is no `GET /vcenter/network/{network}`.** |
| GET | `/vcenter/inventory/network` | `Vcenter.Inventory.Network_find` | Reverse lookup for networks. |
| GET | `/vcenter/network/projects` · `/{project}` | `Vcenter.Network.Projects_list` / `_get` | VPC networking. |
| GET | `/vcenter/network/projects/{project}/vpcs` · `/{vpc}` | `Vcenter.Network.Projects.Vpcs_list` / `_get` | |
| GET | `/vcenter/network/projects/{project}/vpcs/{vpc}/subnets` · `/{subnet}` | `Vcenter.Network.Projects.Vpcs.Subnets_list` / `_get` | |
| GET | `/vcenter/folder` | `Vcenter.Folder_list` | Filters: `folders`, `names`, `parent_folders`, `datacenters`, plus a `filter` object carrying `type`. **List only — no create, get, update or delete.** |
| GET | `/vcenter/resource-pool` | `Vcenter.ResourcePool_list` | Filters: `resource_pools`, `names`, `parent_resource_pools`, `datacenters`, `hosts`, `clusters`. |
| POST | `/vcenter/resource-pool` | `Vcenter.ResourcePool_create` | Body `Vcenter.ResourcePool.CreateSpec`, required: `name`, `parent`; optional `cpu_allocation`, `memory_allocation`. |
| GET | `/vcenter/resource-pool/{resourcePool}` | `Vcenter.ResourcePool_get` | |
| PATCH | `/vcenter/resource-pool/{resourcePool}` | `Vcenter.ResourcePool_update` | |
| DELETE | `/vcenter/resource-pool/{resourcePool}` | `Vcenter.ResourcePool_delete` | **Destructive.** |

Two asymmetries worth internalising, because they break pattern-matching: **`/vcenter/folder`
has only a list operation** (no `POST`, no `/{folder}`), and **`/vcenter/network` has no
single-object `GET`**. Use `/vcenter/inventory/network` if you have a network id and need
information about it.

### Filter parameters — how they are actually encoded

Every filter parameter on these list operations is declared `in: query`, `style: form`,
`explode: true`, with an array schema. **[SPEC]** That means **repeat the parameter**, do not
comma-join, and do not prefix with `filter.`:

```
GET /api/vcenter/vm?names=web01&names=web02&clusters=domain-c7
```

The parameter names are flat and plural: on `Vcenter.VM_list` they are `vms`, `names`,
`folders`, `datacenters`, `hosts`, `clusters`, `resource_pools`, `power_states`. **[SPEC]**
This closes the dossier's open item — the dossier recorded the `filter.*` names as
`UNVERIFIED` because the portal pages did not render them; the spec declares them directly.

Semantics, verbatim from the spec: *"If missing or `null` or empty, virtual machines with
any identifier match the filter"* — an omitted filter is "match everything", not "match
nothing". And across filters: *"If multiple properties are specified, only folders matching
**all** of the properties match the filter"* — filters AND together.

### What the list operations actually return

Each list returns an array of `*.Summary` objects. Know the field names before you write the
`jq`. All **[SPEC]**; **bold** = required by the schema, so always present:

| Operation | Summary fields |
|---|---|
| `Vcenter.VM_list` | **`vm`**, **`name`**, **`power_state`**, `cpu_count`, `memory_size_mib` |
| `Vcenter.Datacenter_list` | **`datacenter`**, **`name`** |
| `Vcenter.Cluster_list` | **`cluster`**, **`name`**, **`ha_enabled`**, **`drs_enabled`** |
| `Vcenter.Host_list` | **`host`**, **`name`**, **`connection_state`**, `power_state`, `host_uuid` |
| `Vcenter.Datastore_list` | **`datastore`**, **`name`**, **`type`**, `free_space`, `capacity` |
| `Vcenter.Network_list` | **`network`**, **`name`**, **`type`** |
| `Vcenter.Folder_list` | **`folder`**, **`name`**, **`type`** |
| `Vcenter.ResourcePool_list` | **`resource_pool`**, **`name`** |
| `Vcenter.Vm.Power_get` | **`state`**, `clean_power_off` (`Vcenter.Vm.Power.Info`) |

Two consequences worth using. **`Vcenter.VM_list` already carries `power_state`** — a
bulk "which of these are powered on" needs one filtered list call, not one power `GET` per
VM. And **`Vcenter.Cluster_list` already carries `drs_enabled`** — that is the flag that
decides whether a clone into that cluster may omit `host` (P5), and it comes back free with
the cluster lookup you were doing anyway.

### Enums you will need

All **[SPEC]**, exact values:

| Enum | Values |
|---|---|
| `Vcenter.Folder.Type` | `DATACENTER`, `DATASTORE`, `HOST`, `NETWORK`, `VIRTUAL_MACHINE` |
| `Vcenter.Network.Type` | `STANDARD_PORTGROUP`, `DISTRIBUTED_PORTGROUP`, `OPAQUE_NETWORK` |
| `Vcenter.Datastore.Type` | `VMFS`, `NFS`, `NFS41`, `CIFS`, `VSAN`, `VFFS`, `VVOL` |
| `Vcenter.Host.ConnectionState` | `CONNECTED`, `DISCONNECTED`, `NOT_RESPONDING` |
| `Vcenter.Vm.Power.State` | `POWERED_OFF`, `POWERED_ON`, `SUSPENDED` |
| `Cis.Task.Status` | `PENDING`, `RUNNING`, `BLOCKED`, `SUCCEEDED`, `FAILED` |

Two notes on these. **A VM folder must be `VIRTUAL_MACHINE`** — placing a VM in a `HOST`
folder is an `InvalidArgument`, and the folder list is the only place that type is visible.
**`OPAQUE_NETWORK` is what an NSX segment looks like from vCenter** — spec description,
verbatim: *"A network whose configuration is managed outside of vSphere."* You attach a vNIC
to it exactly like any other network, but you cannot configure it here; that is
`nsx-security-policy` / NSX Policy API territory.

`Vcenter.Datastore.Type` still lists `VVOL`, but **vVols were deprecated at 9.0** per the
9.0 product support notes **[DOC]**, and the 9.1 support notes do not reinstate them.
Present in the enum is not the same as recommended.

---

## VM lifecycle

All **[SPEC — `9.1__vsphere-automation.ops.json`]**. Paths relative to `/api`.

| Verb | Path | operationId |
|---|---|---|
| GET | `/vcenter/vm` | `Vcenter.VM_list` |
| POST | `/vcenter/vm` | `Vcenter.VM_create` |
| GET | `/vcenter/vm/{vm}` | `Vcenter.VM_get` |
| DELETE | `/vcenter/vm/{vm}` | `Vcenter.VM_delete` |
| POST | `/vcenter/vm?action=clone` | `Vcenter.VM_clone` |
| POST | `/vcenter/vm?action=clone&vmw-task=true` | `Vcenter.VM_clone$Task` |
| POST | `/vcenter/vm?action=instant-clone` | `Vcenter.VM_instantClone` |
| POST | `/vcenter/vm?action=register` | `Vcenter.VM_register` |
| POST | `/vcenter/vm/{vm}?action=unregister` | `Vcenter.VM_unregister` |
| POST | `/vcenter/vm/{vm}?action=relocate` | `Vcenter.VM_relocate` |
| POST | `/vcenter/vm/{vm}?action=relocate&vmw-task=true` | `Vcenter.VM_relocate$Task` |
| GET | `/vcenter/vm/{vm}/library-item` | `Vcenter.Vm.LibraryItem_get` |

Note the asymmetry: **clone has a task form, instant-clone does not.** Instant clone is
memory-sharing and returns fast by design.

### Create — `Vcenter.VM.CreateSpec`

Spec description: *"Creates a virtual machine."* Only **`guest_os` is required**. **[SPEC]**
Full property set **[SPEC]**:

`guest_os` (**required**), `name`, `placement`, `hardware_version`, `boot`, `boot_devices`,
`cpu`, `memory`, `disks`, `nics`, `cdroms`, `floppies`, `parallel_ports`, `serial_ports`,
`sata_adapters`, `scsi_adapters`, `nvme_adapters`, `storage_policy`.

`placement` is a `Vcenter.VM.PlacementSpec`: `folder`, `resource_pool`, `host`, `cluster`,
`datastore` — none individually required by the schema, all subject to the mutual-consistency
rules in P5. The privilege text refers to the same fields under the names
`Vcenter.VM.InventoryPlacementSpec.folder`, `Vcenter.VM.ComputePlacementSpec.resource_pool`
and `Vcenter.VM.StoragePlacementSpec.datastore` — those are the privilege-doc names for the
same three fields, not separate objects you must nest.

Declared 400 causes, verbatim **[SPEC]**: `AlreadyExists` *"if a virtual machine with the
specified name already exists"*; `InvalidArgument`; `ResourceInUse` *"if any of the specified
storage addresses (eg. IDE, SATA, SCSI, NVMe) result in a storage address conflict"*;
`Unsupported` *"if guest_OS is not supported for the requested virtual hardware version"*.

> **Hardware note [DOC]:** virtual hardware version **22** arrived with ESX 9.0
> (960 logical processors, 960 cores per socket, NVMe 1.4, 4KN VMDK, Intel TDX, AMD SEV-SNP)
> and carries into 9.1; the 9.1 what's-new page announces no new VM hardware version, and
> the only `vmx-` version numbers it mentions (*"vmx-10 to vmx-17"*) refer to the **vCenter
> appliance's own** VM, not to what you can create. `hardware_version` is a
> `Vcenter.Vm.Hardware.Version` value; the concrete enum member names were not extracted and
> are `UNVERIFIED` — read them from the spec's `Vcenter.Vm.Hardware.Version` schema before
> hard-coding one.
>
> Two 9.1 ESX behaviors worth knowing when you provision **[DOC]**: **User-Level Monitor
> (ULM) is the default monitor for all virtual machines**, and AMD SEV-SNP / Intel TDX
> confidential VMs move from limited availability to **general availability**. Neither
> changes the create payload in any way this file can evidence.

### Clone — `Vcenter.VM.CloneSpec`

Required: **`name`** and **`source`**. **[SPEC]** Full property set **[SPEC]**:

| Field | Type | Notes (spec wording where quoted) |
|---|---|---|
| `source` | string, **required** | *"Virtual machine to clone from."* Identifier for resource type `VirtualMachine`. |
| `name` | string, **required** | *"Virtual machine name."* |
| `placement` | `Vcenter.VM.ClonePlacementSpec` | `folder`, `resource_pool`, `host`, `cluster`, `datastore`. If omitted, *"the system will use the values from the source virtual machine"*. |
| `disks_to_remove` | array (unique) of disk ids | *"If missing or `null`, all disks will be copied."* Overlap with `disks_to_update` → `InvalidArgument`. |
| `disks_to_update` | map disk-id → `Vcenter.VM.DiskCloneSpec` | Per-disk `datastore` override. The spec marks `DiskCloneSpec.datastore` *"currently required"* when the map entry is present. |
| `power_on` | boolean | *"If missing or `null`, the virtual machine will not be powered on."* |
| `guest_customization_spec` | `Vcenter.VM.GuestCustomizationSpec` | Single property `name` — the name of a customization spec **already stored in vCenter**. *"If missing or `null`, the guest operating system is not customized after clone."* |

Declared errors **[SPEC]**: 400 `AlreadyExists` / `InvalidArgument`; 404 *"if any of the
resources specified in spec could not be found"*; 500 `ResourceInaccessible` /
`UnableToAllocateResource` *"if any of the resources needed to clone the virtual machine
could not be allocated"*.

The synchronous form returns **200** with the new VM's identifier. The `$Task` form returns
**202** — see the ambiguity note in the tasks section.

### Relocate — `Vcenter.VM.RelocateSpec`

Spec description, verbatim **[SPEC]**: *"Relocates a virtual machine based on the
specification. The parts of the virtual machine that can move are: FOLDER, RESOURCE_POOL,
HOST, CLUSTER and DATASTORE of home of the virtual machine and disks."* Privileges:
`Resource.ColdMigrate` on the VM, `Resource.AssignVMToPool` on the target pool. Use the
`$Task` form — a storage relocate moves data.

### Register / unregister

`Vcenter.VM_register` — *"Creates a virtual machine from existing virtual machine files on
storage."* `Vcenter.VM_unregister` — *"Removes the virtual machine … from the vCenter
inventory **without removing any of the virtual machine's files from storage**. All
high-level information stored with the management server (ESXi or vCenter) is removed,
including … statistics, resource pool association, permissions, and alarms."* **[SPEC]**

That pair is the safe alternative to delete when the intent is "get it out of inventory".
Offer it when someone asks to delete a VM they may want back.

### Delete — the destructive one

`DELETE /api/vcenter/vm/{vm}` **[SPEC — `Vcenter.VM_delete`]**. *"Deletes a virtual
machine."* Requires `VirtualMachine.Inventory.Delete`. **400 `NotAllowedInCurrentState`
*"if the virtual machine is running (powered on)"*.** 500 `ResourceBusy` *"if the virtual
machine is busy performing another operation."*

Before executing: `GET /api/vcenter/vm/{vm}` to confirm you have the right object by name,
and `GET /api/vcenter/vm/{vm}/power` to confirm state. Deleting by an identifier you
assembled rather than resolved is how the wrong VM goes away.

---

## VM power

All **[SPEC]**, paths relative to `/api`:

| Verb | Path | operationId | Precondition (spec wording) |
|---|---|---|---|
| GET | `/vcenter/vm/{vm}/power` | `Vcenter.Vm.Power_get` | — |
| POST | `/vcenter/vm/{vm}/power?action=start` | `Vcenter.Vm.Power_start` | *"a powered-off or suspended virtual machine"* |
| POST | `/vcenter/vm/{vm}/power?action=stop` | `Vcenter.Vm.Power_stop` | *"a powered-on or suspended virtual machine"* |
| POST | `/vcenter/vm/{vm}/power?action=suspend` | `Vcenter.Vm.Power_suspend` | *"a powered-on virtual machine"* |
| POST | `/vcenter/vm/{vm}/power?action=reset` | `Vcenter.Vm.Power_reset` | *"a powered-on virtual machine"* |

**`?action=stop` is a hard power-off.** For a graceful in-guest shutdown, use the guest
operations, which require VMware Tools **[SPEC]**:

| Verb | Path | operationId |
|---|---|---|
| GET | `/vcenter/vm/{vm}/guest/power` | `Vcenter.Vm.Guest.Power_get` |
| POST | `/vcenter/vm/{vm}/guest/power?action=shutdown` | `Vcenter.Vm.Guest.Power_shutdown` |
| POST | `/vcenter/vm/{vm}/guest/power?action=reboot` | `Vcenter.Vm.Guest.Power_reboot` |
| POST | `/vcenter/vm/{vm}/guest/power?action=standby` | `Vcenter.Vm.Guest.Power_standby` |

If someone asks to "shut down these VMs", ask which one they mean — the two paths differ by
one path segment and by whether the guest filesystem gets flushed.

---

## VM reconfigure

Aggregate read and hardware-version update **[SPEC]**:

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/vcenter/vm/{vm}/hardware` | `Vcenter.Vm.Hardware_get` | |
| PATCH | `/vcenter/vm/{vm}/hardware` | `Vcenter.Vm.Hardware_update` | Body `Vcenter.Vm.Hardware.UpdateSpec`: `upgrade_policy`, `upgrade_version`. |
| POST | `/vcenter/vm/{vm}/hardware?action=upgrade` | `Vcenter.Vm.Hardware_upgrade` | *"Upgrades the virtual machine to a newer virtual hardware version."* |

Per-component, all **[SPEC]**, paths relative to `/api/vcenter/vm/{vm}/hardware`:

| Component | Operations | Update spec fields |
|---|---|---|
| **CPU** | `GET·PATCH /cpu` — `Vcenter.Vm.Hardware.Cpu_get` / `_update` | `count`, `cores_per_socket`, `hot_add_enabled`, `hot_remove_enabled` |
| **Memory** | `GET·PATCH /memory` — `..Memory_get` / `_update` | `size_mib`, `hot_add_enabled` |
| **Disk** | `GET·POST /disk`, `GET·PATCH·DELETE /disk/{disk}` — `..Disk_list` / `_create` / `_get` / `_update` / `_delete` | `CreateSpec`: `type`, `ide`, `scsi`, `sata`, `nvme`, `backing`, `new_vmdk` |
| **Ethernet** | `GET·POST /ethernet`, `GET·PATCH·DELETE /ethernet/{nic}`, `POST /ethernet/{nic}?action=connect\|disconnect` — `..Ethernet_*` | `CreateSpec`: `type`, `backing`, `mac_type`, `mac_address`, `pci_slot_number`, `wake_on_lan_enabled`, `start_connected`, `allow_guest_control`, `upt_compatibility_enabled`, `upt_v2_compatibility_enabled`. `BackingSpec` **requires `type`**; carries `network`, `distributed_port`. |
| **CD-ROM** | `GET·POST /cdrom`, `GET·PATCH·DELETE /cdrom/{cdrom}`, `POST /cdrom/{cdrom}?action=connect\|disconnect` | |
| **Adapters** | `/adapter/scsi`, `/adapter/sata`, `/adapter/nvme` — list/create/get/delete (SCSI also `PATCH`) | |
| **Boot** | `GET·PATCH /boot`, `GET·PUT /boot/device` | |
| **Serial / parallel / floppy** | list/create/get/update/delete + connect/disconnect | |

Two notes. **`cores_per_socket` and `count` are separate fields** — setting `count: 8` alone
leaves the socket topology to vCenter, which is usually not what a licensing-sensitive
workload wants. **`hot_add_enabled` on CPU and memory generally requires the VM to be
powered off to change**, which the spec does not state on these operations — treat the
powered-on case as **[INFERRED]** and read `GET /hardware/cpu` back after the PATCH.

Adjacent, also **[SPEC]**: `GET·PATCH /vcenter/vm/{vm}/storage/policy`
(`Vcenter.Vm.Storage.Policy_get` / `_update`) — but storage-policy *management* belongs to
`vsphere-content-tags-policies`; this is only the per-VM binding.

Guest customization **[SPEC]**: `GET·PUT /vcenter/vm/{vm}/guest/customization`
(`Vcenter.Vm.Guest.Customization_get` / `_set`) and the pre-check
`POST /vcenter/vm/{vm}/guest/customization?action=check`
(`Vcenter.Vm.Guest.Customization_check`) — the VM-customization pre-check introduced at 9.0
**[DOC]**. Run the check before the set.

**Live (powered-on) customization**, both **[SPEC]**:
`GET /vcenter/vm/{vm}/guest/customization-live` (`Vcenter.Vm.Guest.CustomizationLive_get`)
and `POST /vcenter/vm/{vm}/guest/customization-live?action=run&vmw-task=true`
(`Vcenter.Vm.Guest.CustomizationLive_run$Task`). Spec description, verbatim: *"Customizes a
running virtual machine. Before using the operation, the **Guest Customization Engine** needs
to be installed in the virtual machine."* — that is a hard precondition, not VMware Tools.

> **Correct this premise if it comes up.** The 9.1 release notes list *"Live Network
> Customization"* for powered-on VMs under what's-new **[DOC]**, which reads as new-in-9.1.
> The endpoints are present at the **9.0** tag too, and the spec's own text says the
> operation *"was added in vSphere API 9.0.0.0"* **[SPEC]**. Whatever changed at 9.1 is
> behavior or scope, not the API surface. Do not tell a 9.0 customer this API does not
> exist for them.

---

## Worked example — clone a VM from a template in inventory

**Goal:** clone the inventory template `tmpl-rhel9` into a new VM `app-web-07`, placed in a
named resource pool, VM folder and datastore, using the **task** form and polling to
completion.

The point of the example is the identifier resolution. Every placement field below is a
value the *server returned*; nothing is assembled by hand.

```bash
VC=https://vcenter.example.com
DC_NAME=Datacenter-01
CLUSTER_NAME=cluster-prod-01
POOL_NAME=rp-web
FOLDER_NAME=Web-Tier
DS_NAME=vsanDatastore
SOURCE_NAME=tmpl-rhel9
NEW_NAME=app-web-07
```

> **Which "template" do you have?** If `tmpl-rhel9` is a **VM or template in vCenter
> inventory**, this sequence is right. If it is a **content library VM template item**, the
> operation is `POST /api/vcenter/vm-template/library-items/{templateLibraryItem}?action=deploy`
> **[SPEC — `Vcenter.VmTemplate.LibraryItems_deploy`]** with a
> `Vcenter.VmTemplate.LibraryItems.DeploySpec` (required `name`; plus `vm_home_storage`,
> `disk_storage`, `disk_storage_overrides`, `placement`, `powered_on`, `guest_customization`,
> `hardware_customization`) — and that is `vsphere-content-tags-policies`' territory.
> Establish which one before you start; the two are not interchangeable.

### Step 0 — Authenticate (P1, P2)

```bash
TOKEN=$(curl -sS -u "$VC_USER:$VC_PASS" -X POST "$VC/api/session" | jq -r '.')
[ -z "$TOKEN" ] || [ "$TOKEN" = null ] && { echo "FATAL: no session — check P2 (federated login gate)" >&2; exit 1; }
AUTH=(-H "vmware-api-session-id: $TOKEN" -H 'Content-Type: application/json')
```

`POST /api/session` **[SPEC — `Cis.Session_create`]**, HTTP Basic, **201**, body is the token
string. A 401 here on a credential you trust is P2, not a typo.

### Step 1 — Resolve the datacenter and cluster

```bash
DC=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/datacenter?names=$DC_NAME" | jq -r '.[0].datacenter')
CLJSON=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/cluster?datacenters=$DC&names=$CLUSTER_NAME")
CL=$(jq -r '.[0].cluster'      <<<"$CLJSON")
DRS=$(jq -r '.[0].drs_enabled' <<<"$CLJSON")
```

`GET /api/vcenter/datacenter` **[SPEC — `Vcenter.Datacenter_list`]**,
`GET /api/vcenter/cluster` **[SPEC — `Vcenter.Cluster_list`]**. Note the repeated flat query
parameters — no `filter.` prefix, no comma-joining.

Capture `drs_enabled` while you are here: `Vcenter.Cluster.Summary` carries it as a required
field **[SPEC]**, and it decides whether the clone body may name a `cluster` without a
`host` (P5). On a non-DRS cluster the spec throws `InvalidArgument` for
`resource_pool` + `cluster` with no `host`.

### Step 2 — Resolve resource pool, VM folder and datastore (P5, P6)

```bash
RP=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/resource-pool?clusters=$CL&names=$POOL_NAME" | jq -r '.[0].resource_pool')
FD=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/folder?datacenters=$DC&type=VIRTUAL_MACHINE&names=$FOLDER_NAME" | jq -r '.[0].folder')
DS=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/datastore?datacenters=$DC&names=$DS_NAME" | jq -r '.[0].datastore')
SRC=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/vm?names=$SOURCE_NAME" | jq -r '.[0].vm')

for v in DC CL RP FD DS SRC; do
  case "${!v}" in ''|null)
    echo "FATAL: $v unresolved — fix P5/P6 before continuing" >&2; exit 1 ;;
  esac
done
printf 'dc=%s cluster=%s pool=%s folder=%s ds=%s src=%s\n' "$DC" "$CL" "$RP" "$FD" "$DS" "$SRC"
```

`Vcenter.ResourcePool_list`, `Vcenter.Folder_list`, `Vcenter.Datastore_list`,
`Vcenter.VM_list` — all **[SPEC]**. The `type=VIRTUAL_MACHINE` filter on the folder query is
load-bearing: a `HOST` folder with the same display name will resolve and then fail the
clone with `InvalidArgument`.

The guard is not decoration. An unresolved value becomes the literal string `null` in the
JSON below, and the clone fails at 404 several steps later with a message that does not name
which field was wrong.

### Step 3 — Submit the clone as a task

```bash
# On a non-DRS cluster, name a host instead of the cluster (see P5).
if [ "$DRS" = "true" ]; then
  PLACEMENT=$(jq -n --arg fd "$FD" --arg rp "$RP" --arg cl "$CL" --arg ds "$DS" \
    '{folder:$fd, resource_pool:$rp, cluster:$cl, datastore:$ds}')
else
  HOST=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/host?clusters=$CL" | jq -r '.[0].host')
  PLACEMENT=$(jq -n --arg fd "$FD" --arg rp "$RP" --arg ho "$HOST" --arg ds "$DS" \
    '{folder:$fd, resource_pool:$rp, host:$ho, datastore:$ds}')
fi

TASK=$(curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/vcenter/vm?action=clone&vmw-task=true" \
  -d "$(jq -n --arg src "$SRC" --arg name "$NEW_NAME" --argjson pl "$PLACEMENT" '{
    source:    $src,
    name:      $name,
    placement: $pl,
    power_on:  false
  }')" | jq -r '.')
echo "task=$TASK"
```

`POST /api/vcenter/vm?action=clone&vmw-task=true` **[SPEC — `Vcenter.VM_clone$Task`]**,
body `Vcenter.VM.CloneSpec`, response **202**.

Field notes, all from the spec:
- `source` and `name` are the only **required** properties.
- `placement` is optional and inherits from the source if omitted — which is exactly the
  silent-wrong-datastore failure mode. Set it.
- `cluster` + `resource_pool` together are legal only if *"resource_pool must belong to
  cluster"*. On a **non-DRS** cluster, drop `cluster` and supply `host` instead — the spec
  says `InvalidArgument` otherwise.
- `power_on: false` is the default behavior anyway; stating it makes the intent explicit and
  keeps the VM from booting before customization.
- To customize the guest, add `guest_customization_spec: {name: "<spec-name>"}` — the name of
  a customization spec that must already exist in vCenter.
- To land specific disks elsewhere, add
  `disks_to_update: {"<disk-id>": {"datastore": "<ds-id>"}}`. `disks_to_remove` and
  `disks_to_update` must not name the same disk.

Note the `jq -n --arg` construction. A single-quoted `-d '{...}'` would not expand the shell
variables at all, and you would post the literal strings.

### Step 4 — Poll the task

```bash
while :; do
  INFO=$(curl -sS "${AUTH[@]}" "$VC/api/cis/tasks/$TASK")
  ST=$(jq -r '.status' <<<"$INFO")
  case "$ST" in
    SUCCEEDED) VM=$(jq -r '.result' <<<"$INFO"); break ;;
    FAILED)    jq -r '.description.default_message, (.error|tostring)' <<<"$INFO" >&2; exit 1 ;;
    PENDING|RUNNING|BLOCKED) sleep 5 ;;
    *) echo "unexpected status: $ST" >&2; exit 1 ;;
  esac
done
echo "new vm=$VM"
```

`GET /api/cis/tasks/{task}` **[SPEC — `Cis.Tasks_get`]**. `Cis.Task.Status` is
`PENDING|RUNNING|BLOCKED|SUCCEEDED|FAILED` **[SPEC]**. `BLOCKED` is **not** terminal — keep
polling. Read `result` **only** on `SUCCEEDED`: the spec warns the value *"could change as
the operation progresses"*.

If `$TASK` turns out not to be a task identifier — see the ambiguity note in the tasks
section — this loop 404s immediately on the first poll. Fall back to the synchronous
`POST /api/vcenter/vm?action=clone` (**[SPEC — `Vcenter.VM_clone`]**, 200, returns the VM id
directly), or locate the task via `POST /api/cis/tasks?action=list`
**[SPEC — `Cis.Tasks_list`]**.

### Step 5 — Reconfigure before first boot (optional)

```bash
curl -sS -X PATCH "${AUTH[@]}" "$VC/api/vcenter/vm/$VM/hardware/cpu" \
  -d '{"count": 8, "cores_per_socket": 4}'
curl -sS -X PATCH "${AUTH[@]}" "$VC/api/vcenter/vm/$VM/hardware/memory" \
  -d '{"size_mib": 16384}'
```

`Vcenter.Vm.Hardware.Cpu_update` and `Vcenter.Vm.Hardware.Memory_update` **[SPEC]**. Both are
synchronous. Doing this while the VM is powered off avoids every hot-add caveat.

### Step 6 — Power on and verify

```bash
curl -sS -X POST "${AUTH[@]}" "$VC/api/vcenter/vm/$VM/power?action=start"
curl -sS       "${AUTH[@]}" "$VC/api/vcenter/vm/$VM/power" | jq -r '.state'
curl -sS       "${AUTH[@]}" "$VC/api/vcenter/vm/$VM"       | jq -r '.name'
```

`Vcenter.Vm.Power_start`, `Vcenter.Vm.Power_get`, `Vcenter.VM_get` **[SPEC]**. Expect
`POWERED_ON`.

### Step 7 — Close the session

```bash
curl -sS -X DELETE "${AUTH[@]}" "$VC/api/session"
```

`DELETE /api/session` **[SPEC — `Cis.Session_delete`]** — *"Terminates the validity of a
session token. This is the equivalent of log out."*

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 401 on step 0 with a credential you trust | **P2** — the non-federated username/password block introduced at 9.0 still applies. Not a typo. Route to `vcf-foundation`, or use the 9.1 OAuth 2.0 route. |
| 401 mid-sequence after a pause | Session expired. Re-authenticate; the timeout is not documented (P3). |
| 403 on step 3 | Missing one of the four clone privileges — they are per-object (P4). `VirtualMachine.Provisioning.Clone` on the source is the one most often absent. |
| Empty array from any step-1/2 query | Name mismatch, or the object is outside the datacenter you filtered on. The guard catches it. |
| A step-2 query returns many rows | Duplicate display names across the estate. Add `datacenters=` / `clusters=` and re-check; `.[0]` on an ambiguous list picks arbitrarily. |
| 404 on step 3 | One of `source`, `folder`, `resource_pool`, `datastore`, `cluster` did not resolve — the spec's 404 is *"if any of the resources specified in spec could not be found"* and does not say which. |
| 400 `InvalidArgument` on step 3 | Placement conflict: `resource_pool` not in `cluster`, or a non-DRS cluster with no `host` (P5). Or the folder is not `VIRTUAL_MACHINE` type. |
| 400 `AlreadyExists` on step 3 | A VM named `$NEW_NAME` already exists. |
| 500 `UnableToAllocateResource` on the task | Datastore space, or a resource-pool reservation ceiling. |
| Task sits at `BLOCKED` | Not terminal. Usually a pending question or a lock on the source. Keep polling; investigate in the vSphere Client if it persists. |
| Task 404 on the first poll | The 202 body may not be a task id — see the tasks-section ambiguity note. |
| 404 on step 5/6 | `$VM` came from `result` while status was not yet `SUCCEEDED`. |
| 400 on a later `DELETE /vcenter/vm/{vm}` | The VM is powered on (P8). Stop it first. |

---

## What 9.1 adds and removes in this scope

The 9.1 spec has **1,367** operations against 9.0's 1,275: **101 added, 9 removed, 28 newly
deprecated**. Most of the additions are Supervisor / namespace-management, which is outside
this file. What lands in inventory and VM scope:

### Added at 9.1 — spec-confirmed

All **[SPEC — present in `9.1__vsphere-automation.ops.json`, absent from
`9.0__vsphere-automation.ops.json`]**. Paths relative to `/api`.

| Verb | Path | operationId | What it is |
|---|---|---|---|
| GET | `/vcenter/host/{host}/hardware/direct-path-devices` | `Vcenter.Host.Hardware.DirectPathDevices_list` | *"Returns all the DirectPathDevices on the host."* Requires `System.Read`. |
| POST | `/vcenter/host/{host}/hardware/direct-path-devices?action=configure&vmw-task=true` | `Vcenter.Host.Hardware.DirectPathDevices_configure$Task` | Task-form configure of passthrough devices. |
| GET | `/vcenter/host/crypto/fips/modules` | `Vcenter.Host.Crypto.Fips.Modules_list` | *"Return a list of FIPS validated crypto modules installed on the hosts in the inventory."* |
| GET | `/vcenter/crypto/fips/modules` | `Vcenter.Crypto.Fips.Modules_list` | vCenter-side equivalent. |
| GET | `/vcenter/utilization/connections` | `Vcenter.Utilization.Connections_list` | *"Lists the connection utilization of vCenter server processes."* Requires `System.Read`. |
| GET | `/vcenter/utilization/proxies` | `Vcenter.Utilization.Proxies_list` | *"Get vCenter proxies utilization."* |
| GET | `/vcenter/capacity/usage` | `Vcenter.Capacity.Usage_get` | *"Extracts the current vCenter configuration usage and provides information if the current configuration is compliant with the configuration recommendation."* |
| GET·PATCH | `/vcenter/deployment/size` (+ `/status`) | `Vcenter.Deployment.Size_get` / `_update` / `Size.Status_get` | vCenter appliance sizing. |
| POST | `/vcenter/registered-tokens` | `Vcenter.RegisteredTokens_create` | Registers an Expanded Access Token so an Overflow Access Token can be used against the vCenter API. Auth plumbing — see P2. |
| PATCH | `/vcenter/compute/policies/{policy}` | `Vcenter.Compute.Policies_update` | Compute policies gain an update verb. |
| PATCH | `/vcenter/tagging/associations` | `Vcenter.Tagging.Associations_update` | Atomic multi-tag association update. **Routes to `vsphere-content-tags-policies`.** |

> **The "Utilization API" from the release notes is partly real and partly not.** The 9.1
> what's-new page announces a *"Utilization API"* that *"monitors vCenter capacity and usage
> metrics"* **[DOC]**, and the two `/vcenter/utilization/*` reads plus `/vcenter/capacity/usage`
> above are spec-confirmed and clearly it. But the dossier flagged the Utilization API's
> concrete paths as `UNVERIFIED` from the doc portal, so treat **these three** as the
> verified surface and anything beyond them as still unverified. The **vCenter Group
> Federated API (VGFA)** — announced as *"a single unified API endpoint for managing all
> vCenter instances in a vCenter group"* **[DOC]** — has **no corresponding path in the 9.1
> ops inventory at all**. Its endpoints remain `UNVERIFIED`. Do not construct one.

### Removed at 9.1 — Hybrid Linked Mode `[breaking]`

**Exactly nine operations were removed between the 9.0.0.0 and 9.1.0.0 tags, and all nine
are `/hvc/*`** — Hybrid Linked Mode. Verbatim from `research/spec-inventory/DELTA-9.0-to-9.1.md`:

```
DELETE /hvc/links/{link}                            Vcenter.Hvc.Links_delete
GET    /hvc/links                                   Vcenter.Hvc.Links_list
GET    /hvc/links/{link}                            Vcenter.Hvc.Links_get
GET    /hvc/management/administrators               Vcenter.Hvc.Management.Administrators_get
POST   /hvc/links                                   Vcenter.Hvc.Links_create
POST   /hvc/links/{link}?action=delete              Vcenter.Hvc.Links_deleteWithCredentials
POST   /hvc/management/administrators?action=add    Vcenter.Hvc.Management.Administrators_add
POST   /hvc/management/administrators?action=remove Vcenter.Hvc.Management.Administrators_remove
PUT    /hvc/management/administrators               Vcenter.Hvc.Management.Administrators_set
```

**Why it belongs in an inventory file.** Hybrid Linked Mode is what joined a remote
vCenter's SSO domain — and therefore its inventory — to the local one. Any script that
enumerated inventory across an HLM link, or that created or audited those links, breaks
at 9.1: the paths return 404 and **there is no renamed successor in the 9.1 spec**. This is
a whole capability withdrawn, not a deprecation with a grace period.

Also worth the context: of the seven products present at both tags, only two remove anything
at all, and `/hvc/*` is the largest single removal in the whole 9.0 → 9.1 delta.

> **What the spec does not tell you, and no retrieved page covered — `UNVERIFIED` on all
> three:** whether **existing** HLM links keep working after the upgrade or are torn down;
> whether a replacement mechanism exists in 9.1; and whether the upgrade pre-checks for or
> blocks on the presence of HLM links. The *removal* is machine-confirmed from the two tags.
> The operational consequence is inferred from it and must be confirmed against Broadcom's
> 9.1 vCenter documentation before upgrading an instance that uses HLM. Related deprecation
> for context: **Enhanced Linked Mode was deprecated at 9.0** in favour of grouping under
> VCF Operations **[DOC]** — ELM and HLM are different features, do not conflate them.

### Newly deprecated at 9.1 — none in this scope

28 operations became `deprecated: true` at 9.1. **All 28 are under
`/vcenter/namespace-management`, `/vcenter/namespaces` or `/appliance/health`.** **[SPEC]**
Nothing in inventory traversal, VM lifecycle, power, reconfigure, session or tasks was
deprecated. If someone tells you a VM operation is deprecated in 9.1, that is wrong.

---

## Out of scope — where to route instead

| Topic | Paths | Skill |
|---|---|---|
| Content library, library items, VM template items | `/api/content/*` (**83 ops at 9.1**, up from 72), `/api/vcenter/vm-template/library-items/*` | `vsphere-content-tags-policies` |
| Tags and categories | `/api/cis/tagging/*` (30 ops), `/api/vcenter/tagging/{associations,categories,tags}` — 9.1 adds `PATCH /api/vcenter/tagging/associations` | `vsphere-content-tags-policies` |
| Storage policies and compliance | `/api/vcenter/storage/policies*`, `/api/vcenter/datastore/{datastore}/default-policy` | `vsphere-content-tags-policies` |
| ESX images, drafts, depots, remediation, configuration profiles | `/api/esx/settings/*` (**344 ops at 9.1**) | `vsphere-lifecycle-vlcm` |
| SSO, federation, token exchange, identity providers | — | `vcf-foundation` |
| Anything not covered anywhere | — | `vcf-api-discovery` |

> **Path-separator note, since the dossier left it open.** The dossier could not resolve
> whether vLCM lives at `/api/esx/settings/...` or `/api/esx-settings/...`. The 9.1 ops
> inventory settles it: the paths are **`/esx/settings/...`** (slash), 344 operations.
> **[SPEC]** Detail belongs to `vsphere-lifecycle-vlcm`; this note exists only so nobody
> re-litigates the separator here.

---

## What is unverified for 9.1

- **Session idle timeout.** No number in the spec; no 9.1 page retrieved states one. Build
  for re-authentication on 401.
- **Whether `/api/cis/session` also resolves.** The spec declares only `/session`. The
  portal renders the `cis` form. Only one of these is evidence; the other is prose.
- **Behavior when a list operation exceeds its cap** — silent truncation versus
  `UnableToAllocateResource`. The caps are spec-stated; the over-limit behavior is not.
- **`Vcenter.Vm.Hardware.Version` enum member names** — the hardware-version identifiers for
  vmx-22 and its predecessors were not extracted. Read them from the spec before hard-coding.
- **Whether CPU/memory `hot_add_enabled` can be changed on a powered-on VM.** Not stated on
  those operations. `[INFERRED]` that it cannot.
- **Tag and category operation semantics.** The dossier flags the tag/category operation
  tables as unverified from the portal. The *paths* are now spec-confirmed (30 operations
  under `/cis/tagging`, plus four under `/vcenter/tagging`), but their bodies and semantics were not researched here and belong
  to `vsphere-content-tags-policies` regardless.
- **`filter.*`-prefixed parameter names.** The dossier recorded these as unretrieved; the
  spec shows the parameters are **not** prefixed. If a customer's inherited script uses
  `filter.names`, that is `/rest`-era syntax, not `/api`.
- **The 9.1 Query API.** Announced in the release notes; **no path exists in the 9.1 ops
  inventory**. Paths, verbs and payloads `UNVERIFIED`.
- **The vCenter Group Federated API (VGFA).** Announced in the release notes; **no
  corresponding path in the 9.1 ops inventory**. `UNVERIFIED`.
- **The full extent of the Utilization API.** Three operations are spec-confirmed
  (`/vcenter/utilization/connections`, `/vcenter/utilization/proxies`,
  `/vcenter/capacity/usage`); whether the announced API is larger than those is `UNVERIFIED`.
- **Fate of existing Hybrid Linked Mode links across the 9.0 → 9.1 upgrade**, and whether
  any replacement exists. The removal of the nine `/hvc/*` operations is machine-confirmed;
  the consequence is not documented on any page retrieved.
- **The 9.1 OAuth 2.0 grant/flow details.** The release notes announce OAuth 2.0 token
  support; the token-exchange endpoint itself predates 9.x. What specifically changed at 9.1
  is `UNVERIFIED` — `vcf-foundation` owns this question.
