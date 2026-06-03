---
name: github-release-publisher
description: Prepare a local project for GitHub release by dynamically detecting project scope, organizing release documentation, checking packaging boundaries, scanning for sensitive information, pushing to GitHub, then cloning the remote repository back to verify desensitization and completeness. Use when the user asks to publish, open source, package, sanitize, upload, push, or verify a GitHub release.
---

# GitHub Release Publisher

Use this skill to publish a project to GitHub with explicit scope control and repeatable desensitization checks.

Do not hardcode user names, project paths, GitHub accounts, repository names, emails, API gateways, or secrets. Detect them at runtime or ask the user.

## Workflow

1. Determine project scope.
2. Organize project documentation.
3. Package or stage release files.
4. Run local desensitization before packaging.
5. Run desensitization again immediately before upload.
6. Push to GitHub.
7. Clone the remote repository into a temporary directory.
8. Run remote desensitization and completeness validation.
9. Report exact commit, URL, checks, and remaining risks.

## Release Modes

Use the smallest release root that matches the user's request.

- Existing repository release: publish from the detected git root when the whole repository belongs in the release.
- Subset release: create a clean staging directory when only selected folders or files should be published.
- New repository release: initialize git in the staging directory or project root only after confirming the release boundary.

For subset releases, copy only the intended public files into staging, then run every scan against staging. Do not publish a parent directory just because it contains the requested files.

## 1. Determine Project Scope

Detect the candidate root:

```powershell
git rev-parse --show-toplevel
```

If this fails, use the current directory as the candidate root and ask before running `git init`.

When the candidate root contains multiple unrelated projects, user profile files, installed skills, caches, or private notes, treat it as unsafe for direct publishing. Build a staging directory instead.

Before packaging, identify exclusions:

- `.env`
- `.venv/`
- `__pycache__/`
- `.git/`
- `node_modules/`
- build artifacts
- local test outputs
- archives containing private state
- project-specific paths or names the user wants removed

Do not assume the whole current directory should be published if it contains unrelated files.

Record the intended release tree before committing:

```powershell
python <skill-dir>\scripts\release_check.py tree --root <release-root>
```

## 2. Organize Documentation

Minimum release docs:

- `README.md`: what the project is, install, configure, use, verify
- `LICENSE`: standard license if the user wants open-source licensing
- `.gitignore`: excludes local secrets and generated files
- Optional `docs/`: configuration, publishing, architecture, usage examples

Keep docs factual. Avoid unverifiable claims, invented affiliations, generated-sounding praise, or personal/project-specific residue unless the user explicitly wants it public.

## 3. Desensitization Checks

Use the bundled script:

```powershell
python <skill-dir>\scripts\release_check.py scan --root <release-root>
```

The script scans for common credentials, private keys, local paths, sensitive file names, project-specific terms, `.env`, `.venv`, and cache directories. Add extra terms from the current task with `--extra-pattern`, and add exact sensitive file names with `--extra-sensitive-name`.

The script redacts matched values in output. Treat every finding as real until inspected.

Examples:

```powershell
python <skill-dir>\scripts\release_check.py scan --root . --extra-pattern "internal-project-name"
python <skill-dir>\scripts\release_check.py scan --root . --extra-sensitive-name "local-config.json"
python <skill-dir>\scripts\release_check.py scan --root . --fail-on-placeholder
```

Run this twice:

- before final packaging/staging
- immediately before `git push`

If findings appear, fix them and rerun the scan.

## 4. GitHub Identity and Remote

Detect GitHub CLI login:

```powershell
gh auth status
gh api user --jq "{login:.login,name:.name,email:.email,id:.id}"
```

Set local Git author from detected identity. If public email is missing, use GitHub noreply format:

```text
<id>+<login>@users.noreply.github.com
```

Never use stale global Git identity without checking.

Detect remote:

```powershell
git remote -v
```

If no remote exists and the user already approved repository name and visibility, create it with GitHub CLI:

```powershell
gh repo create <repo-name> --private --source . --remote origin
```

Use `--public` only when the user explicitly requested a public repository. If the remote owner differs from the authenticated account, confirm before replacing it.

## 5. Commit and Push

Standard path:

```powershell
git status --short
git add -A
git commit -m "Initial release"
git push -u origin main
```

If the repository has no commits yet, make the initial commit after scans pass. If the current branch is not `main`, rename it only for a new repository or when the user asked for `main`.

If there is existing history and the user wants a clean single release commit, explain that this rewrites history and ask for confirmation before:

```powershell
git checkout --orphan clean-main
git add -A
git commit -m "Initial release"
git branch -M main
git push --force-with-lease origin main
```

Do not rewrite remote history without explicit user approval.

## 6. Remote Verification

After push, clone the remote repository into a temporary directory:

```powershell
git clone --depth 1 <repo-url> <temp-dir>
```

Run:

```powershell
python <skill-dir>\scripts\release_check.py scan --root <temp-dir>
python <skill-dir>\scripts\release_check.py scan --root <temp-dir> --fail-on-placeholder
python <skill-dir>\scripts\release_check.py tree --root <temp-dir>
```

Also verify the latest commit:

```powershell
gh api repos/<owner>/<repo>/commits/main --jq "{sha:.sha[0:7], author:.commit.author.name, email:.commit.author.email, message:.commit.message}"
```

If remote scan fails, fix locally, commit, push, and repeat remote verification.

## Reporting

Final response must include:

- GitHub URL
- latest commit short SHA
- local scan result
- pre-push scan result
- remote clone scan result
- install or smoke-test result if performed
- any known limitations
