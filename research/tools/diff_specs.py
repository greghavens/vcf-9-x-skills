#!/usr/bin/env python3
"""Diff the 9.0 and 9.1 operation inventories produced by extract_specs.py.

For each product present in both tags, report operations added in 9.1, removed
in 9.1, and operations newly marked deprecated. Keyed on (METHOD, path) since
operationId is not stable across all specs.
"""
import json
import os
import sys

IN = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/vcf-skills/research/spec-inventory"
OUT = os.path.join(IN, "DELTA-9.0-to-9.1.md")

index = json.load(open(os.path.join(IN, "index.json")))
products = list(index["9.0"].keys())

lines = [
    "# Machine-computed API delta: VCF 9.0.0.0 -> 9.1.0.0",
    "",
    "Derived by diffing git tags `9.0.0.0` and `9.1.0.0` of "
    "https://github.com/vmware/vcf-api-specs (cloned 2026-07-31).",
    "Keyed on (METHOD, path). Counts are of spec operations, not doc pages.",
    "",
]

summary = []
details = []

for product in products:
    a, b = index["9.0"][product], index["9.1"][product]
    if not a["present"] and not b["present"]:
        continue
    if not a["present"]:
        summary.append((product, "ADDED IN 9.1", "-", b["operation_count"], "-", "-"))
        details.append(f"\n## `{product}` — spec is new in 9.1\n\n"
                       f"- Not present at tag 9.0.0.0. Present at 9.1.0.0 with "
                       f"{b['operation_count']} operations, base `{b['base_path']}`.\n"
                       f"- Spec file: `{b['spec_file']}` (title: {b['title']}).\n"
                       f"- **Implication:** no machine-readable 9.0 spec exists in this repo "
                       f"for this product; 9.0 facts must come from the version-pinned doc portal.\n")
        continue
    if not b["present"]:
        summary.append((product, "REMOVED IN 9.1", a["operation_count"], "-", "-", "-"))
        details.append(f"\n## `{product}` — spec removed in 9.1\n\n"
                       f"- Present at 9.0.0.0 with {a['operation_count']} operations, base `{a['base_path']}`.\n"
                       f"- Absent at 9.1.0.0. Check for a renamed successor spec.\n")
        continue

    ops_a = json.load(open(os.path.join(IN, f"9.0__{product}.ops.json")))["operations"]
    ops_b = json.load(open(os.path.join(IN, f"9.1__{product}.ops.json")))["operations"]
    key = lambda o: (o["method"], o["path"])
    ka = {key(o): o for o in ops_a}
    kb = {key(o): o for o in ops_b}
    added = sorted(set(kb) - set(ka))
    removed = sorted(set(ka) - set(kb))
    newly_dep = sorted(k for k in (set(ka) & set(kb)) if kb[k]["deprecated"] and not ka[k]["deprecated"])

    summary.append((product, "both", a["operation_count"], b["operation_count"],
                    len(added), len(removed)))

    base_changed = a["base_path"] != b["base_path"]
    d = [f"\n## `{product}`\n",
         f"- 9.0: {a['operation_count']} ops, base `{a['base_path']}`, spec version `{a['spec_version']}`",
         f"- 9.1: {b['operation_count']} ops, base `{b['base_path']}`, spec version `{b['spec_version']}`",
         f"- Base path changed: **{'YES' if base_changed else 'no'}**",
         f"- Added in 9.1: {len(added)} | Removed in 9.1: {len(removed)} | Newly deprecated: {len(newly_dep)}",
         ""]
    if removed:
        d.append("### Removed in 9.1 (present in 9.0, absent in 9.1)\n")
        for k in removed:
            d.append(f"- `{k[0]} {k[1]}` — {ka[k]['summary'] or ka[k]['operationId'] or ''}")
        d.append("")
    if newly_dep:
        d.append("### Newly deprecated in 9.1\n")
        for k in newly_dep:
            d.append(f"- `{k[0]} {k[1]}` — {kb[k]['summary'] or kb[k]['operationId'] or ''}")
        d.append("")
    if added:
        d.append(f"### Added in 9.1 (first {min(len(added), 60)} of {len(added)})\n")
        for k in added[:60]:
            d.append(f"- `{k[0]} {k[1]}` — {kb[k]['summary'] or kb[k]['operationId'] or ''}")
        if len(added) > 60:
            d.append(f"- _...and {len(added)-60} more; see `9.1__{product}.ops.json`_")
        d.append("")
    details.append("\n".join(d))

lines.append("| Product | Status | 9.0 ops | 9.1 ops | added | removed |")
lines.append("|---|---|---|---|---|---|")
for row in summary:
    lines.append("| `{}` | {} | {} | {} | {} | {} |".format(*row))

with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n" + "\n".join(details) + "\n")
print("\n".join(lines))
print(f"\nwrote {OUT}")
