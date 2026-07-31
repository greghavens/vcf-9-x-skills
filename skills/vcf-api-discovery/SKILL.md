---
name: vcf-api-discovery
description: Find and verify any VMware Cloud Foundation 9.0 or 9.1 API operation — across roughly 13,000 operations in vSphere, NSX, SDDC Manager, VCF Operations, VCF Automation, vSAN, fleet lifecycle and VKS — instead of guessing an endpoint. Use this whenever a VCF, vCenter, NSX, vSAN or PowerCLI task needs a call that isn't already documented in another skill, whenever you are unsure whether an endpoint exists in a specific version, whenever someone says they can't find something in the Broadcom docs, and whenever you are about to state an endpoint, cmdlet or CRD you have not confirmed. Also use it to check whether an operation was added, removed or deprecated between 9.0 and 9.1.
license: MIT-0
compatibility: The spec-corpus route needs git and Python 3 (stdlib only). Live-discovery routes need reachability to the target appliances. Doc-portal routes need web access.
---

# Finding VCF API operations without guessing

A plausible-looking endpoint is worse than no endpoint. It survives review, reads like
the real thing, and fails only when someone runs it against a customer's estate. VCF
makes this especially easy to get wrong: the API surface is enormous, it is split across
a dozen products with different conventions, and it changed between 9.0 and 9.1 in ways
that prose documentation does not always record.

So the rule this skill exists to enforce is simple. **If you are about to state an
endpoint, cmdlet, CRD or parameter you have not confirmed for the specific version in
question, stop and confirm it first.** The routes below make that cheap enough that
there is no excuse for guessing.

> **Built from documentation, not from a live environment.** Everything here traces to
> Broadcom documentation or published OpenAPI specifications, captured 2026-07-31.
> Nothing has been executed against a running VCF deployment.

## Route 1 — the published spec corpus (start here)

Broadcom publishes machine-readable API specifications at
`github.com/vmware/vcf-api-specs`, and — the part that makes this decisive — the repo
carries **git tags `9.0.0.0` and `9.1.0.0`**. Checking out the matching tag gives you
ground truth for a specific version rather than "current", which is exactly the
distinction that prose docs blur.

This is the strongest evidence available. Prefer it over prose for paths, payloads and
parameters. When a spec and a doc page disagree, say they disagree rather than silently
picking one.

Two tiers, and the difference matters. The **bundled inventory** at
`references/spec-inventory/` answers *"does this operation exist, at what path, in which
version"* — it holds operations, not schemas. For **payload fields and parameter
details** you need the **raw spec** from the repo at the matching tag. Do not infer a
body field from an operation summary; that is guessing with extra steps.

Read `references/spec-corpus.md` for the per-product spec map, base paths and operation
counts for both versions, and the clone/worktree recipe.

One rule worth internalising before you use it:

> A miss in a product whose spec is **present** for that version is real evidence the
> operation does not exist. A miss in a product whose spec is **absent** for that version
> is no evidence at all.

That matters because **seven** products have no spec at the 9.0 tag — the three NSX specs
(`nsx-policy`, `nsx-manager`, `nsx-global-policy`), plus `fleet-lcm`, `sddc-lcm`,
`realtime-metrics` and `log-management` — while `vcf-operations-for-logs` exists only at
9.0. Searching for an NSX endpoint "in 9.0" and finding nothing tells you nothing.

### The bundled search script

`scripts/find_operation.py` searches the extracted operation inventories by keyword
across path, operationId, summary and tags. It **requires an explicit `--version`**,
which is deliberate: a search that silently spans both versions is how cross-version
contamination gets in.

```
python scripts/find_operation.py --version 9.1 --product fleet-lcm "upgrade plan"
python scripts/find_operation.py --both-versions "depot"
python scripts/find_operation.py --version 9.0 --product sddc-manager --method POST upgrade
```

`--both-versions` is available when the question genuinely is "did this change" — it
labels results per version and warns where a product's spec is absent for one of them.

## Route 2 — ask the running environment

When the user has a reachable appliance, the appliance is more authoritative than any
document, because it reports what that build actually serves.

Read `references/live-discovery.md`. It covers the NSX on-appliance OpenAPI endpoints
(verified in both versions), the VCF Operations swagger UI, PowerShell noun-first
discovery, and kubectl discovery for Supervisor/VKS.

The kubectl case is the clearest illustration of why this route matters: the VCF 9.0 docs
name VM Operator `v1alpha2`/`v1alpha3` while upstream shows `v1alpha5`. There is no way
to resolve that from documents. Query the cluster.

**Tell the user this, don't just know it:** no on-appliance API-explorer URL pattern is
documented for VCF 9.x — only for 7.0 and 8.0. Someone hunting for an endpoint will go
looking for one, and the honest answer is that Broadcom hasn't published a 9.x pattern.
Say so rather than inventing a URL that looks right, and point them at the routes above
that are documented.

## Route 3 — the documentation portals

Read `references/doc-portal.md` for version-pinned developer.broadcom.com patterns and
the techdocs tree grammar.

