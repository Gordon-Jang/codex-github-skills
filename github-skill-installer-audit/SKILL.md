---
name: github-skill-installer-audit
description: Find, compare, verify, install, and post-check Codex-compatible skills from GitHub. Use when the user asks to pull, choose, install, deploy, upgrade, or formalize skills from GitHub; asks for high-star or trusted skill recommendations; wants "verify before deploy"; or needs a repeatable skill installation audit with source, stars, compatibility, dependencies, and validation checks.
---

# GitHub Skill Installer Audit

## Workflow

Use this skill as a guardrailed installation flow, not just a download command.

1. Clarify the requested capabilities, boundaries, and acceptance criteria when they are ambiguous. If the user already provided a concrete list, proceed.
2. Inspect existing skills first:
   - User skills: `$HOME/.codex/skills`
   - System skills: `$HOME/.codex/skills/.system`
   - Treat system skills as already installed unless the user explicitly asks to override them.
3. Search GitHub candidates and prefer sources in this order:
   - Official `openai/skills`
   - High-star, active, capability-specific repositories
   - Lower-star repositories only when no high-star alternative matches the requested capability
4. Record candidate evidence before installing:
   - Repository, path, star count, update time, and description
   - Whether the path contains a `SKILL.md`
   - Whether `SKILL.md` frontmatter has `name` and `description`
   - Whether referenced `scripts/`, `references/`, `assets/`, or `agents/` are present when expected
5. Install only candidates that pass compatibility checks. Prefer the existing skill installer:
   - `~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py`
   - Use `--repo owner/repo --path path/to/skill`
   - Use `--name <name>` only when installing from a repository root or when the folder name is not the desired skill name
6. Run post-install verification:
   - Confirm each target skill directory exists
   - Read each installed `SKILL.md`
   - Extract `name:` and `description:`
   - Count installed files and top-level resources
   - Check tool dependencies mentioned by the skill, such as `npx`, `uv`, `markitdown`, `ffmpeg`, or vendor CLIs
7. Report results with a clear split:
   - Installed and verified
   - Already present
   - Installed with caveats
   - Skipped or failed, with reason

## Acceptance Criteria

An installed skill is verified only when all required checks pass:

- The target directory exists under `$HOME/.codex/skills` or `$HOME/.codex/skills/.system`.
- `SKILL.md` exists and begins with YAML frontmatter bounded by `---`.
- Frontmatter contains scalar `name:` and `description:` values.
- The `name:` value matches the installed folder unless the user explicitly requested an alias.
- Referenced resource folders are present when the skill instructions depend on them.
- Mentioned command-line dependencies are checked with `Get-Command` or an equivalent version command when available.

Treat a missing `agents/openai.yaml` as a caveat, not an installation failure, unless the user requires UI metadata.

## Selection Rules

Prefer star count only after the repository actually matches the requested capability. Do not install a popular but unrelated repository.

Use lower-star skills when they are the only precise match, but say so explicitly and verify more carefully.

Avoid duplicate installations. If a skill exists in `.system`, do not copy it into user skills unless the user wants a modified or pinned copy.

Do not treat a repository as Codex-compatible because the README mentions Codex. Confirm `SKILL.md` or a clear skill folder layout.

For high-risk skills that run code, inspect scripts before recommending or running them. Installation is allowed after directory and metadata checks, but dependency setup should be verified separately. Never run a downloaded script until you have inspected the entrypoint and understood what files, network endpoints, or credentials it touches.

When several candidates are similar, prefer the one with the smallest, clearest skill folder over a repository that requires copying unrelated project files.

## Candidate Compatibility Checks

Before installing, inspect candidates without executing their code:

```powershell
gh repo view owner/repo --json nameWithOwner,description,stargazerCount,updatedAt,url
gh api repos/owner/repo/contents/path/to/skill/SKILL.md --jq ".name,.download_url"
```

If GitHub CLI is unavailable, use the REST examples below with `Invoke-RestMethod`.

For each candidate, verify:

- `SKILL.md` is present at the proposed path.
- Frontmatter appears at the top and includes `name` and `description`.
- Relative references in `SKILL.md` point to files or folders inside the same skill directory.
- Scripts are readable text files or intentionally binary assets are in `assets/`.
- The candidate does not require installing a duplicate of an existing system skill unless the user asked for a modified copy.

## Useful Commands

PowerShell candidate check:

```powershell
$repos = @("owner/repo")
foreach ($r in $repos) {
  $u = "https://api.github.com/repos/$r"
  Invoke-RestMethod -Headers @{ "User-Agent" = "codex-skill-audit" } -Uri $u |
    Select-Object full_name, stargazers_count, forks_count, updated_at, description
}
```

GitHub search:

```powershell
$q = "codex skill obsidian"
$uri = "https://api.github.com/search/repositories?q=$([uri]::EscapeDataString($q))&sort=stars&order=desc&per_page=5"
Invoke-RestMethod -Headers @{ "User-Agent" = "codex-skill-audit" } -Uri $uri |
  Select-Object -ExpandProperty items |
  Select-Object full_name, stargazers_count, updated_at, description
```

Install:

```powershell
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" --repo owner/repo --path path/to/skill
```

Run the bundled post-install checker:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME/.codex/skills/github-skill-installer-audit/scripts/verify-installed-skills.ps1" -SkillNames skill-a,skill-b
powershell -ExecutionPolicy Bypass -File "$HOME/.codex/skills/github-skill-installer-audit/scripts/verify-installed-skills.ps1" -SkillNames skill-a,skill-b -Strict
```

Use `-Strict` when preparing a formal installation report. It fails on warnings such as a missing `agents/openai.yaml`.

## Post-Install Dependency Checks

After installing skills with CLI dependencies, actually test the command entrypoint where possible.

Examples:

```powershell
npx --version
python -m uv --version
$env:PATH = "$HOME/.local/bin;$env:PATH"
markitdown --version
```

If a dependency requires a different runtime, prefer an isolated tool environment over changing the user's default runtime. For example, use `uv tool install --python 3.12 "markitdown[all]"` when the default Python is too old for MarkItDown.

For skills that mention GitHub or package managers, verify authentication or versions before claiming readiness:

```powershell
gh auth status
git --version
python --version
```

## Reporting

Keep the final report concise but auditable:

- Name each installed skill.
- Name the source repository.
- Mention why the source was chosen, especially high-star or official status.
- Include caveats such as low-star exception, missing PATH entry, missing optional dependency, or restart requirement.
- End by telling the user to restart Codex when new skills were installed.
