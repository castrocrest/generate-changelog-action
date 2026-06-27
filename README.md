# Generate Changelog Action

Generate `CHANGELOG.md` from conventional commits — automatically on every release or merge to main.

## Usage

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # full history for changelog

      - uses: castrocrest/generate-changelog-action@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          release-tag: ${{ github.ref_name }}  # creates a GitHub Release
          include-types: "feat,fix,perf,docs"
```

## Auto-update on every merge

```yaml
name: Update Changelog
on:
  push:
    branches: [main]

jobs:
  changelog:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: castrocrest/generate-changelog-action@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Commit changelog
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add CHANGELOG.md
          git diff --cached --quiet || git commit -m "chore: update CHANGELOG [skip ci]"
          git push
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `token` | Yes | `${{ github.token }}` | GitHub token |
| `output-file` | No | `CHANGELOG.md` | Output file path |
| `release-tag` | No | `""` | Tag for GitHub Release (skip if empty) |
| `from-tag` | No | `""` | Generate from this tag forward (uses latest tag if empty) |
| `include-types` | No | `feat,fix,perf,refactor,docs,chore` | Commit types to include |

## Outputs

| Output | Description |
|--------|-------------|
| `changelog-path` | Path to the generated changelog file |

## Supported commit types

Follows the [Conventional Commits](https://www.conventionalcommits.org/) spec:

| Type | Section |
|------|---------|
| `feat` | Features |
| `fix` | Bug Fixes |
| `perf` | Performance |
| `refactor` | Refactoring |
| `docs` | Documentation |
| `chore` | Chores |
| `ci` | CI |

## More developer tools

For more production-ready developer tools — GitHub Actions workflows, Docker Compose stacks, MCP servers, and more — see the **[Developer Tools & Templates](https://castrocrest.gumroad.com)** collection.

