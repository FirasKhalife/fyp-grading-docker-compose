# Project documents

How Assay got from a final-year-project codebase to a live portfolio demo: the product decisions, the hosting
study and the redesign. The code lives in the `fyp-grading-*` repositories; these documents explain why it looks the
way it does.

| Document | What it is |
|---|---|
| [PRODUCT-BRIEF.md](PRODUCT-BRIEF.md) | The product: domain, roles, business rules, every screen (P1–P12) and the demo data. Its business rules win over anything else |
| [DECISIONS.md](DECISIONS.md) | The decisions that shape the demo: hosting, public repos, demo personas |
| [PHASE1-REPORT.md](PHASE1-REPORT.md) | Phase 1, hosting feasibility: memory measurements of the whole stack and the host comparison |
| [phase1-measurement/](phase1-measurement/) | The raw data and scripts behind the Phase 1 report |
| [phase2-proposal.html](phase2-proposal.html) | The approved Phase 2 plan: roadmap, work items and effort |
| [DESIGN-HANDOFF-PROMPT.md](DESIGN-HANDOFF-PROMPT.md) | The design handoff: tokens, the level mark, the component mapping and the build order |
| [design/assay-canvas/](design/assay-canvas/) | A copy of every board of the Assay design canvas (plain HTML) |

The API contract shared by the frontend and the services is [`../../contract/openapi.yaml`](../../contract/openapi.yaml).
