#!/usr/bin/env python3
"""Package the VCF 9.0/9.1 agent skills for five target ecosystems.

One canonical source tree (`skills/`) authored to the open agentskills.io spec,
transformed per target. All transforms are additive or subtractive on the YAML
frontmatter; no skill body is ever rewritten.

Targets and what each needs (from the ecosystem research on file):

  windsurf     .windsurf/skills/<name>/            no change
  claude       ~/.claude/skills/<name>/            no change, plus .skill zips
  codex        .agents/skills/<name>/              no change (path only)
  triggerfish  ~/.triggerfish/.../skills/<name>/   +top-level version,
                                                    classification_ceiling,
                                                    requires_tools, network_domains
                                                    (top-level, NOT under metadata:
                                                    nesting is silently ignored and
                                                    defaults to PUBLIC)
  openclaw     ~/.agents/skills/<name>/            -license (per-skill overrides are
                                                    rejected), +metadata.openclaw.requires

Real directories are copied, never symlinked: the Triggerfish loader skips
symlinked directories and ClawHub dereferences at publish.
"""
import json
import os
import re
import shutil
import sys
import zipfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
SKIP = {"evals", "_shared"}

# Skills that handle infrastructure credentials or drive production-affecting
# change. Triggerfish gates execution on classification_ceiling; over-declaring
# needlessly restricts who can run a skill, so discovery/reference-only skills
# stay INTERNAL.
INTERNAL_ONLY = {"vcf-api-discovery"}

BIN_CANDIDATES = ["curl", "jq", "kubectl", "pwsh", "openssl", "vcf", "git"]


def read_frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit(f"no frontmatter: {path}")
    fields = []
    for line in m.group(1).split("\n"):
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if km:
            v = km.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1].replace('\\"', '"')
            fields.append([km.group(1), v])
    return fields, text[m.end():]


def emit(fields, body):
    out = []
    for k, v in fields:
        if isinstance(v, (dict, list)):
            out.append(f"{k}:")
            out.append("\n".join("  " + ln for ln in json.dumps(v, indent=2).split("\n")))
        elif ":" in str(v) or str(v).startswith(("[", "{", ">", "|", "*", "&")):
            out.append(f'{k}: "{str(v).replace(chr(34), chr(92) + chr(34))}"')
        else:
            out.append(f"{k}: {v}")
    return "---\n" + "\n".join(out) + "\n---\n" + body


def scan_requirements(skill_dir):
    """Find binaries and externally-configured env vars this skill references.

    ClawHub's audit flags a metadata mismatch when a skill's files reference an
    undeclared env var, so this scan drives the declaration rather than a
    hand-maintained list that would drift.
    """
    blob = []
    for root, _, files in os.walk(skill_dir):
        if "spec-inventory" in root:
            continue
        for f in files:
            if f.endswith((".md", ".py", ".sh", ".ps1")):
                blob.append(open(os.path.join(root, f), encoding="utf-8", errors="replace").read())
    blob = "\n".join(blob)
    bins = [b for b in BIN_CANDIDATES if re.search(rf"(?<![\w-]){re.escape(b)}\s", blob)]
    # Only genuinely external configuration, not shell locals used in examples.
    envs = sorted(set(re.findall(r"\b(VCF_[A-Z0-9_]+|VCFA_[A-Z0-9_]+|SDDC_[A-Z0-9_]+)\b", blob)))
    return bins, envs


