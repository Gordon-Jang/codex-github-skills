# Release Checklist

Use this checklist for GitHub publishing tasks.

## Scope

- Confirm release root.
- Confirm files intentionally included.
- Confirm generated/local files excluded.
- Confirm no unrelated project folders are included.

## Documentation

- README includes install/configure/use/verify.
- LICENSE is standard or intentionally omitted.
- .gitignore excludes local state.
- Examples use placeholders or empty values, not realistic secrets.

## Desensitization

- Run local scan before packaging.
- Run scan before push.
- Clone remote and run scan again.
- Include task-specific extra patterns.

## GitHub

- `gh auth status` matches expected account.
- `git config user.name` and `git config user.email` match expected author.
- remote URL points to intended owner/repo.
- latest remote commit author is correct.

## Verification

- Clone from GitHub into a temporary directory.
- Run smoke test or install test when possible.
- Report commit SHA and check results.
