# Triage Labels

This project uses five canonical triage labels. Each label represents one step in the triage workflow.

## Label vocabulary

| Label | Meaning | When to apply |
|-------|---------|---------------|
| `needs-triage` | Issue awaits initial review | New issues, unclear scope |
| `needs-info` | Blocked; waiting for more information | Missing details, unclear requirements |
| `ready-for-agent` | Issue is well-scoped and ready for agent implementation | Clear spec, acceptance criteria defined |
| `ready-for-human` | Agent work is done; needs human review or merge | PR ready, code complete, tests passing |
| `wontfix` | Issue will not be addressed | Out of scope, duplicate, won't fix |

## How the triage skill uses these

The `triage` skill reads these labels to understand which issues are ready for different kinds of work:

- Issues labeled `ready-for-agent` are candidates for agent implementation.
- Issues labeled `ready-for-human` are waiting in the human review queue.
- Issues labeled `needs-info` or `needs-triage` are skipped by automatic workflows.

## Creating labels

If the labels don't exist in GitHub, the setup will create them automatically. Otherwise, they must exist for the triage skill to function correctly.

## See also

- Issue tracker configuration: `docs/agents/issue-tracker.md`
- Domain docs and glossary: `docs/agents/domain.md`