def copy_tree(name, dest_root, subpath):
    dest = os.path.join(dest_root, subpath, name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    # symlinks=False: Triggerfish's loader skips symlinked dirs, ClawHub
    # dereferences at publish. Real directories work everywhere.
    shutil.copytree(name and os.path.join(SRC, name), dest, symlinks=False)
    return dest


def main():
    skills = sorted(
        d for d in os.listdir(SRC)
        if os.path.isdir(os.path.join(SRC, d)) and d not in SKIP
    )
    if os.path.exists(OUT):
        shutil.rmtree(OUT)

    report = {"skills": len(skills), "targets": {}}

    # --- windsurf / claude / codex: byte-identical to source -----------------
    for target, subpath in [
        ("windsurf", ".windsurf/skills"),
        ("claude", "skills"),
        ("codex", ".agents/skills"),
    ]:
        for s in skills:
            copy_tree(s, os.path.join(OUT, target), subpath)
        report["targets"][target] = {"path": subpath, "transform": "none", "skills": len(skills)}

    # --- claude: also emit .skill zips --------------------------------------
    zips = os.path.join(OUT, "claude", "skill-packages")
    os.makedirs(zips, exist_ok=True)
    for s in skills:
        src = os.path.join(SRC, s)
        with zipfile.ZipFile(os.path.join(zips, f"{s}.skill"), "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(src):
                dirs[:] = [d for d in dirs if d not in {"__pycache__", "node_modules"}]
                for f in files:
                    if f.endswith(".pyc") or f == ".DS_Store":
                        continue
                    full = os.path.join(root, f)
                    z.write(full, os.path.join(s, os.path.relpath(full, src)))
    report["targets"]["claude"]["packages"] = len(skills)

    # --- triggerfish: additive top-level keys --------------------------------
    tf_meta = {}
    for s in skills:
        dest = copy_tree(s, os.path.join(OUT, "triggerfish"), "skills")
        p = os.path.join(dest, "SKILL.md")
        fields, body = read_frontmatter(p)
        bins, _ = scan_requirements(dest)
        ceiling = "INTERNAL" if s in INTERNAL_ONLY else "CONFIDENTIAL"
        keys = dict(fields)
        # Top level, deliberately: the docs show these nested under
        # metadata.triggerfish.*, but the loader reads them top-level and
        # silently defaults to PUBLIC otherwise.
        for k, v in [
            ("version", "1.0.0"),
            ("classification_ceiling", ceiling),
            ("requires_tools", json.dumps(bins)),
            ("network_domains", json.dumps(
                ["techdocs.broadcom.com", "developer.broadcom.com", "github.com"])),
        ]:
            if k not in keys:
                fields.append([k, v])
        open(p, "w", encoding="utf-8").write(emit(fields, body))
        tf_meta[s] = ceiling
    report["targets"]["triggerfish"] = {
        "path": "skills", "transform": "+version, +classification_ceiling, "
        "+requires_tools, +network_domains (all TOP-LEVEL)",
        "classification": tf_meta,
    }

    # --- openclaw / clawhub: strip license, declare requirements -------------
    oc = {}
    for s in skills:
        dest = copy_tree(s, os.path.join(OUT, "openclaw"), ".agents/skills")
        p = os.path.join(dest, "SKILL.md")
        fields, body = read_frontmatter(p)
        bins, envs = scan_requirements(dest)
        # ClawHub rejects per-skill license overrides; publishing is MIT-0.
        fields = [f for f in fields if f[0] != "license"]
        requires = {}
        # anyBins, not bins: bins is an AND gate and would make a skill inert
        # on a host missing any one of them.
        if bins:
            requires["anyBins"] = bins
        if s == "vcf-api-discovery":
            requires["bins"] = ["python3"]  # the bundled search script is hard-required
        meta = {"openclaw": {"requires": requires}}
        if envs:
            meta["openclaw"]["envVars"] = [
                {"name": e, "required": False,
                 "description": f"Optional: {e} used in worked examples"} for e in envs
            ]
        fields.append(["metadata", meta])
        open(p, "w", encoding="utf-8").write(emit(fields, body))
        oc[s] = {"anyBins": bins, "envVars": envs}
    report["targets"]["openclaw"] = {
        "path": ".agents/skills",
        "transform": "-license (ClawHub rejects per-skill overrides; MIT-0 applies), "
                     "+metadata.openclaw.requires",
        "requirements": oc,
    }

    json.dump(report, open(os.path.join(OUT, "packaging-report.json"), "w"), indent=1)
    print(json.dumps({k: (v if k != "targets" else
                          {t: {kk: vv for kk, vv in d.items() if kk != "requirements"}
                           for t, d in v.items()}) for k, v in report.items()}, indent=1)[:2600])
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
