# Finding the vSAN stretched-cluster API in VCF 9.1

Short version: the API exists, and there are **two** of them depending on what you actually
want to automate. The reason you can't find it is that neither one lives where people look
first — the vCenter REST (`/api`) reference has **no** vSAN stretched-cluster operations at all.

I ran the searches rather than describing them. Everything below is quoted from the OpenAPI
specifications at **git tag `9.1.0.0`** of `github.com/vmware/vcf-api-specs`, which is
version-exact ground truth for 9.1 — not "latest", not prose.

---

## 1. The method — how to find it yourself next time

Broadcom publishes machine-readable specs at `https://github.com/vmware/vcf-api-specs`, and the
repo carries **per-release git tags** (`9.0.0.0`, `9.1.0.0`). That tagging is the whole trick:
it lets you answer "does this exist *in 9.1*" instead of "does this exist *now*".

```bash
git clone https://github.com/vmware/vcf-api-specs /tmp/vcf-api-specs
git -C /tmp/vcf-api-specs worktree add /tmp/vcf-specs-91 9.1.0.0
git -C /tmp/vcf-api-specs worktree add /tmp/vcf-specs-90 9.0.0.0   # both on disk, diffable
```

`main` is not a version. Never answer a 9.1 question from an untagged checkout.

The search I actually ran, against a pre-extracted operation inventory of all 16,673 operations
across both tags:

```bash
python3 scripts/find_operation.py --version 9.1 "stretch"
python3 scripts/find_operation.py --both-versions "stretch"
python3 scripts/find_operation.py --version 9.1 --any witness
python3 scripts/find_operation.py --version 9.1 "fault domain"
```

**Why the docs felt empty.** Three specific traps, all of which you probably hit:

- The `vmware-cloud-foundation-api` reference on developer.broadcom.com still serves **VCF 5.2.4
  as "Latest"**. Do not cite it for 9.x. The right slug is
  `https://developer.broadcom.com/xapis/sddc-manager-api/latest/` (`latest` = 9.1; there is a
  pinned `/9.0/` if you need the older one).
- A **nonexistent** developer-portal page returns the SPA navigation shell with **HTTP 200**. It
  looks like a successful fetch of an empty page, so "I searched and found nothing" is not
  evidence of absence there.
- The operation you want is a **`PATCH` on a generic cluster resource**, not a
  `/stretched-clusters` noun. No amount of searching the docs for "stretched cluster endpoint"
  surfaces `PATCH /v1/clusters/{id}` — you have to search *summaries*, which is exactly what the
  spec corpus lets you do.

---

## 2. What the search found — the two real routes

Searching `"stretch"` across all 14 products at 9.1 returns **14 operations, in exactly two
products**. Nothing in `vsphere-automation`, nothing in `vcf-installer`, nothing in NSX.

### Route A — SDDC Manager (use this for a VCF-managed workload domain)

This is almost certainly the one you want. It is the VCF-aware path: it consumes hosts from the
free pool, wires up the secondary AZ in NSX, and returns a VCF `Task` you can poll.

| | |
|---|---|
| Operation | `PATCH /v1/clusters/{id}` |
| operationId | `updateCluster` |
| Summary | "Update a Cluster by adding or removing Hosts, **Stretching a standard vSAN cluster, Unstretching a stretched cluster** or by marking for deletion" |
| Spec file | `specifications/sddc-manager/sddc-manager-openapi.json` (OpenAPI 3.0.1) |
| Base | `http://localhost:80` in the spec — that is the **on-appliance loopback default**. Substitute the SDDC Manager FQDN over HTTPS. |
| Request body | `ClusterUpdateSpec` (required) |
| Responses | `200`/`202` → `Task`; `400`, `403`, `404`, `500` → `Error` |

**Dry-run first.** There is a matching validator that takes the *same* body:

- `POST /v1/clusters/{id}/validations` — `validateClusterUpdateSpec`, body `ClusterUpdateSpec`
- `GET /v1/clusters/{id}/validations/{validationId}` — `getClusterUpdateValidation`

