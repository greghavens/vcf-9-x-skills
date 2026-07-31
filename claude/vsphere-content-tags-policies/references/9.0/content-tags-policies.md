# vSphere content library, tags and storage policies — VCF 9.0

**Applies to:** vCenter **9.0.0.0**, the version in the VCF 9.0 Bill of Materials.
**Do not apply this file to VCF 9.1.** Use `../9.1/content-tags-policies.md` for 9.1 and
`../deltas.md` for the change list.

## Provenance of everything below

| Tag | Meaning |
|---|---|
| **[SPEC-A]** | The exact `method + path` was found in `research/spec-inventory/9.0__vsphere-automation.ops.json`, machine-extracted from `specifications/vsphere/openapi/automation/vcenter.yaml` at git tag `9.0.0.0` of `github.com/vmware/vcf-api-specs` (`info.version: 9.0.0.0`, `servers[0].url: https://{host}/api`, 1,275 operations). Schema and description quotes come from that same file. |
| **[SPEC-V]** | Same, but for the **VI-JSON** surface: `9.0__vsphere-vi-json.ops.json`, from `specifications/vsphere/openapi/vi-json/vi-json.yaml` at the same tag (`info.version: 9.0.0.0`, `servers[0].url: https://{vcenter-host}/sdk/vim25/{release}`, 2,195 operations). |
| **[DOC]** | Verified only from version-pinned Broadcom prose captured in `research/vsphere-vcenter-vsan.md`. |
| **[INFERRED]** | Neither — a shape or convention, not a verified fact. Confirm before relying on it. |
| **`UNVERIFIED`** | The research could not establish it. Do not fill the gap by guessing. |

**All of it was captured 2026-07-31 and none of it has been run against a live vCenter.** The
two operations in this file that change production state are `DELETE` on a library or library
item (content removal from the storage backing is asynchronous and may need manual cleanup on
failure) and any change to a storage policy that is in use (`PATCH /vcenter/vm/{vm}/storage/policy`,
`PbmUpdate`, `PbmDelete` — these re-apply to every bound object). Resolve the target with a
`GET`, and check what is bound, before executing either.

