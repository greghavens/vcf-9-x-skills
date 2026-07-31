# Live discovery — asking a running environment what it serves

The spec corpus tells you what a *release* contains. A running environment tells you what *this
deployment* actually serves — the deployed build, the enabled features, the API versions the
Supervisor is really registering. When both are available, live discovery wins on version accuracy
and the corpus wins on breadth.

Use this file when: the corpus has no data for the version in question (notably NSX at 9.0), the
answer depends on what is installed (PowerCLI modules, VCF CLI plugins, CRDs), or the user has an
environment in front of them and precision matters more than generality.

---

## 1. NSX — ask the appliance for its own OpenAPI spec

**Verified in both the 9.0 and 9.1 NSX API guides; the endpoint set is identical across versions.**

```
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_policy_api.json    # Policy API — use this one
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_policy_api.yaml
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_api.json           # Manager API — node/cluster/fabric
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_api.yaml
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_vmc_policy_api.{yaml,json}
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_vmc_aws_integration_api.{yaml,json}
```

Why this is the best NSX route:

- The spec is served by the **running** manager, so it matches the deployed build exactly
  (9.0.0.0 / build 24733065 or 9.1.0.0 / build 25318225). Version-contamination risk goes to zero.
- It is the **only** first-class route for **NSX at 9.0**, because the `9.0.0.0` spec tag ships no
  NSX files at all (see `spec-corpus.md` §4).
- These are the same OpenAPI **2.0** documents as in the repo — `basePath`, `definitions`,
  `in: body`. Do not feed them to a 3.0-only parser.

Authenticate first. Either:

```
POST /api/session/create        # form fields j_username / j_password
                                # returns Set-Cookie: JSESSIONID + X-XSRF-TOKEN; send both back
POST /api/session/destroy
```

or HTTP Basic (`Authorization: Basic …`), or X.509 principal-identity certs. Runtime notes that
matter when scripting against a live manager: default page size 1000 (follow `cursor`); rate limit
100 req/s and 40 concurrent per client, exceeded → **HTTP 429**; expired session surfaces as
**403**, not 401; session cookies are pinned to one manager node, so do not reuse them across a VIP.

Note that NSX in VCF 9.x is **Policy-mode only** — "The Manager mode and Manager API provided by NSX
4.x and earlier are no longer supported" for configuring networking. `nsx_api.json` is still served
and still relevant for node/cluster/fabric administration, but reach for `nsx_policy_api.json` first.

---

## 2. VCF Operations — the on-appliance Swagger UI

```
https://<operations-fqdn>/suite-api/doc/swagger-ui.html
```

Verbatim from the docs: "Swagger based API documentation is available with the product, with the
capability of making REST API calls right from the landing page." You must **log into VCF Operations
first** at the instance URL — the Swagger UI relies on that session.

Language-specific client bindings are served from `https://<operations-fqdn>/suite-api/`.

**Note the singular `doc`, not `docs`.** That is how it is printed in the source, and `/suite-api/docs/…`
is a common wrong guess.

This is also the right place to settle questions the published spec cannot. Example: no dashboard
endpoints appear in the VCF Operations spec at 9.0 or 9.1, while legacy vROps had
`/suite-api/api/dashboards`. Whether it persists undocumented is unresolved — check the live Swagger
UI before asserting either way.

**VCF Operations for Networks** has an in-product **API Explorer**, documented at
`.../9-0/administration-sdks-cli-and-tools/vmware-cloud-foundation-operations-for-networks-api-guide/understanding-the-rest-apis/using-api-explorer.html`.
The doc page's contents were not retrievable during research, so treat the explorer as "exists,
details unverified".

---

## 3. What this skill deliberately does NOT teach: on-appliance API explorers for 9.x

**There is no documented on-appliance API-explorer or spec-metadata URL pattern for VCF 9.x**, other
than the two above. This is a real gap, and it was checked:

- The **vCenter Developer Center / API Explorer** is documented only for the **vSphere 7.0 and 8.0**
  doc sets (`.../vsphere/vsphere/8-0/vcenter-and-host-management/working-with-the-developer-center-host-management.html`).
  Targeted site-restricted search found **no equivalent page in the `vcf-9-0-and-later` doc sets**.
  Whether vCenter 9 still serves Developer Center at its vSphere-8 UI location is **unverified**.
- The 9.1 *VCF APIs and SDKs* overview page explicitly does **not** provide "API explorer appliance
  access points."
- The OpenAPI setup page states outright that it does not specify on-appliance URLs "(like
  `/apiexplorer` or `/api` metadata endpoints) for retrieving OpenAPI specifications from running VCF
  components."

**So: do not invent one.** Do not tell a user to try `https://<vcenter>/apiexplorer`, `/api/metadata`,
`/openapi.json`, `/v3/api-docs` or similar. If asked where to browse a spec on an appliance, give the
two verified answers (NSX spec endpoints, VCF Operations Swagger UI) and otherwise point at the
tagged GitHub repo or the developer-portal ZIP. A confident-sounding wrong URL is worse than "the
docs don't publish one; use the spec repo."

---

## 4. PowerShell / PowerCLI — noun-first discovery

Only one discovery idiom is actually doc-verified (the VCF 9.1 PowerShell Basics page):

> "For a full list of the common parameters and more details on their usage, run
> `Get-Help about_CommonParameters`."

Everything below is **standard PowerShell**, not quoted from Broadcom docs — say so if you surface it
to a user as an official instruction. It is nevertheless the correct escape hatch when a cmdlet name
is unknown.

```powershell
# What is installed / loaded?
Get-Module -ListAvailable VMware.*, VCF.*
Get-Module                                     # currently imported

# Which module owns a cmdlet; what does a module export?
Get-Command -Module VMware.Sdk.Vcf.SddcManager
Get-Command -Module VMware.VimAutomation.Nsxt

# Noun-first — the highest-signal search
Get-Command -Noun Sddc*
Get-Command -Noun *Vsan*
Get-Command -Verb Connect                      # every Connect-*Server entry point
Get-Command *Vsan*Capacity*                    # wildcard when only a concept is known

# Full syntax, examples, parameter semantics
Get-Help Connect-VcfSddcManagerServer -Full
Get-Help Connect-VcfSddcManagerServer -Examples
Get-Help Set-PowerCLIConfiguration -Parameter InvalidCertificateAction

# PowerCLI returns rich typed objects, not text — inspect them
Get-VM | Get-Member
Get-VM | Select-Object -First 1 | Format-List *

# Version self-check
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version
Get-PowerCLIConfiguration
```

**Why noun-first, specifically.** The module split is **by product**, and the noun prefix tracks the
product: `*-Vcf*` (VCF SDK modules), `*-Sddc*` (SDDC Manager), `*-Vsan*`, `*-Nsx*`, `*-VI*` (core
vSphere). So the noun is effectively a product selector, and `Get-Command -Noun Sddc*` is the fastest
route to the whole SDDC Manager surface — it is how you would find `Get-SddcTask` or
`Remove-SddcCluster` with no prior knowledge of their names. Verb-first (`Get-Command -Verb Get`)
returns thousands of cmdlets across every module and tells you nothing about which product owns what.

Mirror this onto the corpus: the noun maps to a product key in `index.json`, so a `Get-Command -Noun
Sddc*` result and a `find_operation.py --product sddc-manager` result should be describing the same
API surface from two directions. If they disagree, the module version and the VCF version differ.

(`Get-PowerCLIConfiguration` is inferred as the read counterpart to `Set-PowerCLIConfiguration`; its
reference page was not retrievable — **unverified**.)

---

## 5. kubectl — query the Supervisor, do not guess the served API version

Doc-verified idioms:

```bash
kubectl get virtualmachineclass        # available VM classes
kubectl describe namespace <ns>        # storage classes for the namespace
kubectl get kr                         # Kubernetes releases (short name)
kubectl get kubernetesreleases
kubectl get cluster                    # provisioning status
kubectl get nodes / namespaces / pods -A
```

Generic discovery (standard kubectl; the VCF docs do not present these):

```bash
kubectl api-resources                                  # every kind: short name, group, namespaced-ness
kubectl api-resources --api-group=vmoperator.vmware.com
kubectl api-resources --api-group=cluster.x-k8s.io
kubectl api-versions | grep -E 'vmoperator|cluster.x-k8s|run.tanzu'

kubectl explain cluster.spec.topology                  # schema walk, served by the live API server
kubectl explain virtualmachine --recursive
kubectl get crd
kubectl get clusterclass -A
```

### Why this matters — the VM Operator version conflict

This is not a generic "kubectl is useful" recommendation. There is a **documented contradiction**:

- The **VCF 9.0 product docs** state that as of VCF 9.0 the `v1alpha1` VM Operator API is deprecated
  and you should "use **v1alpha2 or v1alpha3** instead, as both are supported on Supervisor."
- The **upstream VM Operator project docs** show `apiVersion: vmoperator.vmware.com/**v1alpha5**` and
  reference v1alpha1 through v1alpha5.
- **What the shipped Supervisor serves in 9.1 could not be verified** — no VCF 9.1 page stating the
  served versions was retrievable.

So any answer of the form "use `vmoperator.vmware.com/v1alphaN`" is a guess, and a manifest written
against the wrong version fails to apply. The resolution is mechanical:

```bash
kubectl api-resources --api-group=vmoperator.vmware.com   # what this cluster actually serves
kubectl explain virtualmachine                            # and the schema it serves for it
```

**Query the cluster, don't guess the served version.** State the doc conflict to the user and give
them the command rather than picking a side.

The same applies to **ClusterClass**: the name is VKS-version-coupled (`builtin-generic-v3.4.0`,
`builtin-generic-v3.6.0` both appear in docs), so `kubectl get clusterclass -A` is the practical way
to learn which one to reference in a `Cluster` topology. Do not hard-code a version suffix.

`TanzuKubernetesCluster` v1alpha2/v1alpha3 are deprecated; the exact `run.tanzu.vmware.com` group
string is **unverified** — confirm with `kubectl api-resources` before writing a manifest.

---

## 6. VCF CLI

```bash
vcf version                    # verified: reports v9.1.0.0
vcf context create --help      # verified: doc-recommended syntax check
vcf context list               # verified
vcf plugin                     # verified command group
```

Command groups worth enumerating: system — `context`, `plugin`, `config`, `version`, `completion`;
plugins — `cluster`, `namespaces`, `kubernetes-release`, `package`, `vm`, `secret`,
`registry-secret`, `imgpkg`, `pais`, `telemetry`, `addon`.

The CLI is **plugin-based and plugin availability is context-dependent**, auto-discovered from the
endpoint you are attached to. So "does command X exist?" is only answerable against a live context.
`vcf plugin list` is the inferred way to enumerate what is installed; exact `vcf plugin` subcommand
syntax is **unverified**.

---

## 7. Choosing a route

| Situation | Route |
|---|---|
| NSX, any version, environment available | §1 appliance spec endpoint — best possible evidence |
| NSX at 9.0, no environment | Portal reference pinned to `9.0.0` (`doc-portal.md`) — corpus has nothing |
| VCF Operations, endpoint not in spec | §2 Swagger UI on the appliance |
| "Which cmdlet does X?" | §4 noun-first |
| Any Supervisor / VM Operator / VKS API version question | §5 — always query, never assert |
| Anything else | Spec corpus first (`spec-corpus.md`) |

Always label the route in the answer. "Confirmed against the running NSX Manager's own spec" and
"found in the 9.1 spec tag" are different strengths of evidence, and "the docs don't publish this" is
a legitimate, useful answer.