Both exist at 9.0 as well, so this pattern is stable across the upgrade.

**The payload.** `ClusterUpdateSpec` is a union-ish object — you set the one sub-spec you want:

```
ClusterUpdateSpec
  name, markForDeletion, markAsDefault, prepareForStretch (bool)
  clusterExpansionSpec / clusterCompactionSpec
  clusterStretchSpec        <- stretch
  clusterUnstretchSpec      <- unstretch
  clusterTransitionSpec, clusterImageComplianceCheckSpec,
  dnsNtpUpdateSpec, clusterPrimaryDatastoreUpdateSpec
```

Note `prepareForStretch: boolean` — a separate preparation flag distinct from
`clusterStretchSpec`. Sequence it deliberately.

```
ClusterStretchSpec        required: hostSpecs, witnessSpec
  hostSpecs[]             HostSpec  (required: id; also licenseKey, ipAddress, hostName,
                                     username, password, hostNetworkSpec, azName,
                                     sshThumbprint, serialNumber)
  witnessSpec             WitnessSpec
  witnessTrafficSharedWithVsanTraffic : bool
  vsanNetworkSpecs[]      VSANNetworkSpec
  networkSpec             ClusterStretchNetworkSpec
  isEdgeClusterConfiguredForMultiAZ : bool
  deployWithoutLicenseKeys : bool
  secondaryAzOverlayVlanId : int32      ** DEPRECATED in the 9.1 spec **
                                        -> put the secondary-AZ overlay VLAN in the
                                           uplinkProfile instead

WitnessSpec               required: fqdn, vsanIp, vsanCidr
  fqdn      - "Management ip of the witness host"   (note: the description says IP, the
                                                     field is named fqdn — verbatim from spec)
  vsanIp    - vSAN IP of the witness host
  vsanCidr  - vSAN subnet CIDR of the witness host

VSANNetworkSpec           required: vsanCidr, vsanGatewayIP

ClusterStretchNetworkSpec required: nsxClusterSpec, networkProfiles
  nsxClusterSpec          NsxStretchClusterSpec
                            required: uplinkProfiles[]  (UplinkProfile: required name, teamings;
                                        also transportVlan, supportedTeamingPolicies)
                            optional: ipAddressPoolsSpec[]
  networkProfiles[]       StretchClusterNetworkProfile
                            required: name, nsxtHostSwitchConfigs[]
                            NsxtHostSwitchConfig required: vdsName, uplinkProfileName,
                                                           vdsUplinkToNsxUplink
                                                 optional: ipAddressPoolName

ClusterUnstretchSpec
  azToRemove : string      ** ADDED IN 9.1 — see the delta note below **
```

**Auth for SDDC Manager** (not SSO-brokered):

```
POST   /v1/tokens                            {"username": "...", "password": "..."}
       -> accessToken (JWT), refreshToken.id (UUID)
PATCH  /v1/tokens/access-token/refresh       body = raw refresh-token UUID; response body = raw JWT
DELETE /v1/tokens/refresh-token
```
Then `Authorization: Bearer <accessToken>` on every call. All three token paths are
spec-confirmed present and unchanged at both 9.0.0.0 and 9.1.0.0. Caveat worth stating: the
SDDC Manager spec declares **no `securitySchemes`** in either version, so the header and payload
shapes are carried from Broadcom's prose reference, not from the spec.

### Route B — vCenter VI/JSON API (`/sdk/vim25`) — the vSAN management object

If the cluster is not VCF-managed, or you need the finer-grained operations (replace a witness,
flip the preferred fault domain, shared-witness ROBO topologies), the vSAN managed object is
exposed as JSON-over-REST here. Managed object: `VimClusterVsanVcStretchedClusterSystem`.

Base: `https://{vcenter-host}/sdk/vim25/{release}` where `{release}` is an enum including
`9.1.0.0` and `9.0.0.0`. Auth: `vmware-api-session-id` header (scheme `Session`), from the
`SessionManager` `Login` operation.