**Every operation in this file is tagged with the surface it belongs to.** That is not
decoration: storage-policy authoring is on a different surface from storage-policy reading,
and getting it wrong produces a 404 that reads like a permissions problem.

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
  - [P9 — privileges, per object, per surface](#p9--privileges-per-object-per-surface)
- [Surfaces and base paths](#surfaces-and-base-paths)
- [Content library](#content-library) — libraries, items, sessions, subscriptions, deploy
- [Tags and categories](#tags-and-categories) — **the dossier's `UNVERIFIED` resolved**
- [Storage policies](#storage-policies) — read/compliance on `/api`, authoring on `/pbm`
- [**Worked example** — create a category, create a tag, attach it to a VM](#worked-example--create-a-category-create-a-tag-attach-it-to-a-vm) (Steps 0–6 + [failure decode](#failure-decode-for-this-sequence))
- [Out of scope — where to route instead](#out-of-scope--where-to-route-instead)
- [What is unverified for 9.0](#what-is-unverified-for-90)

---

## Prerequisites

Everything here must be true **before** you issue any content-library, tagging or
storage-policy call. Each item carries four elements — if one is missing the item is
incomplete:

1. **What must be true.**
2. **How to verify it** — a concrete, *non-destructive* check.
3. **Which version it applies to** — every item applies to **vCenter 9.0.0.0** unless said
   otherwise.
4. **Whether it exists in 9.1** — stated as a "9.1 difference" line on every item.

### P1 — You are on the right base path, with a live session header

- **Must be true:** the vSphere Automation calls in this file go to
  **`https://<vcenter>/api/...`** — `servers[0].url` is `https://{host}/api` **[SPEC-A]** —
  and every one of them carries the **`vmware-api-session-id`** header (security scheme
  `api_key_auth`, `type: apiKey`, `in: header`) **[SPEC-A]**. The PBM operations go to
  **`https://<vcenter>/sdk/vim25/{release}/pbm/...`** and take the **same header** (VI-JSON
  security scheme `Session`, `apiKey`, header `vmware-api-session-id`) **[SPEC-V]**.
- **Obtaining the credential is `vcf-foundation`'s job.** This file states the mechanism and
  the base path and stops there. Do not re-derive the federation flow here.
- **Verify:** any cheap read on each surface. `GET /api/content/library` **[SPEC-A —
  `Content.Library_list`]** returns 200 and an array. `GET /sdk/vim25/9.0.0.0/pbm/PbmServiceInstance/{moId}/content`
  **[SPEC-V — `PbmServiceInstance_getContent`]** returns 200 and a `PbmServiceInstanceContent`.
  A 404 on the second while the first works is a *surface* problem, not an auth problem.
- **9.1 difference:** none. Same base paths, same header, same schemes on both surfaces.

### P2 — The library you are creating has a resolved storage backing

- **Must be true:** `Content.LibraryModel.storage_backings` is, verbatim, *"must be provided
  for the `create` operation"* **[SPEC-A]**. A `Content.Library.StorageBacking` has a `type`
  — the enum is exactly `DATASTORE` and `OTHER` **[SPEC-A]** — plus:
  - `DATASTORE` → `datastore_id`, *"only relevant when the value of type is …DATASTORE"*, an
    identifier for resource type `Datastore`. This is the datastore-backed case, and it is
    what "content library needs a datastore" means concretely.
  - `OTHER` → `storage_uri`, an NFS or SMB URI. Spec-listed forms include
    `nfs://server/path?version=4`, `nfs://server/path`, `smb://server/path` **[SPEC-A]**.
- **Only one backing.** Both `Content.LocalLibrary_create` and `Content.SubscribedLibrary_create`
  declare a 400 `Vapi.Std.Errors.Unsupported` *"if using multiple storage backings"* **[SPEC-A]**.
  The property is an array; treat it as an array of one.
- **Verify:** resolve the datastore first and check it came back —
  `GET /api/vcenter/datastore?names=<ds>` (that endpoint belongs to
  `vsphere-inventory-vm-lifecycle`; you only need the returned `datastore` value). A
  zero-length array is fatal *before* the create, not after. For an `OTHER` backing there is
  no pre-flight endpoint; the create itself is the test.
- **9.1 difference:** none. `Content.LibraryModel`, `Content.Library.StorageBacking` and the
  `Unsupported`-on-multiple-backings error are identical at the 9.1 tag.

### P3 — Publishing and subscribing are configured before create, not after

- **Must be true, publishing side:** `Content.Library.PublishInfo.authentication_method`
  (`BASIC` | `NONE`) and `.published` are both *"required for the
  `POST /content/local-library` operation"* **[SPEC-A]**. If you choose `BASIC`, the spec's
  own note on `user_name` is worth reading: *"the username is ignored in the current release.
  It defaults to `vcsp`. It is preferable to leave this missing or `null`. If specified, it
  must be set to `vcsp`."* The `password` *"should be a non-empty string"* under `BASIC`.
  `publish_url` is **not** an input — it is *"not used for the `create` operation"* and comes
  back on `get`.
- **Must be true, subscribing side:** `Content.Library.SubscriptionInfo.authentication_method`,
  `.automatic_sync_enabled`, `.on_demand` and `.subscription_url` are all *"must be provided
  for the `create` operation"* **[SPEC-A]**. `subscription_url` is normally the publisher's
  `publish_info.publish_url`. Credentials go in `user_name` / `password`;
  `ssl_thumbprint` is an optional SHA-1 hash and, when set, *"the standard certificate chain
  validation behavior is not used"*.
- **Verify — probe before you create.** `POST /api/content/subscribed-library?action=probe`
  **[SPEC-A — `Content.SubscribedLibrary_probe`]**, body `{"subscription_info": {…}}`,
  returns a `Content.SubscribedLibrary.ProbeResult` whose `status` enum is exactly
  `SUCCESS`, `INVALID_URL`, `TIMED_OUT`, `HOST_NOT_FOUND`, `RESOURCE_NOT_FOUND`,
  `INVALID_CREDENTIALS`, `CERTIFICATE_ERROR`, `UNKNOWN_ERROR` **[SPEC-A]**. On
  `CERTIFICATE_ERROR` the spec says the returned thumbprint *"should be set in
  `Content.Library.SubscriptionInfo.ssl_thumbprint`"* — i.e. probe, take the thumbprint,
  probe again, then create. Probe requires `ContentLibrary.ProbeSubscription`.
- **Consequence of skipping it:** `Content.SubscribedLibrary_create` declares a **500
  `ResourceInaccessible`** *"if subscribing to a published library which cannot be
  accessed"* **[SPEC-A]** — you get a half-built library and a 500, instead of a clean answer
  from a probe.
- **9.1 difference:** none for probe, publish or subscribe. 9.1 *adds* the ability to convert
  a fully-synced subscribed library into a published local one
  (`POST /content/library/{libraryId}?action=convert`); see `../deltas.md`.

### P4 — The category exists before the tag

- **Must be true:** `Cis.Tagging.Tag.CreateSpec` **requires** `category_id`, `description`
  and `name` **[SPEC-A]**. There is no create-category-implicitly path.
- **The failure is a 404, not a 400.** `Cis.Tagging.Tag_create` declares 404 *"if the
  category for in the given createSpec does not exist in the system"* **[SPEC-A]**, while
  400 is reserved for `AlreadyExists` (*"the name of an already existing tag in the input
  category"*) and `InvalidArgument`. A 404 on a tag create is almost always a wrong or stale
  `category_id`.
- **Tag names are unique per category, not globally.** Spec, verbatim: *"The display name of
  the tag. The name must be unique within its category."* **[SPEC-A]**
- **Verify:** `GET /api/vcenter/tagging/categories?names=<name>` **[SPEC-A —
  `Vcenter.Tagging.Categories_list`, *"added in vSphere API 9.0.0.0"*]** returns
  `{items: [{category_id, info}]}`. An empty `items` means create the category first.
  (`GET /api/cis/tagging/category` also exists but returns identifiers only — see P6.)
- **9.1 difference:** none for create. 9.1 adds `PATCH /vcenter/tagging/associations`, which
  can attach by **tag name + category name** without resolving ids at all — but the category
  and tag must still already exist.

### P5 — The category's cardinality and associable types permit the attach

- **Must be true:** `Cis.Tagging.Category.CreateSpec` **requires** `associable_types`,
  `cardinality`, `description` and `name` **[SPEC-A]**. Both constraints are enforced at
  *attach* time, not at create time:
  - **`cardinality`** — enum exactly `SINGLE` | `MULTIPLE` **[SPEC-A]**. Verbatim: *"`SINGLE`:
    An object can only be assigned one of the tags in this category"*; *"`MULTIPLE`: An object
    can be assigned several of the tags in this category"*. A `SINGLE` category with a tag
    already attached rejects the second tag.
  - **`associable_types`** — *"Object types to which this category's tags can be attached."*
    On `Cis.Tagging.CategoryModel` the fuller wording is: *"If the set is empty, then tags can
    be attached to all types of objects. This field works only for objects that reside in
    Inventory Service (IS). For non IS objects, this check is not performed today and hence a
    tag can be attached to any non IS object."* **[SPEC-A]** An empty set is the permissive
    choice, and the check is **not** universal.
- **The attach operation says so itself.** `Cis.Tagging.TagAssociation_attach`, verbatim:
  *"The tag needs to meet the cardinality (`Cis.Tagging.CategoryModel.cardinality`) and
  associability (`Cis.Tagging.CategoryModel.associable_types`) criteria in order to be
  eligible for attachment."* Its 400 is *"if the input tag is not eligible to be attached to
  this object or if the objectId is not valid"* **[SPEC-A]** — one error code for two very
  different causes.
- **Verify — non-destructively, and this is the good one:**
  `POST /api/cis/tagging/tag-association?action=list-attachable-tags` **[SPEC-A —
  `Cis.Tagging.TagAssociation_listAttachableTags`]** with body `{"object_id": {"type": …,
  "id": …}}`. Spec description: *"Fetches the list of attachable tags for the given object,
  omitting the tags that have already been attached."* If your tag is not in that list, the
  attach will fail — check that before writing the attach, not after.
- **The exact string values for `associable_types` are not enumerated anywhere in the spec.**
  See P6 and the unverified list.
- **9.1 difference:** none. `Cis.Tagging.Category.CreateSpec`, `CategoryModel`,
  `Cardinality` and the attach-eligibility wording are identical at the 9.1 tag.

### P6 — You resolved identifiers rather than constructing them

- **Must be true:** every id in this file is server-issued. The spec names the resource type
  per field **[SPEC-A]**:

  | Field | Resource type |
  |---|---|
  | library id | `com.vmware.content.Library` |
  | library item id | `com.vmware.content.library.Item` |
  | subscription id | `com.vmware.content.library.Subscriptions` |
  | category id | `com.vmware.cis.tagging.Category` |
  | tag id | `com.vmware.cis.tagging.Tag` |
  | storage policy id | `com.vmware.vcenter.StoragePolicy` |
  | datastore / VM / disk | `Datastore`, `VirtualMachine`, `com.vmware.vcenter.vm.hardware.Disk` |

- **The `/cis/tagging` list operations give you ids and nothing else.**
  `Cis.Tagging.Category_list` returns *"The list of resource identifiers for the categories
  in the system"* — a bare `array of string`. Same for `Cis.Tagging.Tag_list`. **[SPEC-A]**
  Name → id therefore goes through `/vcenter/tagging/*`:
  - `GET /api/vcenter/tagging/categories?names=<n>` → `Vcenter.Tagging.Categories.ListResult`
    = `{items: [{category_id, info}], marker?}`, where `info` is `{name, description,
    cardinality, associable_types, used_by}`. **[SPEC-A — `Vcenter.Tagging.Categories_list`]**
  - `GET /api/vcenter/tagging/tags?names=<n>` → `{items: [{tag, info}], marker?}`, `info` =
    `{name, category, description, used_by}`. **[SPEC-A — `Vcenter.Tagging.Tags_list`]**
    Note `info.category` is the **category id**, which is how you disambiguate two tags with
    the same display name in different categories.
  - Both were *"added in vSphere API 9.0.0.0"* and both declare **400 *"If marker and filter
    are supplied together"*** **[SPEC-A]** — you may page, or you may filter by name, not both
    in one call.
- **Storage policies have no name filter at all.** `GET /api/vcenter/storage/policies` takes
  only `policies` (an array of ids) **[SPEC-A]**. To find a policy by name you list and match
  `Vcenter.Storage.Policies.Summary.name` client-side. The list returns *"at most 1024
  visible … storage policies"* and declares **500 `UnableToAllocateResource` *"if more than
  1024 storage policies exist"*** — an explicit error, not silent truncation.
- **9.1 difference:** none. Identical resource types, identical lookup endpoints, identical
  marker/filter conflict, identical 1024 cap.

### P7 — The policy is attached before you ask about compliance

- **Must be true:** compliance is computed against a policy *binding*. Two spec statements
  make this a prerequisite rather than a footnote **[SPEC-A]**:
  - `Vcenter.Storage.Policies.Compliance_list` — *"Returns compliance information about
    entities matching the filter … **Entities without storage policy association are not
    returned.**"*
  - `Vcenter.Storage.Policies.Compliance.VM_list` — *"If there are no virtual machines
    matching the … FilterSpec an empty List is returned. **Virtual machines without storage
    policy association are not returned.**"*

  So an empty result is ambiguous between "everything is compliant" and "nothing is bound".
- **Verify the binding first:** `GET /api/vcenter/vm/{vm}/storage/policy` **[SPEC-A —
  `Vcenter.Vm.Storage.Policy_get`]** returns `Vcenter.Vm.Storage.Policy.Info` = `{vm_home?,
  disks}` where `vm_home` is a policy id and `disks` maps disk id → policy id. Spec: *"If
  missing or `null`, the virtual machine's home directory doesn't have any storage policy."*
- **Cached versus recomputed.** `GET /api/vcenter/vm/{vm}/storage/policy/compliance` returns
  *"the **cached** storage policy compliance information"*;
  `POST /api/vcenter/vm/{vm}/storage/policy/compliance?action=check` returns it *"after
  explicitly **re-computing** compliance check"* **[SPEC-A]**. If you are answering "is it
  compliant right now", the cached read is the wrong call.
- **9.1 difference:** none. Identical operations, identical wording, identical schemas.

### P8 — The PBM surface is reachable and you hold its managed-object ids

- **Must be true:** every `/pbm` operation is `POST /sdk/vim25/{release}/pbm/{ManagedObjectType}/{moId}/{Operation}`
  **[SPEC-V]**, and `{moId}` is a real managed-object id, not a placeholder. The spec's own
  `moId` parameter description: *"A unique identifier (within this vCenter Server instance)
  for a specific managed object such as `group-d1` or `vm-015` or `ServiceInstance`."*
  **[SPEC-V]**
- **Verify / bootstrap:** `POST /sdk/vim25/9.0.0.0/pbm/PbmServiceInstance/{moId}/PbmRetrieveServiceContent`
  **[SPEC-V — `PbmServiceInstance_PbmRetrieveServiceContent`]** or the `GET` form
  `.../PbmServiceInstance/{moId}/content` **[SPEC-V — `PbmServiceInstance_getContent`]**.
  Both return `PbmServiceInstanceContent`, whose properties are `aboutInfo`,
  `sessionManager`, `capabilityMetadataManager`, **`profileManager`**, **`complianceManager`**,
  **`placementSolver`**, `replicationManager` **[SPEC-V]**. Those three bolded values are the
  `{moId}` you substitute into every other `/pbm` call. Both service-instance operations
  require only `System.Anonymous` **[SPEC-V]**, so this is the cheapest possible probe.
- **The concrete `{moId}` string for `PbmServiceInstance` itself is not stated in the spec.**
  The `moId` parameter description offers `ServiceInstance` as an example of the *form*, not
  as the PBM service-instance value. `UNVERIFIED` — confirm on first run.
- **The PBM schemas are explicit about the surface split.** `PbmServerObjectRef`,
  `PbmCapabilityProfileCreateSpec` and `PbmComplianceResult` each carry the sentence *"This
  structure may be used only with operations rendered under `/pbm`."* **[SPEC-V]** They are
  not usable against `/api`.
- **9.1 difference:** none. All 33 `/pbm` operations, the same 5 deprecated ones, and
  `PbmServiceInstanceContent` are byte-identical at the 9.1 tag.

### P9 — Privileges, per object, per surface

- **Must be true:** privileges here are per-object and named per operation — and the two
  surfaces name them very differently.
- **Content library — the spec states the privilege on every operation** **[SPEC-A]**.
  Selected, verbatim from the `Returns an authorization error if you do not have all of the
  privileges described as follows` blocks:

  | Operation | Privilege |
  |---|---|
  | `Content.LocalLibrary_create` | `ContentLibrary.CreateLocalLibrary`, **plus** `Datastore.AllocateSpace` on the `Datastore` referenced by `storage_backings[].datastore_id` |
  | `Content.SubscribedLibrary_create` | `ContentLibrary.CreateSubscribedLibrary` + `Datastore.AllocateSpace` |
  | `Content.LocalLibrary_update` / `_delete` | `ContentLibrary.UpdateLocalLibrary` / `ContentLibrary.DeleteLocalLibrary` |
  | `Content.SubscribedLibrary_update` / `_delete` / `_sync` / `_evict` | `ContentLibrary.UpdateSubscribedLibrary` / `DeleteSubscribedLibrary` / `SyncLibrary` / `EvictSubscribedLibrary` |
  | `Content.SubscribedLibrary_probe` | `ContentLibrary.ProbeSubscription` |
  | `Content.LocalLibrary_publish` | `ContentLibrary.PublishLibrary` |
  | `Content.Library.Item_create` / `_update` / `_delete` | `ContentLibrary.AddLibraryItem` / `UpdateLibraryItem` / `DeleteLibraryItem` |
  | `Content.Library_migrate` | `ContentLibrary.MigrateLibrary` |
  | `Content.Library_list` / `_get` | `System.Read` |

  The full 9.0 vocabulary in the spec is 34 `ContentLibrary.*` strings; the ones above are
  the ones you hit in ordinary work.
- **Tagging — the spec describes privileges in prose, not as strings.** The 9.0 operation
  descriptions say things like *"you need the create category privilege"*, *"you need the
  attach tag privilege on the tag and the read privilege on the object"*, *"you need the
  read privilege on the individual categories"* **[SPEC-A]**. **No `InventoryService.Tagging.*`
  privilege string appears anywhere in the 9.0 spec.** The canonical strings are
  `UNVERIFIED` for 9.0. (They *do* appear in 9.1 — see the 9.1 file and `../deltas.md`.)
- **Storage policy — split by surface.**
  - `/pbm` names them exactly **[SPEC-V]**: **`StorageProfile.Update`** on `PbmCreate`,
    `PbmUpdate`, `PbmDelete`, `PbmAssignDefaultRequirementProfile`,
    `PbmResetDefaultRequirementProfile`, `PbmResetVSanDefaultProfile`; **`StorageProfile.View`**
    on every query, fetch and compliance operation; **`System.Anonymous`** on the two
    service-instance operations.
  - `/api/vcenter/storage/policies*` does **not** name any privilege — the 403 descriptions
    read only *"if the user doesn't have the required privileges"* **[SPEC-A]**. Assuming they
    are `StorageProfile.View` is reasonable and is **[INFERRED]**, not stated.
- **Verify — read, do not test by writing.** Use
  `POST /api/vcenter/authorization/permissions?action=list` and
  `GET /api/vcenter/authorization/roles` (both `vsphere-inventory-vm-lifecycle`'s territory)
  rather than attempting a production create to see whether it 403s.
- **9.1 difference:** content-library privileges are unchanged and 9.1 adds five
  (`ContentLibrary.DeleteLibrary`, `ConvertLibrary`, `LibraryMaintenance`, `AddLibraryUsage`,
  `RemoveLibraryUsage`) for its new operations. 9.1 also introduces the first two tagging
  privilege *strings* in the spec. `/pbm` privileges are unchanged.

---

## Surfaces and base paths

| Surface | Base | Evidence | Carries |
|---|---|---|---|
| **vSphere Automation** | `https://{host}/api` | `9.0__vsphere-automation.ops.json`, 1,275 ops **[SPEC-A]** | `/content/*` (72), `/cis/tagging/*` (30), `/vcenter/tagging/*` (3), `/vcenter/storage/policies*` (5), `/vcenter/vm/{vm}/storage/policy*` (4), `/vcenter/vm-template/library-items/*` (12), `/vcenter/ovf/*` (6) |
| **VI-JSON (PBM)** | `https://{vcenter-host}/sdk/vim25/{release}` | `9.0__vsphere-vi-json.ops.json`, 2,195 ops, security scheme `Session` = header `vmware-api-session-id` **[SPEC-V]** | `/pbm/*` (33, of which 5 deprecated) — the **only** place a storage policy can be created, updated or deleted |
| Legacy REST | `https://{host}/rest` | **[DOC]** — deprecated, operations up to vSphere 7.0.2 only | Recognize it in inherited scripts; do not write new work against it |

**Nothing in this scope has a `?vmw-task=true` variant.** Zero of the 72 `/content`
operations, zero of the 30 `/cis/tagging` operations and zero of the storage-policy
operations carry the task suffix at 9.0 **[SPEC-A]**. Several are nonetheless *asynchronous
in effect* — library delete, item delete and library migrate all say so in prose — and the
spec gives you no task handle for them. See the notes at each operation.

---

## Content library

All **[SPEC-A]** unless marked. Paths shown relative to `/api`. 72 operations at 9.0.

### Libraries — three views of one object

`/content/library` is the read-only union view; `/content/local-library` and
`/content/subscribed-library` are the type-specific views where creation and type-specific
updates happen. `Content.LibraryModel.type` is the discriminator, enum exactly `LOCAL` |
`SUBSCRIBED`.

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/content/library` | `Content.Library_list` | Ids only. |
| POST | `/content/library?action=find` | `Content.Library_find` | Body `Content.Library.FindSpec`: `name`, `type`, `storage_backing`. |
| GET | `/content/library/{libraryId}` | `Content.Library_get` | Returns `Content.LibraryModel`. |
| PATCH | `/content/library/{libraryId}` | `Content.Library_update` | *"will only update the common properties for all library types. This will not, for example, update the `publish_info` of a local library, nor the `subscription_info` of a subscribed library."* |
| POST | `/content/library/{libraryId}?action=migrate` | `Content.Library_migrate` | *"added in vSphere API 9.0.0.0."* Datastore→datastore only; *"Migrating Virtual machine template items is not supported."* Puts the library into `MAINTENANCE` for the duration. |
| GET·POST | `/content/local-library` | `Content.LocalLibrary_list` / `_create` | Create takes optional `Client-Token` header (a UUID) for idempotency; **201** with the new id. |
| GET·PATCH·DELETE | `/content/local-library/{libraryId}` | `Content.LocalLibrary_get` / `_update` / `_delete` | See the delete note below. |
| POST | `/content/local-library/{libraryId}?action=publish` | `Content.LocalLibrary_publish` | *"added in vSphere API 6.7.2."* Publishes to specified subscriptions, or all if none given. |
| GET·POST | `/content/subscribed-library` | `Content.SubscribedLibrary_list` / `_create` | Create is **201**; 500 `ResourceInaccessible` if the source cannot be reached (P3). |
| GET·PATCH·DELETE | `/content/subscribed-library/{libraryId}` | `..._get` / `_update` / `_delete` | |
| POST | `/content/subscribed-library/{libraryId}?action=sync` | `Content.SubscribedLibrary_sync` | |
| POST | `/content/subscribed-library/{libraryId}?action=evict` | `Content.SubscribedLibrary_evict` | Drops cached content, keeps metadata. |
| POST | `/content/subscribed-library?action=probe` | `Content.SubscribedLibrary_probe` | P3. |
| GET·POST | `/content/library/{library}/subscriptions` | `Content.Library.Subscriptions_list` / `_create` | Publisher-side view of who subscribes. |
| GET·PATCH·DELETE | `/content/library/{library}/subscriptions/{subscription}` | `..._get` / `_update` / `_delete` | |
| GET·PATCH | `/content/configuration` | `Content.Configuration_get` / `_update` | `Content.ConfigurationModel`: `automatic_sync_enabled`, `automatic_sync_start_hour`, `automatic_sync_stop_hour`, `maximum_concurrent_item_syncs`. Global — it gates every subscribed library's automatic sync. |
| GET | `/content/security-policies` | `Content.SecurityPolicies_list` | `{policy, name, item_type_rules}`. |
| GET·POST | `/content/trusted-certificates` | `Content.TrustedCertificates_list` / `_create` | |
| GET·DELETE | `/content/trusted-certificates/{certificate}` | `..._get` / `_delete` | |
| GET | `/content/type` | `Content.Type_list` | |

> **`DELETE /content/local-library/{libraryId}` is not the whole story.** Spec, verbatim:
> *"Deleting a local library will remove the entry immediately and begin an asynchronous task
> to remove all cached content for the library. **If the asynchronous task fails, file
> content may remain on the storage backing. This content will require manual removal.**"*
> **[SPEC-A]** Its 400 cases are `InvalidElementType` *"if the library specified by libraryId
> is not a local library"* and `NotAllowedInCurrentState` *"if the library contains a library
> item that cannot be deleted in its current state. For example, the library item contains a
> virtual machine template and a virtual machine is checked out of the library item."*
>
> **There is no `DELETE /content/library/{libraryId}` at 9.0**, and no `force-delete` on any
> library type. Both arrive in 9.1. If a runbook written against the 9.1 portal tells you to
> `POST /content/local-library/{libraryId}?action=force-delete`, that operation **does not
> exist in 9.0** — check `../deltas.md`.

**`Content.LibraryModel` fields you will actually set on create:** `name` (*"must be provided
for the `create` operation"*), `storage_backings` (same), `description` (optional, defaults
to empty string), `publish_info` (local only), `subscription_info` (subscribed only),
`optimization_info`, `security_policy_id`. Fields that are **server-owned and rejected or
ignored on create**: `id`, `type`, `creation_time`, `last_modified_time`, `last_sync_time`,
`version`, `state_info`, and `publish_info.publish_url`.

**`version` is an optimistic-concurrency token.** On `PATCH`, if you omit it the spec
declares a **500 `ResourceBusy`** *"if the `version` of updateSpec is missing or `null` and
the library is being concurrently updated by another user"*, and if you supply a stale one, a
**409 `ConcurrentChange`** **[SPEC-A]**. Read-modify-write, carrying `version` through.

**`Content.Library.StateInfo` is new at 9.0** (*"This schema was added in vSphere API
9.0.0.0"*), enum `ACTIVE` | `MAINTENANCE`: *"the library state when library is in migration.
Library content will be inaccessible and operations mutating library content will be
disallowed when in this state."* **[SPEC-A]** At 9.0 the **only** way into `MAINTENANCE` is
`?action=migrate`; explicit enter/exit endpoints are 9.1-only.

### Library items

| Verb | Path | operationId | Notes |
|---|---|---|---|
| POST | `/content/library/item` | `Content.Library.Item_create` | Body `Content.Library.ItemModel`; `library_id` *"must be provided for the `create` operation"*. Optional `Client-Token`. **201**. |
| GET | `/content/library/item?library_id` | `Content.Library.Item_list` | |
| POST | `/content/library/item?action=find` | `Content.Library.Item_find` | `Content.Library.Item.FindSpec`: `name`, `library_id`, `source_id`, `type`, `cached`. |
| GET·PATCH·DELETE | `/content/library/item/{libraryItemId}` | `Content.Library.Item_get` / `_update` / `_delete` | |
| POST | `/content/library/item/{libraryItemId}?action=publish` | `Content.Library.Item_publish` | |
| POST | `/content/library/item/{sourceLibraryItemId}?action=copy` | `Content.Library.Item_copy` | |
| GET | `/content/library/item/{libraryItemId}/file` · `?name` | `Content.Library.Item.File_list` / `_get` | |
| GET | `/content/library/item/{libraryItemId}/storage` · `?file_name` | `Content.Library.Item.Storage_list` / `_get` | |
| GET | `/content/library/item/{libraryItem}/changes` · `/{version}` | `Content.Library.Item.Changes_list` / `_get` | |
| POST | `/content/library/subscribed-item/{libraryItemId}?action=sync` | `Content.Library.SubscribedItem_sync` | Force-sync one on-demand item. |
| POST | `/content/library/subscribed-item/{libraryItemId}?action=evict` | `Content.Library.SubscribedItem_evict` | |

> **`DELETE /content/library/item/{libraryItemId}` — read this before running it.** Verbatim:
> *"This operation will immediately remove the item from the library that owns it. The content
> of the item will be asynchronously removed from the storage backings. The content deletion
> can be tracked with a task. In the event that the task fails, an administrator may need to
> manually remove the files from the storage backing. **This operation cannot be used to
> delete a library item that is a member of a subscribed library.** Removing an item from a
> subscribed library requires deleting the item from the original published local library and
> syncing the subscribed library."* **[SPEC-A]**
>
> Note the phrase *"can be tracked with a task"* — the spec does not say **which** task, and
> the operation declares no task identifier in its response. How to obtain that handle is
> `UNVERIFIED`.

### Upload and download sessions

Content goes in and out through sessions, not through a single PUT. **20 operations** at 9.0
across `/content/library/item/update-session*` and `/content/library/item/download-session*`
**[SPEC-A]**.

**Upload shape:** `POST /content/library/item/update-session` (`..UpdateSession_create`,
optional `Client-Token`) → `POST …/{updateSessionId}/file` (`..Updatesession.File_add`, body
`Content.Library.Item.Updatesession.File.AddSpec`, **required** `name` and `source_type`;
optional `source_endpoint`, `size`, `checksum_info`) → optionally
`POST …/file?action=validate` → `POST …/{updateSessionId}?action=complete`. Long uploads need
`?action=keep-alive`; abandon with `?action=cancel` or `?action=fail`.
`Content.Library.Item.UpdateSessionModel` carries `state`, `expiration_time`,
`client_progress`, `error_message`, `preview_info`, `warning_behavior`.

**Download shape** mirrors it: `create` → `POST …/file?action=prepare` → `GET …/file?file_name`
→ `delete`, with `keep-alive`, `cancel` and `fail`.

Sessions expire. `client_progress` exists so you can push progress back and keep the session
alive on a slow transfer; a session that times out mid-upload leaves the item in whatever
state the last completed step left it.

### Turning a library item into a VM — and back

| Verb | Path | operationId | Key spec fields |
|---|---|---|---|
| POST | `/vcenter/vm-template/library-items` | `Vcenter.VmTemplate.LibraryItems_create` | `Vcenter.VmTemplate.LibraryItems.CreateSpec` — **required** `library`, `name`, `source_vm`; optional `description`, `vm_home_storage`, `disk_storage`, `disk_storage_overrides`, `placement`. |
| GET | `/vcenter/vm-template/library-items/{templateLibraryItem}` | `..._get` | |
| POST | `/vcenter/vm-template/library-items/{templateLibraryItem}?action=deploy` | `Vcenter.VmTemplate.LibraryItems_deploy` | `DeploySpec` — **required** `name` only; optional `description`, `vm_home_storage`, `disk_storage`, `disk_storage_overrides`, `placement`, `powered_on`, `guest_customization`, `hardware_customization`. |
| POST·GET | `.../{templateLibraryItem}/check-outs?action=check-out` · `/check-outs` | `..CheckOuts_checkOut` / `_list` | |
| GET·DELETE | `.../check-outs/{vm}` | `..CheckOuts_get` / `_delete` | |
| POST | `.../check-outs/{vm}?action=check-in` | `..CheckOuts_checkIn` | |
| GET | `.../versions` · `/{version}` | `..Versions_list` / `_get` | |
| DELETE | `.../versions/{version}` | `..Versions_delete` | |
| POST | `.../versions/{version}?action=rollback` | `..Versions_rollback` | |
| POST | `/vcenter/ovf/library-item` | `Vcenter.Ovf.LibraryItem_create` | `CreateTarget`: `library_id`, `library_item_id`. |
| POST | `/vcenter/ovf/library-item/{ovfLibraryItemId}?action=deploy` | `Vcenter.Ovf.LibraryItem_deploy` | `DeploymentTarget` **requires** `resource_pool_id`; optional `host_id`, `folder_id`. `ResourcePoolDeploymentSpec` **requires** `accept_all_eula`; carries `name`, `annotation`, `network_mappings`, `storage_mappings`, `storage_provisioning`, **`storage_profile_id`**, `locale`, `flags`, `additional_parameters`, `default_datastore_id`, `vm_config_spec`. |
| POST | `/vcenter/ovf/library-item/{ovfLibraryItemId}?action=filter` | `Vcenter.Ovf.LibraryItem_filter` | Dry run — what the deploy would need. |
| POST | `/vcenter/ovfs?action=deploy&vmw-task=true` | `Vcenter.Ovfs_deploy$Task` | The one task-form operation adjacent to this scope. |
| GET | `/vcenter/ovf/export-flag` · `/import-flag` | `Vcenter.Ovf.ExportFlag_list` / `ImportFlag_list` | |
| GET | `/vcenter/vm/{vm}/library-item` | `Vcenter.Vm.LibraryItem_get` | Reverse lookup: which item did this VM come from. |
| POST | `/vcenter/iso/image?action=mount` · `unmount` | `Vcenter.Iso.Image_mount` / `_unmount` | Mount an ISO library item to a VM. |

**`ResourcePoolDeploymentSpec.storage_profile_id` is where the two halves of this skill
meet** — it takes a `com.vmware.vcenter.StoragePolicy` identifier, which you get from
`GET /api/vcenter/storage/policies`. Deploy is the cheapest moment to bind a policy; doing it
afterwards is a `PATCH /vcenter/vm/{vm}/storage/policy` and a reconfigure.

**Check-out/check-in is not clone.** `check-out` produces an editable VM linked back to the
template item; `check-in` produces a new **version** of the item. Rolling back is
`?action=rollback` on a version. A plain clone of a template in inventory is
`vsphere-inventory-vm-lifecycle`'s `POST /api/vcenter/vm?action=clone` and has nothing to do
with library versions.

---

## Tags and categories

All **[SPEC-A]**. Paths relative to `/api`. **30 operations under `/cis/tagging`, 3 under
`/vcenter/tagging`** at 9.0.

> ### Path conflict: `/api/cis/tagging` vs `/api/cis-tagging` — resolved in favour of the spec
>
> The research dossier records the tagging group as `/api/cis-tagging/category`,
> `/api/cis-tagging/tag`, `/api/cis-tagging/tag-association`, read off the Broadcom developer
> portal, and marks the per-operation verbs and paths **`UNVERIFIED — could not retrieve`**
> because the `cis-tagging-*` reference pages did not render operation tables.
>
> **The specification declares them with a slash.** In `vcenter.yaml` at tag `9.0.0.0` the
> paths are `/cis/tagging/category`, `/cis/tagging/tag`, `/cis/tagging/tag-association` (and
> their sub-paths), under `servers[0].url = https://{host}/api`, composing to
> `https://<vcenter>/api/cis/tagging/...`. `Cis.Tagging.Category` / `.Tag` / `.TagAssociation`
> are the OpenAPI **tags** on those operations — grouping labels, not path segments. The same
> is true at the `9.1.0.0` tag.
>
> **The dossier's `UNVERIFIED` on the operation tables is resolved by the tables below** — all
> 30 operations, their verbs, their request bodies and their required fields are spec-confirmed.
> Whether `/api/cis-tagging/...` *also* resolves on a live appliance is a separate question
> and remains `UNVERIFIED`; the spec does not contain that spelling.

### Categories

| Verb | Path | operationId | Body / notes |
|---|---|---|---|
| GET | `/cis/tagging/category` | `Cis.Tagging.Category_list` | 200, `array of string` — ids only. *"you need the read privilege on the individual categories."* |
| POST | `/cis/tagging/category` | `Cis.Tagging.Category_create` | `Cis.Tagging.Category.CreateSpec` — **required** `associable_types`, `cardinality`, `description`, `name`; optional `category_id` (*"added in vSphere API 6.7"*, server-generated if omitted). **201**, body is the id string. |
| GET | `/cis/tagging/category/{categoryId}` | `Cis.Tagging.Category_get` | 200 `Cis.Tagging.CategoryModel`; 404 if absent. |
| PATCH | `/cis/tagging/category/{categoryId}` | `Cis.Tagging.Category_update` | `UpdateSpec`: `name`, `description`, `cardinality`, `associable_types` — all optional, *"if missing or `null` … will not be modified"*. |
| DELETE | `/cis/tagging/category/{categoryId}` | `Cis.Tagging.Category_delete` | **Destructive — deletes the category and, by implication, orphans its tags.** |
| POST | `/cis/tagging/category?action=list-used-categories` | `Cis.Tagging.Category_listUsedCategories` | |
| POST | `/cis/tagging/category/{categoryId}?action=add-to-used-by` | `Cis.Tagging.Category_addToUsedBy` | Manages `CategoryModel.used_by`. |
| POST | `/cis/tagging/category/{categoryId}?action=remove-from-used-by` | `Cis.Tagging.Category_removeFromUsedBy` | |
| POST | `/cis/tagging/category/{categoryId}?action=revoke-propagating-permissions` | `Cis.Tagging.Category_revokePropagatingPermissions` | |

**`Cis.Tagging.CategoryModel`** — required `associable_types`, `cardinality`, `description`,
`id`, `name`, `used_by`. `used_by` is *"The set of users that can use this category … You
should not modify other users subscription from this set."*

### Tags

| Verb | Path | operationId | Body / notes |
|---|---|---|---|
| GET | `/cis/tagging/tag` | `Cis.Tagging.Tag_list` | 200, `array of string` — ids only. |
| POST | `/cis/tagging/tag` | `Cis.Tagging.Tag_create` | `Cis.Tagging.Tag.CreateSpec` — **required** `category_id`, `description`, `name`; optional `tag_id`. **201**, id string. **404 if the category does not exist** (P4). |
| GET | `/cis/tagging/tag/{tagId}` | `Cis.Tagging.Tag_get` | 200 `Cis.Tagging.TagModel` — required `category_id`, `description`, `id`, `name`, `used_by`. |
| PATCH | `/cis/tagging/tag/{tagId}` | `Cis.Tagging.Tag_update` | `UpdateSpec`: `name`, `description` **only**. You **cannot** move a tag to another category. |
| DELETE | `/cis/tagging/tag/{tagId}` | `Cis.Tagging.Tag_delete` | **Destructive — removes every association of this tag.** |
| POST | `/cis/tagging/tag?action=list-tags-for-category` | `Cis.Tagging.Tag_listTagsForCategory` | Body `{"category_id": "<id>"}` (**required**). |
| POST | `/cis/tagging/tag?action=list-used-tags` | `Cis.Tagging.Tag_listUsedTags` | |
| POST | `/cis/tagging/tag/{tagId}?action=add-to-used-by` · `remove-from-used-by` · `revoke-propagating-permissions` | `Cis.Tagging.Tag_addToUsedBy` / `_removeFromUsedBy` / `_revokePropagatingPermissions` | |

### Tag associations — two path shapes, and which to use

Eleven operations. The split is **tag id in the path** (one tag, one-or-many objects) versus
**no tag id** (one object, one-or-many tags).

| Verb | Path | operationId | Body |
|---|---|---|---|
| POST | `/cis/tagging/tag-association/{tagId}?action=attach` | `Cis.Tagging.TagAssociation_attach` | `{"object_id": Vapi.Std.DynamicID}` (**required**). **204** on success. |
| POST | `/cis/tagging/tag-association/{tagId}?action=detach` | `..._detach` | Same body. |
| POST | `/cis/tagging/tag-association/{tagId}?action=attach-tag-to-multiple-objects` | `..._attachTagToMultipleObjects` | *"added in vSphere API 6.5."* Returns `BatchResult`. |
| POST | `/cis/tagging/tag-association/{tagId}?action=detach-tag-from-multiple-objects` | `..._detachTagFromMultipleObjects` | |
| POST | `/cis/tagging/tag-association/{tagId}?action=list-attached-objects` | `..._listAttachedObjects` | No body beyond the path id. |
| POST | `/cis/tagging/tag-association?action=attach-multiple-tags-to-object` | `..._attachMultipleTagsToObject` | `{"object_id": DynamicID, "tag_ids": [..]}` (both **required**). Returns `BatchResult`. |
| POST | `/cis/tagging/tag-association?action=detach-multiple-tags-from-object` | `..._detachMultipleTagsFromObject` | |
| POST | `/cis/tagging/tag-association?action=list-attached-tags` | `..._listAttachedTags` | `{"object_id": DynamicID}`. |
| POST | `/cis/tagging/tag-association?action=list-attachable-tags` | `..._listAttachableTags` | `{"object_id": DynamicID}`. P5's pre-check. |
| POST | `/cis/tagging/tag-association?action=list-attached-objects-on-tags` | `..._listAttachedObjectsOnTags` | Returns `TagToObjects[]`. |
| POST | `/cis/tagging/tag-association?action=list-attached-tags-on-objects` | `..._listAttachedTagsOnObjects` | Returns `ObjectToTags[]`. |

**Attach and detach are idempotent.** Verbatim: *"If the tag is already attached to the
object, then this operation is a no-op and an error will not be thrown."* **[SPEC-A]** The
batch forms say the same and add that no entry appears in
`Cis.Tagging.TagAssociation.BatchResult.error_messages` for the no-op case. Do not build
"already attached?" checks; just attach.

**The batch forms return 200 with a `BatchResult`, not an error, on partial failure.** If you
use `attach-multiple-tags-to-object` you must read `error_messages`; a 200 does not mean all
tags attached. At 9.0 there is **no atomic multi-tag operation** — that is 9.1's
`PATCH /vcenter/tagging/associations`.

### `Vapi.Std.DynamicID` — the object reference, and its one gap

```json
{ "type": "<resource type string>", "id": "<managed object id>" }
```

Both `type` and `id` are **required** **[SPEC-A]**. The spec's description of `type` is *"The
type of resource being identified (for example `com.acme.Person`)"* — a deliberately generic
placeholder.

> **The concrete `type` strings for vSphere objects are not enumerated anywhere in the
> vSphere Automation spec.** Neither `DynamicID.type` nor `CategoryModel.associable_types`
> carries an enum or an example list. This is a real gap, and it is the single most likely
> reason a well-formed attach returns 400.
>
> **What the corpus does establish:** the VI-JSON spec declares managed-object type names as
> path segments, and they include `VirtualMachine`, `HostSystem`, `ClusterComputeResource`,
> `Datastore`, `Datacenter`, `Folder`, `Network`, `DistributedVirtualPortgroup`,
> `DistributedVirtualSwitch`, `ResourcePool`, `StoragePod`, `VirtualApp` **[SPEC-V]**. That
> `DynamicID.type` takes exactly these strings is **[INFERRED]** — strongly corroborated,
> not stated.
>
> **How to settle it in one read call, before you write anything:**
> `GET /api/vcenter/tagging/associations` **[SPEC-A — `Vcenter.Tagging.Associations_list`]**
> returns `Vcenter.Tagging.Associations.Summary` objects of the form `{tag, object}` where
> `object` **is** a `DynamicID`. Any existing association in the estate shows you the exact
> spelling the server uses. If the estate has no tags yet, attach one from the vSphere Client
> and read it back.

### `/vcenter/tagging/*` — the name-lookup surface

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/vcenter/tagging/associations` | `Vcenter.Tagging.Associations_list` | *"added in vSphere API 7.0.0.0."* Paginated: `iterate.marker` in, `{associations, marker?, status}` out. `status` enum `READY` \| `END_OF_DATA`. 400 if `marker` is not one this operation issued. |
| GET | `/vcenter/tagging/categories` | `Vcenter.Tagging.Categories_list` | *"added in vSphere API 9.0.0.0."* `names` filter (array, `style: form`, `explode: true`) + `iterate`. Returns `{items: [{category_id, info}], marker?}`. **400 *"If marker and filter are supplied together."*** |
| GET | `/vcenter/tagging/tags` | `Vcenter.Tagging.Tags_list` | Same shape; `info` = `{name, category, description, used_by}` where `category` is the category **id**. |

**This is the only paginated part of tagging.** `/cis/tagging` has no marker, no page size and
no documented cap. `/vcenter/tagging/associations` is therefore the right tool for "give me
every tag association in the estate", and the `END_OF_DATA` status is how you know to stop —
not an empty page.

**At 9.0 all three are read-only.** There is no `POST`, `PATCH` or `DELETE` under
`/vcenter/tagging`. Writing goes through `/cis/tagging`.

---

## Storage policies

### Read and compliance — vSphere Automation, `/api`

All **[SPEC-A]**. Nine operations plus the datastore default.

| Verb | Path | operationId | Notes |
|---|---|---|---|
| GET | `/vcenter/storage/policies` | `Vcenter.Storage.Policies_list` | *"at most 1024 visible … storage policies."* Only filter is `policies` (ids). **500 `UnableToAllocateResource` *"if more than 1024 storage policies exist"***. Returns `Summary` = **required** `policy`, `name`, `description`. |
| POST | `/vcenter/storage/policies/{policy}?action=check-compatibility` | `Vcenter.Storage.Policies_checkCompatibility` | Body `{"datastores": [ids]}` (**required**), *"limited to 1024"*. Returns `CompatibilityInfo.compatible_datastores[].datastore`. |
| GET | `/vcenter/storage/policies/entities/compliance` | `Vcenter.Storage.Policies.Compliance_list` | `status` query param is **required**. Enum `Vcenter.Storage.Policies.Compliance.Status`. Returns `Compliance.Summary` = **required** `vm`, plus `vm_home` and `disks` (map disk-id → status). |
| GET | `/vcenter/storage/policies/compliance/vm` | `Vcenter.Storage.Policies.Compliance.VM_list` | *"at most 1000 virtual machines."* `status` **required**, `vms` optional. Enum `Vcenter.Storage.Policies.Compliance.VM.Status` — **a different enum**. |
| GET | `/vcenter/storage/policies/{policy}/vm` | `Vcenter.Storage.Policies.VM_list` | Returns a **map** VM id → `{vm_home: bool, disks: [disk ids]}`. **500 `UnableToAllocateResource` *"if more than 1000 virtual machines are associated with the specified policy"***. This is the "what would I break" call. |
| GET | `/vcenter/vm/{vm}/storage/policy` | `Vcenter.Vm.Storage.Policy_get` | `Info` = `{vm_home?, disks}` — policy ids. |
| PATCH | `/vcenter/vm/{vm}/storage/policy` | `Vcenter.Vm.Storage.Policy_update` | See below. **Production-affecting.** |
| GET | `/vcenter/vm/{vm}/storage/policy/compliance` | `Vcenter.Vm.Storage.Policy.Compliance_get` | **Cached.** |
| POST | `/vcenter/vm/{vm}/storage/policy/compliance?action=check` | `Vcenter.Vm.Storage.Policy.Compliance_check` | **Recomputes.** Body `CheckSpec` (optional) — **required** `vm_home` (bool) when present, optional `disks`. Omitting the body means *"vmHome set to true and disks populated with all disks attached"*. |
| GET | `/vcenter/datastore/{datastore}/default-policy` | `Vcenter.Datastore.DefaultPolicy_get` | *"the identifier of the current default storage policy associated with the specified datastore."* |

**Exact paths matter here.** It is `/vcenter/storage/policies/**entities**/compliance` and
`/vcenter/storage/policies/**compliance/vm**`. The dossier records these as
`/api/vcenter/storage/policies/compliance` and `/api/vcenter/storage/policies/vm` — neither of
those paths exists in the spec, and neither does `/api/vcenter/datastore-default-policy`
(it is `/vcenter/datastore/{datastore}/default-policy`). Use the spec spellings.

**Two enums, three declarations, one difference.** **[SPEC-A]**

| Enum | Used by | Values |
|---|---|---|
| `Vcenter.Storage.Policies.Compliance.Status` | `/vcenter/storage/policies/entities/compliance` | `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN`**, `NOT_APPLICABLE`, `OUT_OF_DATE` |
| `Vcenter.Storage.Policies.Compliance.VM.Status` | `/vcenter/storage/policies/compliance/vm` | `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN_COMPLIANCE`**, `NOT_APPLICABLE`, `OUT_OF_DATE` |
| `Vcenter.Vm.Storage.Policy.Compliance.Status` | `/vcenter/vm/{vm}/storage/policy/compliance` | `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN_COMPLIANCE`**, `NOT_APPLICABLE`, `OUT_OF_DATE` |

Both list endpoints declare **400 `InvalidArgument`** if `status` *"contains a value that is
not supported by the server"*. Sending `UNKNOWN` to `/compliance/vm` is a 400, not an empty
list. `OUT_OF_DATE` is the one people misread — verbatim: *"Compliance status becomes out of
date when the profile associated with the entity is **edited and not applied**. The
compliance status will remain out of date until the latest policy is applied."*

**`PATCH /vcenter/vm/{vm}/storage/policy` — `Vcenter.Vm.Storage.Policy.UpdateSpec`:**

```json
{
  "vm_home": { "type": "USE_SPECIFIED_POLICY", "policy": "<policy-id>" },
  "disks":   { "<disk-id>": { "type": "USE_DEFAULT_POLICY" } }
}
```

Both `vm_home` and `disks` are optional and *"if missing or `null` the current storage policy
is retained"*. Inside each spec, `type` is **required**, enum exactly `USE_SPECIFIED_POLICY` |
`USE_DEFAULT_POLICY`, and `policy` is *"only relevant when the value of type is
…USE_SPECIFIED_POLICY"* **[SPEC-A]**. Declared errors: 400 `InvalidArgument` *"if the storage
policy specified is invalid"*; 500 `ResourceBusy` *"if the virtual machine or disk is busy
performing another operation"*; 500 `ResourceInaccessible`.

> **This is the production-affecting call in this file.** Re-binding a VM home or a disk to a
> different policy triggers whatever the storage provider does to satisfy the new
> requirements — on vSAN, a resync. Before running it: `GET .../storage/policy` to record
> what is bound now, `POST /vcenter/storage/policies/{policy}?action=check-compatibility`
> against the target datastore, and — if you are changing the *policy itself* rather than a
> single VM's binding — `GET /vcenter/storage/policies/{policy}/vm` to see every VM and disk
> that will move with it.

### Authoring — VI-JSON, `/pbm`, and only there

All **[SPEC-V]**. Base `https://{vcenter-host}/sdk/vim25/{release}`, so a full URL looks like
`https://vcenter.example.com/sdk/vim25/9.0.0.0/pbm/PbmProfileProfileManager/{moId}/PbmCreate`.
Every one is a `POST` except `PbmServiceInstance_getContent`. **33 operations at 9.0, of
which 5 are deprecated.**

**Entry point (P8):** `PbmServiceInstance_PbmRetrieveServiceContent` or
`GET /pbm/PbmServiceInstance/{moId}/content` → `PbmServiceInstanceContent` → take
`profileManager`, `complianceManager`, `placementSolver` as the `{moId}` for everything below.

**`PbmProfileProfileManager` — 20 operations.** Authoring:
`PbmCreate`, `PbmUpdate`, `PbmDelete` (all `StorageProfile.Update`).
Query: `PbmQueryProfile`, `PbmRetrieveContent`, `PbmQueryAssociatedEntity`,
`PbmQueryAssociatedEntities`, `PbmQueryAssociatedProfile`, `PbmQueryAssociatedProfiles`,
`PbmQuerySpaceStatsForStorageContainer`.
Capability metadata: `PbmFetchCapabilityMetadata`, `PbmFetchCapabilitySchema`,
`PbmFetchResourceType`, `PbmFetchVendorInfo`.
Defaults: `PbmAssignDefaultRequirementProfile`, `PbmQueryDefaultRequirementProfile`,
`PbmQueryDefaultRequirementProfiles`, `PbmFindApplicableDefaultProfile`,
`PbmResetVSanDefaultProfile`, and `PbmResetDefaultRequirementProfile` (**deprecated**).

**`PbmComplianceManager` — 5 operations:** `PbmCheckCompliance`, `PbmCheckRollupCompliance`,
`PbmFetchComplianceResult`, `PbmFetchRollupComplianceResult`,
`PbmQueryByRollupComplianceStatus`. All `StorageProfile.View`.

**`PbmPlacementSolver` — 5 operations:** `PbmCheckRequirements` (current), plus
`PbmCheckCompatibility`, `PbmCheckCompatibilityWithSpec`, `PbmQueryMatchingHub`,
`PbmQueryMatchingHubWithSpec` — **all four deprecated in the 9.0 spec**. Prefer
`PbmCheckRequirements`, or the `/api` `checkCompatibility` for the simple datastore question.

**`PbmReplicationManager`:** `PbmQueryReplicationGroups`.

**`PbmCreate` body — `PbmCreateRequestType` = `{createSpec: PbmCapabilityProfileCreateSpec}`.**
`PbmCapabilityProfileCreateSpec` **requires `name`, `resourceType`, `constraints`**; optional
`description`, `category` **[SPEC-V]**. Two traps in that required list:

- **`resourceType` is required *and* deprecated.** Spec, verbatim: *"Deprecated as of vSphere
  API 6.5. Specifies the type of resource to which the profile applies. The only legal value
  is STORAGE - deprecated."* It sits in the `required` array anyway. Send it.
- **`category`** — verbatim: *"This can be REQUIREMENT … or null when creating a storage
  policy. And it can be DATA\_SERVICE\_POLICY … when creating a data service policy. RESOURCE
  … is not allowed as resource profile is created by the system."*

`name` has a stated limit: *"The maximum length of the name is 80 characters."* `constraints`
is a `PbmCapabilityConstraints` holding `subProfiles[]`, each a `PbmCapabilitySubProfile`
(`name`, `capability[]`, `forceProvision`) — *"A subprofile corresponds to a rule set in the
vSphere Web Client."* Build the capability expressions from
`PbmFetchCapabilityMetadata` / `PbmFetchCapabilitySchema`; do not hand-write them.

`PbmCreate` declares a **500** carrying `InvalidArgument` *"if `PbmCapabilityProfileCreateSpec`
is invalid"*, `PbmFaultProfileStorageFault`, or `PbmDuplicateName` *"if a profile with the
same name already exists"* **[SPEC-V]**. Note that VI-JSON reports faults as **500**, not
400 — a validation error here does not look like a validation error.

**`PbmDelete` will refuse a policy in use.** Its result is an array of
`PbmProfileOperationOutcome`, and the spec lists `PbmResourceInUse` — *"Profile is still
associated with an entity"* — among the faults **[SPEC-V]**. Deletion is per-profile and
reported per-profile: a 200 does not mean every id in your request was deleted. Check the
outcomes.

**Object references on `/pbm` are `PbmServerObjectRef`, not `DynamicID`.** **Required**
`objectType` and `key`; optional `serverUuid`. The spec gives the key mapping verbatim:
`virtualMachine` → *virtual-machine-MOR*; `virtualDiskId` → *virtual-disk-MOR:VirtualDisk.key*;
`datastore` → *datastore-MOR* **[SPEC-V]**. Note the lower-camel object type names — these are
**not** the same strings as the tagging `DynamicID.type` values.

**`PbmCheckCompliance` body** = `{entities: PbmServerObjectRef[], profile?: PbmProfileId}`;
`PbmProfileId` is `{uniqueId}`. Results are `PbmComplianceResult` = `{checkTime, entity,
profile, complianceTaskStatus, complianceStatus, violatedPolicies, errorCause,
operationalStatus, info, mismatch(deprecated)}` **[SPEC-V]**. The value spaces of
`complianceStatus` (`PbmComplianceStatus_enum`) and `complianceTaskStatus`
(`PbmComplianceResultComplianceTaskStatus_enum`) are referenced by name but **not expanded as
JSON schema enums** in `vi-json.yaml` — their member lists are `UNVERIFIED` from this corpus.
Use the `/api` compliance endpoints when you need enum values you can rely on.

---

## Worked example — create a category, create a tag, attach it to a VM

**Goal:** create a `MULTIPLE`-cardinality category `Environment`, create the tag
`Environment / production` in it, and attach that tag to the VM `app-web-07`. Every
identifier below is a value the server returned.

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

Credential acquisition, and any 401 here, belongs to `vcf-foundation`. Everything below just
sends the header (P1).

### Step 1 — Settle the object-type string before writing anything (P6)

```bash
curl -sS "${AUTH[@]}" "$VC/api/vcenter/tagging/associations" \
  | jq -r '.associations[0].object | "\(.type)  \(.id)"'
```

`GET /api/vcenter/tagging/associations` **[SPEC-A — `Vcenter.Tagging.Associations_list`]**.
`Vcenter.Tagging.Associations.Summary.object` is a `Vapi.Std.DynamicID`, so this prints the
exact `type` spelling this vCenter uses. The rest of this example assumes it is
`VirtualMachine` — **[INFERRED]**, corroborated by the VI-JSON managed-object type names.
If the estate has no associations yet, this returns an empty array; tag one object in the
vSphere Client and re-run rather than guessing.

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

Field notes, all spec-stated:
- `associable_types`, `cardinality`, `description`, `name` are **all four required**. There is
  no "just give me a name" form — `description: ""` is how you decline to write one.
- `cardinality: "MULTIPLE"` lets a VM carry `production` *and* `pci-scope` from this category.
  `SINGLE` would make the second attach a 400 (P5).
- `associable_types: ["VirtualMachine"]` restricts this category's tags to VMs. **`[]` means
  all types** — *"If the set is empty, then tags can be attached to all types of objects."*
  If you are unsure of the exact strings, `[]` is the safe choice and the check is enforced
  only for Inventory Service objects anyway.
- Optional `category_id` lets you supply your own id; omit it and *"an identifier will be
  generated by the server"*.
- **400 `AlreadyExists`** if a category with that name exists; **400 `InvalidArgument`**
  otherwise; **403** if you lack the create-category privilege.

If the category may already exist, resolve instead of creating:

```bash
CAT=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/tagging/categories?names=$CAT_NAME" \
      | jq -r '.items[0].category_id')
```

`GET /api/vcenter/tagging/categories` **[SPEC-A — `Vcenter.Tagging.Categories_list`, *"added
in vSphere API 9.0.0.0"*]**. Do **not** add `iterate` to this call — `marker` and the filter
together are a documented **400**.

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
- **404 means the category id is wrong**, not that the endpoint is wrong — *"if the category
  for in the given createSpec does not exist in the system"*.
- **400 `AlreadyExists`** is scoped: *"the name of an already existing tag **in the input
  category**"*. The same tag name in a different category is legal.
- The privilege is *"the create tag privilege **on the input category**"* — per-object, not
  global.
- Note the `jq -n --arg` construction. A single-quoted `-d '{...}'` would post the literal
  string `$cat`.

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

`GET /api/vcenter/vm` belongs to `vsphere-inventory-vm-lifecycle`; it is here only to produce
a real `vm-NNN` identifier.
`POST /api/cis/tagging/tag-association?action=list-attachable-tags`
**[SPEC-A — `Cis.Tagging.TagAssociation_listAttachableTags`]**, body `{"object_id": DynamicID}`
(**required**). Spec: *"Fetches the list of attachable tags for the given object, omitting the
tags that have already been attached."*

That last clause matters: a tag **already attached** is absent from this list, so the warning
above can fire on a no-op re-run. Treat it as a warning, not a failure.

### Step 5 — Attach

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association/$TAG?action=attach" \
  -d "$(jq -n --argjson o "$OBJ" '{object_id: $o}')"
```

`POST /api/cis/tagging/tag-association/{tagId}?action=attach`
**[SPEC-A — `Cis.Tagging.TagAssociation_attach`]**. Body `{"object_id": DynamicID}`,
**`object_id` required**. Success is **204 No Content** — there is no body to parse, and
`jq` on the response will fail. Privileges: *"the attach tag privilege on the tag and the read
privilege on the object"*.

Idempotent by design: *"If the tag is already attached to the object, then this operation is a
no-op and an error will not be thrown."*

**To attach several tags at once**, use the other path shape:

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association?action=attach-multiple-tags-to-object" \
  -d "$(jq -n --argjson o "$OBJ" --arg t1 "$TAG" '{object_id:$o, tag_ids:[$t1]}')" \
  | jq '.'
```

`..._attachMultipleTagsToObject` **[SPEC-A]** returns **200** and a
`Cis.Tagging.TagAssociation.BatchResult`. **It is not atomic at 9.0** — read
`error_messages`; a 200 with failures inside is the normal partial-failure shape. 9.1's
`PATCH /vcenter/tagging/associations` is the atomic, roll-back-on-failure alternative and
does not exist here.

### Step 6 — Verify both directions

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association?action=list-attached-tags" \
  -d "$(jq -n --argjson o "$OBJ" '{object_id: $o}')" | jq -r '.[]'

curl -sS -X POST "${AUTH[@]}" \
  "$VC/api/cis/tagging/tag-association/$TAG?action=list-attached-objects" | jq -r '.[].id'
```

`..._listAttachedTags` and `..._listAttachedObjects` **[SPEC-A]**. The first should contain
`$TAG`; the second should contain `$VM`. Note the second takes **no request body** — the tag
id is in the path.

To read it back with names rather than ids:
`GET /api/vcenter/tagging/tags?names=production` **[SPEC-A]** gives `{tag, info:{name,
category, description, used_by}}`.

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 404 on step 2 or 3 with the path itself | You used `/api/cis-tagging/...`. The spec path is `/api/cis/tagging/...` (slash). |
| 400 `AlreadyExists` on step 2 | The category name is taken. Resolve it with `/vcenter/tagging/categories?names=` instead. |
| **404** on step 3 | `$CAT` is wrong or stale — the tag create's 404 is specifically *"the category … does not exist"*. |
| 400 `AlreadyExists` on step 3 | A tag with that name already exists **in that category**. |
| 400 on step 3 with a valid category | A required field is missing — `category_id`, `description` and `name` are all mandatory. |
| 400 on step 5, *"not eligible to be attached to this object or … objectId is not valid"* | Three distinct causes behind one code: wrong `DynamicID.type` string (step 1), `SINGLE` cardinality already satisfied, or the object type is not in `associable_types` (P5). |
| 403 on step 5 | Per-object privileges: attach-tag on the tag **and** read on the object. Holding one is not enough. |
| `jq` parse error on step 5 | Success. The attach returns **204** with no body. |
| Step 6 shows the tag but a later report does not | Check whether the report reads `/vcenter/tagging/associations` and stopped before `status: END_OF_DATA` — that endpoint pages. |
| 400 on `/vcenter/tagging/categories` | You supplied `iterate` **and** `names`. Documented 400: *"If marker and filter are supplied together."* |

---

## Out of scope — where to route instead

| Topic | Paths | Skill |
|---|---|---|
| VM create, clone, power, reconfigure, delete; datacenter/cluster/host/datastore/network/folder/resource-pool traversal | `/api/vcenter/vm*`, `/api/vcenter/{datacenter,cluster,host,datastore,network,folder,resource-pool}` | `vsphere-inventory-vm-lifecycle` |
| ESX images, software drafts, depots, remediation, configuration profiles | `/api/esx/settings/*` (339 ops at 9.0) | `vsphere-lifecycle-vlcm` |
| vSAN cluster config, disk groups, health, vSAN Data Protection | `/api/vcenter/vsan/*`, snapservice | `vsan-storage` |
| SSO, federation, token exchange, identity providers | — | `vcf-foundation` |
| Anything not covered anywhere | — | `vcf-api-discovery` |

**One deliberate overlap.** `vsan-storage` also documents the `/pbm` families, because vSAN
storage policies *are* SPBM policies. Both skills describe the same 33 operations from the
same spec; neither invented a separate API. If the question is "vSAN policy for this cluster",
that skill has the vSAN-specific capability context. If it is "storage policies generally",
stay here.

---

## What is unverified for 9.0

- **The concrete `Vapi.Std.DynamicID.type` strings** (and therefore the
  `associable_types` vocabulary). No enum, no example list anywhere in the vSphere Automation
  spec. `VirtualMachine` and friends are **[INFERRED]** from VI-JSON managed-object type path
  segments. Resolve per-estate via `GET /api/vcenter/tagging/associations` before writing a
  client.
- **Canonical tagging privilege strings.** The 9.0 spec describes them only in prose (*"the
  attach tag privilege"*). No `InventoryService.Tagging.*` string appears in the 9.0 spec at
  all. They do appear at 9.1 — see `../deltas.md`.
- **Privilege names for `/api/vcenter/storage/policies*`.** The 403s say only *"the required
  privileges"*. `StorageProfile.View` is **[INFERRED]** from the `/pbm` equivalents.
- **The `{moId}` value for `PbmServiceInstance`.** The spec offers `ServiceInstance` only as
  an example of the *form* of a managed-object id.
- **`PbmComplianceStatus_enum` and `PbmComplianceResultComplianceTaskStatus_enum` member
  lists.** Referenced by name in `vi-json.yaml`, not expanded as JSON schema enums.
- **How to obtain the task handle for asynchronous content deletion.** The library-item delete
  says the content removal *"can be tracked with a task"* but returns no task identifier, and
  no `/content` operation has a `vmw-task=true` form.
- **Whether `/api/cis-tagging/...` also resolves on a live appliance.** The spec declares only
  `/cis/tagging/...`; the portal renders the hyphenated form. Only one of those is evidence.
- **Whether `Content.Library_migrate` reports progress or completion anywhere reachable.** The
  description narrates three phases and a `MAINTENANCE` transition; the operation's response
  shape and any polling route were not established.
- **Behavior of `Cis.Tagging.Category_delete` on a category with attached tags.** The
  operation exists and is destructive; the spec does not state whether it cascades to tags and
  associations or refuses.
- **Any cap or pagination on the `/cis/tagging` list operations.** Unlike the inventory lists
  and the storage-policy list, no cap is stated and no marker exists. Whether a very large
  estate truncates is not addressed.
