# Finding the vSAN stretched-cluster API in VCF 9.1

Short version: the API exists, it's `PATCH /v1/clusters/{id}` on **SDDC Manager**, and the reason you can't find it is that the VCF 9.x API reference is no longer where search engines point you. Below is the answer plus the general method for finding *any* VCF 9.1 API when the docs come up empty — that method is worth more than the one endpoint.

---

## 1. Why you can't find it

Two traps:

- **`developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/`** is the page every search result lands on. Its version selector tops out at **5.2.4** — there is no 9.0 or 9.1 in it. It looks authoritative and it looks current ("latest"), so people conclude the API doesn't exist. It's just the legacy VCF 4.x/5.x reference that never got a 9.x branch.
- **"vSAN stretched cluster" is not a vSAN API in VCF.** Stretching is a *fleet* operation (hosts, fault domains, NSX overlay, witness), so it lives in the SDDC Manager API, not in vSphere Automation. Searching the vSphere/vCenter REST docs returns nothing — I checked the 9.1 `vcenter.yaml` Automation spec and the string "stretch" appears **zero** times. That dead end is expected, not a sign you're looking wrong.

---

## 2. The reliable discovery method: grep the OpenAPI spec

As of 9.0, VMware publishes machine-readable OpenAPI 3.0 specs for every VCF component in a public GitHub repo, tagged per release. **This is the source of truth** — it is generated from the same code that serves the API, so it can't drift from reality the way HTML docs can.

Repo: **https://github.com/vmware/vcf-api-specs** (release tag `VCF API Specs 9.1.0.0`)

```bash
# blobless clone keeps it fast — the vSphere WSDLs in this repo are large
git clone --filter=blob:none --no-checkout --depth 1 \
  https://github.com/vmware/vcf-api-specs.git
cd vcf-api-specs
git ls-tree -r --name-only HEAD | grep specifications/
git checkout HEAD -- specifications/sddc-manager/sddc-manager-openapi.json
```

The component layout (verified, `main` @ 9.1):

| Component | Spec file |
|---|---|
| SDDC Manager | `specifications/sddc-manager/sddc-manager-openapi.json` |
| VCF Installer | `specifications/vcf-installer/vcf-installer-openapi.json` |
| vSphere (REST) | `specifications/vsphere/openapi/automation/vcenter.yaml` |
| vSphere (VI/JSON) | `specifications/vsphere/openapi/vi-json/vi-json.yaml` |
| vSphere (SOAP) | `specifications/vsphere/wsdl/{vim,vsan,pbm,eam,sms,vslm,ssoclient}/` |
| NSX | `specifications/nsx/openapi-2.0/nsx_{api,policy_api,global_policy_api}.yaml` |
| VCF Operations | `specifications/vcf-operations/vcf-operations-openapi.json` |
| Fleet LCM / SDDC LCM | `specifications/fleet-lcm/…`, `specifications/sddc-lcm/…` |
| vSAN Data Protection | `specifications/vsan-data-protection/vsan-data-protection-openapi.yaml` |

Then search it by **schema name**, not by URL path. VCF overloads a handful of endpoints with big discriminated union bodies, so the capability you want is almost always a *schema*, invisible if you only scan paths:

```bash
python3 - <<'PY'
import json
s = json.load(open('specifications/sddc-manager/sddc-manager-openapi.json'))
print(s['info']['version'])                      # -> 9.1.0.0
print([k for k in s['components']['schemas'] if 'tretch' in k])
PY
```

Output:

```
9.1.0.0
['ClusterStretchNetworkSpec', 'ClusterStretchSpec', 'ClusterUnstretchSpec',
 'NsxStretchClusterSpec', 'StretchClusterNetworkProfile']
```

There it is. This whole loop is about two minutes and it works for every VCF subsystem.

---

## 3. What the stretched-cluster API actually is

**`PATCH /v1/clusters/{id}`** on SDDC Manager. Official summary from the 9.1 spec:

> *"Update a Cluster by adding or removing Hosts, Stretching a standard vSAN cluster, Unstretching a stretched cluster or by marking for deletion"* (`operationId: updateCluster`)

The body is a `ClusterUpdateSpec`, which is a union — you set exactly one of these fields:

