# Prompt for Claude Code: build the Assay frontend redesign

Paste everything below the line into Claude Code, started in `C:\src\0. personal\fyp-grading`.

---

You are implementing the frontend redesign of the FYP grading app. The product is now called **Assay** (lowercase wordmark "assay"). The design is finished and approved. Your job is to build it in `fyp-grading-frontend`, not to redesign it.

## Sources of truth, in this order

1. `PRODUCT-BRIEF.md` (in this folder): domain, roles, business rules, every screen, demo data. Business rules there win over anything in the design.
2. The design canvas: https://claude.ai/artifact/Di7AuvAGWwEF77mkzmuW87. A local copy of every board is in `design/assay-canvas/*.dc.html`, with the layout in `canvas.json`. Each file is plain HTML. The `<style>` block holds the design tokens and component styles. The `<script data-dc-script>` block holds the demo data and the interaction logic: live score, release flow, filters, rubric weight total, conflict fix, mark as read. Read these files; don't guess from screenshots.
3. This prompt: the decisions made during design that the brief doesn't cover.

## The boards and what each one specifies

| Board file | Screen | Notes |
|---|---|---|
| `Main.dc.html` | Brand and direction | Name, wordmark, palette (light and dark), type, the level mark, status chips, focus, shadcn mapping |
| `P1-Landing`, `P1-Mobile` | P1 demo landing | Persona cards link to each persona's landing screen |
| `P2-Banner` | P2 demo banner | Default, role switcher panel, in-place reset confirm, resetting, after the nightly reset |
| `P3-MyTeams`, `P3-Mobile`, `P3-States` | P3 My teams (Jane) | Loading, empty and error states |
| `P4-Grading`, `P4-Confirm`, `P4-Dark`, `P4-Mobile` | P4 grading form | Interactive. Same source file with a `CFG` line for theme, device and state |
| `P5-Overview`, `P5-Dark`, `P5-States` | P5 coordinator overview | Interactive release flow, filter tabs, live feed, toast |
| `P6-TeamDetail` | P6 Team detail (Team Beta) | Spread indicator, criterion × reviewer table, draft audit trail, conflict alert |
| `P7-Rubrics`, `P7-Edit` | P7 rubric view and editor | Tabs per assessment; editor has a live 100% check and arrow-button reorder |
| `P9-Schedule` | P9 Schedule (admin) | Day and list views, conflict banner with a one-click fix, due-date inputs |
| `P10-Notifications` | P10 bell and panel | Unread state, mark one or all as read, live note |
| `P11-Student`, `P11-Before`, `P11-Mobile` | P11 Student home (Nour) | After all five releases, and before the last one |

Not designed, so build them from the same patterns:
- P8 Teams and people: use the P6 cards and the composition-rule line.
- P12 utility pages: use the P3 and P5 empty and error patterns.
- The advisor persona's (Karim's) home: same as P3, showing one assessment per team.
- P5 on mobile: the grid scrolls horizontally inside its card.

## Stack

- The current repo uses Vite, React 18, TypeScript, MUI and react-router.
- Per the brief, move to **shadcn/ui (Radix) + Tailwind** and remove MUI. Use Recharts if you add the grade distribution chart.
- Keep Vite and react-router.

## Design tokens

Put these in CSS variables in `globals.css` (shadcn style). Use `.dark` for dark mode, and map them in `tailwind.config`. Copy the exact values from the `.t` and `.t.dark` blocks in any board.

- **Light:**
  - paper #F6F5F1, surface #FFFFFF, raised #F1F0EB
  - line #D9D6CC, line2 #B9B6AC
  - ink #1B1F24, ink2 #3B424C, muted #545B66
  - primary #1F4E8C (hover #163A69), primary-soft #EEF3FA
  - amber #94470C on #FBEEDF, amber-line #C98A4B, amber-bg #FFF9F2
  - green #1D6A4C on #E3F1EA
  - banner #1B1F24
- **Dark:** designed separately, not inverted.
  - paper #111418, surface #181C22, raised #1F242B
  - line #2E353F, line2 #4A525E
  - ink #E7E9EC, ink2 #C9CED6, muted #A3AAB5
  - primary #8DB4EE with dark text #0E1620, primary-soft #1C2A3D
  - amber #F0A65E on #33240F
  - green #6FCB9F on #11291F
- **Level fills (light):** 4 #1F3F70 (white text), 3 #44699F (white text), 2 #A9BEDD (ink text), 1 #DCE5F2 (ink text), 0 #F1F0EB with a dashed #545B66 border.
- **Level fills (dark):** 4 #B5CFF5 (dark text), 3 #6F98D6 (dark text), 2 #34507A (light text), 1 #233247 (light text), 0 transparent with a dashed #6B7380 border.
- **Type:** IBM Plex Sans (400/500/600) for text. IBM Plex Mono with tabular numbers for scores, weights, dates and outcome codes.
- **Radii:** 14 px cards, 10 px buttons and inputs, 6–8 px chips and cells, 999 px status pills.
- **Focus:** 3 px ring in the primary colour, 2–3 px offset, on every control.
- **Motion:** 150 ms colour fades and the skeleton shimmer only. All of it goes off under `prefers-reduced-motion`.

## The level mark: build it once and use it everywhere

Make a `<LevelMark level={0..4} />` component and a `<ScoreChip score={n} />` component.

