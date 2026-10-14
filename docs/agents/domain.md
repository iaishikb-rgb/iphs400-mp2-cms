# Domain Docs & Glossary

This project uses a **single-context** layout: one shared glossary and one ADR collection at the repo root.

## Files

- **`GLOSSARY.md`** at the repo root: Project vocabulary. When new terms appear (entities, roles, workflows), add them here with definitions instead of using multiple names for the same thing.
- **`docs/adr/`**: Architecture Decision Records. When a significant technical decision is made, document it as an ADR.

## How skills use these

Engineering skills (`to-spec`, `to-tickets`, `diagnosing-bugs`, `domain-modeling`) read from and write to these files:

- **Reading the glossary**: Skills use `GLOSSARY.md` to understand project vocabulary when writing specs, tickets, or analyzing code.
- **Reading ADRs**: Skills consult `docs/adr/` to understand past decisions and constraints.
- **Writing**: Skills may add entries to `GLOSSARY.md` or suggest new ADRs when a decision needs recording.

## Consumer rules

- Whenever a ticket, spec, or ADR uses a term that could be ambiguous, **check `GLOSSARY.md` first** and use the term as defined there.
- If a better word appears, **update `GLOSSARY.md`** rather than using both names.
- If a technical decision is non-obvious or has implications, **consider an ADR** rather than only documenting it in code.

## Single vs. multi-context

This repo is **single-context** (one app, one codebase, one glossary). If it becomes a monorepo with multiple packages, this should be updated to multi-context:

- Upgrade `GLOSSARY.md` to `GLOSSARY-MAP.md` pointing to per-package glossaries.
- Create `packages/<pkg>/docs/adr/` alongside the root `docs/adr/`.
- Update this file to reflect the change.

## See also

- Triage labels and issue tracker: `docs/agents/issue-tracker.md`
- Triage label vocabulary: `docs/agents/triage-labels.md`
