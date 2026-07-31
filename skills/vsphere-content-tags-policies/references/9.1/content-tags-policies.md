# vSphere content library, tags and storage policies — VCF 9.1

**Applies to:** vCenter **9.1.0.0**, the version in the VCF 9.1 Bill of Materials.
**Do not apply this file to VCF 9.0.** Use `../9.0/content-tags-policies.md` for 9.0 and
`../deltas.md` for the change list.

## Provenance of everything below

| Tag | Meaning |
|---|---|
| **[SPEC-A]** | The exact `method + path` was found in `research/spec-inventory/9.1__vsphere-automation.ops.json`, machine-extracted from `specifications/vsphere/openapi/automation/vcenter.yaml` at git tag `9.1.0.0` of `github.com/vmware/vcf-api-specs` (`info.version: 9.1.0.0`, `servers[0].url: https://{host}/api`, 1,367 operations). Schema and description quotes come from that same file. |
| **[SPEC-V]** | Same, but for the **VI-JSON** surface: `9.1__vsphere-vi-json.ops.json`, from `specifications/vsphere/openapi/vi-json/vi-json.yaml` at the same tag (`info.version: 9.1.0.0`, `servers[0].url: https://{vcenter-host}/sdk/vim25/{release}`, 2,243 operations). |
| **[DOC]** | Verified only from version-pinned Broadcom prose captured in `research/vsphere-vcenter-vsan.md`. |
| **[INFERRED]** | Neither — a shape or convention, not a verified fact. Confirm before relying on it. |
| **`UNVERIFIED`** | The research could not establish it. Do not fill the gap by guessing. |

**All of it was captured 2026-07-31 and none of it has been run against a live vCenter.** The
operations in this file that change production state are `DELETE` and `force-delete` on a
library or library item (content removal from the storage backing is asynchronous and may need
manual cleanup on failure; `force-delete` additionally *skips the usage check*) and any change
to a storage policy that is in use (`PATCH /vcenter/vm/{vm}/storage/policy`, `PbmUpdate`,
`PbmDelete` — these re-apply to every bound object). Resolve the target with a `GET`, read
`usages`, and check what is bound, before executing any of them.

**Every operation in this file is tagged with the surface it belongs to.** Storage-policy
authoring is on a different surface from storage-policy reading, and getting it wrong
produces a 404 that reads like a permissions problem.

**A `[SPEC-A]` / `[SPEC-V]` tag in this file is evidence about 9.1**, extracted independently
from the 9.1 tag. The 9.0 file carries its own.

---

## Contents