| Field | Purpose |
|---|---|
| `prepareForStretch` (bool) | Pre-stage the cluster before the stretch call |
| `clusterStretchSpec` | Do the stretch |
| `clusterUnstretchSpec` | Collapse back (`azToRemove`) |
| `clusterExpansionSpec` / `clusterCompactionSpec` | Add/remove hosts |
| `markForDeletion`, `markAsDefault`, `name`, `dnsNtpUpdateSpec`, `clusterTransitionSpec`, `clusterImageComplianceCheckSpec`, `clusterPrimaryDatastoreUpdateSpec` | Other cluster mutations |

`ClusterStretchSpec` — **required: `hostSpecs`, `witnessSpec`**:

| Field | Type | Notes |
|---|---|---|
| `hostSpecs` | array | Hosts from the free pool for the second AZ |
| `witnessSpec` | `WitnessSpec` | **required:** `fqdn`, `vsanIp`, `vsanCidr` |
| `networkSpec` | `ClusterStretchNetworkSpec` | **required:** `networkProfiles`, `nsxClusterSpec` |
| `vsanNetworkSpecs` | array | vSAN network pool specs |
| `witnessTrafficSharedWithVsanTraffic` | bool | |
| `isEdgeClusterConfiguredForMultiAZ` | bool | |
| `deployWithoutLicenseKeys` | bool | |
| `secondaryAzOverlayVlanId` | int | **deprecated in 9.1** — set the secondary-AZ overlay VLAN via `networkSpec.nsxClusterSpec.uplinkProfiles` instead |

`NsxStretchClusterSpec` requires `uplinkProfiles`, optionally `ipAddressPoolsSpec`.

### Validate before you commit

Don't fire the PATCH blind — the same spec body goes to a dry-run endpoint first:

**`POST /v1/clusters/{id}/validations`** accepts a `ClusterUpdateSpec` (same object), then poll **`GET /v1/clusters/{id}/validations/{validationId}`**. This catches witness reachability, VLAN, and host-compat problems before you've half-stretched a production cluster. Build every VCF automation this way — nearly every mutating VCF endpoint has a paired `/validations` sibling.

### Working sequence

```
GET   /v1/hosts?status=UNASSIGNED_USEABLE   -> host ids for AZ2
GET   /v1/clusters                          -> target cluster id
PATCH /v1/clusters/{id}   { "prepareForStretch": true }
POST  /v1/clusters/{id}/validations   { "clusterStretchSpec": {...} }
GET   /v1/clusters/{id}/validations/{validationId}   -> poll until SUCCEEDED
PATCH /v1/clusters/{id}   { "clusterStretchSpec": {...} }   -> returns a Task
GET   /v1/tasks/{taskId}                    -> poll to completion
```

Auth is the standard SDDC Manager flow: `POST /v1/tokens` with your SSO credentials, then `Authorization: Bearer <accessToken>`.

### If the cluster is *not* VCF-managed

A plain vSphere/vSAN cluster outside a workload domain doesn't go through SDDC Manager at all — it uses the **vSAN Management API (SOAP/WSDL)**, managed object `vim.cluster.VsanVcStretchedClusterSystem`. Methods, from the 9.1 vSAN API reference:

`VSANVcConvertToStretchedCluster`, `VSANVcSetPreferredFaultDomain`, `VSANVcGetPreferredFaultDomain`, `VSANVcAddWitnessHost` / `RemoveWitnessHost` / `GetWitnessHosts`, `VSANVcAddWitnessHostForClusters`, `VSANVcReplaceWitnessHostForClusters` (shared witness), `VSANVcQuerySharedWitnessCompatibility`, `VSANVcRetrieveStretchedClusterVcCapability`.

Knowing which of the two applies to you is the single biggest fork in this problem. If the cluster is in a VCF workload domain, use the SDDC Manager API — driving vCenter directly behind SDDC Manager's back leaves the VCF inventory out of sync.

---

## 4. Four other discovery routes worth having

**a. Pull the spec off the appliance itself.** SDDC Manager ships its own Swagger doc, so it always matches your exact patch level (useful when GA specs lag a hotfix):

```
/opt/vmware/vcf/sddc-manager-ui-app/vcf-installer-ui/assets/swagger.json
```

Import straight into Postman or Insomnia and you get every endpoint with example payloads.

**b. Watch what the UI does.** Open the SDDC Manager / VCF Operations UI, F12 → Network → filter XHR, then perform the operation manually in a lab. You get the exact URL, headers, and a known-good request body — including undocumented or preview fields. This is the fastest route when the spec is ambiguous about which of several union fields the workflow actually uses, and it's how you settle "is this really the call?" arguments.

