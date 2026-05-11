---
name: github-mcp-issues
description: >-
  Creates, updates, lists, searches, reads, comments on, and nests GitHub issues
  via the GitHub MCP (call_mcp_tool). Use when the user wants GitHub issues/PR
  comments without the gh CLI, or says "GitHub MCP", "create issues", "sub-issues",
  or "track in GitHub".
---

# GitHub MCP — issue interactions

Use **`call_mcp_tool`** with the workspace GitHub MCP server id (commonly **`user-github`**; UI may show **github**). If a call fails with “unknown tool” or “invalid arguments”, the server id or tool surface changed—retry with the server name Cursor lists for GitHub MCP.

**Parameters**: use the tables in this file only—do not read MCP tool descriptor files on disk.

## Pick the right MCP server first

Before calling any tool, verify which GitHub MCP servers are actually available in this workspace (look at the MCP server folders Cursor lists). Don't assume `user-github` exists.

- If exactly one GitHub MCP server is available, use it.
- If **more than one** is available (e.g. one per identity/org such as `user-github-<org>` and `user-github-<personal>`), do not guess: use the **AskQuestion** tool to let the user pick the server whose token can access the target `owner/repo`.
- If the user already named the server in the request, trust that and skip the question.
- Stick with the chosen server id for the rest of the task.

Same rule applies to the sibling **`github-mcp-pull-requests`** skill.

## Resolve `owner` and `repo`

- Prefer `git remote get-url origin` and parse `github.com/<owner>/<repo>.git` (strip `.git`).
- If the user names a repo explicitly, use that.

## Tool reference (arguments)

### `issue_write` — create or update one issue

| Argument        | Required                      | Notes                                                                                |
| --------------- | ----------------------------- | ------------------------------------------------------------------------------------ |
| `method`        | yes                           | `create` or `update`                                                                 |
| `owner`, `repo` | yes                           | Repository                                                                           |
| `title`         | create (required in practice) | Issue title                                                                          |
| `body`          | no                            | Markdown body (recommended)                                                          |
| `issue_number`  | update                        | Issue to change                                                                      |
| `labels`        | no                            | Array of label names                                                                 |
| `assignees`     | no                            | Array of GitHub usernames                                                            |
| `milestone`     | no                            | Milestone **number** (not title)                                                     |
| `type`          | no                            | Issue type string; only if org/repo supports types (discover via `list_issue_types`) |
| `state`         | no                            | `open` or `closed`                                                                   |
| `state_reason`  | with close                    | `completed`, `not_planned`, or `duplicate`                                           |
| `duplicate_of`  | no                            | Issue **number** when closing as `duplicate`                                         |

**Create response**: keep numeric **`id`** (database id) for **`sub_issue_write`**; **`number`** is the visible `#issue`.

### `issue_read` — one issue

| Argument          | Required | Notes                                                    |
| ----------------- | -------- | -------------------------------------------------------- |
| `method`          | yes      | `get`, `get_comments`, `get_sub_issues`, or `get_labels` |
| `owner`, `repo`   | yes      |                                                          |
| `issue_number`    | yes      |                                                          |
| `page`, `perPage` | no       | Pagination for comments/labels (`perPage` 1–100)         |

- **`get`**: full issue payload (includes `id`, `number`, `body`, state, …).
- **`get_sub_issues`**: child issues (each includes `id` and `number`).
- **`get_comments`** / **`get_labels`**: paginated lists.

### `list_issues` — many issues in one repo

| Argument        | Required | Notes                                                                                            |
| --------------- | -------- | ------------------------------------------------------------------------------------------------ |
| `owner`, `repo` | yes      |                                                                                                  |
| `state`         | no       | `OPEN` or `CLOSED`; omit for both                                                                |
| `labels`        | no       | Array of label names                                                                             |
| `since`         | no       | ISO 8601 timestamp filter                                                                        |
| `orderBy`       | no       | `CREATED_AT`, `UPDATED_AT`, or `COMMENTS` — if set, **`direction`** is required (`ASC` / `DESC`) |
| `perPage`       | no       | 1–100                                                                                            |
| `after`         | no       | Pagination cursor from previous response `pageInfo.endCursor`                                    |

### `search_issues` — GitHub issue search

| Argument          | Required | Notes                                                                 |
| ----------------- | -------- | --------------------------------------------------------------------- |
| `query`           | yes      | Issue search syntax (tool is scoped to **issues**, not PR-only lists) |
| `owner`, `repo`   | no       | Restrict to one repo                                                  |
| `sort`            | no       | e.g. `created`, `updated`, `comments`, `reactions`, …                 |
| `order`           | no       | `asc` or `desc`                                                       |
| `page`, `perPage` | no       | Pagination                                                            |

### `add_issue_comment` — timeline comment

| Argument        | Required | Notes                                                            |
| --------------- | -------- | ---------------------------------------------------------------- |
| `owner`, `repo` | yes      |                                                                  |
| `issue_number`  | yes      | For a PR, use the **PR number** (same as issue number on GitHub) |
| `body`          | yes      | Markdown                                                         |

Not for inline **review** threads; use normal review tools/workflows for those.

### `sub_issue_write` — parent/child links

| Argument                 | Required                | Notes                                                        |
| ------------------------ | ----------------------- | ------------------------------------------------------------ |
| `method`                 | yes                     | `add`, `remove`, or `reprioritize`                           |
| `owner`, `repo`          | yes                     |                                                              |
| `issue_number`           | yes                     | **Parent** issue `#`                                         |
| `sub_issue_id`           | add/remove/reprioritize | Child issue’s numeric **database `id`**, **not** `number`    |
| `replace_parent`         | no                      | Boolean; **`add` only** — move child from another parent     |
| `after_id` / `before_id` | reprioritize            | Child **`id`** to insert after/before (use **one** of these) |

**Critical**: `sub_issue_id` is the **`id`** field from **`issue_write`** (create) or **`issue_read`** `get` / `get_sub_issues` — not the GitHub `#n`.

**Workflow**: create parent → create children → `sub_issue_write` with `method: "add"` for each child **`id`**.

### `list_issue_types` — org issue types

| Argument | Required | Notes                                                    |
| -------- | -------- | -------------------------------------------------------- |
| `owner`  | yes      | **Organization** login that owns repos with typed issues |

Pass `type` on **`issue_write` create** only when this applies to the target repo.

## Practices

- **Titles**: follow team conventions (e.g. Conventional Commits prefixes like `feat(scope): …` if the project uses them for issues).
- **Bodies**: link related issues with full GitHub URLs; include acceptance criteria and dependencies.
- **Epics**: optional parent issue + **sub-issues** for vertical slices (schema / API / UI); avoids one unreadable mega-issue.
- **Security**: never paste tokens or secrets into issue bodies; use abstract examples.

## Minimal examples (shape only)

Create:

```json
{
  "server": "user-github",
  "toolName": "issue_write",
  "arguments": {
    "method": "create",
    "owner": "ORG",
    "repo": "REPO",
    "title": "feat(scope): short title",
    "body": "## Scope\n\n…"
  }
}
```

Add sub-issue (after you know child database `id`):

```json
{
  "server": "user-github",
  "toolName": "sub_issue_write",
  "arguments": {
    "method": "add",
    "owner": "ORG",
    "repo": "REPO",
    "issue_number": 6,
    "sub_issue_id": 4301416013
  }
}
```

Close as completed:

```json
{
  "server": "user-github",
  "toolName": "issue_write",
  "arguments": {
    "method": "update",
    "owner": "ORG",
    "repo": "REPO",
    "issue_number": 6,
    "state": "closed",
    "state_reason": "completed"
  }
}
```