All 13 operations, verbatim from the 9.1 spec:

| Method + path (relative to base) | Purpose |
|---|---|
| `POST /vsan/VimClusterVsanVcStretchedClusterSystem/{moId}/VSANVcConvertToStretchedCluster` | **The main one** — convert a traditional vSAN cluster to stretched |
| `.../VSANVcRetrieveStretchedClusterVcCapability` | Pre-check: do the hosts support stretched cluster |
| `.../VSANVcAddWitnessHost` | Add a witness to re-enable stretched mode |
| `.../VSANVcRemoveWitnessHost` | Remove witness (disables stretched cluster) |
| `.../VSANVcGetWitnessHosts` | Query witness configuration |
| `.../VSANVcIsWitnessHost` | Is this host a witness |
| `.../VSANIsWitnessVirtualAppliance` | Is the witness a virtual appliance |
| `.../VSANVcGetPreferredFaultDomain` | Read preferred FD |
| `.../VSANVcSetPreferredFaultDomain` | Set preferred FD |
| `.../VsanVcAddWitnessHostForClusters` | Batch convert clusters sharing one witness |
| `.../VsanVcReplaceWitnessHostForClusters` | Replace witness across stretched clusters |
| `.../QuerySharedWitnessClusterInfo` | Runtime info per cluster for a shared witness |
| `.../QuerySharedWitnessCompatibility` | Can this host be a shared witness for these ROBO clusters |

`VSANVcConvertToStretchedCluster` request body
(`VSANVcConvertToStretchedClusterRequestType`):

```
required: cluster, faultDomainConfig, witnessHost, preferredFd
  cluster           ManagedObjectReference -> ClusterComputeResource
                    (privilege: Host.Inventory.EditCluster)
  faultDomainConfig VimClusterVSANStretchedClusterFaultDomainConfig
                      required: firstFdName, firstFdHosts[], secondFdName, secondFdHosts[]
                      (hosts must cover ALL hosts in the cluster; no host in both sites,
                       else InvalidArgument)
  witnessHost       ManagedObjectReference -> HostSystem
                    (same vCenter, must NOT be in the target cluster)
  preferredFd       string
optional (mutually exclusive — setting both is InvalidArgument):
  diskMapping       VsanHostDiskMapping         (not needed if witness auto-claim is on)
  storagePoolSpec   VsanAddStoragePoolDiskSpec
```

Returns a `ManagedObjectReference` to a `vim.Task`. Documented `500` faults:
`InvalidState` (a host not connected to vCenter), `InvalidArgument` (vSAN not enabled, witness
inside the target cluster, no IPv4/IPv6 configured for vSAN traffic on all hosts, already
stretched, or both `diskMapping` and `storagePoolSpec` set), `VsanFault`.

Related and useful for day-2 automation — `VsanSiteMaintenanceSystem` (site/fault-domain
maintenance mode): `VsanEnterSiteMaintenanceMode`, `VsanExitSiteMaintenanceMode`,
`VsanPerformSiteMaintenancePrecheck`, `VsanGetSiteMaintenancePrecheckStatus`,
`VsanQueryClusterSiteMaintenanceState`.

---

## 3. Confirmed negatives (this is why you couldn't find it)

These are misses in products whose spec **is present** at 9.1, so they are genuine evidence of
absence, not gaps in my search:

- **`vsphere-automation` (the modern vCenter REST API, `https://{host}/api`, 1,367 operations)
  has no vSAN stretched-cluster operations.** The only `witness` hits are
  `POST /vcenter/vcha/cluster/witness?action=check` and `?action=redeploy` — that is **vCenter
  High Availability**, a completely different feature. If you were searching the vCenter REST
  reference for "witness", this is the false positive that sent you down the wrong path.
- **`vcf-installer` has zero matches** for `stretch` or `vsan`.
- **`PATCH /v1/clusters` (bulk, new in 9.1)** does *not* do stretch — its body is
  `ClustersUpdateSpec`, which carries only `clusterIds[]` and `clustersRefreshSpec`. Do not
  reach for it hoping to stretch clusters in bulk.