**c. Grep the generated SDKs.** The 9.1 SDKs are generated from the same specs, so the class names are a searchable index:

```bash
pip install vcf-sdk          # umbrella, 9.1.0.0 — pulls all VCF client libs
pip install vmware-sddc-manager==9.1.0.0   # SDDC Manager alone
grep -n "class .*Stretch" \
  .../site-packages/vmware/sddc_manager/model_client.py
# -> ClusterStretchNetworkSpec, ClusterStretchSpec,
#    NsxStretchClusterSpec, StretchClusterNetworkProfile
```

PowerShell equivalent: module **`VMware.Sdk.Vcf.SddcManager`**. Cmdlets map 1:1 to operationIds — `updateCluster` → **`Invoke-VcfUpdateCluster`**, `getClusters` → `Invoke-VcfGetClusters`. So once you have the operationId from the spec you already know the cmdlet name. Java SDK is on Maven Central; 9.1 extended both Java and Python to cover NSX, VCF Operations, Log Management, Fleet LCM and SDDC LCM.

**d. Use the right TechDocs branch.** Everything 9.x lives under `.../vcf/vcf-9-0-and-later/9-1/`, with the developer material under **"Administration SDKs, APIs, and CLI"**. The prose procedure for this task is under *Building Cloud Infrastructure → Stretching Clusters* ("Stretch a vSAN Compute Cluster Using the VMware Cloud Foundation API"). Force the branch in your search — `site:techdocs.broadcom.com vcf-9-0-and-later/9-1 stretch` — otherwise Google will keep serving you 5.2 and 9.0 pages, which is probably what's been happening.

---

## 5. Practical notes for automating this

- **Everything is async.** The PATCH returns a task, not a result. Poll `GET /v1/tasks/{id}`; a stretch runs for a long time (host commissioning + NSX prep). Build in generous timeouts and make the job resumable — re-polling an existing task id is much better than re-issuing the PATCH.
- **The witness is a prerequisite, not part of the call.** `witnessSpec` references an already-deployed, already-reachable witness appliance with its vSAN IP/CIDR. Deploy and verify it first, or validation fails on something that reads like a network error.
- **Pin your spec to your build.** Diff `sddc-manager-openapi.json` between the 9.0.0.0 and 9.1.0.0 tags before an upgrade — that diff is the real changelog and it's how you catch things like `secondaryAzOverlayVlanId` being deprecated.
- **Don't hand-roll JSON.** Use the SDK spec classes (`ClusterStretchSpec` etc.); the required-field validation alone will save you several failed runs, since a malformed union body tends to surface as a vague 400.

---

## Sources

- [vmware/vcf-api-specs (GitHub) — OpenAPI specs, tag 9.1.0.0](https://github.com/vmware/vcf-api-specs)
- [specifications/README.md — repo layout](https://github.com/vmware/vcf-api-specs/blob/main/README.md)
- [Introducing OpenAPI Specification for VMware Cloud Foundation](https://blogs.vmware.com/cloud-foundation/2025/07/14/introducing-openapi-specification-for-vmware-cloud-foundation-9-0/)
- [VCF API Specification — Broadcom Developer Portal](https://developer.broadcom.com/sdks/vcf-api-specification/latest)
- [VCF 9.1 — SDKs, APIs, and CLIs (release notes)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html)
- [Changelog for VCF 9.1](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-changelog.html)
- [Stretch a vSAN Compute Cluster Using the VCF API](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure/stretching-clusters/stretch-a-vsan-compute-cluster-using-the-vmware-cloud-foundation-api.html)
- [Stretching vSAN Clusters in VMware Cloud Foundation](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure/stretching-clusters.html)
- [Automate VMware Cloud Foundation 9.0 with OpenAPI — on-appliance swagger.json path](https://my-cloudy-world.com/2025/09/04/automate-vmware-cloud-foundation-9-0-with-openapi/)
- [Using VMware.Sdk.Vcf.SddcManager — PowerCLI cmdlet mapping](https://jadenetworksolutions.co.uk/post/vcf-90/vcf-90-powercli-sddcm-cmdlets/)
- [VCF Python SDK — Broadcom Developer Portal](https://developer.broadcom.com/vcf-python-sdk)
- vSAN Management API reference (`vim.cluster.VsanVcStretchedClusterSystem`), from `documentation/vsphere/wsdl/vsan/vsan_apiref.zip` in vcf-api-specs
