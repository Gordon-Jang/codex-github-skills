# Codex GitHub Skills

This repository contains two Codex skills for GitHub-oriented workflows.

## Skills

- `github-release-publisher`: Prepare a local project for GitHub release, scan for sensitive information, push to GitHub, and verify the remote clone.
- `github-skill-installer-audit`: Find, inspect, install, and post-check Codex-compatible skills from GitHub.

## Install

Copy a skill directory into your Codex skills folder:

```powershell
Copy-Item -Recurse .\github-release-publisher "$HOME\.codex\skills\github-release-publisher"
Copy-Item -Recurse .\github-skill-installer-audit "$HOME\.codex\skills\github-skill-installer-audit"
```

Restart Codex after installing or updating skills.

## Verify

Validate skill metadata:

```powershell
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\github-release-publisher
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\github-skill-installer-audit
```

Run the bundled post-install checker:

```powershell
powershell -ExecutionPolicy Bypass -File ".\github-skill-installer-audit\scripts\verify-installed-skills.ps1" -SkillNames github-release-publisher,github-skill-installer-audit
```

Run the release scan:

```powershell
python ".\github-release-publisher\scripts\release_check.py" scan --root . --fail-on-placeholder
```
