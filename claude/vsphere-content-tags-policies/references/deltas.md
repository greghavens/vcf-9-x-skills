# VCF 9.0 → 9.1 — content library, tags and storage policies delta

Scoped to the content library, tagging and storage-policy surfaces: `/api/content/*`,
`/api/cis/tagging/*`, `/api/vcenter/tagging/*`, `/api/vcenter/storage/policies*`,
`/api/vcenter/vm/{vm}/storage/policy*`, the library-item deploy paths, and the VI-JSON
`/pbm/*` family.

**Source keys.**
`SPECA9.0` / `SPECA9.1` = `research/spec-inventory/9.{0,1}__vsphere-automation.ops.json`,
machine-extracted from `specifications/vsphere/openapi/automation/vcenter.yaml` at git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`.
`SPECV9.0` / `SPECV9.1` = the corresponding `*__vsphere-vi-json.ops.json`, from
`specifications/vsphere/openapi/vi-json/vi-json.yaml`.
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed tag diff).
`DVS` = `research/vsphere-vcenter-vsan.md` (the dossier).
`[DOC]` = version-pinned Broadcom prose. `UNVERIFIED` = the research could not establish it.

---

## Headline: content library moved, tagging gained one operation, policies did not move at all

| | 9.0 | 9.1 |
|---|---|---|
| `/content/*` | **72** | **83** (+11, −0) |
| `/cis/tagging/*` | **30** | **30** — identical |
| `/vcenter/tagging/*` | **3** | **4** (+1) |
| `/vcenter/storage/policies*` | **5** | **5** — identical |
| `/vcenter/vm/{vm}/storage/policy*` | **4** | **4** — identical |
| `/vcenter/vm-template/library-items/*` | **12** | **12** — identical |
| `/vcenter/ovf/*` | **6** | **6** — identical |
| VI-JSON `/pbm/*` | **33** (5 deprecated) | **33** (same 5 deprecated) — identical |
| Newly deprecated in scope | — | **none** |
| Removed in scope | — | **none** |

[SPECA9.0; SPECA9.1; SPECV9.0; SPECV9.1; DELTA]

**Nothing in this scope was removed or newly deprecated.** Every 9.0 path still resolves at
9.1. The migration risk runs the other way: 9.1 runbooks that use the new library operations
404 on 9.0.

**Storage policies are the flat part.** All nine `/api` storage-policy operations, both
compliance enums, `Vcenter.Vm.Storage.Policy.UpdateSpec`, the 1024/1000 caps, and all 33
`/pbm` operations including the five deprecated placement-solver/reset ones are **identical at
both tags**. A storage-policy client written for one version works on the other unchanged.

---

## Three premises to correct on contact

**1. "`force-delete` on a content library works everywhere."** No — it is **9.1-only**. The
dossier's *"fully verified operation table for local libraries"* lists
`POST /api/content/local-library/{libraryId}?action=force-delete` **[DVS]**, and that table was
read from the portal's *latest* (9.1) pages. `Content.LocalLibrary_forceDelete` does not exist
in `SPECA9.0`; its spec description at 9.1 says *"This operation was added in vSphere API
9.1.0.0."* Same for `Content.Library_forceDelete` and `Content.SubscribedLibrary_forceDelete`.
Running that call against a 9.0 vCenter is a 404.

**2. "`DELETE /api/content/library/{libraryId}` has always been there."** No. At 9.0 the union
view `/content/library/{libraryId}` supports only `GET` and `PATCH`; delete is per-type
(`/content/local-library/{id}`, `/content/subscribed-library/{id}`). `Content.Library_delete`
is new at 9.1, and it is the one that performs the usage check.

**3. "Multi-tag attach is atomic."** Only at 9.1, and only on the new endpoint. At **both**
versions `POST /cis/tagging/tag-association?action=attach-multiple-tags-to-object` returns 200
with a `Cis.Tagging.TagAssociation.BatchResult` and reports partial failure in
`error_messages` — no rollback. 9.1's `PATCH /vcenter/tagging/associations` is the atomic one:
*"Partial completion is not allowed; in case of failure, the partially applied operation will
be rolled back."* [SPECA9.1]

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **Base paths** | `/api` for content, tagging, policy read; `/sdk/vim25/{release}` for `/pbm` | **Unchanged** on both surfaces | SPECA both; SPECV both |
| **Session mechanism** | `vmware-api-session-id` header on both surfaces | **Unchanged** | SPECA both; SPECV both |
| **Tagging paths** | `/cis/tagging/{category,tag,tag-association}` — *not* `/cis-tagging` | **Unchanged**, same 30 operations, same operationIds | SPECA both; DVS records the hyphenated portal spelling |
| **Tag / category schemas** | `Category.CreateSpec` (4 required + `category_id`), `Tag.CreateSpec` (3 required + `tag_id`), `Cardinality` = `SINGLE`\|`MULTIPLE` | **Identical** property sets and required lists | SPECA both |
| **Tag association write** | 6 write operations on `/cis/tagging/tag-association`, batch forms non-atomic | Same 6, **plus `PATCH /vcenter/tagging/associations`** — atomic, roll-back-on-failure, accepts tag **name + category name** | SPECA9.1 |
| **Tagging privilege strings** | **None in the spec** — prose only (*"the attach tag privilege"*) | Two appear: `InventoryService.Tagging.ObjectAttachable`, `InventoryService.Tagging.AttachTag`, on the new `PATCH` only | SPECA both |
| **`/vcenter/tagging` read ops** | `associations` (7.0.0.0), `categories` + `tags` (9.0.0.0), `names` filter, `iterate` marker, 400 on both together | **Unchanged**, same "added in" notes | SPECA both |
| **`Vapi.Std.DynamicID`** | `{type, id}`, both required, `type` values not enumerated | **Unchanged, still not enumerated** | SPECA both |
| **Content library core** | 72 ops; `Content.LibraryModel`, `StorageBacking` (`DATASTORE`\|`OTHER`), `PublishInfo`, `SubscriptionInfo`, probe, sync, evict, migrate | **83 ops**, all 72 retained with identical schemas | SPECA both; DELTA |
| **Library delete** | Per-type only. No usage check | Adds `DELETE /content/library/{libraryId}` with a usage check, plus **three** `force-delete` actions that skip it | SPECA9.1 |
| **Library usages** | — | `GET·POST /content/library/{library}/usages`, `GET·DELETE /usages/{usage}`. *"A content library can be safely deleted if no usage is present"*. `resource_urn` format `urn:vmomi:vm:vm-12` | SPECA9.1 |
| **Library maintenance state** | `Content.Library.StateInfo` (`ACTIVE`\|`MAINTENANCE`) exists — *"added in vSphere API 9.0.0.0"* — but the **only** route in is `?action=migrate` | Adds explicit `?action=enter-maintenance` / `?action=exit-maintenance` | SPECA both |
| **Subscribed → published conversion** | Not possible via API | `POST /content/library/{libraryId}?action=convert`, `ConversionSpec.conversion_type` = `TO_PUBLISHED_LIBRARY`, five documented `NotAllowedInCurrentState` preconditions | SPECA9.1 |
| **Content library privileges** | **34** distinct `ContentLibrary.*` strings in the spec | **39** — the same 34 **plus** `DeleteLibrary`, `ConvertLibrary`, `LibraryMaintenance`, `AddLibraryUsage`, `RemoveLibraryUsage` | SPECA both |
| **Library item + sessions** | `Item_*`, 20 update/download-session operations | **Identical** — no additions, no schema changes | SPECA both |
| **VM template / OVF library items** | 12 + 6 operations; `CreateSpec` requires `library`+`name`+`source_vm`, `DeploySpec` requires `name`, `ResourcePoolDeploymentSpec` requires `accept_all_eula` | **Byte-identical** | SPECA both |
| **Storage policy read + compliance** | 9 operations + `datastore/{ds}/default-policy`; caps 1024 policies / 1000 VMs | **Identical** paths, operationIds, schemas, caps and errors | SPECA both |
| **Compliance enums** | `Compliance.Status` has `UNKNOWN`; `Compliance.VM.Status` and `Vm.Storage.Policy.Compliance.Status` have `UNKNOWN_COMPLIANCE` | **All three unchanged**, including the mismatch | SPECA both |
| **Storage policy authoring** | VI-JSON `/pbm/*`, 33 ops, `PbmCreate`/`PbmUpdate`/`PbmDelete`; 5 deprecated | **Byte-identical** — same 33, same 5 deprecated | SPECV both |
| **Supervisor storage policies** | — | Adds `GET·PATCH /vcenter/namespace-management/supervisors/{supervisor}/control-plane/storage/policies` and `.../workloads/storage/policies` | SPECA9.1; DELTA |
| **Task forms** | No `vmw-task=true` variant anywhere in this scope | **Still none** | SPECA both |
| **Deprecations in scope** | — | **Zero** newly deprecated `/content`, `/cis/tagging`, `/vcenter/tagging` or storage-policy operations | SPECA both |

---

## The eleven new content-library operations, verbatim from the tag diff

```
DELETE /content/library/{libraryId}                              Content.Library_delete
POST   /content/library/{libraryId}?action=convert               Content.Library_convert
POST   /content/library/{libraryId}?action=enter-maintenance     Content.Library_enterMaintenance
POST   /content/library/{libraryId}?action=exit-maintenance      Content.Library_exitMaintenance
POST   /content/library/{libraryId}?action=force-delete          Content.Library_forceDelete
GET    /content/library/{library}/usages                         Content.Library.Usages_list
POST   /content/library/{library}/usages                         Content.Library.Usages_add
GET    /content/library/{library}/usages/{usage}                 Content.Library.Usages_get
DELETE /content/library/{library}/usages/{usage}                 Content.Library.Usages_remove
POST   /content/local-library/{libraryId}?action=force-delete     Content.LocalLibrary_forceDelete
POST   /content/subscribed-library/{libraryId}?action=force-delete Content.SubscribedLibrary_forceDelete
```

[DELTA; SPECA9.1] Every one carries *"This operation was added in vSphere API 9.1.0.0"* in its
own description.

**They form one coherent feature, not eleven unrelated additions:** a library now has a
declared *usage* registry and an explicit *maintenance* state, and delete is gated on the
first while content mutation is gated on the second. `force-delete` is the documented override
— *"skipping the usage check"* — and carries the same warning as every other library delete:
*"If the asynchronous task fails, file content may remain on the storage backing. This content
will require manual removal."*

**Upgrade consequence.** Nothing breaks on upgrade — the 9.0 per-type deletes still exist. But
a 9.0-era teardown script that deletes a library will now succeed where an operator might
expect the usage check to stop it, because the 9.0 paths **do not consult usages**. If you rely
on the new safety, call `DELETE /content/library/{libraryId}`, not
`DELETE /content/local-library/{libraryId}`.

---

## The one new tagging operation, and why it is worth rewriting a client for

```
PATCH /vcenter/tagging/associations                             Vcenter.Tagging.Associations_update
```

[DELTA; SPECA9.1] *"This operation was added in vSphere API 9.1.0.0."*

Body `Vcenter.Tagging.Associations.UpdateSpec` — **required** `object` (`Vapi.Std.DynamicID`)
and `tag_spec_list` (array of `TagSpec`). `TagSpec` requires `operation`
(`ATTACH` | `DETACH`) and at least one of `tag_id` or
`tag_category_name_info: {tag_name, category_name}` — *"If both are specified,
`TagCategoryNameInfo` must refer to the same `Tag`. If … both are missing or `null`, the update
operation will throw an `InvalidArgument`."*

Three things it gives you that no 9.0 operation does:

1. **Atomicity.** *"Partial completion is not allowed; in case of failure, the partially applied
   operation will be rolled back."* The 9.0 batch forms report partial failure inside a 200.
2. **Name-based addressing.** `tag_category_name_info` removes the
   `/vcenter/tagging/categories?names=` + `/vcenter/tagging/tags?names=` lookup pair that every
   9.0 tagging script opens with.
3. **Mixed attach and detach in one call**, against one object.

**Read `UpdateResult` carefully.** `success` is the only required property. `results` is
*"populated only when … `success` is set to `true`"* and lists *"which tags were newly added or
removed as part of this call"* — **not** which operations succeeded. Re-running an already-satisfied
request returns `success: true` with an empty `results`; that is correct. `errors` appears only
when `success` is `false`.

**Its 403 is the first spec-stated tagging privilege in this corpus:**
`InventoryService.Tagging.ObjectAttachable` on the object and
`InventoryService.Tagging.AttachTag` on each tag. The `/cis/tagging` operations still describe
their privileges only in prose at both versions, so those strings remain `UNVERIFIED`.

**Dual-version clients:** feature-detect rather than version-detect. Try the `PATCH`; on 404 or
405 fall back to `POST /cis/tagging/tag-association?action=attach-multiple-tags-to-object` and
**add your own reconciliation**, because the fallback is not atomic.

---

## Corrections the specs make to the dossier, at both versions

The dossier `[DVS]` was assembled from the Broadcom developer portal and flags several of these
itself. All of them are resolved the same way at both tags.

| Dossier record | Spec at both tags | Effect |
|---|---|---|
| `/api/cis-tagging/category`, `/tag`, `/tag-association`; **operation tables `UNVERIFIED — could not retrieve`** | `/cis/tagging/category`, `/cis/tagging/tag`, `/cis/tagging/tag-association` — **30 operations, verbs, bodies and required fields all present** | **The `UNVERIFIED` is resolved.** Use the slash form. Whether the hyphenated form also resolves live is still `UNVERIFIED` |
| `GET /api/vcenter/storage/policies/compliance` | **No such path.** It is `/vcenter/storage/policies/entities/compliance` | 404 as written |
| `GET /api/vcenter/storage/policies/vm` | **No such path.** It is `/vcenter/storage/policies/{policy}/vm` | 404 as written |
| `GET /api/vcenter/datastore-default-policy` | **No such path.** It is `/vcenter/datastore/{datastore}/default-policy` | 404 as written |
| `POST /api/vcenter/storage/policies?action=check-compatibility` | It is per-policy: `/vcenter/storage/policies/{policy}?action=check-compatibility` | 404 as written |
| `POST /api/content/local-library/{libraryId}?action=force-delete` listed as verified | **9.1 only** | 404 on 9.0 |
| Content-library group paths only, no operation tables | 72 / 83 operations fully enumerated | — |

---

## What did *not* change, restated for change records

- **Every `/api` and `/pbm` base path, and the `vmware-api-session-id` header on both.**
- **All 30 `/cis/tagging` operations**, their operationIds, request bodies and required fields.
- **`Cis.Tagging.Category.CreateSpec`, `Tag.CreateSpec`, `CategoryModel`, `TagModel`,
  `Cardinality`, `Vapi.Std.DynamicID`** — identical property sets and required lists.
- **All 72 of 9.0's content-library operations**, with identical schemas — `LibraryModel`,
  `StorageBacking`, `PublishInfo`, `SubscriptionInfo`, `ItemModel`, `ProbeResult.Status`,
  `StateInfo.State`, and the optimistic-concurrency behaviour of `version` (500 `ResourceBusy`
  / 409 `ConcurrentChange`).
- **The 20 update/download-session operations**, unchanged.
- **All 12 VM-template and 6 OVF library-item operations**, and their create/deploy specs
  including `ResourcePoolDeploymentSpec.storage_profile_id`.
- **Every storage-policy read and compliance operation on `/api`**, their required `status`
  query parameters, the three compliance enums, the 1024-policy and 1000-VM caps, and the
  explicit `UnableToAllocateResource` on exceeding them.
- **`Vcenter.Vm.Storage.Policy.UpdateSpec`** and both `PolicyType` enums
  (`USE_SPECIFIED_POLICY` | `USE_DEFAULT_POLICY`).
- **All 33 `/pbm` operations**, including which five are deprecated, the
  `PbmCapabilityProfileCreateSpec` required list (`name`, `resourceType`, `constraints` — with
  `resourceType` required *and* deprecated), `PbmServerObjectRef`, `PbmServiceInstanceContent`,
  and the `StorageProfile.View` / `StorageProfile.Update` / `System.Anonymous` privilege split.
- **The absence of any `vmw-task=true` form** anywhere in this scope.

## Deltas this research could NOT establish

- **The concrete `Vapi.Std.DynamicID.type` and `associable_types` strings** at either version —
  so no statement about whether the vocabulary changed. Not enumerated in either spec.
- **Canonical privilege strings for the `/cis/tagging` operations** at either version. 9.1 names
  two, on one new endpoint only; the rest is prose at both tags.
- **Privilege names for `/api/vcenter/storage/policies*`** at either version.
- **The `{moId}` for `PbmServiceInstance`**, and therefore whether it changed.
- **`PbmComplianceStatus_enum` / `PbmComplianceResultComplianceTaskStatus_enum` member lists** at
  either version.
- **Whether `Content.Library.Usages` is populated automatically by consuming subsystems or only
  by explicit `Usages_add` calls.** This decides whether the new usage check is a genuine safety
  net or an advisory one, and the spec does not say.
- **Whether an existing 9.0 library acquires usage entries on upgrade to 9.1**, or starts empty
  — i.e. whether `DELETE /content/library/{libraryId}` will be permissive on freshly upgraded
  estates.
- **How to obtain the task handle for asynchronous content deletion** at either version.
- **Whether `/api/cis-tagging/...` resolves on a live appliance** at either version.
