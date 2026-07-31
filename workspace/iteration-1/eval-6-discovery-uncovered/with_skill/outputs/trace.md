# Trace — eval-6 (discovery, uncovered topic)

Task: "How do I find the vSAN stretched cluster config API on VCF 9.1? It isn't in the docs."

## Skill selection

Read all four `SKILL.md` frontmatter descriptions first.

| Skill | Used | Why |
|---|---|---|
| `vcf-api-discovery` | **Primary** | Description explicitly covers "whenever someone says they can't find something in the Broadcom docs" and vSAN. Exact match. |
| `vcf-foundation` | **Secondary** | Auth flow needed to actually call the endpoints found (SDDC Manager `/v1/tokens`, VI JSON session header). Version already pinned to 9.1 by the user. |
| `nsx-security-policy` | No | Task is not DFW / microsegmentation. (NSX uplink profiles appear inside the stretch payload, but that is a schema field, not NSX policy work.) |
| `vcf-lifecycle-upgrade` | No | Not an upgrade/patch/precheck/bundle question. |

## Files read

- `/home/claude/vcf-skills/skills/vcf-api-discovery/SKILL.md`
- `/home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-corpus.md` (routes, tags, clone/worktree recipe, absent-product rule, OpenAPI 2.0 vs 3.0 gotcha)
- `/home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-inventory/SUMMARY.md`
- `/home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-inventory/DELTA-9.0-to-9.1.md`
- `/home/claude/vcf-skills/skills/vcf-api-discovery/references/live-discovery.md` (§2 Operations Swagger UI, §3 "no on-appliance explorer for 9.x — do not invent one", §4 PowerCLI noun-first)
- `/home/claude/vcf-skills/skills/vcf-api-discovery/references/doc-portal.md` (verified slugs, stale `vmware-cloud-foundation-api` = 5.2.4 trap, SPA-shell-with-200 failure signature)
- `/home/claude/vcf-skills/skills/vcf-foundation/references/9.1/auth-and-identity.md` (§1.2 SDDC Manager tokens, §1.3 vSphere Automation, §1.4 VI JSON `Session` scheme)

## Scripts run (bundled)

`scripts/find_operation.py` — the skill's bundled inventory search. All executed:

```
find_operation.py --version 9.1 "stretch"                         -> 14 hits, 2 products
find_operation.py --both-versions "stretch"                       -> 9.0=14, 9.1=14 (identical)
find_operation.py --version 9.1 "vsan"                            -> 334 hits
find_operation.py --version 9.1 --any witness                     -> 12 hits
find_operation.py --version 9.1 "fault domain"                    -> 9 hits
find_operation.py --version 9.1 --product sddc-manager "clusters" -> 86 hits
find_operation.py --version 9.1 --product sddc-manager --json "clusters/{id}"
find_operation.py --version 9.1 --product vsphere-automation --any stretch witness "fault domain"  -> only VCHA (negative)
find_operation.py --version 9.1 --product vcf-installer --any stretch vsan                          -> 0 (negative)
```

The `--both-versions` run emitted the skill's built-in caveat that the 9.0 tag ships no NSX
specs, so a 9.0 NSX miss is not evidence — noted, though not load-bearing here.

## Route 1 escalation — raw spec at the matching git tag

The bundled inventory carries operations only, not schemas. Per `spec-corpus.md` §1/§6, escalated
to the raw spec for payload detail. A clone of `github.com/vmware/vcf-api-specs` already existed
at `/tmp/vcf-api-specs` with both tags present; created worktrees per the skill's recipe:

```
git -C /tmp/vcf-api-specs worktree add /tmp/vcf-specs-91 9.1.0.0
git -C /tmp/vcf-api-specs worktree add /tmp/vcf-specs-90 9.0.0.0
```

Extracted from `specifications/sddc-manager/sddc-manager-openapi.json` (both tags):
`ClusterUpdateSpec`, `ClusterStretchSpec`, `WitnessSpec`, `ClusterStretchNetworkSpec`,
`NsxStretchClusterSpec`, `StretchClusterNetworkProfile`, `ClusterUnstretchSpec`, `VSANNetworkSpec`,
`HostSpec`, `UplinkProfile`, `NsxtHostSwitchConfig`, `ClustersUpdateSpec`; plus the `PATCH
/v1/clusters/{id}` operation object and the `/v1/clusters/{id}/validations` pair.

Parsed the 10.4 MB `specifications/vsphere/openapi/vi-json/vi-json.yaml` at 9.1.0.0 (cached to
`/tmp/vijson91.json`) to extract `VSANVcConvertToStretchedCluster`, its
`VSANVcConvertToStretchedClusterRequestType` body, `VimClusterVSANStretchedClusterFaultDomainConfig`,
the `moId` parameter, `servers[]` (with the `{release}` enum) and the `Session` securityScheme.

Ran a direct schema diff of the 9.0 and 9.1 worktrees over all stretch-related schemas.

## Key findings

- `PATCH /v1/clusters/{id}` (`updateCluster`, sddc-manager) — the VCF-managed route; hidden
  because it is a generic cluster PATCH, not a `/stretched-clusters` noun.
- 13 ops under `VimClusterVsanVcStretchedClusterSystem` in `vsphere-vi-json` — the vCenter route.
- Confirmed negative: `vsphere-automation` (vCenter REST `/api`) has **no** vSAN stretched-cluster
  operations; its only `witness` hits are VCHA. Present-product miss = real evidence of absence.
- Confirmed negative: 9.1's new bulk `PATCH /v1/clusters` cannot stretch (body is refresh-only).
- Operation surface identical 9.0 vs 9.1, but two **schema** deltas found by direct diff that no
  operation-count comparison or release note surfaces: `ClusterUnstretchSpec.azToRemove` added in
  9.1, and `ClusterUpdateSpec` gained `markAsDefault` / `dnsNtpUpdateSpec` /
  `clusterPrimaryDatastoreUpdateSpec`.
- `ClusterStretchSpec.secondaryAzOverlayVlanId` is marked deprecated in the 9.1 spec (use
  `uplinkProfile`).

## Skill guidance deliberately honoured

- Did not invent an on-appliance API-explorer URL (`live-discovery.md` §3).
- Labelled SDDC Manager Bearer/token payload as prose-grade, since that spec declares no
  `securitySchemes` in either version; paths themselves labelled spec-confirmed.
- Stated provenance per claim, and flagged that nothing was run against a live VCF estate.
- Warned about the stale `vmware-cloud-foundation-api` (5.2.4-as-latest) reference and the
  SPA-shell-returns-200 failure signature, which plausibly explain the user's failed doc search.
