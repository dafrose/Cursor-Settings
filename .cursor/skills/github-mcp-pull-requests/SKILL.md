---
name: github-mcp-pull-requests
description: >-
  Creates, updates, discovers, and inspects GitHub pull requests via GitHub MCP
  (call_mcp_tool). Use when the user wants a PR opened or edited without the gh
  CLI, says "GitHub MCP" and pull request, or asks to draft PR titles/bodies before
  or after creation.
---

# GitHub MCP — pull requests

Use **`call_mcp_tool`** with the workspace GitHub MCP server id (commonly **`user-github`**; the IDE may label it **github**). If a call fails with "unknown tool" or invalid arguments, the server id or tool surface changed—use the name Cursor lists for the GitHub MCP server.

## Resolve `owner` and `repo`

1. Run `git remote get-url origin` in the relevant clone and parse `github.com/<owner>/<repo>` (strip `.git` and optional trailing `/`).
2. If the user names `owner/repo` explicitly, use that.

## Before creating a PR

1. Confirm **`head`** exists on GitHub (pushed). Same-repo PRs fail if the branch only exists locally.
2. Optionally avoid duplicates: **`list_pull_requests`** with `base` / `head`, or **`search_pull_requests`** with a scoped `query` (see below).
3. Gather a good **title** and **body**: `git log <base>..<head> --oneline`, diff summary, linked issues. Align with team conventions (e.g. Conventional Commits for the title when the project uses them).

## `head` branch format

| Case | `head` value |
| ---- | -------------- |
| Branch lives on the same repo as `base` | Branch name only, e.g. `feature/foo` |
| Head is on a **fork** | `forkowner:branch`, e.g. `contributor:patch-1` |

`base` is always the branch name on the target repo (e.g. `main`, `develop`, `version-15`).

## Tool reference (arguments)

### `create_pull_request`

| Argument | Required | Notes |
| -------- | -------- | ----- |
| `owner`, `repo` | yes | Target repository (where the PR opens) |
| `title` | yes | PR title |
| `head` | yes | Head branch (see table above) |
| `base` | yes | Branch to merge into |
| `body` | no | Markdown description |
| `draft` | no | `true` for draft PR |
| `maintainer_can_modify` | no | Allow upstream edits to the PR branch (fork PRs) |

Response includes PR **`url`** and numeric id metadata—surface the **URL** to the user.

### `update_pull_request`

| Argument | Required | Notes |
| -------- | -------- | ----- |
| `owner`, `repo` | yes | |
| `pullNumber` | yes | PR number |
| `title`, `body` | no | Replace title/description |
| `base` | no | Change base branch |
| `state` | no | `open` or `closed` |
| `draft` | no | `true` / `false` |
| `reviewers` | no | Array of GitHub usernames (review requests) |
| `maintainer_can_modify` | no | |

### `pull_request_read`

| Argument | Required | Notes |
| -------- | -------- | ----- |
| `method` | yes | One of: `get`, `get_diff`, `get_status`, `get_files`, `get_review_comments`, `get_reviews`, `get_comments`, `get_check_runs` |
| `owner`, `repo`, `pullNumber` | yes | |
| `page`, `perPage` | no | Pagination where applicable (`perPage` 1–100, `page` ≥ 1) |

- **`get`**: metadata (head/base, state, mergeable, etc.).
- **`get_diff`**: patch text for summarizing or reviewing.
- **`get_files`**: changed paths (paginated).
- **`get_comments`**: issue-style timeline comments (not inline review threads).
- **`get_review_comments`**: review threads on code (paginated with cursor `after` when the tool supports it per server version).
- **`get_reviews`**: submitted reviews (APPROVED/COMMENTED/CHANGES_REQUESTED).
- **`get_status`**: combined commit status on head.
- **`get_check_runs`**: CI check runs on head.

### `list_pull_requests`

| Argument | Required | Notes |
| -------- | -------- | ----- |
| `owner`, `repo` | yes | |
| `state` | no | `open`, `closed`, or `all` |
| `base`, `head` | no | Filters; `head` is user/org **and** branch per GitHub API shape |
| `sort`, `direction` | no | `created` / `updated` / `popularity` / `long-running`; `asc` / `desc` |
| `page`, `perPage` | no | |

**Note:** If the user specifies an **author**, do **not** use `list_pull_requests`—use **`search_pull_requests`** instead (per tool description).

### `search_pull_requests`

| Argument | Required | Notes |
| -------- | -------- | ----- |
| `query` | yes | GitHub search syntax; tool is already scoped to **pull requests** |
| `owner`, `repo` | no | Restrict to one repository when both set |
| `sort`, `order`, `page`, `perPage` | no | |

Example scoped query shape: keywords plus `repo:owner/name` and filters such as `is:open`, `head:branch`, `base:main`, `author:login`.

## PR description (body) checklist

Use Markdown. Suggested sections (omit empty):

- **Summary** — what changes and why merge now.
- **How to test** — commands or QA steps.
- **Risk / rollout** — migrations, feature flags, backwards compatibility.
- **Links** — issues or prior PRs (full `https://github.com/...` URLs).

**Security:** never put tokens, passwords, or private site names in titles or bodies; use generic examples.

## Timeline comments on a PR

For a normal PR conversation comment (not an inline review), use **`add_issue_comment`** from the issues tool surface with the same **`owner`**, **`repo`**, and **`issue_number` = PR number** (GitHub unifies PRs and issues by number). For review-specific writes, use the server's **`pull_request_review_write`** / reply tools if present and read their schemas before calling.

## Minimal `create_pull_request` shape

```json
{
  "server": "user-github",
  "toolName": "create_pull_request",
  "arguments": {
    "owner": "OWNER",
    "repo": "REPO",
    "title": "feat(scope): short imperative title",
    "head": "feature-branch",
    "base": "main",
    "body": "## Summary\n\n…"
  }
}
```

## Related

- Issue-only workflows (labels, milestones, sub-issues): **`github-mcp-issues`** skill.
