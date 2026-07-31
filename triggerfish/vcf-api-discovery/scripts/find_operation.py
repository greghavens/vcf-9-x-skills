#!/usr/bin/env python3
"""Search the VCF OpenAPI operation inventory by keyword, scoped to a VCF version.

PROVENANCE
----------
The inventories this script reads (`<version>__<product>.ops.json`, plus `index.json`)
are machine-extracted from the OpenAPI specifications published at:

    https://github.com/vmware/vcf-api-specs

specifically from its two release git tags:

    tag 9.0.0.0  -> VCF 9.0   (8 specs, 5083 operations)
    tag 9.1.0.0  -> VCF 9.1  (14 specs, 11590 operations)

Each `*.ops.json` file is `{"meta": {...}, "operations": [...]}` where `meta` records the
source spec file, its OpenAPI version, its declared base path and its spec version, and each
operation carries `method`, `path`, `operationId`, `summary`, `tags` and `deprecated`.

WHY --version IS MANDATORY
--------------------------
The 9.0 and 9.1 API surfaces genuinely differ: NSX (x3), fleet-lcm, sddc-lcm, realtime-metrics
and log-management have NO spec at 9.0, `vcf-operations-for-logs` exists only at 9.0, and every
shared product gained (and in some cases lost) operations in 9.1. Searching both versions at once
and presenting a merged list is the fastest way to hand someone a 9.1-only endpoint as though it
worked on 9.0. So: pass `--version 9.0` or `--version 9.1`. If you really want both, ask for it
explicitly with `--both-versions`, and the output stays labelled per version.

A MISS IS NOT ALWAYS EVIDENCE OF ABSENCE
----------------------------------------
If a product has no spec at the requested version, a zero-result search says nothing about whether
the API exists. The script warns you when this applies (notably NSX at 9.0). See
`references/spec-corpus.md` section 4.

EXAMPLES
--------
    python3 find_operation.py --version 9.1 "edge cluster"
    python3 find_operation.py --version 9.0 --product sddc-manager --method POST upgrade
    python3 find_operation.py --both-versions depot
    python3 find_operation.py --version 9.1 --product fleet-lcm --json ""
    python3 find_operation.py --version 9.1 --list-products
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

VERSIONS = ("9.0", "9.1")

# Products present only at 9.1 (absent from the 9.0.0.0 tag), and vice versa.
ONLY_9_1 = (
    "nsx-policy",
    "nsx-manager",
    "nsx-global-policy",
    "fleet-lcm",
    "sddc-lcm",
    "realtime-metrics",
    "log-management",
)
ONLY_9_0 = ("vcf-operations-for-logs",)

TAGS = {"9.0": "9.0.0.0", "9.1": "9.1.0.0"}

# Candidate inventory locations, tried in order when --inventory is not given.
# First entry keeps the script working wherever the skill is installed.
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INVENTORY_CANDIDATES = (
    os.path.normpath(os.path.join(_HERE, "..", "references", "spec-inventory")),
    os.path.normpath(os.path.join(_HERE, "..", "spec-inventory")),
    os.path.normpath(os.path.join(_HERE, "..", "..", "..", "research", "spec-inventory")),
)

REGEN_HELP = """\
How to regenerate the inventory
-------------------------------
  1. Clone the spec repo and put both release tags on disk:

       git clone https://github.com/vmware/vcf-api-specs /tmp/vcf-api-specs
       git -C /tmp/vcf-api-specs checkout 9.1.0.0
       git -C /tmp/vcf-api-specs worktree add /tmp/vcf-specs-90 9.0.0.0

  2. For every OpenAPI file under <checkout>/specifications, emit
     <version>__<product>.ops.json as:

       {"meta": {"spec_file": ..., "openapi": ..., "base_path": ...,
                 "spec_version": ..., "operation_count": N, "title": ..., "tags": [...]},
        "operations": [{"method": "GET", "path": "/v1/...", "operationId": ...,
                        "summary": ..., "tags": [...], "deprecated": false}, ...]}

     Base path is `servers[0].url` for OpenAPI 3.x specs and `basePath` for the NSX
     OpenAPI 2.0 specs -- they differ, see references/spec-corpus.md section 5.

  3. Point this script at the result with --inventory <dir>, or place it at the
     default location printed above.
