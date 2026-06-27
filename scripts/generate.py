#!/usr/bin/env python3
"""Generate CHANGELOG.md from conventional commits."""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_commits(from_tag: str = "") -> list[dict]:
    if from_tag:
        range_spec = f"{from_tag}..HEAD"
    else:
        # Try last tag, fall back to all history
        last_tag = run(["git", "describe", "--tags", "--abbrev=0", "HEAD^"])
        range_spec = f"{last_tag}..HEAD" if last_tag else "HEAD"

    log = run([
        "git", "log", range_spec,
        "--pretty=format:%H|%s|%an|%ae|%ad",
        "--date=short",
    ])
    if not log:
        return []

    commits = []
    for line in log.splitlines():
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        sha, subject, author, email, date = parts
        commits.append({"sha": sha[:7], "subject": subject, "author": author, "date": date})
    return commits


def parse_conventional(subject: str) -> tuple[str, str, str]:
    """Parse 'type(scope): description' -> (type, scope, desc)."""
    m = re.match(r"^(\w+)(?:\(([^)]+)\))?!?:\s*(.+)$", subject)
    if m:
        return m.group(1), m.group(2) or "", m.group(3)
    return "misc", "", subject


TYPE_LABELS = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "chore": "Chores",
    "ci": "CI",
    "test": "Tests",
    "style": "Style",
    "misc": "Other",
}


def generate_changelog(commits: list[dict], include_types: list[str]) -> str:
    grouped: dict[str, list] = defaultdict(list)
    for c in commits:
        ctype, scope, desc = parse_conventional(c["subject"])
        if ctype in include_types or "misc" in include_types:
            grouped[ctype].append({**c, "scope": scope, "desc": desc})

    lines = [f"# Changelog\n", f"*Generated {datetime.now().strftime('%Y-%m-%d')}*\n\n"]

    for ctype in ["feat", "fix", "perf", "refactor", "docs", "chore", "ci", "test", "misc"]:
        if ctype not in grouped or ctype not in include_types:
            continue
        label = TYPE_LABELS.get(ctype, ctype.title())
        lines.append(f"## {label}\n\n")
        for c in grouped[ctype]:
            scope_str = f"**{c['scope']}**: " if c["scope"] else ""
            lines.append(f"- {scope_str}{c['desc']} (`{c['sha']}` by {c['author']})\n")
        lines.append("\n")

    return "".join(lines)


def create_release(tag: str, changelog: str, token: str) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo or not token or not tag:
        return

    api_url = f"https://api.github.com/repos/{repo}/releases"
    payload = {
        "tag_name": tag,
        "name": f"Release {tag}",
        "body": changelog[:65536],  # GitHub limit
        "draft": False,
        "prerelease": tag.startswith("v0") or "alpha" in tag or "beta" in tag,
    }

    import urllib.request
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"✓ Release created: {data.get('html_url', '')}")
    except Exception as e:
        print(f"Warning: could not create release: {e}", file=sys.stderr)


def main() -> None:
    output_file = os.environ.get("OUTPUT_FILE", "CHANGELOG.md")
    release_tag = os.environ.get("RELEASE_TAG", "")
    from_tag = os.environ.get("FROM_TAG", "")
    include_types_raw = os.environ.get("INCLUDE_TYPES", "feat,fix,perf,refactor,docs,chore")
    include_types = [t.strip() for t in include_types_raw.split(",")]
    token = os.environ.get("GITHUB_TOKEN", "")

    commits = get_commits(from_tag)
    if not commits:
        print("No commits found — skipping changelog generation.")
        return

    changelog = generate_changelog(commits, include_types)

    with open(output_file, "w") as f:
        f.write(changelog)

    print(f"✓ Wrote {len(commits)} commits to {output_file}")

    # Set output for GitHub Actions
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changelog-path={output_file}\n")

    if release_tag:
        create_release(release_tag, changelog, token)


if __name__ == "__main__":
    main()