Use it for *understanding* — workflow, constraints, intent — more than for extracting
exact parameters, which the specs do better. And navigate by fetching a guide's landing
page and reading its children rather than constructing URLs, because Broadcom's slugs are
unreliable: release-notes paths differ non-obviously between 9.0 and 9.1, several 9.1
pages retain 5.2-era slugs, and one page is misspelled upstream.

Three failure signatures that mislead if you don't know them:

- A **nonexistent developer-portal page returns the SPA navigation shell with HTTP 200**.
  That is not evidence the endpoint is absent — it looks like a successful fetch.
- **HTTP 429** means rate-limited. Back off and retry; it does not mean the page is gone.
- The `vmware-cloud-foundation-api` reference still serves **VCF 5.2.4 as "Latest"**.
  Do not cite it for 9.x.

## Choosing a route

| Situation | Route |
|---|---|
| "Does this endpoint exist in 9.1?" | Spec corpus — definitive |
| **"I can't find X anywhere" / "where do I look?"** | **Both 1 and 2 — see below** |
| "What changed between 9.0 and 9.1?" | Spec corpus, `--both-versions` |
| "What are the exact payload fields?" | Spec corpus — prose docs are less reliable here |
| "Which cmdlet does X?" | Live discovery, noun-first PowerShell |
| "What CRD version does this cluster serve?" | Live discovery — documents are known to be wrong |
| "Why would I do this / what are the constraints?" | Doc portal |
| Product has no spec at that version (NSX 9.0) | Doc portal, and say the evidence is prose-grade |

When someone asks **where to look** rather than asking you to confirm one specific
endpoint, the corpus alone is a half-answer. They are going to keep hunting after you
reply, and they will hunt on their own appliance. Give them Route 1 *and* Route 2, plus
the API-explorer gap, so they stop looking for a door that isn't there.

## Reporting what you found

Carry the provenance through into your answer. "Confirmed in the 9.1 NSX policy spec" and
"documented in the 9.0 admin guide, no spec published" are different claims, and the user
is entitled to know which one they are acting on — particularly when they are about to
write it into a runbook.

When you cannot confirm something, say that, name the route you tried, and give the user
the command to check it against their own appliance. That is a genuinely useful answer.
A confident guess is not.

## Shaping your answer

### Answer the question that was asked, at the length it deserves

"Give me the exact API calls" means: give the calls. A numbered sequence of requests with
the payloads, and the two or three things that will actually bite. Not a runbook, not a
failure-mode table, not every caveat the reference file carries.

The reference material exists so your answer is *correct*, not so your answer is *long*.
Most of what you read should never appear in the reply. A useful test before sending:
would a VMware engineer who knows their environment skim this and find the command, or
would they have to hunt for it?

### A discovery answer has three parts

Brevity is the default everywhere else in this section, but "where do I find this" is the
one question where a short answer is an incomplete one. Cover all three:

1. **The spec corpus** — `github.com/vmware/vcf-api-specs` at the `9.0.0.0` / `9.1.0.0`
   tag, and how to search it.
2. **At least one on-appliance route** — the NSX OpenAPI endpoints, the VCF Operations
   Swagger UI at `/suite-api/doc/swagger-ui.html`, `kubectl api-resources`, or noun-first
   PowerShell, whichever fits their product.
3. **The gap** — no documented on-appliance API-explorer URL pattern for 9.x.

Dropping (2) sends the user back to the same dead end they arrived with; dropping (3)
leaves them hunting for a page that was never published. Neither is brevity.

### Lead with the thing they asked for

Put the calls, the script, or the direct answer first. Context, prerequisites and
caveats come after, and only the ones that bear on this specific task.

If a prerequisite would actually cause the call to fail — the group doesn't exist yet,
the token type is wrong, the version gate isn't met — that belongs up top, because it
changes what they do next. A prerequisite that is merely true does not.

### Caveats: fewer, and where they matter

Every skill carries a documentation-not-live-validated caveat and a
destructive-operations warning. State them once, briefly, and place them where they bear
on the task rather than repeating them per section.

For a read-only query, one line is enough. For something that changes a production
firewall or starts an upgrade, say more — that is where the warning earns its space.
Uniform hedging on everything trains the reader to skip all of it, including the one that
mattered.

### Version labeling stays, and stays short

Say which version the answer applies to. Once, clearly, near the top. You do not need to
re-tag every line — the tags in the reference files are for you, not for the reply.

When evidence quality genuinely differs — a 9.1 endpoint confirmed in the spec versus a
9.0 endpoint sourced only from prose — say so in one sentence at the point it matters. A
user writing a change record needs that. A user prototyping does not need it five times.

### Length calibration

| They asked for | Give them |
|---|---|
| "the exact API calls" | The call sequence with payloads. Prereqs that would break it. Nothing else. |
| "write me a script" | The script, runnable. A short note on what to set. |
| "how do I find X" / "I can't find X" | Both lookup routes — corpus *and* on-appliance — plus the answer if you found it. |
| "walk me through the upgrade" | The ordered steps with gates — this one legitimately runs long. |
| "is X true?" | Yes or no, then why. Two paragraphs, not ten. |
| A question with a false premise | Correct the premise first, briefly, then answer what they meant. |

When in doubt, answer short and offer the depth: "there's more on rollback and drafts if
you want it" costs one line and lets them pull rather than being pushed.
