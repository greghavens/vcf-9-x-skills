#!/usr/bin/env python3
"""Extract a version-tagged operation inventory from the vmware/vcf-api-specs repo.

Produces, per (version, product): a list of {method, path, operationId, summary, tags}
plus the declared base path / server URL and security schemes.

Sources are the git tags 9.0.0.0 and 9.1.0.0 of github.com/vmware/vcf-api-specs.
Everything here is derived mechanically from those spec files -- no prose docs,
no model memory.
"""
import json
import os
import sys
import yaml

ROOTS = {
    "9.0": "/tmp/vcf-specs-90",
    "9.1": "/tmp/vcf-api-specs",
}

# product key -> relative spec path (may be absent in a given version)
SPECS = {
    "sddc-manager": "specifications/sddc-manager/sddc-manager-openapi.json",
    "vcf-installer": "specifications/vcf-installer/vcf-installer-openapi.json",
    "vcf-operations": "specifications/vcf-operations/vcf-operations-openapi.json",
    "vcf-operations-for-logs": "specifications/vcf-operations/vcf-operations-for-logs-openapi.json",
    "log-management": "specifications/vcf-operations/log-management-openapi.json",
    "vcf-operations-for-networks": "specifications/vcf-operations/vcf-operations-for-networks-openapi.yaml",
    "realtime-metrics": "specifications/vcf-operations/realtime-metrics/realtime-metrics-openapi.yaml",
    "fleet-lcm": "specifications/fleet-lcm/fleet-lcm-openapi.yaml",
    "sddc-lcm": "specifications/sddc-lcm/sddc-lcm-openapi.yaml",
    "vsphere-automation": "specifications/vsphere/openapi/automation/vcenter.yaml",
    "vsphere-vi-json": "specifications/vsphere/openapi/vi-json/vi-json.yaml",
    "vsan-data-protection": "specifications/vsan-data-protection/vsan-data-protection-openapi.yaml",
    "nsx-policy": "specifications/nsx/openapi-2.0/nsx_policy_api.yaml",
    "nsx-manager": "specifications/nsx/openapi-2.0/nsx_api.yaml",
    "nsx-global-policy": "specifications/nsx/openapi-2.0/nsx_global_policy_api.yaml",
}

METHODS = ("get", "put", "post", "delete", "patch", "head", "options")


def load(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        if path.endswith(".json"):
            return json.load(fh)
        return yaml.safe_load(fh)


def base_path(doc):
    if "basePath" in doc:  # OpenAPI/Swagger 2.0
        return doc["basePath"]
    servers = doc.get("servers") or []
    return servers[0].get("url") if servers else None


def extract(doc):
    ops = []
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            ops.append({
                "method": method.upper(),
                "path": path,
                "operationId": op.get("operationId"),
                "summary": (op.get("summary") or "").strip()[:200],
                "tags": op.get("tags") or [],
                "deprecated": bool(op.get("deprecated")),
            })
    ops.sort(key=lambda o: (o["path"], o["method"]))
    return ops


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/vcf-skills/research/spec-inventory"
    os.makedirs(out_dir, exist_ok=True)
    index = {}
    for version, root in ROOTS.items():
        index[version] = {}
        for product, rel in SPECS.items():
            full = os.path.join(root, rel)
            if not os.path.exists(full):
                index[version][product] = {"present": False}
                continue
            doc = load(full)
            info = doc.get("info", {})
            ops = extract(doc)
            sec = doc.get("securityDefinitions") or (doc.get("components", {}) or {}).get("securitySchemes") or {}
            rec = {
                "present": True,
                "spec_file": rel,
                "spec_version": info.get("version"),
                "title": info.get("title"),
                "openapi": doc.get("openapi") or doc.get("swagger"),
                "base_path": base_path(doc),
                "operation_count": len(ops),
                "security_schemes": {k: {kk: vv for kk, vv in (v or {}).items() if kk in ("type", "name", "in", "scheme", "flows", "description")} for k, v in sec.items()},
                "tags": sorted({t for o in ops for t in o["tags"]}),
            }
            index[version][product] = rec
            with open(os.path.join(out_dir, f"{version}__{product}.ops.json"), "w") as fh:
                json.dump({"meta": rec, "operations": ops}, fh, indent=1)
    with open(os.path.join(out_dir, "index.json"), "w") as fh:
        json.dump(index, fh, indent=1)

    # human-readable summary
    lines = ["# Machine-extracted spec inventory (github.com/vmware/vcf-api-specs)", ""]
    lines.append("| Product | 9.0 present | 9.0 ops | 9.0 base | 9.1 present | 9.1 ops | 9.1 base |")
    lines.append("|---|---|---|---|---|---|---|")
    for product in SPECS:
        a = index["9.0"][product]
        b = index["9.1"][product]
        lines.append("| `{}` | {} | {} | `{}` | {} | {} | `{}` |".format(
            product,
            "yes" if a["present"] else "**no**", a.get("operation_count", "-"), a.get("base_path", "-"),
            "yes" if b["present"] else "**no**", b.get("operation_count", "-"), b.get("base_path", "-"),
        ))
    with open(os.path.join(out_dir, "SUMMARY.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