- **Three cues, always together:** four ascending bars (filled count = level; empty bars are outlined, not just faded), the numeral, and the name where there's room. Colour is a fourth, redundant cue.
- **Score bands:** 0–12.4 → 0, 12.5–37.4 → 1, 37.5–62.4 → 2, 62.5–87.4 → 3, 87.5–100 → 4. Any 0–100 score uses the mark of its band.
- **Status chips (icon + word):** Not started (outlined circle), Draft (dashed primary, pencil), Submitted (green, lock), Overdue (amber, clock), "N of M submitted" (half-filled circle), Released (eye).

## Component mapping

- Level picker → Radix RadioGroup.
  - Each item is a card showing bars, numeral, name and description. Order 4 → 0, 5 columns on desktop, a vertical list on mobile.
  - Arrow keys move between levels.
  - A selected card gets the fill, a 2 px ring and a check.
- Status chips → Badge variants. Panels → Card. Assessment tabs → Tabs. Assessment rows → Accordion.
- P4 submit confirm → an inline Alert inside the sticky score panel on desktop, and a bottom-sheet confirm in the mobile score bar. The text is exactly: "Submitting locks this evaluation. You won't be able to change it."
- P5 grid → a real `<table>` of links with roving focus (arrow keys).
- Release confirm and reset confirm → inline, in place. No modals.
- Toasts → Sonner. Bell → Popover. Schedule → a custom day grid (shadcn Calendar for date pickers).

## Decisions made during design

- **"Today" in the demo is Wed 10 June 2026.**
  - Defenses run 9–11 June.
  - Due dates: Proposal 20 Feb, Progress 27 Mar, Advisor 5 Jun, Final report 12 Jun, Final presentation 12 Jun.
- **Rosters:**

  | Team | Advisor | Jury |
  |---|---|---|
  | Alpha | Emily Clark | Jane Smith, John Doe, Lea Mansour |
  | Beta | Emily Clark | Jane Smith, John Doe, Michael Johnson |
  | Gamma | Lea Mansour | Rania Haddad, Karim Nassar, Michael Johnson |
  | Delta | Karim Nassar | John Doe, Emily Clark |
  | Epsilon | John Doe | Jane Smith, Lea Mansour, Karim Nassar |
  | Zeta | Michael Johnson | Emily Clark, Lea Mansour, John Doe |

- **Defense slots** (40 minutes each):
  - Tue 9 Jun: Alpha 09:00, Amphi A · Gamma 11:00, Amphi A · Zeta 14:00, Room B-204
  - Wed 10 Jun: Epsilon 09:00, Amphi A
  - Thu 11 Jun: Beta 09:00, Amphi A · Delta 09:00, Room B-204. This is a deliberate conflict for John Doe; the fix moves Delta to 11:00.
- **Team grades:** P5's `TEAMS` array has every team's grades.
  - Alpha's final grade 88.0 = 86.7, 84.0, 90.0, 87.5 and 87.5 weighted 15/0/25/30/30.
  - Gamma's final grade is 92.2.
  - The Beta proposal has reviewer scores 85.0 / 63.8 / 73.8 (a 21.3-point spread).
  - The Delta progress report has the 35.0 outlier.
- **Per-criterion levels and comments:**
  - Alpha's final presentation, for each reviewer: P11.
  - Beta's proposal: P6.
  - Jane's Beta final report draft: P4. The draft has 8 of 13 criteria scored, 53.8 so far.
- **Students:**
  - Alpha: Nour Khoury, Rami Saade, Maya Aoun, Joe Karam.
  - Beta: Ahmad Fares, Christelle Nader, Georges Hanna, Yara Saliba.
  - Make up the other teams' students in the same style, with `@usj.edu.lb` emails.
- **Release state:**
  - Proposal and Progress: released for all six teams.
  - Advisor: Alpha and Gamma.
  - Final report: Alpha and Gamma.
  - Final presentation: Alpha.
  - The final grade is visible to students only when all five are released.
- **Weights I filled in** because the brief only says they're "in the data". Replace them with the real seed weights, and fill the rubric descriptions the P7 board marks `[seed data]` from the seed:
  - Proposal: 15/10/15/15/15/10/10/10
  - Progress report and Advisor: 20% for each criterion
- **No reopening, ever.** Grades are always the plain average, and the spread indicator is informational only. This is from the brief and stays.

## Constraints you must keep

- WCAG 2.2 AA: 4.5:1 text contrast in both themes, a visible focus ring everywhere, and 44 px minimum targets, including the banner buttons.
- Levels never rely on colour alone.
- The P4 level picker is a keyboard radio group, and the P5 grid is keyboard navigable.
- Criterion names up to ~200 characters wrap in place, with `overflow-wrap: anywhere` and no truncation.
- Mobile at 375 px must work for P1, P3, P4 (stacked levels, sticky bottom score bar) and P11 (vertical timeline).
- Every data region has a skeleton, an empty state and an error state (a plain sentence, what to do, a retry). See `P3-States` and `P5-States`.

## Suggested order

1. Tokens, fonts and Tailwind/shadcn setup. Remove MUI.
2. App shell: demo banner (P2) and header (with a nav per role), plus the `LevelMark`, `ScoreChip` and status chip components.
3. P4 grading form, the core flow, with its score maths unit-tested against the brief's example: levels 4, 3, 2 on weights 20/40/40 → 70.0.
4. P3, then P5 (with release), then P11 (before and after), then P6, P7, P9, P10 and P1.
5. Dark mode pass on P4 and P5 first, then everywhere.
6. Mobile pass.
7. Accessibility check: keyboard-only walkthrough and axe.

Work in `fyp-grading-frontend` only. It is a public repo: never commit secrets. Ask before pushing or opening a PR, one PR per repo. Start by reading the brief, `design/assay-canvas/Main.dc.html` and `P4-Grading.dc.html`, then propose the file and component structure before writing code.
