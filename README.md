# Codex GitHub Skills

This repository contains two Codex skills for GitHub-oriented workflows.

## Project status

This repository is now a mixture of one workflow that is still useful and one workflow that has been largely overtaken by better tooling.

If I were starting from scratch today, I would **not build a general GitHub integration layer this way**.

### What has become outdated

`github-skill-installer-audit` is the part that has aged the most.

It searches GitHub, inspects repositories, checks `SKILL.md`, installs a skill, verifies files and dependencies, and uses `gh` / GitHub API calls as the transport. That made sense when GitHub access from coding agents was fragmented. It is much less compelling now.

The main problems are:

- GitHub already maintains the official [GitHub MCP Server](https://github.com/github/github-mcp-server), which gives agents a maintained GitHub integration instead of requiring every skill to wrap `gh api` or REST calls again.
- Modern agent environments can often search, read, create, and update GitHub content through a native connector or MCP server. Re-implementing that transport inside a skill adds maintenance without adding much capability.
- Repository star count is only a rough popularity signal. It is not a security review and should never be treated as one.
- GitHub repository layout, skill conventions, installer locations, and agent tooling evolve. A skill that hard-codes local installation behavior will require periodic repairs.
- "Download it, inspect a few files, then run its installer" is still a supply-chain risk. The audit reduces obvious mistakes but cannot prove that a third-party skill is safe.
- The workflow is verbose for normal installs. For a well-known official skill, the checks can cost more effort than the installation itself.

For those reasons, `github-skill-installer-audit` should be viewed as a conservative historical workflow or a manual audit checklist, not as the preferred GitHub integration architecture.

### Better approaches now

For normal GitHub work:

- Use the official [GitHub MCP Server](https://github.com/github/github-mcp-server) or a trusted native GitHub connector for repository operations.
- Use the agent environment's built-in skill installer when one is available instead of maintaining another installer wrapper.
- For third-party skills, inspect the source and permissions, pin a commit or release when reproducibility matters, and run untrusted code in an isolated environment.
- Use GitHub Actions, Dependabot, secret scanning, code scanning, release workflows, and repository protections for checks that belong on the repository side instead of trying to put every check into a Codex skill.

### The part that is still useful

`github-release-publisher` is different.

The useful idea is not "Codex can push to GitHub". There are already much better ways to push to GitHub.

The useful part is the release procedure:

1. Decide exactly which files are supposed to become public.
2. Scan the local release tree for secrets, private paths, placeholders, and accidental files.
3. Scan again immediately before upload.
4. Push the repository.
5. Clone the public remote into a clean temporary directory.
6. Scan the clone again and verify what was actually published.

That last remote-clone verification is intentionally redundant. It catches mistakes that a successful `git push` does not catch, such as publishing the wrong tree, forgetting an ignored/generated file boundary, or assuming the remote contains what the local working directory contains.

A GitHub MCP server can perform repository operations, but it does not automatically impose this release discipline for you.

### What is different about this repository?

This repo is intentionally procedural rather than magical.

- `github-skill-installer-audit` prefers inspection before execution and records why a source was selected.
- It treats missing dependencies and metadata problems as explicit audit findings instead of silently installing everything.
- `github-release-publisher` treats **release scope** as a first-class problem. It can stage only a subset instead of blindly publishing the current directory.
- It performs **local scan -> pre-push scan -> remote clone scan**, which is more paranoid than a normal publish workflow.
- It tries to leave an auditable explanation of what was installed or published instead of only reporting "success".

### If you still choose to use it

Use this repository if you specifically want a slow, explicit, inspect-first workflow and you are willing to accept duplicated GitHub tooling in exchange for a checklist you can read and modify.

The installer audit can still be useful when you are evaluating small or unfamiliar third-party skills and you want the process to force you to look at metadata, files, dependencies, and source before execution.

The release publisher is more defensible: if you frequently open-source local projects that may contain private paths, credentials, test artifacts, or unrelated files, the extra scans and remote re-clone are useful even when GitHub access itself is handled by MCP or another connector.

If you only need ordinary GitHub operations or ordinary skill installation, use the official/native tooling instead.

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
