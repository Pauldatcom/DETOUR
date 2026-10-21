# Contributing to DÉTOUR

This project uses GitHub Issues as the source of truth and a GitHub Projects
Kanban board for tracking. Every change starts from an issue.

## Workflow

1. An issue describes the problem or the task.
2. A branch is created for the change.
3. Commits follow the Conventional Commits format.
4. A pull request references the issue.
5. One approving review is required before merging.
6. The issue closes when the pull request merges.

## Issues

Every change must be linked to a GitHub Issue. If no issue covers your
change, create one first and describe the problem before writing code.

## Branches

Branch names use this format:

```
<type>/<issue-number>-<short-description>
```

Allowed types:

`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, `revert`

Examples:

```
feat/12-add-travel-request-form
fix/27-handle-price-changes
docs/31-document-contribution-rules
```

## Commits

Commit messages use the Conventional Commits format:

```
type(scope): imperative summary
```

Examples:

```
feat(requests): add travel request form
fix(availability): handle price changes
docs(workflow): document contribution rules
```

## Pull requests

Pull request titles follow the same Conventional Commit format.

Pull request descriptions must be written in English.

Pull requests must reference an issue with one of:

- `Closes #123`
- `Fixes #123`
- `Refs #123`

Pull request descriptions must explain:

- the problem;
- the before/after behavior;
- the affected data or flow when relevant;
- important rules or decisions;
- limitations or open questions.

The pull request template in `.github/pull_request_template.md` provides the
expected sections.

## Protected branches

The `main` branch is protected:

- direct pushes are rejected, including for administrators;
- pull requests require one approving review;
- approving reviews are kept when new commits are pushed;
- force pushes are disabled.

All changes reach `main` through a pull request.

## Local checks before opening a pull request

Run the test suites from the repository root:

```
python3 -m unittest discover -s server/tests -v
python3 -m unittest discover -s conseiller/tests -v
```

## Secrets

Never commit keys or credentials. Team keys, approval keys and API keys
belong to environment variables, not to the repository.