---

## 4. The 9.0 → 9.1 delta (matters if you're writing this into a runbook)

I diffed the two tags directly. The **operation surface for stretched clusters is identical** —
14 matches at 9.0, the same 14 at 9.1. Paths, methods and operationIds unchanged. Your automation
is portable in that respect.

But two **schema** changes are not visible from an operation list, and I did not find them
announced anywhere in prose:

1. **`ClusterUnstretchSpec` gained `azToRemove`** (string, "Availability zone which needs to be
   removed from the compute stretch cluster") in 9.1. It did not exist at 9.0. If you are writing
   an unstretch path, this is new capability worth using — and a body written for 9.1 will be
   silently ignored or rejected on 9.0.
2. **`ClusterUpdateSpec` gained** `markAsDefault`, `dnsNtpUpdateSpec` and
   `clusterPrimaryDatastoreUpdateSpec` in 9.1.

`ClusterStretchSpec`, `WitnessSpec`, `ClusterStretchNetworkSpec`, `NsxStretchClusterSpec` and
`StretchClusterNetworkProfile` are **byte-identical** between the two tags.

Context: `sddc-manager` went 375 → 423 operations (48 added, 0 removed, 21 newly deprecated —
mostly edge-cluster reads and DNS/NTP configuration reads).

---

## 5. Suggested working sequence

1. `POST /v1/tokens` on SDDC Manager → Bearer token.
2. `GET /v1/clusters` → find your cluster `id`.
3. Build `ClusterUpdateSpec` with `clusterStretchSpec`.
4. `POST /v1/clusters/{id}/validations` with that exact body; poll
   `GET /v1/clusters/{id}/validations/{validationId}` until it passes. **Do not skip this** —
   the same body validates, so it is a true dry run.
5. `PATCH /v1/clusters/{id}` → returns a `Task`; poll it.
6. Only drop to Route B (`/sdk/vim25`) for operations SDDC Manager does not expose — witness
   replacement, preferred-FD changes, shared-witness ROBO topologies, site maintenance mode.

## 6. Verifying against your own estate

The spec tells you what the *release* contains; your appliance tells you what *your build*
serves. Two checks that cost nothing:

```powershell
Get-Command -Noun *Vsan*                       # noun-first is the high-signal PowerCLI search
Get-Command -Module VMware.Sdk.Vcf.SddcManager
Get-Help <cmdlet> -Full
```

For VCF Operations there is an on-appliance Swagger UI at
`https://<operations-fqdn>/suite-api/doc/swagger-ui.html` (singular `doc`, not `docs`) — log into
Operations first.

One honest caveat: **there is no documented on-appliance API-explorer URL for VCF 9.x.** The
vCenter Developer Center is documented only for vSphere 7.0/8.0, and the 9.1 "VCF APIs and SDKs"
page explicitly does not publish appliance access points. So I am not going to hand you a
`https://<vcenter>/apiexplorer` or `/openapi.json` guess. Use the tagged spec repo.

---

## Provenance

| Claim | Evidence grade |
|---|---|
| Paths, methods, operationIds, request/response schemas, required fields, deprecations | **Spec-confirmed** at git tag `9.1.0.0` (and `9.0.0.0` for the delta). Strongest available. |
| 9.0→9.1 schema deltas | **Spec-confirmed** — computed by direct diff of the two tags. |
| SDDC Manager `Authorization: Bearer` header and `/v1/tokens` payload shape | **Prose-grade** — the SDDC Manager spec declares no `securitySchemes`; carried from Broadcom's API reference. Paths themselves are spec-confirmed. |
| Doc-portal slugs and failure signatures | Prose/observational. |
| Anything about your specific deployment | **Not verified** — nothing here was run against a live VCF environment. Validate against Broadcom's docs for your exact build before executing; stretching a cluster is production-affecting. |