"""


def die(msg: str, code: int = 2) -> "None":
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def resolve_inventory(explicit: "str | None") -> str:
    """Return a usable inventory directory, or exit non-zero with instructions."""
    if explicit:
        candidates = [os.path.abspath(os.path.expanduser(explicit))]
    else:
        candidates = list(DEFAULT_INVENTORY_CANDIDATES)

    for path in candidates:
        if os.path.isdir(path) and _has_ops_files(path):
            return path

    tried = "\n".join("  - " + c for c in candidates)
    die(
        "ERROR: no usable spec inventory found.\n"
        "Looked for a directory containing <version>__<product>.ops.json files in:\n"
        + tried
        + "\n\nDefault install location: "
        + DEFAULT_INVENTORY_CANDIDATES[0]
        + "\n\n"
        + REGEN_HELP
    )
    return ""  # unreachable


def _has_ops_files(path: str) -> bool:
    try:
        return any(n.endswith(".ops.json") for n in os.listdir(path))
    except OSError:
        return False


def load_products(inv_dir: str, version: str) -> "list[tuple[str, dict]]":
    """Load (product, payload) pairs for a version, sorted by product name."""
    prefix = version + "__"
    out = []
    for name in sorted(os.listdir(inv_dir)):
        if not (name.startswith(prefix) and name.endswith(".ops.json")):
            continue
        product = name[len(prefix): -len(".ops.json")]
        full = os.path.join(inv_dir, name)
        try:
            with open(full, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, ValueError) as exc:
            sys.stderr.write("WARNING: skipping unreadable %s (%s)\n" % (full, exc))
            continue
        out.append((product, payload))
    return out


def compile_terms(keywords: "list[str]", regex: bool, ignore_case: bool):
    flags = re.IGNORECASE if ignore_case else 0
    pats = []
    for kw in keywords:
        pats.append(re.compile(kw if regex else re.escape(kw), flags))
    return pats


def haystack(op: dict) -> str:
    tags = op.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]
    return "\n".join(
        [
            str(op.get("path") or ""),
            str(op.get("operationId") or ""),
            str(op.get("summary") or ""),
            " ".join(str(t) for t in tags),
        ]
    )


def search_version(
    inv_dir: str,
    version: str,
    patterns,
    product_filter: "list[str]",
    method_filter: "list[str]",
    match_any: bool,
    drop_deprecated: bool,
) -> "tuple[list[dict], list[str]]":
    """Return (hits, products_searched)."""
    hits = []
    searched = []
    for product, payload in load_products(inv_dir, version):
        if product_filter and not any(_prod_match(product, f) for f in product_filter):
            continue
        searched.append(product)
        meta = payload.get("meta") or {}
        for op in payload.get("operations") or []:
            if method_filter and str(op.get("method", "")).upper() not in method_filter:
                continue
            if drop_deprecated and op.get("deprecated"):
                continue
            text = haystack(op)
            if patterns:
                results = [bool(p.search(text)) for p in patterns]
                ok = any(results) if match_any else all(results)
                if not ok:
                    continue
            hits.append(
                {
                    "version": version,
                    "product": product,
                    "method": str(op.get("method", "")).upper(),
                    "path": op.get("path") or "",
                    "operationId": op.get("operationId") or "",
                    "summary": op.get("summary") or "",
                    "tags": op.get("tags") or [],
                    "deprecated": bool(op.get("deprecated")),
                    "base_path": meta.get("base_path") or "",
                    "spec_version": meta.get("spec_version") or "",
                    "spec_file": meta.get("spec_file") or "",
                    "openapi": meta.get("openapi") or "",
                    "git_tag": TAGS.get(version, ""),
                }
            )
    hits.sort(key=lambda h: (h["product"], h["path"], h["method"]))
    return hits, searched


def _prod_match(product: str, wanted: str) -> bool:
    wanted = wanted.strip().lower()
    if not wanted:
        return False
    if wanted.endswith("*"):
        return product.lower().startswith(wanted[:-1])
    return product.lower() == wanted or wanted in product.lower()


def format_hit(h: dict) -> str:
    summary = h["summary"].strip().replace("\n", " ")
    if not summary:
        summary = h["operationId"] or "(no summary in spec)"
    dep = "  [DEPRECATED]" if h["deprecated"] else ""
    trace = "%s, spec %s, base %s" % (
        h["product"],
        h["spec_version"] or h["version"],
        h["base_path"] or "(none declared)",
    )
    return "%-7s %s — %s (%s)%s" % (h["method"], h["path"], summary, trace, dep)


def absence_note(version: str, searched: "list[str]", hit_count: int = 0,
                 product_filter: "list[str] | None" = None) -> "list[str]":
    """Warn when a miss might be misread as evidence of absence.

    The NSX-at-9.0 warning is shown on every unfiltered 9.0 search, because it is the
    trap most likely to produce a confidently wrong "that API doesn't exist in 9.0".
    The other notes appear only when they could actually explain the result: a
    zero-hit search, or an explicit --product filter naming an absent product.
    """
    product_filter = product_filter or []
    absent_here = ONLY_9_1 if version == "9.0" else ONLY_9_0
    missing = [p for p in absent_here if p not in searched]
    if product_filter:
        missing = [p for p in missing if any(_prod_match(p, f) for f in product_filter)]
    if not missing:
        return []
    # Anything other than the NSX-at-9.0 warning is suppressed on a fruitful search.
    quiet = bool(hit_count)
    notes = []
    if version == "9.0":
        nsx_missing = [p for p in missing if p.startswith("nsx-")]
        if nsx_missing:
            notes.append(
                "NOTE: the 9.0.0.0 spec tag ships no NSX specs (%s), so NSX was not searched. "
                "A miss here is NOT evidence that the NSX API lacks the operation at 9.0 — query "
                "a running NSX Manager (GET /api/v1/spec/openapi/nsx_policy_api.json) or the "
                "9.0.0 portal reference instead." % ", ".join(nsx_missing)
            )
        others = [p for p in missing if not p.startswith("nsx-")]
        if others and not quiet:
            notes.append(
                "NOTE: these products have no spec at 9.0 because the services are new in 9.1: %s."
                % ", ".join(others)
            )
    if version == "9.1":
        gone = missing
        if gone and not quiet:
            notes.append(
                "NOTE: %s exists only at 9.0; at 9.1 it is replaced by log-management "
                "(different base path)." % ", ".join(gone)
            )
    return notes


def list_products(inv_dir: str, versions: "list[str]") -> int:
    for version in versions:
        rows = load_products(inv_dir, version)
        total = sum(len(p.get("operations") or []) for _, p in rows)
        print("=== VCF %s (git tag %s) — %d specs, %d operations"
              % (version, TAGS.get(version, "?"), len(rows), total))
        for product, payload in rows:
            meta = payload.get("meta") or {}
            print("  %-30s %5d ops  openapi %-6s base %s"
                  % (product, len(payload.get("operations") or []),
                     meta.get("openapi") or "?", meta.get("base_path") or "(none)"))
        print("")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="find_operation.py",
        description="Search the extracted VCF OpenAPI operation inventory, scoped to a VCF version.",
        epilog="Inventories are extracted from git tags 9.0.0.0 and 9.1.0.0 of "
               "github.com/vmware/vcf-api-specs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("keywords", nargs="*",
                   help="Keyword(s) matched against path, operationId, summary and tags. "
                        "All must match unless --any is given. Omit to list everything "
                        "(combine with --product / --method).")
    p.add_argument("--version", choices=VERSIONS,
                   help="VCF version to search. REQUIRED unless --both-versions is given.")
    p.add_argument("--both-versions", action="store_true",
                   help="Explicitly search 9.0 and 9.1; results stay labelled per version.")
    p.add_argument("--product", action="append", default=[], metavar="NAME",
                   help="Restrict to a product key (repeatable; substring or trailing '*' ok). "
                        "See --list-products.")
    p.add_argument("--method", action="append", default=[], metavar="VERB",
                   help="Restrict to an HTTP method (repeatable), e.g. --method GET --method POST.")
    p.add_argument("--any", dest="match_any", action="store_true",
                   help="Match ANY keyword instead of all of them.")
    p.add_argument("--regex", action="store_true",
                   help="Treat keywords as regular expressions.")
    p.add_argument("--case-sensitive", action="store_true",
                   help="Case-sensitive matching (default is case-insensitive).")
    p.add_argument("--no-deprecated", action="store_true",
                   help="Omit operations marked deprecated in the spec.")
    p.add_argument("--limit", type=int, default=0, metavar="N",
                   help="Print at most N hits per version (0 = no limit).")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON instead of text.")
    p.add_argument("--inventory", metavar="DIR",
                   help="Inventory directory. Default: %s" % DEFAULT_INVENTORY_CANDIDATES[0])
    p.add_argument("--list-products", action="store_true",
                   help="List products, operation counts and base paths, then exit.")
    return p


def main(argv: "list[str] | None" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    inv_dir = resolve_inventory(args.inventory)

    if args.list_products:
        versions = [args.version] if args.version else list(VERSIONS)
        return list_products(inv_dir, versions)

    if args.both_versions:
        versions = list(VERSIONS)
    elif args.version:
        versions = [args.version]
    else:
        die(
            "ERROR: --version is required (choose 9.0 or 9.1).\n"
            "\n"
            "The 9.0 and 9.1 API surfaces differ substantially — NSX (x3), fleet-lcm, sddc-lcm,\n"
            "realtime-metrics and log-management have no spec at 9.0, vcf-operations-for-logs\n"
            "exists only at 9.0, and shared products gained operations in 9.1. Searching both\n"
            "silently would let a 9.1-only endpoint be reported as valid on 9.0.\n"
            "\n"
            "  python3 find_operation.py --version 9.1 \"<keyword>\"\n"
            "  python3 find_operation.py --both-versions \"<keyword>\"   # explicit, labelled output\n",
            2,
        )

    method_filter = []
    for m in args.method:
        method_filter.extend(x.strip().upper() for x in m.split(",") if x.strip())

    patterns = compile_terms(
        [k for k in args.keywords if k != ""], args.regex, not args.case_sensitive
    )

    payload = {
        "query": {
            "keywords": args.keywords,
            "versions": versions,
            "products": args.product,
            "methods": method_filter,
            "match": "any" if args.match_any else "all",
            "regex": bool(args.regex),
        },
        "provenance": {
            "source": "https://github.com/vmware/vcf-api-specs",
            "git_tags": {v: TAGS[v] for v in versions},
            "inventory_dir": inv_dir,
        },
        "results": {},
    }

    counts = {}
    for version in versions:
        hits, searched = search_version(
            inv_dir, version, patterns, args.product, method_filter,
            args.match_any, args.no_deprecated,
        )
        counts[version] = len(hits)
        shown = hits[: args.limit] if args.limit and args.limit > 0 else hits

        if args.json:
            payload["results"][version] = {
                "git_tag": TAGS[version],
                "products_searched": searched,
                "match_count": len(hits),
                "notes": absence_note(version, searched, len(hits), args.product),
                "operations": shown,
            }
            continue

        header = "=== VCF %s (git tag %s) — %d match%s across %d product%s" % (
            version, TAGS[version], len(hits), "" if len(hits) == 1 else "es",
            len(searched), "" if len(searched) == 1 else "s",
        )
        print(header)
        if not searched:
            print("  (no matching product specs at this version)")
        for h in shown:
            print("  " + format_hit(h))
        if args.limit and len(hits) > len(shown):
            print("  ... %d more (raise --limit to see them)" % (len(hits) - len(shown)))
        if not hits:
            print("  no matches")
        for note in absence_note(version, searched, len(hits), args.product):
            print("  " + note)
        print("")

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    if len(versions) > 1:
        print("Totals: " + ", ".join("%s=%d" % (v, counts[v]) for v in versions))
    # Exit 0 for any successfully executed search, including one with no hits.
    # A non-zero exit means the inventory could not be used (see resolve_inventory).
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. piped into `head`
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