- [Provenance](#provenance-of-everything-below)
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — base path, session header, surface](#p1--you-are-on-the-right-base-path-with-a-live-session-header)
  - [P2 — a library has a resolved storage backing](#p2--the-library-you-are-creating-has-a-resolved-storage-backing)
  - [P3 — publishing and subscribing are configured before create](#p3--publishing-and-subscribing-are-configured-before-create-not-after)
  - [P4 — the category exists before the tag](#p4--the-category-exists-before-the-tag)
  - [P5 — cardinality and associable types permit the attach](#p5--the-categorys-cardinality-and-associable-types-permit-the-attach)
  - [P6 — identifiers resolved, not constructed](#p6--you-resolved-identifiers-rather-than-constructing-them)
  - [P7 — the policy is attached before you ask about compliance](#p7--the-policy-is-attached-before-you-ask-about-compliance)
  - [P8 — the PBM surface is reachable and you hold its managed-object ids](#p8--the-pbm-surface-is-reachable-and-you-hold-its-managed-object-ids)
  - [P9 — the library is `ACTIVE` and has no usages before you delete it](#p9--the-library-is-active-and-has-no-usages-before-you-delete-it) — **9.1-only**
  - [P10 — privileges, per object, per surface](#p10--privileges-per-object-per-surface)
- [Surfaces and base paths](#surfaces-and-base-paths)
- [Content library](#content-library) — libraries, items, sessions, subscriptions, deploy, **maintenance and usages**
- [Tags and categories](#tags-and-categories) — **the dossier's `UNVERIFIED` resolved**
- [Storage policies](#storage-policies) — read/compliance on `/api`, authoring on `/pbm`
- [**Worked example** — create a category, create a tag, attach it to a VM](#worked-example--create-a-category-create-a-tag-attach-it-to-a-vm) (Steps 0–6 + [failure decode](#failure-decode-for-this-sequence))
- [Out of scope — where to route instead](#out-of-scope--where-to-route-instead)
- [What is unverified for 9.1](#what-is-unverified-for-91)

---

## Prerequisites

Everything here must be true **before** you issue any content-library, tagging or
storage-policy call. Each item carries four elements — if one is missing the item is
incomplete:

1. **What must be true.**
2. **How to verify it** — a concrete, *non-destructive* check.
3. **Which version it applies to** — every item applies to **vCenter 9.1.0.0** unless said
   otherwise.
4. **Whether it exists in 9.0** — stated as a "9.0 difference" line on every item.

### P1 — You are on the right base path, with a live session header

- **Must be true:** the vSphere Automation calls in this file go to
  **`https://<vcenter>/api/...`** — `servers[0].url` is `https://{host}/api` **[SPEC-A]** —
  and every one of them carries the **`vmware-api-session-id`** header (security scheme
  `api_key_auth`, `type: apiKey`, `in: header`) **[SPEC-A]**. The PBM operations go to
  **`https://<vcenter>/sdk/vim25/{release}/pbm/...`** and take the **same header** (VI-JSON
  security scheme `Session`, `apiKey`, header `vmware-api-session-id`) **[SPEC-V]**.
- **Obtaining the credential is `vcf-foundation`'s job.** This file states the mechanism and
  the base path and stops there.
- **Verify:** `GET /api/content/library` **[SPEC-A — `Content.Library_list`]** returns 200 and
  an array; `GET /sdk/vim25/9.1.0.0/pbm/PbmServiceInstance/{moId}/content` **[SPEC-V —
  `PbmServiceInstance_getContent`]** returns 200 and a `PbmServiceInstanceContent`. A 404 on
  the second while the first works is a *surface* problem, not an auth problem.
- **9.0 difference:** none. Same base paths, same header, same schemes.

### P2 — The library you are creating has a resolved storage backing

- **Must be true:** `Content.LibraryModel.storage_backings` is, verbatim, *"must be provided
  for the `create` operation"* **[SPEC-A]**. A `Content.Library.StorageBacking` has a `type`
  — enum exactly `DATASTORE` and `OTHER` **[SPEC-A]** — plus:
  - `DATASTORE` → `datastore_id`, *"only relevant when the value of type is …DATASTORE"*, an
    identifier for resource type `Datastore`. This is the datastore-backed case.
  - `OTHER` → `storage_uri`; spec-listed forms include `nfs://server/path?version=4`,
    `nfs://server/path`, `smb://server/path` **[SPEC-A]**.
- **Only one backing.** Both `Content.LocalLibrary_create` and `Content.SubscribedLibrary_create`
  declare a 400 `Vapi.Std.Errors.Unsupported` *"if using multiple storage backings"* **[SPEC-A]**.
- **Verify:** resolve the datastore first —`GET /api/vcenter/datastore?names=<ds>` (that
  endpoint belongs to `vsphere-inventory-vm-lifecycle`) — and treat a zero-length array as
  fatal before the create.
- **9.0 difference:** none. Identical schemas and identical error.

### P3 — Publishing and subscribing are configured before create, not after

- **Must be true, publishing side:** `Content.Library.PublishInfo.authentication_method`
  (`BASIC` | `NONE`) and `.published` are both *"required for the
  `POST /content/local-library` operation"* **[SPEC-A]**. Under `BASIC`, the spec's note on
  `user_name`: *"the username is ignored in the current release. It defaults to `vcsp`. It is
  preferable to leave this missing or `null`. If specified, it must be set to `vcsp`."*
  `publish_url` is output-only.
- **Must be true, subscribing side:** `Content.Library.SubscriptionInfo.authentication_method`,
  `.automatic_sync_enabled`, `.on_demand` and `.subscription_url` are all *"must be provided
  for the `create` operation"* **[SPEC-A]**. `ssl_thumbprint`, when set, means *"the standard
  certificate chain validation behavior is not used"*.
- **Verify — probe before you create.** `POST /api/content/subscribed-library?action=probe`
  **[SPEC-A — `Content.SubscribedLibrary_probe`]**, body `{"subscription_info": {…}}`, returns
  a `ProbeResult` whose `status` enum is exactly `SUCCESS`, `INVALID_URL`, `TIMED_OUT`,
  `HOST_NOT_FOUND`, `RESOURCE_NOT_FOUND`, `INVALID_CREDENTIALS`, `CERTIFICATE_ERROR`,
  `UNKNOWN_ERROR` **[SPEC-A]**. On `CERTIFICATE_ERROR` the returned thumbprint *"should be set
  in `Content.Library.SubscriptionInfo.ssl_thumbprint`"* — probe, take the thumbprint, probe
  again, then create. Requires `ContentLibrary.ProbeSubscription`.
- **Consequence of skipping it:** `Content.SubscribedLibrary_create` declares **500
  `ResourceInaccessible`** *"if subscribing to a published library which cannot be accessed"*
  **[SPEC-A]**.
- **9.1-only escape hatch:** if a subscribed library needs to become a publisher, you no
  longer rebuild it. `POST /content/library/{libraryId}?action=convert`
  **[SPEC-A — `Content.Library_convert`, *"added in vSphere API 9.1.0.0"*]** with
  `{"conversion_type": "TO_PUBLISHED_LIBRARY"}` does it — subject to hard preconditions, see
  the content-library section.
- **9.0 difference:** probe, publish and subscribe are identical. **`?action=convert` does not
  exist in 9.0.**

### P4 — The category exists before the tag

- **Must be true:** `Cis.Tagging.Tag.CreateSpec` **requires** `category_id`, `description`
  and `name` **[SPEC-A]**. There is no create-category-implicitly path.
- **The failure is a 404, not a 400.** `Cis.Tagging.Tag_create` declares 404 *"if the category
  for in the given createSpec does not exist in the system"* **[SPEC-A]**; 400 is reserved for
  `AlreadyExists` (*"the name of an already existing tag in the input category"*) and
  `InvalidArgument`.
- **Tag names are unique per category, not globally** — *"The name must be unique within its
  category."* **[SPEC-A]**
- **Verify:** `GET /api/vcenter/tagging/categories?names=<name>` **[SPEC-A —
  `Vcenter.Tagging.Categories_list`; the 9.1 spec still records it as *"added in vSphere API
  9.0.0.0"*]** returns `{items: [{category_id, info}]}`.
- **9.1 shortcut worth knowing:** `PATCH /vcenter/tagging/associations` accepts
  `tag_category_name_info: {tag_name, category_name}` and resolves the ids server-side — so
  for *attaching*, 9.1 lets you skip the id lookup entirely. It does **not** let you skip
  creating the category and tag.
- **9.0 difference:** identical create semantics; the name-based attach does not exist in 9.0.

### P5 — The category's cardinality and associable types permit the attach

- **Must be true:** `Cis.Tagging.Category.CreateSpec` **requires** `associable_types`,
  `cardinality`, `description` and `name` **[SPEC-A]**. Both constraints are enforced at
  *attach* time:
  - **`cardinality`** — enum exactly `SINGLE` | `MULTIPLE` **[SPEC-A]**. *"`SINGLE`: An object
    can only be assigned one of the tags in this category"*; *"`MULTIPLE`: An object can be
    assigned several of the tags in this category"*.
  - **`associable_types`** — *"Object types to which this category's tags can be attached."*
    Fuller wording on `CategoryModel`: *"If the set is empty, then tags can be attached to all
    types of objects. This field works only for objects that reside in Inventory Service (IS).
    For non IS objects, this check is not performed today and hence a tag can be attached to
    any non IS object."* **[SPEC-A]**
- **The attach operation says so itself.** `Cis.Tagging.TagAssociation_attach`, verbatim: *"The
  tag needs to meet the cardinality … and associability … criteria in order to be eligible for
  attachment."* Its 400 is *"if the input tag is not eligible to be attached to this object or
  if the objectId is not valid"* **[SPEC-A]** — one code, two very different causes.
- **Verify — non-destructively:**
  `POST /api/cis/tagging/tag-association?action=list-attachable-tags` **[SPEC-A —
  `Cis.Tagging.TagAssociation_listAttachableTags`]**, body `{"object_id": DynamicID}`.
  *"Fetches the list of attachable tags for the given object, omitting the tags that have
  already been attached."*
- **9.0 difference:** none. Identical schemas, identical enum, identical wording.

### P6 — You resolved identifiers rather than constructing them

- **Must be true:** every id here is server-issued. Resource types per field **[SPEC-A]**:
  library `com.vmware.content.Library`, item `com.vmware.content.library.Item`, subscription
  `com.vmware.content.library.Subscriptions`, category `com.vmware.cis.tagging.Category`, tag
  `com.vmware.cis.tagging.Tag`, policy `com.vmware.vcenter.StoragePolicy`, plus `Datastore`,
  `VirtualMachine` and `com.vmware.vcenter.vm.hardware.Disk`.
- **The `/cis/tagging` list operations give you ids and nothing else** — *"The list of resource
  identifiers for the categories in the system"*, a bare `array of string`; same for tags
  **[SPEC-A]**. Name → id goes through `/vcenter/tagging/*`:
  - `GET /api/vcenter/tagging/categories?names=<n>` → `{items: [{category_id, info}], marker?}`,
    `info` = `{name, description, cardinality, associable_types, used_by}`.
  - `GET /api/vcenter/tagging/tags?names=<n>` → `{items: [{tag, info}], marker?}`, `info` =
    `{name, category, description, used_by}` where `category` is the **category id**.
  - Both declare **400 *"If marker and filter are supplied together"*** **[SPEC-A]** — page, or
    filter, not both.
- **Storage policies have no name filter at all.** `GET /api/vcenter/storage/policies` takes
  only `policies` (ids) **[SPEC-A]**; match `Summary.name` client-side. *"at most 1024
  visible"*, with **500 `UnableToAllocateResource` *"if more than 1024 storage policies
  exist"*** — an explicit error, not silent truncation.
- **9.1 relaxes exactly one case:** `PATCH /vcenter/tagging/associations` takes a tag by name
  **and** category name (`Vcenter.Tagging.Associations.TagCategoryNameInfo`, **required**
  `tag_name` and `category_name`). Everything else still needs ids.
- **9.0 difference:** identical, minus that one relaxation.

### P7 — The policy is attached before you ask about compliance

- **Must be true:** compliance is computed against a policy *binding*. Two spec statements
  **[SPEC-A]**:
  - `Vcenter.Storage.Policies.Compliance_list` — *"**Entities without storage policy
    association are not returned.**"*
  - `Vcenter.Storage.Policies.Compliance.VM_list` — *"**Virtual machines without storage policy
    association are not returned.**"*

  An empty result is therefore ambiguous between "all compliant" and "nothing bound".
- **Verify the binding first:** `GET /api/vcenter/vm/{vm}/storage/policy` **[SPEC-A —
  `Vcenter.Vm.Storage.Policy_get`]** → `{vm_home?, disks}`. *"If missing or `null`, the virtual
  machine's home directory doesn't have any storage policy."*
- **Cached versus recomputed.** `GET /api/vcenter/vm/{vm}/storage/policy/compliance` returns
  *"the **cached** … compliance information"*; `POST …/compliance?action=check` returns it
  *"after explicitly **re-computing** compliance check"* **[SPEC-A]**.
- **9.0 difference:** none. Identical operations, wording and schemas.

### P8 — The PBM surface is reachable and you hold its managed-object ids

- **Must be true:** every `/pbm` operation is
  `POST /sdk/vim25/{release}/pbm/{ManagedObjectType}/{moId}/{Operation}` **[SPEC-V]**, and
  `{moId}` is a real managed-object id. The spec's `moId` parameter description: *"A unique
  identifier (within this vCenter Server instance) for a specific managed object such as
  `group-d1` or `vm-015` or `ServiceInstance`."* **[SPEC-V]**
- **Verify / bootstrap:** `POST /sdk/vim25/9.1.0.0/pbm/PbmServiceInstance/{moId}/PbmRetrieveServiceContent`
  **[SPEC-V — `PbmServiceInstance_PbmRetrieveServiceContent`]** or `GET .../content`
  **[SPEC-V — `PbmServiceInstance_getContent`]**. Both return `PbmServiceInstanceContent` with
  `aboutInfo`, `sessionManager`, `capabilityMetadataManager`, **`profileManager`**,
  **`complianceManager`**, **`placementSolver`**, `replicationManager` **[SPEC-V]**. Those
  three bolded values are the `{moId}` for every other `/pbm` call. Both require only
  `System.Anonymous` **[SPEC-V]** — the cheapest possible probe.
- **The concrete `{moId}` for `PbmServiceInstance` itself is not stated in the spec.**
  `UNVERIFIED` — confirm on first run.
- **The PBM schemas state the surface split themselves.** `PbmServerObjectRef`,
  `PbmCapabilityProfileCreateSpec` and `PbmComplianceResult` each say *"This structure may be
  used only with operations rendered under `/pbm`."* **[SPEC-V]**
- **9.0 difference:** none. All 33 `/pbm` operations, the same 5 deprecated ones, and
  `PbmServiceInstanceContent` are byte-identical at the 9.0 tag.

### P9 — The library is `ACTIVE` and has no usages before you delete it

**This item is 9.1-only. It has no 9.0 equivalent, and it is the most consequential change in
this scope.**

- **Must be true, state:** `Content.Library.StateInfo.state` (enum `ACTIVE` | `MAINTENANCE`)
  must be `ACTIVE` for content-mutating operations. Verbatim: *"This is the library state when
  library is in migration. Library content will be inaccessible and operations mutating
  library content will be disallowed when in this state."* **[SPEC-A]** At 9.1 you can enter
  and leave that state deliberately —
  `POST /content/library/{libraryId}?action=enter-maintenance` and `?action=exit-maintenance`
  **[SPEC-A — `Content.Library_enterMaintenance` / `_exitMaintenance`, both *"added in vSphere
  API 9.1.0.0"*]**, both requiring `ContentLibrary.LibraryMaintenance`. `enterMaintenance`
  *"will raise a NotAllowedInCurrentState error with appropriate message indicating that it
  cannot enter MAINTENANCE at this time"* if a restricted operation is already running.
- **Must be true, usage:** 9.1 adds a usage-tracking surface.
  `GET /content/library/{library}/usages` **[SPEC-A — `Content.Library.Usages_list`, *"added in
  vSphere API 9.1.0.0"*]** — *"Retrieves the list of resources currently using a content
  library. **A content library can be safely deleted if no usage is present for that
  library.**"* Entries are `{usage, resource_urn}`, with `addition_time` on the single-usage
  `get`.
- **The new `DELETE /content/library/{libraryId}` respects it.** **[SPEC-A —
  `Content.Library_delete`]** Its 400 `NotAllowedInCurrentState` covers both *"if the library
  contains a library item that cannot be deleted in its current state"* **and** *"**If the
  library is currently used by other resource(s).**"*
- **Verify:** `GET /content/library/{library}/usages` — an empty list is the green light.
  `GET /content/library/{libraryId}` and read `state_info.state` for `ACTIVE`.
- **The escape hatch is real and it is dangerous.** Three `force-delete` operations *"skip the
  usage check"* **[SPEC-A]**:
  `POST /content/library/{libraryId}?action=force-delete` (`Content.Library_forceDelete`,
  *"applies to all library types"*),
  `POST /content/local-library/{libraryId}?action=force-delete` (`Content.LocalLibrary_forceDelete`),
  `POST /content/subscribed-library/{libraryId}?action=force-delete`
  (`Content.SubscribedLibrary_forceDelete`). All three carry the same warning as the ordinary
  delete: *"If the asynchronous task fails, file content may remain on the storage backing.
  This content will require manual removal."* **Do not reach for `force-delete` because the
  ordinary delete returned 400 — read the usages first and find out what is using it.**
- **9.0 difference:** **none of this exists in 9.0.** No `DELETE /content/library/{libraryId}`,
  no `usages` sub-resource, no `force-delete` on any type, no explicit maintenance
  enter/exit. In 9.0 the only delete is per-type (`/content/local-library/{id}`,
  `/content/subscribed-library/{id}`), there is no usage check, and the only route into
  `MAINTENANCE` is `?action=migrate`. A 9.1 runbook run against 9.0 404s on these paths.

### P10 — Privileges, per object, per surface

- **Content library — the spec states the privilege on every operation** **[SPEC-A]**:

  | Operation | Privilege |
  |---|---|
  | `Content.LocalLibrary_create` | `ContentLibrary.CreateLocalLibrary` **plus** `Datastore.AllocateSpace` on the backing datastore |
  | `Content.SubscribedLibrary_create` | `ContentLibrary.CreateSubscribedLibrary` + `Datastore.AllocateSpace` |
  | `Content.SubscribedLibrary_probe` | `ContentLibrary.ProbeSubscription` |
  | `Content.LocalLibrary_publish` | `ContentLibrary.PublishLibrary` |
  | `Content.Library.Item_create` / `_update` / `_delete` | `ContentLibrary.AddLibraryItem` / `UpdateLibraryItem` / `DeleteLibraryItem` |
  | `Content.Library_migrate` | `ContentLibrary.MigrateLibrary` |
  | **`Content.Library_delete` / `_forceDelete`** | **`ContentLibrary.DeleteLibrary`** — 9.1-only privilege |
  | **`Content.Library_convert`** | **`ContentLibrary.ConvertLibrary`** — 9.1-only |
  | **`Content.Library_enterMaintenance` / `_exitMaintenance`** | **`ContentLibrary.LibraryMaintenance`** — 9.1-only |
  | **`Content.Library.Usages_add` / `_remove`** | **`ContentLibrary.AddLibraryUsage`** / **`ContentLibrary.RemoveLibraryUsage`** — 9.1-only |
  | `Content.Library_list` / `_get` / `Usages_list` | `System.Read` |

- **Tagging — 9.1 is the first version where the spec names privilege strings at all.** The
  `/cis/tagging` operations still describe them in prose (*"you need the attach tag privilege
  on the tag and the read privilege on the object"*), but the new
  `PATCH /vcenter/tagging/associations` states its 403 precisely **[SPEC-A]**: *"if the user
  does not have `InventoryService.Tagging.ObjectAttachable` on the
  `Vcenter.Tagging.Associations.UpdateSpec.object` and `InventoryService.Tagging.AttachTag` on
  the tags specified in the `Vcenter.Tagging.Associations.TagSpec`."* Those two strings are the
  **only** `InventoryService.Tagging.*` strings in the 9.1 spec; the prose privileges on the
  `/cis/tagging` operations still have no canonical spelling.
- **Storage policy — split by surface.**
  - `/pbm` names them exactly **[SPEC-V]**: **`StorageProfile.Update`** on `PbmCreate`,
    `PbmUpdate`, `PbmDelete`, `PbmAssignDefaultRequirementProfile`,
    `PbmResetDefaultRequirementProfile`, `PbmResetVSanDefaultProfile`;
    **`StorageProfile.View`** on every query, fetch and compliance operation;
    **`System.Anonymous`** on the two service-instance operations.
  - `/api/vcenter/storage/policies*` names **none** — the 403s read only *"if the user doesn't
    have the required privileges"* **[SPEC-A]**. `StorageProfile.View` is **[INFERRED]**.
- **Verify — read, do not test by writing.** `POST /api/vcenter/authorization/permissions?action=list`
  and `GET /api/vcenter/authorization/roles` (`vsphere-inventory-vm-lifecycle`'s territory).
- **9.0 difference:** the 9.1 spec carries **39** distinct `ContentLibrary.*` privilege strings
  against 9.0's **34** — the same 34, plus the five listed above. 9.0 has **no
  `InventoryService.Tagging.*` string anywhere**. `/pbm` privileges are unchanged.

---

## Surfaces and base paths

| Surface | Base | Evidence | Carries |
|---|---|---|---|
| **vSphere Automation** | `https://{host}/api` | `9.1__vsphere-automation.ops.json`, 1,367 ops **[SPEC-A]** | `/content/*` (**83**), `/cis/tagging/*` (30), `/vcenter/tagging/*` (**4**), `/vcenter/storage/policies*` (5), `/vcenter/vm/{vm}/storage/policy*` (4), `/vcenter/vm-template/library-items/*` (12), `/vcenter/ovf/*` (6) |
| **VI-JSON (PBM)** | `https://{vcenter-host}/sdk/vim25/{release}` | `9.1__vsphere-vi-json.ops.json`, 2,243 ops, security scheme `Session` = header `vmware-api-session-id` **[SPEC-V]** | `/pbm/*` (33, of which 5 deprecated) — the **only** place a storage policy can be created, updated or deleted |
| Legacy REST | `https://{host}/rest` | **[DOC]** — deprecated, operations up to vSphere 7.0.2 only | Recognise it in inherited scripts; do not write new work against it |

**Nothing in this scope has a `?vmw-task=true` variant** — zero of the 83 `/content`
operations, zero of the 30 `/cis/tagging` operations, zero of the storage-policy operations
**[SPEC-A]**. Several are asynchronous in effect (library delete, item delete, migrate) and
the spec gives you no task handle for them.

**Nothing in this scope is deprecated at 9.1** on the vSphere Automation surface — zero of the
`/content`, `/cis/tagging`, `/vcenter/tagging` and storage-policy operations carry
`deprecated: true` **[SPEC-A]**. The five deprecated `/pbm` operations are the same five as at
9.0.

---

## Content library

All **[SPEC-A]** unless marked. Paths shown relative to `/api`. **83 operations at 9.1** — the
72 that exist at 9.0 plus 11 new ones, and nothing removed.

### Libraries — three views of one object

`/content/library` is the union view; `/content/local-library` and
`/content/subscribed-library` are the type-specific views. `Content.LibraryModel.type` is the
discriminator, enum exactly `LOCAL` | `SUBSCRIBED`.

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/content/library` | `Content.Library_list` | Ids only. |
| POST | `/content/library?action=find` | `Content.Library_find` | `FindSpec`: `name`, `type`, `storage_backing`. |
| GET | `/content/library/{libraryId}` | `Content.Library_get` | Returns `Content.LibraryModel`. |
| PATCH | `/content/library/{libraryId}` | `Content.Library_update` | *"will only update the common properties for all library types."* |
| **DELETE** | **`/content/library/{libraryId}`** | **`Content.Library_delete`** | **9.1-only.** Type-agnostic delete with a usage check — see P9. |
| **POST** | **`/content/library/{libraryId}?action=force-delete`** | **`Content.Library_forceDelete`** | **9.1-only.** *"skipping the usage check … applies to all library types."* |
| **POST** | **`/content/library/{libraryId}?action=convert`** | **`Content.Library_convert`** | **9.1-only.** See below. |
| **POST** | **`/content/library/{libraryId}?action=enter-maintenance`** | **`Content.Library_enterMaintenance`** | **9.1-only.** |
| **POST** | **`/content/library/{libraryId}?action=exit-maintenance`** | **`Content.Library_exitMaintenance`** | **9.1-only.** *"Once the state … is changed from MAINTENANCE to ACTIVE, all operations are permitted."* |
| **GET·POST** | **`/content/library/{library}/usages`** | **`Content.Library.Usages_list` / `_add`** | **9.1-only.** See below. |
| **GET·DELETE** | **`/content/library/{library}/usages/{usage}`** | **`Content.Library.Usages_get` / `_remove`** | **9.1-only.** |
| POST | `/content/library/{libraryId}?action=migrate` | `Content.Library_migrate` | *"added in vSphere API 9.0.0.0."* Datastore→datastore only; *"Migrating Virtual machine template items is not supported."* |
| GET·POST | `/content/local-library` | `Content.LocalLibrary_list` / `_create` | Create takes optional `Client-Token` header (a UUID) for idempotency; **201** with the new id. |
| GET·PATCH·DELETE | `/content/local-library/{libraryId}` | `..._get` / `_update` / `_delete` | |
| **POST** | **`/content/local-library/{libraryId}?action=force-delete`** | **`Content.LocalLibrary_forceDelete`** | **9.1-only.** |
| POST | `/content/local-library/{libraryId}?action=publish` | `Content.LocalLibrary_publish` | |
| GET·POST | `/content/subscribed-library` | `Content.SubscribedLibrary_list` / `_create` | 500 `ResourceInaccessible` if the source is unreachable (P3). |
| GET·PATCH·DELETE | `/content/subscribed-library/{libraryId}` | `..._get` / `_update` / `_delete` | |
| **POST** | **`/content/subscribed-library/{libraryId}?action=force-delete`** | **`Content.SubscribedLibrary_forceDelete`** | **9.1-only.** |
| POST | `/content/subscribed-library/{libraryId}?action=sync` · `evict` | `..._sync` / `_evict` | |
| POST | `/content/subscribed-library?action=probe` | `Content.SubscribedLibrary_probe` | P3. |
| GET·POST | `/content/library/{library}/subscriptions` | `Content.Library.Subscriptions_list` / `_create` | |
| GET·PATCH·DELETE | `/content/library/{library}/subscriptions/{subscription}` | `..._get` / `_update` / `_delete` | |
| GET·PATCH | `/content/configuration` | `Content.Configuration_get` / `_update` | `automatic_sync_enabled`, `automatic_sync_start_hour`, `automatic_sync_stop_hour`, `maximum_concurrent_item_syncs`. Global. |
| GET | `/content/security-policies` | `Content.SecurityPolicies_list` | `{policy, name, item_type_rules}`. |
| GET·POST | `/content/trusted-certificates` · GET·DELETE `/{certificate}` | `Content.TrustedCertificates_*` | |
| GET | `/content/type` | `Content.Type_list` | |

**Usages — the 9.1 answer to "can I delete this library?"**
`Content.Library.Usages.Summary` is `{usage, resource_urn}` (both **required**);
`Content.Library.Usages.Info` adds `addition_time`. `Content.Library.Usages.AddSpec` requires
`resource_urn`, and the spec gives the format verbatim **[SPEC-A]**:
*"`<urn-scheme>:<global-namespace>:<resource-type>:<resource-id>`"* with examples
`urn:vmomi:vm:vm-12`, `urn:vmomi:supervisor:sup-56789`, `urn:vmomi:namespace:ns-abcde`. Note
that this is a **declared** usage registry — `Usages_add` and `Usages_remove` exist, so a
resource has to register itself (or be registered) to appear. An empty usages list means "no
*declared* usage", which is not identical to "nothing references it". Treat it as a strong
signal, not a proof.

**`?action=convert` — the preconditions are the whole story.** Body is
`Content.Library.ConversionSpec`, **required** `conversion_type`, enum with the single value
`TO_PUBLISHED_LIBRARY` — *"conversion from `Content.SubscribedLibrary` to
`Content.LocalLibrary` with `PublishInfo#published` set to `true`"*. The spec lists five
`NotAllowedInCurrentState` cases verbatim **[SPEC-A]**: *"When the library item(s) in the
library contains VM templates · When `Content.SubscribedLibrary` is on-demand and the content
is not synchronized · When the `Content.SubscribedLibrary` item(s) are not synchronized · When
the library is put to … MAINTENANCE and currently undergoing library migration · When the
published library of the given library is put to … MAINTENANCE and currently undergoing
library migration."* It also declares 400 `InvalidElementType` *"If the library specified by
libraryId is not a subscribed library."* In short: fully synced, no VM templates, not
on-demand-with-missing-content, nobody migrating. Sync first, check items, then convert.

**`Content.LibraryModel` fields you set on create:** `name`, `storage_backings` (both *"must be
provided"*), `description`, `publish_info` (local only), `subscription_info` (subscribed only),
`optimization_info`, `security_policy_id`. Server-owned: `id`, `type`, `creation_time`,
`last_modified_time`, `last_sync_time`, `version`, `state_info`, `publish_info.publish_url`.

**`version` is an optimistic-concurrency token.** On `PATCH`, omitting it declares **500
`ResourceBusy`** *"if the `version` of updateSpec is missing or `null` and the library is being
concurrently updated by another user"*; a stale one is **409 `ConcurrentChange`** **[SPEC-A]**.

> **`DELETE /content/local-library/{libraryId}`, verbatim:** *"Deleting a local library will
> remove the entry immediately and begin an asynchronous task to remove all cached content for
> the library. **If the asynchronous task fails, file content may remain on the storage
> backing. This content will require manual removal.**"* Its 400 cases are `InvalidElementType`
> *"if the library specified by libraryId is not a local library"* and
> `NotAllowedInCurrentState` *"if the library contains a library item that cannot be deleted in
> its current state. For example, the library item contains a virtual machine template and a
> virtual machine is checked out of the library item."* **[SPEC-A]**
>
> At 9.1 you have three delete routes — type-specific `DELETE`, type-agnostic
> `DELETE /content/library/{libraryId}` (usage-checked), and `?action=force-delete`
> (usage-skipping). Prefer the second; reach for the third only after reading `usages`.

### Library items

| Verb | Path | operationId | Notes |
|---|---|---|---|
| POST | `/content/library/item` | `Content.Library.Item_create` | `Content.Library.ItemModel`; `library_id` *"must be provided for the `create` operation"*. Optional `Client-Token`. **201**. |
| GET | `/content/library/item?library_id` | `Content.Library.Item_list` | |
| POST | `/content/library/item?action=find` | `Content.Library.Item_find` | `FindSpec`: `name`, `library_id`, `source_id`, `type`, `cached`. |
| GET·PATCH·DELETE | `/content/library/item/{libraryItemId}` | `..._get` / `_update` / `_delete` | |
| POST | `/content/library/item/{libraryItemId}?action=publish` | `Content.Library.Item_publish` | |
| POST | `/content/library/item/{sourceLibraryItemId}?action=copy` | `Content.Library.Item_copy` | |
| GET | `/content/library/item/{libraryItemId}/file` · `?name` | `Content.Library.Item.File_list` / `_get` | |
| GET | `/content/library/item/{libraryItemId}/storage` · `?file_name` | `Content.Library.Item.Storage_list` / `_get` | |
| GET | `/content/library/item/{libraryItem}/changes` · `/{version}` | `Content.Library.Item.Changes_list` / `_get` | |
| POST | `/content/library/subscribed-item/{libraryItemId}?action=sync` · `evict` | `Content.Library.SubscribedItem_sync` / `_evict` | |

> **`DELETE /content/library/item/{libraryItemId}`, verbatim:** *"This operation will
> immediately remove the item from the library that owns it. The content of the item will be
> asynchronously removed from the storage backings. The content deletion can be tracked with a
> task. In the event that the task fails, an administrator may need to manually remove the
> files from the storage backing. **This operation cannot be used to delete a library item that
> is a member of a subscribed library.** Removing an item from a subscribed library requires
> deleting the item from the original published local library and syncing the subscribed
> library."* **[SPEC-A]**
>
> The spec says *"can be tracked with a task"* but declares no task identifier in the response
> and gives the operation no `vmw-task=true` form. How to obtain that handle is `UNVERIFIED`.

### Upload and download sessions

**20 operations** across `/content/library/item/update-session*` and
`/content/library/item/download-session*` **[SPEC-A]**, identical to 9.0.

**Upload shape:** `POST /content/library/item/update-session` (optional `Client-Token`) →
`POST …/{updateSessionId}/file` (`Content.Library.Item.Updatesession.File.AddSpec`,
**required** `name` and `source_type`; optional `source_endpoint`, `size`, `checksum_info`) →
optionally `?action=validate` → `?action=complete`. `?action=keep-alive` for long transfers;
`?action=cancel` / `?action=fail` to abandon. `Content.Library.Item.UpdateSessionModel` carries
`state`, `expiration_time`, `client_progress`, `error_message`, `preview_info`,
`warning_behavior`.

**Download shape** mirrors it: `create` → `?action=prepare` → `GET …/file?file_name` →
`delete`, with `keep-alive`, `cancel`, `fail`.

### Turning a library item into a VM — and back

Identical to 9.0: **12** `vm-template/library-items` operations and **6** `ovf` operations
**[SPEC-A]**.

| Verb | Path | operationId | Key spec fields |
|---|---|---|---|
| POST | `/vcenter/vm-template/library-items` | `Vcenter.VmTemplate.LibraryItems_create` | `CreateSpec` — **required** `library`, `name`, `source_vm`; optional `description`, `vm_home_storage`, `disk_storage`, `disk_storage_overrides`, `placement`. |
| GET | `/vcenter/vm-template/library-items/{templateLibraryItem}` | `..._get` | |
| POST | `.../{templateLibraryItem}?action=deploy` | `Vcenter.VmTemplate.LibraryItems_deploy` | `DeploySpec` — **required** `name` only; optional `description`, `vm_home_storage`, `disk_storage`, `disk_storage_overrides`, `placement`, `powered_on`, `guest_customization`, `hardware_customization`. |
| POST·GET | `.../check-outs?action=check-out` · `/check-outs` | `..CheckOuts_checkOut` / `_list` | |
| GET·DELETE | `.../check-outs/{vm}` | `..CheckOuts_get` / `_delete` | |
| POST | `.../check-outs/{vm}?action=check-in` | `..CheckOuts_checkIn` | |
| GET | `.../versions` · `/{version}` | `..Versions_list` / `_get` | |
| DELETE | `.../versions/{version}` | `..Versions_delete` | |
| POST | `.../versions/{version}?action=rollback` | `..Versions_rollback` | |
| POST | `/vcenter/ovf/library-item` | `Vcenter.Ovf.LibraryItem_create` | `CreateTarget`: `library_id`, `library_item_id`. |
| POST | `/vcenter/ovf/library-item/{ovfLibraryItemId}?action=deploy` | `Vcenter.Ovf.LibraryItem_deploy` | `DeploymentTarget` **requires** `resource_pool_id`; optional `host_id`, `folder_id`. `ResourcePoolDeploymentSpec` **requires** `accept_all_eula`; carries `name`, `annotation`, `network_mappings`, `storage_mappings`, `storage_provisioning`, **`storage_profile_id`**, `locale`, `flags`, `additional_parameters`, `default_datastore_id`, `vm_config_spec`. |
| POST | `.../{ovfLibraryItemId}?action=filter` | `Vcenter.Ovf.LibraryItem_filter` | Dry run. |
| POST | `/vcenter/ovfs?action=deploy&vmw-task=true` | `Vcenter.Ovfs_deploy$Task` | The one task-form operation adjacent to this scope. |
| GET | `/vcenter/ovf/export-flag` · `/import-flag` | `Vcenter.Ovf.ExportFlag_list` / `ImportFlag_list` | |
| GET | `/vcenter/vm/{vm}/library-item` | `Vcenter.Vm.LibraryItem_get` | Reverse lookup. |
| POST | `/vcenter/iso/image?action=mount` · `unmount` | `Vcenter.Iso.Image_mount` / `_unmount` | |

**`ResourcePoolDeploymentSpec.storage_profile_id` is where the two halves of this skill meet** —
it takes a `com.vmware.vcenter.StoragePolicy` identifier from
`GET /api/vcenter/storage/policies`. Binding at deploy time is cheaper than a later
`PATCH /vcenter/vm/{vm}/storage/policy`.

**Check-out/check-in is not clone.** `check-out` gives an editable VM linked to the item;
`check-in` produces a new **version**; `?action=rollback` returns to an older one. A plain
clone of an inventory template is `vsphere-inventory-vm-lifecycle`'s
`POST /api/vcenter/vm?action=clone`.

---

## Tags and categories

All **[SPEC-A]**. Paths relative to `/api`. **30 operations under `/cis/tagging`** (unchanged
from 9.0) **and 4 under `/vcenter/tagging`** (9.0 has 3).

> ### Path conflict: `/api/cis/tagging` vs `/api/cis-tagging` — resolved in favour of the spec
>
> The research dossier records the tagging group as `/api/cis-tagging/category`,
> `/api/cis-tagging/tag`, `/api/cis-tagging/tag-association`, read off the Broadcom developer
> portal, and marks the per-operation verbs and paths **`UNVERIFIED — could not retrieve`**
> because the `cis-tagging-*` reference pages did not render operation tables.
>
> **The specification declares them with a slash.** At tag `9.1.0.0` the paths are
> `/cis/tagging/category`, `/cis/tagging/tag`, `/cis/tagging/tag-association` and their
> sub-paths, under `servers[0].url = https://{host}/api`, composing to
> `https://<vcenter>/api/cis/tagging/...`. `Cis.Tagging.Category` / `.Tag` / `.TagAssociation`
> are the OpenAPI **tags** — grouping labels, not path segments. The same is true at `9.0.0.0`.
>
> **The dossier's `UNVERIFIED` on the operation tables is resolved by the tables below** — all
> 30 operations, their verbs, their request bodies and their required fields are spec-confirmed
> at this tag. Whether `/api/cis-tagging/...` *also* resolves on a live appliance remains
> `UNVERIFIED`; the spec does not contain that spelling.

### Categories

| Verb | Path | operationId | Body / notes |
|---|---|---|---|
| GET | `/cis/tagging/category` | `Cis.Tagging.Category_list` | 200, `array of string` — ids only. |
| POST | `/cis/tagging/category` | `Cis.Tagging.Category_create` | `CreateSpec` — **required** `associable_types`, `cardinality`, `description`, `name`; optional `category_id`. **201**, id string. |
| GET | `/cis/tagging/category/{categoryId}` | `Cis.Tagging.Category_get` | 200 `Cis.Tagging.CategoryModel`; 404 if absent. |
| PATCH | `/cis/tagging/category/{categoryId}` | `Cis.Tagging.Category_update` | `UpdateSpec`: `name`, `description`, `cardinality`, `associable_types`, all optional. |
| DELETE | `/cis/tagging/category/{categoryId}` | `Cis.Tagging.Category_delete` | **Destructive.** |
| POST | `/cis/tagging/category?action=list-used-categories` | `..._listUsedCategories` | |
| POST | `/cis/tagging/category/{categoryId}?action=add-to-used-by` · `remove-from-used-by` · `revoke-propagating-permissions` | `..._addToUsedBy` / `_removeFromUsedBy` / `_revokePropagatingPermissions` | |

`Cis.Tagging.CategoryModel` — required `associable_types`, `cardinality`, `description`, `id`,
`name`, `used_by`.

### Tags

| Verb | Path | operationId | Body / notes |
|---|---|---|---|
| GET | `/cis/tagging/tag` | `Cis.Tagging.Tag_list` | Ids only. |
| POST | `/cis/tagging/tag` | `Cis.Tagging.Tag_create` | `CreateSpec` — **required** `category_id`, `description`, `name`; optional `tag_id`. **201**. **404 if the category does not exist** (P4). |
| GET | `/cis/tagging/tag/{tagId}` | `Cis.Tagging.Tag_get` | `Cis.Tagging.TagModel` — required `category_id`, `description`, `id`, `name`, `used_by`. |
| PATCH | `/cis/tagging/tag/{tagId}` | `Cis.Tagging.Tag_update` | `UpdateSpec`: `name`, `description` **only** — a tag cannot move category. |
| DELETE | `/cis/tagging/tag/{tagId}` | `Cis.Tagging.Tag_delete` | **Destructive — removes every association.** |
| POST | `/cis/tagging/tag?action=list-tags-for-category` | `..._listTagsForCategory` | Body `{"category_id": "<id>"}` (**required**). |
| POST | `/cis/tagging/tag?action=list-used-tags` | `..._listUsedTags` | |
| POST | `/cis/tagging/tag/{tagId}?action=add-to-used-by` · `remove-from-used-by` · `revoke-propagating-permissions` | `..._addToUsedBy` / `_removeFromUsedBy` / `_revokePropagatingPermissions` | |

### Tag associations — two path shapes on `/cis/tagging`, plus one atomic PATCH on `/vcenter/tagging`

| Verb | Path | operationId | Body |
|---|---|---|---|
| POST | `/cis/tagging/tag-association/{tagId}?action=attach` | `Cis.Tagging.TagAssociation_attach` | `{"object_id": Vapi.Std.DynamicID}` (**required**). **204**. |
| POST | `/cis/tagging/tag-association/{tagId}?action=detach` | `..._detach` | Same body. |
| POST | `/cis/tagging/tag-association/{tagId}?action=attach-tag-to-multiple-objects` | `..._attachTagToMultipleObjects` | *"added in vSphere API 6.5."* `BatchResult`. |
| POST | `/cis/tagging/tag-association/{tagId}?action=detach-tag-from-multiple-objects` | `..._detachTagFromMultipleObjects` | |
| POST | `/cis/tagging/tag-association/{tagId}?action=list-attached-objects` | `..._listAttachedObjects` | No body. |
| POST | `/cis/tagging/tag-association?action=attach-multiple-tags-to-object` | `..._attachMultipleTagsToObject` | `{"object_id", "tag_ids"}` (both **required**). `BatchResult`. |
| POST | `/cis/tagging/tag-association?action=detach-multiple-tags-from-object` | `..._detachMultipleTagsFromObject` | |
| POST | `/cis/tagging/tag-association?action=list-attached-tags` | `..._listAttachedTags` | `{"object_id"}`. |
| POST | `/cis/tagging/tag-association?action=list-attachable-tags` | `..._listAttachableTags` | `{"object_id"}`. P5's pre-check. |
| POST | `/cis/tagging/tag-association?action=list-attached-objects-on-tags` | `..._listAttachedObjectsOnTags` | `TagToObjects[]`. |
| POST | `/cis/tagging/tag-association?action=list-attached-tags-on-objects` | `..._listAttachedTagsOnObjects` | `ObjectToTags[]`. |
| **PATCH** | **`/vcenter/tagging/associations`** | **`Vcenter.Tagging.Associations_update`** | **9.1-only.** See below. |

**Attach and detach are idempotent** — *"If the tag is already attached to the object, then this
operation is a no-op and an error will not be thrown."* **[SPEC-A]**

**The `/cis/tagging` batch forms are not atomic.** They return **200** with a
`Cis.Tagging.TagAssociation.BatchResult`; partial failure appears in `error_messages`, not as
an error status. Read it.

### `PATCH /vcenter/tagging/associations` — the 9.1 addition worth changing your client for

**[SPEC-A — `Vcenter.Tagging.Associations_update`, *"added in vSphere API 9.1.0.0"*]**

Body is `Vcenter.Tagging.Associations.UpdateSpec` — **required** `object` (a
`Vapi.Std.DynamicID`) and `tag_spec_list` (array of `Vcenter.Tagging.Associations.TagSpec`).

`TagSpec` — **required** `operation`, enum exactly **`ATTACH` | `DETACH`**
(`Vcenter.Tagging.Associations.Operation`); optional `tag_id`; optional
`tag_category_name_info` (`{tag_name, category_name}`, both **required** within it). The
constraint, verbatim: *"At least one of `Cis.Tagging.Tag` or
`Vcenter.Tagging.Associations.TagCategoryNameInfo` should be provided. If both are specified,
`TagCategoryNameInfo` must refer to the same `Tag`. If … both are missing or `null`, the update
operation will throw an `InvalidArgument`."*

```json
{
  "object": { "type": "VirtualMachine", "id": "vm-101" },
  "tag_spec_list": [
    { "operation": "ATTACH", "tag_category_name_info": { "tag_name": "production", "category_name": "Environment" } },
    { "operation": "DETACH", "tag_id": "<tag-id>" }
  ]
}
```

Two reasons this matters:

**It is atomic.** Verbatim: *"The … `operation` on tags will be atomic. **Partial completion is
not allowed; in case of failure, the partially applied operation will be rolled back.** … If
one or more `TagSpec` in `tag_spec_list` is invalid, the partially applied operation will be
rolled back and invalid entries will be returned in `UpdateResult.errors` with
`UpdateResult.success` set to `false`."* That is the guarantee `attach-multiple-tags-to-object`
does not give you at either version.

**It takes names.** `tag_category_name_info` removes the two lookup calls that every 9.0 tag
script starts with. Attach and detach can be mixed in one call.

**Response is `Vcenter.Tagging.Associations.UpdateResult`** — **required** `success` (boolean);
optional `results` (array of `ResultItem` = `{operation, tag, tag_category_name_info}`, all
required within it) and `errors` (array of `Vapi.Std.LocalizableMessage`). Two subtleties from
the spec **[SPEC-A]**: `results` is *"populated only when … `success` is set to `true`"*, and it
reports *"which tags were newly added or removed as part of this call"*, **not** which
operations succeeded — re-attaching an already-attached tag succeeds and is absent from
`results`. `errors` is populated *"only when … `success` is set to `false`"*.

**Declared errors:** 400 `InvalidArgument` on an empty or malformed spec; 401; **403 naming the
privileges explicitly** — `InventoryService.Tagging.ObjectAttachable` on the object and
`InventoryService.Tagging.AttachTag` on each tag (P10); 404 *"if the resource object is not
registered on the vCenter Server"*; 500.

**9.0 difference:** this operation does not exist. A 9.1 client using it falls back to
`attach-multiple-tags-to-object` on 9.0 — and loses atomicity and name resolution in the
process. Handle that explicitly rather than letting a 405/404 surprise you.

### `Vapi.Std.DynamicID` — the object reference, and its one gap

```json
{ "type": "<resource type string>", "id": "<managed object id>" }
```

Both **required** **[SPEC-A]**. The spec's description of `type` is *"The type of resource being
identified (for example `com.acme.Person`)"* — a generic placeholder.

> **The concrete `type` strings for vSphere objects are not enumerated anywhere in the vSphere
> Automation spec**, at either tag. Neither `DynamicID.type` nor `CategoryModel.associable_types`
> carries an enum or an example list. This is the single most likely reason a well-formed attach
> returns 400.
>
> **What the corpus does establish:** the 9.1 VI-JSON spec declares managed-object type names as
> path segments, including `VirtualMachine`, `HostSystem`, `ClusterComputeResource`, `Datastore`,
> `Datacenter`, `Folder`, `Network`, `DistributedVirtualPortgroup`, `DistributedVirtualSwitch`,
> `ResourcePool`, `StoragePod`, `VirtualApp` **[SPEC-V]**. That `DynamicID.type` takes exactly
> these strings is **[INFERRED]** — strongly corroborated, not stated.
>
> **How to settle it in one read call:** `GET /api/vcenter/tagging/associations` **[SPEC-A —
> `Vcenter.Tagging.Associations_list`]** returns `Summary` objects `{tag, object}` where `object`
> **is** a `DynamicID`. Any existing association shows the exact spelling the server uses.

### `/vcenter/tagging/*` — the name-lookup surface

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/vcenter/tagging/associations` | `Vcenter.Tagging.Associations_list` | *"added in vSphere API 7.0.0.0."* Paginated: `iterate.marker` in, `{associations, marker?, status}` out. `status` enum `READY` \| `END_OF_DATA`. 400 on a marker this operation did not issue. |
| **PATCH** | **`/vcenter/tagging/associations`** | **`Vcenter.Tagging.Associations_update`** | **9.1-only.** Above. |
| GET | `/vcenter/tagging/categories` | `Vcenter.Tagging.Categories_list` | *"added in vSphere API 9.0.0.0."* `names` filter + `iterate`. `{items: [{category_id, info}], marker?}`. **400 *"If marker and filter are supplied together."*** |
| GET | `/vcenter/tagging/tags` | `Vcenter.Tagging.Tags_list` | Same shape; `info` = `{name, category, description, used_by}`, `category` being the category **id**. |

**This is the only paginated part of tagging.** `/cis/tagging` has no marker, no page size and
no documented cap. Use `END_OF_DATA` as the stop condition, not an empty page.

---

## Storage policies

### Read and compliance — vSphere Automation, `/api`

All **[SPEC-A]**. Identical to 9.0: nine operations plus the datastore default.

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/vcenter/storage/policies` | `Vcenter.Storage.Policies_list` | *"at most 1024 visible … storage policies."* Only filter is `policies` (ids). **500 `UnableToAllocateResource` *"if more than 1024 storage policies exist"***. `Summary` = **required** `policy`, `name`, `description`. |
| POST | `/vcenter/storage/policies/{policy}?action=check-compatibility` | `Vcenter.Storage.Policies_checkCompatibility` | Body `{"datastores": [ids]}` (**required**), *"limited to 1024"*. Returns `CompatibilityInfo.compatible_datastores[].datastore`. |
| GET | `/vcenter/storage/policies/entities/compliance` | `Vcenter.Storage.Policies.Compliance_list` | `status` **required**. Enum `Vcenter.Storage.Policies.Compliance.Status`. `Compliance.Summary` = **required** `vm`, plus `vm_home`, `disks`. |
| GET | `/vcenter/storage/policies/compliance/vm` | `Vcenter.Storage.Policies.Compliance.VM_list` | *"at most 1000 virtual machines."* `status` **required**, `vms` optional. Enum `Vcenter.Storage.Policies.Compliance.VM.Status` — **a different enum**. |
| GET | `/vcenter/storage/policies/{policy}/vm` | `Vcenter.Storage.Policies.VM_list` | Map VM id → `{vm_home: bool, disks: [disk ids]}`. **500 `UnableToAllocateResource` *"if more than 1000 virtual machines are associated with the specified policy"***. The "what would I break" call. |
| GET | `/vcenter/vm/{vm}/storage/policy` | `Vcenter.Vm.Storage.Policy_get` | `Info` = `{vm_home?, disks}`. |
| PATCH | `/vcenter/vm/{vm}/storage/policy` | `Vcenter.Vm.Storage.Policy_update` | **Production-affecting** — see below. |
| GET | `/vcenter/vm/{vm}/storage/policy/compliance` | `Vcenter.Vm.Storage.Policy.Compliance_get` | **Cached.** |
| POST | `/vcenter/vm/{vm}/storage/policy/compliance?action=check` | `Vcenter.Vm.Storage.Policy.Compliance_check` | **Recomputes.** `CheckSpec` optional; when present, **required** `vm_home` (bool), optional `disks`. Omitting the body means *"vmHome set to true and disks populated with all disks attached"*. |
| GET | `/vcenter/datastore/{datastore}/default-policy` | `Vcenter.Datastore.DefaultPolicy_get` | *"the identifier of the current default storage policy associated with the specified datastore."* |

**Exact paths matter.** It is `/vcenter/storage/policies/**entities**/compliance` and
`/vcenter/storage/policies/**compliance/vm**`. The dossier records
`/api/vcenter/storage/policies/compliance` and `/api/vcenter/storage/policies/vm` — neither
exists in the spec, and neither does `/api/vcenter/datastore-default-policy` (it is
`/vcenter/datastore/{datastore}/default-policy`).

**Two enums, three declarations, one difference.** **[SPEC-A]**

| Enum | Used by | Values |
|---|---|---|
| `Vcenter.Storage.Policies.Compliance.Status` | `/vcenter/storage/policies/entities/compliance` | `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN`**, `NOT_APPLICABLE`, `OUT_OF_DATE` |
| `Vcenter.Storage.Policies.Compliance.VM.Status` | `/vcenter/storage/policies/compliance/vm` | `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN_COMPLIANCE`**, `NOT_APPLICABLE`, `OUT_OF_DATE` |
| `Vcenter.Vm.Storage.Policy.Compliance.Status` | `/vcenter/vm/{vm}/storage/policy/compliance` | `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN_COMPLIANCE`**, `NOT_APPLICABLE`, `OUT_OF_DATE` |

Both list endpoints declare **400 `InvalidArgument`** if `status` *"contains a value that is not
supported by the server"* — sending `UNKNOWN` to `/compliance/vm` is a 400, not an empty list.
`OUT_OF_DATE`, verbatim: *"Compliance status becomes out of date when the profile associated
with the entity is **edited and not applied**. The compliance status will remain out of date
until the latest policy is applied."*

**`PATCH /vcenter/vm/{vm}/storage/policy` — `Vcenter.Vm.Storage.Policy.UpdateSpec`:**

```json
{
  "vm_home": { "type": "USE_SPECIFIED_POLICY", "policy": "<policy-id>" },
  "disks":   { "<disk-id>": { "type": "USE_DEFAULT_POLICY" } }
}
```

Both properties optional — *"if missing or `null` the current storage policy is retained"*.
Inside each, `type` is **required**, enum exactly `USE_SPECIFIED_POLICY` | `USE_DEFAULT_POLICY`,
and `policy` is *"only relevant when the value of type is …USE_SPECIFIED_POLICY"* **[SPEC-A]**.
Errors: 400 `InvalidArgument` *"if the storage policy specified is invalid"*; 500 `ResourceBusy`
*"if the virtual machine or disk is busy performing another operation"*; 500
`ResourceInaccessible`.

> **This is the production-affecting call in this file.** Re-binding a VM home or disk triggers
> whatever the storage provider does to satisfy the new requirements — on vSAN, a resync.
> Before running it: `GET .../storage/policy` to record the current binding,
> `POST /vcenter/storage/policies/{policy}?action=check-compatibility` against the target
> datastore, and — if you are changing the *policy itself* rather than one VM's binding —
> `GET /vcenter/storage/policies/{policy}/vm` to see every VM and disk that moves with it.

**9.1 adds four Supervisor storage-policy operations** with no 9.0 equivalent **[SPEC-A]**:
`GET·PATCH /vcenter/namespace-management/supervisors/{supervisor}/control-plane/storage/policies`
(`Vcenter.NamespaceManagement.Supervisors.ControlPlane.Storage.Policies_get` / `_update`) and
`GET·PATCH /vcenter/namespace-management/supervisors/{supervisor}/workloads/storage/policies`
(`...Workloads.Storage.Policies_get` / `_update`), all *"added in vSphere API 9.1.0.0"*, the
`GET`s requiring `System.Read` on the Supervisor. These configure which policies a Supervisor
offers, not the policies themselves — Supervisor/namespace management is not covered by this
skill or its siblings; route it to `vcf-api-discovery`.

### Authoring — VI-JSON, `/pbm`, and only there

All **[SPEC-V]**. Base `https://{vcenter-host}/sdk/vim25/{release}`, so a full URL is
`https://vcenter.example.com/sdk/vim25/9.1.0.0/pbm/PbmProfileProfileManager/{moId}/PbmCreate`.
All `POST` except `PbmServiceInstance_getContent`. **33 operations at 9.1, of which 5 are
deprecated — byte-identical to 9.0.**

**Entry point (P8):** `PbmServiceInstance_PbmRetrieveServiceContent` or
`GET /pbm/PbmServiceInstance/{moId}/content` → `PbmServiceInstanceContent` → take
`profileManager`, `complianceManager`, `placementSolver` as the `{moId}` for everything below.

**`PbmProfileProfileManager` — 20 operations.** Authoring: `PbmCreate`, `PbmUpdate`, `PbmDelete`
(all `StorageProfile.Update`). Query: `PbmQueryProfile`, `PbmRetrieveContent`,
`PbmQueryAssociatedEntity`, `PbmQueryAssociatedEntities`, `PbmQueryAssociatedProfile`,
`PbmQueryAssociatedProfiles`, `PbmQuerySpaceStatsForStorageContainer`. Capability metadata:
`PbmFetchCapabilityMetadata`, `PbmFetchCapabilitySchema`, `PbmFetchResourceType`,
`PbmFetchVendorInfo`. Defaults: `PbmAssignDefaultRequirementProfile`,
`PbmQueryDefaultRequirementProfile`, `PbmQueryDefaultRequirementProfiles`,
`PbmFindApplicableDefaultProfile`, `PbmResetVSanDefaultProfile`, and
`PbmResetDefaultRequirementProfile` (**deprecated**).

**`PbmComplianceManager` — 5:** `PbmCheckCompliance`, `PbmCheckRollupCompliance`,
`PbmFetchComplianceResult`, `PbmFetchRollupComplianceResult`, `PbmQueryByRollupComplianceStatus`.
All `StorageProfile.View`.

**`PbmPlacementSolver` — 5:** `PbmCheckRequirements` (current), plus `PbmCheckCompatibility`,
`PbmCheckCompatibilityWithSpec`, `PbmQueryMatchingHub`, `PbmQueryMatchingHubWithSpec` — **all
four deprecated**, at 9.1 as at 9.0. Prefer `PbmCheckRequirements`, or the `/api`
`checkCompatibility` for the simple datastore question.

**`PbmReplicationManager`:** `PbmQueryReplicationGroups`.

**`PbmCreate` body — `PbmCreateRequestType` = `{createSpec: PbmCapabilityProfileCreateSpec}`.**
`PbmCapabilityProfileCreateSpec` **requires `name`, `resourceType`, `constraints`**; optional
`description`, `category` **[SPEC-V]**. Two traps:

- **`resourceType` is required *and* deprecated** — *"Deprecated as of vSphere API 6.5. …
  The only legal value is STORAGE - deprecated."* It is in the `required` array. Send it.
- **`category`** — *"This can be REQUIREMENT … or null when creating a storage policy. And it
  can be DATA\_SERVICE\_POLICY … when creating a data service policy. RESOURCE … is not allowed
  as resource profile is created by the system."*

`name` — *"The maximum length of the name is 80 characters."* `constraints` is a
`PbmCapabilityConstraints` holding `subProfiles[]`, each a `PbmCapabilitySubProfile` (`name`,
`capability[]`, `forceProvision`) — *"A subprofile corresponds to a rule set in the vSphere Web
Client."* Build the capability expressions from `PbmFetchCapabilityMetadata` /
`PbmFetchCapabilitySchema`; do not hand-write them.

`PbmCreate` declares a **500** carrying `InvalidArgument` *"if `PbmCapabilityProfileCreateSpec`
is invalid"*, `PbmFaultProfileStorageFault`, or `PbmDuplicateName` *"if a profile with the same
name already exists"* **[SPEC-V]**. VI-JSON reports faults as **500**, not 400 — a validation
error here does not look like one.

**`PbmDelete` will refuse a policy in use.** Its result is an array of
`PbmProfileOperationOutcome`; the spec lists `PbmResourceInUse` — *"Profile is still associated
with an entity"* — among the faults **[SPEC-V]**. Deletion is reported per-profile: a 200 does
not mean every id in your request was deleted.

**Object references on `/pbm` are `PbmServerObjectRef`, not `DynamicID`.** **Required**
`objectType` and `key`; optional `serverUuid`. Key mapping, verbatim: `virtualMachine` →
*virtual-machine-MOR*; `virtualDiskId` → *virtual-disk-MOR:VirtualDisk.key*; `datastore` →
*datastore-MOR* **[SPEC-V]**. Lower-camel object type names — **not** the same strings as
tagging's `DynamicID.type`.

**`PbmCheckCompliance` body** = `{entities: PbmServerObjectRef[], profile?: PbmProfileId}`;
`PbmProfileId` is `{uniqueId}`. Results are `PbmComplianceResult` = `{checkTime, entity, profile,
complianceTaskStatus, complianceStatus, violatedPolicies, errorCause, operationalStatus, info,
mismatch(deprecated)}` **[SPEC-V]**. The value spaces of `complianceStatus`
(`PbmComplianceStatus_enum`) and `complianceTaskStatus`
(`PbmComplianceResultComplianceTaskStatus_enum`) are referenced by name but **not expanded as
JSON schema enums** in `vi-json.yaml` — `UNVERIFIED` from this corpus. Use the `/api`
compliance endpoints when you need enum values you can rely on.

---

## Worked example — create a category, create a tag, attach it to a VM

**Goal:** create a `MULTIPLE`-cardinality category `Environment`, create the tag
`Environment / production` in it, and attach that tag to the VM `app-web-07`. Every identifier
below is a value the server returned.

```bash
VC=https://vcenter.example.com
CAT_NAME=Environment
TAG_NAME=production
VM_NAME=app-web-07
```

### Step 0 — Session

```bash
TOKEN=$(curl -sS -u "$VC_USER:$VC_PASS" -X POST "$VC/api/session" | jq -r '.')
[ -z "$TOKEN" ] || [ "$TOKEN" = null ] && { echo "FATAL: no session — see vcf-foundation" >&2; exit 1; }
AUTH=(-H "vmware-api-session-id: $TOKEN" -H 'Content-Type: application/json')
```

**If you hit `FATAL: no session`, read this before re-checking the password.** The most likely
cause is not a typo: vCenter **blocks non-federated username/password logins**, so on a federated
deployment the plain basic-auth login above returns **401 — indistinguishable from a wrong
password, a locked account or a bad username.** Verbatim from the VCF **9.0** product support
notes, under removals: *"Blocked non-federated username/password logins to vCenter: vCenter 9.0
blocks logins with just a user name and password, which might sometimes allow bypassing the
federated provider domain."* **[DOC]** The spec's own trace is the `federated_identity_auth`
security scheme (`http`/`bearer`) sitting alongside `basic_auth`. **Evidence caveat:** the **9.1**
support notes do not restate the removal; a 9.0 removal does not un-remove itself, so treat the
gate as still applying, but note there is no 9.1-pinned citation for it. Do not brute-force
username variations — each attempt counts against lockout policy.

Credential acquisition, the federated flow, and any 401 here belong to `vcf-foundation` (P1); the
fuller treatment is P2 in `vsphere-inventory-vm-lifecycle`.

### Step 1 — Settle the object-type string before writing anything (P6)

```bash
curl -sS "${AUTH[@]}" "$VC/api/vcenter/tagging/associations" \
  | jq -r '.associations[0].object | "\(.type)  \(.id)"'
```

`GET /api/vcenter/tagging/associations` **[SPEC-A — `Vcenter.Tagging.Associations_list`]**.
`Summary.object` is a `Vapi.Std.DynamicID`, so this prints the exact `type` spelling this
vCenter uses. The rest assumes `VirtualMachine` — **[INFERRED]**, corroborated by the VI-JSON
managed-object type names. On an estate with no associations this returns an empty array; tag
one object in the vSphere Client and re-run rather than guessing.

### Step 2 — Create the category

```bash
CAT=$(curl -sS -X POST "${AUTH[@]}" "$VC/api/cis/tagging/category" -d '{
  "name": "Environment",
  "description": "Deployment environment of the object",
  "cardinality": "MULTIPLE",
  "associable_types": ["VirtualMachine"]
}' | jq -r '.')
echo "category=$CAT"
```

`POST /api/cis/tagging/category` **[SPEC-A — `Cis.Tagging.Category_create`]**, body
`Cis.Tagging.Category.CreateSpec`, response **201**, body is the id string.

- `associable_types`, `cardinality`, `description`, `name` are **all four required**;
  `description: ""` is how you decline to write one.
- `cardinality: "MULTIPLE"` lets a VM carry `production` *and* `pci-scope` from this category.
  `SINGLE` makes the second attach a 400 (P5).
- `associable_types: ["VirtualMachine"]` restricts this category to VMs. **`[]` means all
  types** — *"If the set is empty, then tags can be attached to all types of objects."*
- Optional `category_id` supplies your own id; omit it and *"an identifier will be generated by
  the server"*.
- **400 `AlreadyExists`** if the name is taken; **400 `InvalidArgument`** otherwise; **403** if
  you lack the create-category privilege.

If the category may already exist, resolve instead:

```bash
CAT=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/tagging/categories?names=$CAT_NAME" \
      | jq -r '.items[0].category_id')
```

`GET /api/vcenter/tagging/categories` **[SPEC-A — `Vcenter.Tagging.Categories_list`]**. Do
**not** add `iterate` — `marker` plus a filter is a documented **400**.

### Step 3 — Create the tag in that category (P4)

```bash
TAG=$(curl -sS -X POST "${AUTH[@]}" "$VC/api/cis/tagging/tag" -d "$(jq -n --arg cat "$CAT" '{
  name:        "production",
  description: "Production workload",
  category_id: $cat
}')" | jq -r '.')
echo "tag=$TAG"
```

`POST /api/cis/tagging/tag` **[SPEC-A — `Cis.Tagging.Tag_create`]**, body
`Cis.Tagging.Tag.CreateSpec`, response **201**.

- `category_id`, `description`, `name` are **all three required**.
- **404 means the category id is wrong** — *"if the category for in the given createSpec does
  not exist in the system"*.
- **400 `AlreadyExists`** is scoped to *"an already existing tag **in the input category**"*.
- Privilege: *"the create tag privilege **on the input category**"* — per-object.
- The `jq -n --arg` construction is load-bearing; a single-quoted `-d '{...}'` posts the literal
  `$cat`.

### Step 4 — Resolve the VM, then check the tag is attachable (P5)

```bash
VM=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/vm?names=$VM_NAME" | jq -r '.[0].vm')
[ -z "$VM" ] || [ "$VM" = null ] && { echo "FATAL: VM unresolved" >&2; exit 1; }

OBJ=$(jq -n --arg id "$VM" '{type:"VirtualMachine", id:$id}')

curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association?action=list-attachable-tags" \
  -d "$(jq -n --argjson o "$OBJ" '{object_id: $o}')" | jq -r '.[]' | grep -qx "$TAG" \
  || echo "WARN: $TAG is not attachable to $VM — check cardinality / associable_types"
```

`GET /api/vcenter/vm` belongs to `vsphere-inventory-vm-lifecycle`; it is here only to produce a
real `vm-NNN` identifier.
`POST /api/cis/tagging/tag-association?action=list-attachable-tags`
**[SPEC-A — `Cis.Tagging.TagAssociation_listAttachableTags`]**, body `{"object_id": DynamicID}`
(**required**) — *"omitting the tags that have already been attached"*. A tag already attached is
absent from the list, so the warning can fire on a no-op re-run. Treat it as a warning.

### Step 5 — Attach

**On 9.1, prefer the atomic PATCH.** It takes names, so `$CAT` and `$TAG` are not even needed:

```bash
curl -sS -X PATCH "${AUTH[@]}" "$VC/api/vcenter/tagging/associations" \
  -d "$(jq -n --argjson o "$OBJ" '{
    object: $o,
    tag_spec_list: [
      { operation: "ATTACH",
        tag_category_name_info: { tag_name: "production", category_name: "Environment" } }
    ]
  }')" | jq '{success, results, errors}'
```

`PATCH /api/vcenter/tagging/associations` **[SPEC-A — `Vcenter.Tagging.Associations_update`,
*"added in vSphere API 9.1.0.0"*]**. **200** with a
`Vcenter.Tagging.Associations.UpdateResult`. Check `success` — *"Partial completion is not
allowed; in case of failure, the partially applied operation will be rolled back."* `results`
lists what actually changed, so a re-run of an already-attached tag returns `success: true`
with an empty `results`; that is correct, not a failure. `errors` appears **only** when
`success` is `false`. Privileges: `InventoryService.Tagging.ObjectAttachable` on the object and
`InventoryService.Tagging.AttachTag` on each tag.

**The 9.0-compatible form still works** and is what you write if the script must run against
both versions:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association/$TAG?action=attach" \
  -d "$(jq -n --argjson o "$OBJ" '{object_id: $o}')"
```

`POST /api/cis/tagging/tag-association/{tagId}?action=attach`
**[SPEC-A — `Cis.Tagging.TagAssociation_attach`]**. Success is **204 No Content** — no body,
so `jq` on the response fails. Idempotent: *"If the tag is already attached … this operation is
a no-op and an error will not be thrown."*

### Step 6 — Verify both directions

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association?action=list-attached-tags" \
  -d "$(jq -n --argjson o "$OBJ" '{object_id: $o}')" | jq -r '.[]'

curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association/$TAG?action=list-attached-objects" | jq -r '.[].id'
```

`..._listAttachedTags` and `..._listAttachedObjects` **[SPEC-A]**. The first should contain
`$TAG`; the second should contain `$VM`. The second takes **no request body** — the tag id is
in the path.

To read it back with names: `GET /api/vcenter/tagging/tags?names=production` **[SPEC-A]** gives
`{tag, info:{name, category, description, used_by}}`.

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 404 on step 2 or 3 with the path itself | You used `/api/cis-tagging/...`. The spec path is `/api/cis/tagging/...` (slash). |
| 400 `AlreadyExists` on step 2 | The category name is taken. Resolve it with `/vcenter/tagging/categories?names=` instead. |
| **404** on step 3 | `$CAT` is wrong or stale — the tag create's 404 is specifically *"the category … does not exist"*. |
| 400 `AlreadyExists` on step 3 | A tag with that name already exists **in that category**. |
| 400 on step 3 with a valid category | A required field is missing — `category_id`, `description`, `name` are all mandatory. |
| 400 `InvalidArgument` on the PATCH | A `TagSpec` with neither `tag_id` nor `tag_category_name_info`, or an empty `tag_spec_list`. |
| PATCH returns `success: false` | Read `errors`. Everything was rolled back — nothing partially applied. |
| PATCH returns `success: true` with empty `results` | Every tag was already in the requested state. Correct, not a failure. |
| 404 on the PATCH | *"if the resource object is not registered on the vCenter Server"* — the `object.id` or `object.type` is wrong. |
| 405 or 404 on the PATCH against a 9.0 host | `Vcenter.Tagging.Associations_update` is 9.1-only. Fall back to `?action=attach`. |
| 400 on the `?action=attach` form | Wrong `DynamicID.type` (step 1), `SINGLE` cardinality already satisfied, or the type is not in `associable_types` (P5) — one code, three causes. |
| 403 on either attach form | Per-object privileges: attach-tag on the tag **and** object-attachable/read on the object. |
| `jq` parse error on `?action=attach` | Success. That form returns **204** with no body. |
| 400 on `/vcenter/tagging/categories` | You supplied `iterate` **and** `names`. Documented 400. |

---

## Out of scope — where to route instead

| Topic | Paths | Skill |
|---|---|---|
| VM create, clone, power, reconfigure, delete; datacenter/cluster/host/datastore/network/folder/resource-pool traversal | `/api/vcenter/vm*`, `/api/vcenter/{datacenter,cluster,host,datastore,network,folder,resource-pool}` | `vsphere-inventory-vm-lifecycle` |
| ESX images, software drafts, depots, remediation, configuration profiles | `/api/esx/settings/*` (344 ops at 9.1) | `vsphere-lifecycle-vlcm` |
| vSAN cluster config, disk groups, health, vSAN Data Protection | `/api/vcenter/vsan/*`, snapservice | `vsan-storage` |
| Supervisor / namespace management, including its storage-policy configuration | `/api/vcenter/namespace-management/*` | `vcf-api-discovery` |
| SSO, federation, token exchange, identity providers | — | `vcf-foundation` |
| Anything not covered anywhere | — | `vcf-api-discovery` |

**One deliberate overlap.** `vsan-storage` also documents the `/pbm` families, because vSAN
storage policies *are* SPBM policies. Both skills describe the same 33 operations from the same
spec; neither invented a separate API. For vSAN-specific capability context use that skill; for
storage policies generally, stay here.

---

## What is unverified for 9.1

- **The concrete `Vapi.Std.DynamicID.type` strings** (and therefore the `associable_types`
  vocabulary). No enum, no example list anywhere in the vSphere Automation spec at either tag.
  `VirtualMachine` and friends are **[INFERRED]** from VI-JSON managed-object type path
  segments. Resolve per-estate via `GET /api/vcenter/tagging/associations`.
- **Canonical privilege strings for the `/cis/tagging` operations.** 9.1 names exactly two
  (`InventoryService.Tagging.ObjectAttachable`, `InventoryService.Tagging.AttachTag`), and both
  only on the new `PATCH /vcenter/tagging/associations`. The create/delete/read privileges on
  `/cis/tagging` are still prose only.
- **Privilege names for `/api/vcenter/storage/policies*`.** The 403s say only *"the required
  privileges"*. `StorageProfile.View` is **[INFERRED]** from the `/pbm` equivalents.
- **The `{moId}` value for `PbmServiceInstance`.** The spec offers `ServiceInstance` only as an
  example of the *form* of a managed-object id.
- **`PbmComplianceStatus_enum` and `PbmComplianceResultComplianceTaskStatus_enum` member
  lists.** Referenced by name in `vi-json.yaml`, not expanded as JSON schema enums.
- **How to obtain the task handle for asynchronous content deletion.** The library-item delete
  says the content removal *"can be tracked with a task"* but returns no task identifier, and no
  `/content` operation has a `vmw-task=true` form.
- **Whether `/api/cis-tagging/...` also resolves on a live appliance.** The spec declares only
  `/cis/tagging/...`.
- **Whether `Content.Library.Usages` is populated automatically by consumers or only by explicit
  `Usages_add` calls.** The `add`/`remove` operations exist and take a `resource_urn`; nothing in
  the spec says which subsystems register themselves. An empty `usages` list is therefore a
  strong signal, not a proof, that a library is unused.
- **Behaviour of `Cis.Tagging.Category_delete` on a category with attached tags.** The operation
  exists and is destructive; the spec does not state whether it cascades.
- **Any cap or pagination on the `/cis/tagging` list operations.** No cap is stated and no marker
  exists, unlike `/vcenter/tagging/*` and the storage-policy list.
- **What happens to a library left in `MAINTENANCE` if `exit-maintenance` is never called**, and
  whether a failed `migrate` leaves it there. The state enum and both transitions are
  spec-confirmed; the failure path is not documented.
