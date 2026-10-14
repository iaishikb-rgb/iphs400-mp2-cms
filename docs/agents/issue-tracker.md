# Issue Tracker

Work for this project is tracked in **GitHub Issues** at https://github.com/iaishikb-rgb/iphs400-mp2-cms/issues.

## How skills use this

Engineering skills (`to-tickets`, `triage`, `to-spec`) read from and write to GitHub Issues:

- **Creating an issue**: Skills use `gh issue create` to open new issues.
- **Reading issues**: Skills use `gh issue list`, `gh issue view`, and related commands to find and read issues.
- **Labeling**: Skills apply the five triage labels (see `docs/agents/triage-labels.md`).
- **Comments**: Skills may post findings and decisions as issue comments.

## Prerequisites

The `gh` (GitHub CLI) tool must be installed and authenticated:

```bash
gh auth status
```

If not authenticated, run `gh auth login` and follow the prompts.

## See also

- Triage label vocabulary: `docs/agents/triage-labels.md`
- Domain docs and glossary: `docs/agents/domain.md`
