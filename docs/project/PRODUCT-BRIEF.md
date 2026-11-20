# Product brief: FYP Grading (frontend redesign)

*For a designer who has never seen the code. Written 15 Nov 2026 from an audit of every repository, then updated with the owner's decisions the same day. Paste it into Claude Design as-is.*

**How to read the labels**
- **[Current]**: the code does this today, even if it's broken.
- **[Proposed]**: new for the redesign. The owner has approved everything marked proposed in this version.
- **OPEN QUESTION**: still undecided. The few that remain are in section 9.

---

## 1. What the product is

This is a web app that a university engineering department uses to grade **final-year projects** (FYP). Teams of students build a project over the year. Faculty members **review** them at five checkpoints: proposal, progress, advisor assessment, final report and final defense. Each checkpoint is scored against a **rubric**, a grid of criteria where each criterion has performance levels and a written description of each level. Today this is often done in spreadsheets and paper forms. The app gives each reviewer a guided grading form, computes the weighted scores automatically, combines several reviewers' scores into a team grade, tracks due dates and the defense schedule, and keeps coordinators, reviewers and students informed as grades become final. The main problem it solves is **consistent, traceable grading by several reviewers against a shared rubric, without manual arithmetic, with students seeing how and why they were graded**.

It is also a **public portfolio demo**. Recruiters and engineers open it from a link, pick a role, and click around for about five minutes. Each visitor gets their own private copy of the demo data (section 4.7), so they never see what another visitor did.

**Name:** the working name is "FYP Grading". The owner wants a friendlier product name. **The designer should propose 3 options** (the earlier mockups used "Defense Day" as a placeholder).

---

## 2. Domain model (in plain words)

| Concept | What it is | Relations |
|---|---|---|
| **Team** | A group of students doing one project. Has a name (e.g. "Team Alpha"), a **project title** and short description **[Proposed]**, and a final grade. | Has 3–4 students, 1–5 reviewers, one grade per assessment, one final grade, and one defense slot. |
| **Student** **[Proposed]** | A team member: name, email. | Belongs to one team. |
| **Reviewer** | A faculty member who grades: first name, last name, email. | Can be on many teams. On each team they have a role. |
| **Reviewer role on a team** | **Jury** or **Advisor**, set per team: the same person can advise Team A and sit on the jury for Team B. | Decides which assessments the reviewer grades for that team. |
| **System role** | **Admin** (the coordinator) or **Dev** (a technical account, not shown in the UI). | An admin may also be a reviewer. |
| **Assessment** | One of five fixed grading checkpoints, each with a weight in the final grade, an owning reviewer role, and a **due date** **[Proposed]**. | Has a rubric. |
| **Rubric** | The grading grid for one assessment: a list of **criteria**, each with a weight in %. The weights of one assessment add up to 100. | Each criterion has levels with descriptions. |
| **Level** | The performance scale: **Exemplary (4), Accomplished (3), Developing (2), Beginning (1)**, plus **[Proposed] Not demonstrated (0)**. | For each criterion, each level 1–4 has a written **level description** (see below). |
| **Evaluation** | One reviewer's filled-in rubric for one team and one assessment: a level and an optional **comment [Proposed]** per criterion, plus an overall comment **[Proposed]**. It's either a **draft** or **submitted** (locked for good). | Produces one score from 0 to 100. |
| **Grade** | Each reviewer's score per assessment, then the **team assessment grade** (the average of the reviewers), then the **team final grade** (the weighted sum). | |
| **Defense slot** **[Proposed]** | Date, time and room of a team's final presentation. Its jury is the team's jury members. | One per team. |
| **Notification** | A message about something that happened, e.g. "The Final report grade for Team Gamma is ready". | **[Current]**: one shared list for admins. **[Proposed]**: personal, for everyone (section 4.5). |

### What a level description is

For every criterion, the rubric spells out what the work looks like at each level. The reviewer reads the four descriptions and clicks the one that matches, instead of picking a number from a dropdown. A real example from the data (criterion "Project objectives / Expected outcomes", proposal presentation):

| Level | Description |
|---|---|
| Exemplary (4) | Students presented all the objectives of the project and set out all the outcomes with justification. |
| Accomplished (3) | Students presented the main objectives of the project and identified the main outcomes. |
| Developing (2) | *(similar sentence describing partial work)* |
| Beginning (1) | *(similar sentence describing little or no work)* |
| Not demonstrated (0) **[Proposed]** | No description needed: "Not addressed." |

### The five assessments

| Assessment | Graded by | Weight in final grade | Criteria | Level descriptions |
|---|---|---|---|---|
| Proposal presentation | Jury | 15% | 8 (objectives, recent developments, functional requirements, constraints, solution specs, future work plan, oral expression, slides) | In the data |
| Progress report | Jury | **0%** (but required; see 4.2) | 5 (meeting management, proposal report, progress report, implementation progress, motivation) | In the data |
| Advisor assessment | Advisor | 25% | 5 (learning new knowledge, teamwork, engineering practice skills, achievement of objectives, motivation and meetings) | In the data |
| Final report | Jury | 30% | 13 (objectives, related work, requirements, constraints, problem formulation, standards, alternative solutions, implementation and testing, results, conclusion, impact, written communication, referencing) | **Written for the redesign: Appendix A** |
| Final presentation | Jury | 30% | 10 (objectives, related work, requirements, constraints, alternatives, implementation and demo, results, conclusion, oral communication, slides) | **Written for the redesign: Appendix A** |

Criteria are real engineering-accreditation learning outcomes. Some carry outcome codes like "(2.1)". Criterion names can be long (up to ~200 characters).

---

## 3. Roles and permissions

| Can… | Admin (coordinator) | Jury member | Advisor | Student **[Proposed]** |
|---|---|---|---|---|
| See their own assigned teams and what they must grade, with due dates | yes, if also a reviewer | yes | yes | sees their own team's progress (what's been graded, what's next) |
| Grade an assessment for a team | only if assigned | the 4 jury assessments, for teams where they're jury | the advisor assessment, for teams they advise | — |
| Comment per criterion and overall | if grading | yes **[Proposed]** | yes **[Proposed]** | reads comments once results are released |
| Save a draft, then submit | yes | yes | yes | — |
| Reopen a submitted evaluation | **no, never** | no | no | — |
| See all teams' grades (the grade matrix) | yes | no | no | no |
| See each reviewer's breakdown for a team | yes | no | no | — |
| View rubrics, with level descriptions | yes | yes | yes | **yes [Proposed]** |
| Edit rubrics (criteria, weights, descriptions) | yes | no | no | no |
| Create teams, add students, assign reviewers and roles | **yes [Proposed]** (today only in seed data) | no | no | no |
| Set due dates and the defense schedule | **yes [Proposed]** | no | no | no |
| See the defense schedule | yes, all | their own defenses | their teams' defenses | their own team's slot |
| Release an assessment's results to students | **yes [Proposed]**, one assessment at a time | no | no | no |
| See released grades: per assessment, per criterion, with comments | yes | — | — | **their own team, released assessments only [Proposed]** |
| Receive personal notifications | yes | yes **[Proposed]** | yes **[Proposed]** | yes **[Proposed]** |

**Dev** is a technical role in the code. Leave it out of the design.

---

## 4. Business rules

### 4.1 Who grades what [Current]
- Each assessment belongs to exactly one reviewer role. Jury members grade the proposal presentation, progress report, final report and final presentation. Advisors grade the advisor assessment.
- A reviewer grades an assessment for a team only if they hold that assessment's role on that team.
- One evaluation per reviewer, per team, per assessment. **Once submitted it is locked permanently** (owner's decision: no reopening, by anyone).

### 4.2 How scores combine
1. For each criterion the reviewer picks a level: **0 to 4** **[Proposed: adds level 0]**. Every criterion must be scored before submitting.
2. **Reviewer's score** = Σ (level × criterion weight %) ÷ 4. It runs from **0** (all "Not demonstrated") to **100** (all "Exemplary"). Example: levels 4, 3, 2 on criteria weighted 20%, 40%, 40% give (80 + 120 + 80) ÷ 4 = **70.0**. *(Today the lowest possible score is 25 because level 0 doesn't exist. The owner chose to allow 0.)*
3. **Team assessment grade** = the **plain average** of all reviewers' scores. It's computed once every reviewer holding that role on the team has submitted. Before that, show "2 of 3 submitted".
4. **Team final grade** = Σ (team assessment grade × assessment weight %). It's computed once **all five** assessments are final.
5. **The progress report counts 0% but is mandatory:** the final grade can't be computed until it's submitted (owner's decision; matches the code).
6. Scores are shown to one decimal place, on 0–100.

### 4.3 Team composition **[Proposed]**
- 1 to 5 reviewers per team in total (advisors plus jury members).
- At least 1 jury member.
- At least 1 advisor (otherwise the advisor assessment could never be graded).
- 3–4 students per team in the demo data; no enforced limit.

### 4.4 Dates and states **[Proposed]**
- Each assessment has a **due date**, the same for all teams. An evaluation not submitted by then is **overdue**. Show it, but don't block grading after the date.
- Each team has a **defense slot** (date, time, room) for the final presentation.
- **Evaluation:** *not started → draft → submitted (locked)*, plus an *overdue* flag.
- **Team assessment:** *waiting (N of M submitted) → final*.
- **Team assessment (continued):** *final → released*. The coordinator releases **one assessment at a time, for all teams whose grade is final**, so students see earlier results before the next checkpoint.
- **Team:** *in progress → final grade computed → final grade visible to students* (once all five assessments are released).

### 4.5 Notifications **[Proposed]: personal, live, for every role**

| Event | Coordinator | Reviewer | Student |
|---|---|---|---|
| A team assessment grade became final | yes | yes, if on that team | no (wait for release) |
| A team's final grade is computed | yes | yes, if on that team | no |
| An assessment's results released | — | — | yes: "Your Proposal presentation results are available" |
| Due date approaching (e.g. 3 days) or overdue | summary | yes, for their own pending evaluations | — |
| Assigned to a team / role changed | — | yes | — |
| Defense slot scheduled or changed | yes | yes, if on the jury | yes |

Read state is per person (today it's shared). New notifications appear live, without reloading.

### 4.6 Known inconsistencies (being fixed; design for the intended behaviour)
- Level 3 is "Accomplished" in the data. The old UI called it "Achieved". Use **Accomplished**.
- Seed grades use a different scale from the live calculation. Everything will be 0–100.
- Login, the grading pipeline, team names in the API, rubric editing and admin-only checks are broken today and will be fixed.

### 4.7 Demo isolation and reset **[Proposed]**
- **Each visitor gets a private copy of the demo data.** On their first visit the browser receives a random **demo session ID**, stored in the browser. It's not a device fingerprint and not personal data. The first click on a persona creates a fresh copy of the seed data tagged with that ID. Every read and write is scoped to it, so two visitors never see each other's changes.
- **Switching role keeps the same copy.** A visitor can grade as Jane (jury), switch to the coordinator, and see their own submission arrive. This is the key demo moment.
- **Reset:** all visitor copies are deleted every night at **midnight (Europe/Paris)**. A visitor can also click **"Reset my demo"** at any time to get a fresh copy.
- **What the UI shows:** a banner such as "Your private demo copy · resets at midnight · Reset now". Clearing the browser's data, or opening a private window, starts a new copy. The page should say so.

---

## 5. Screens and flows

### Today's screens [Current] (for reference: all will be replaced)
| Screen | What it does today | Main problems |
|---|---|---|
| Login | Email + password + "Remember me" | Doesn't work. No product name or explanation. Generic error. |
| Home | Three grey bands of buttons: "All teams" (admin), "Team 1 / Team 2…", one button per rubric | Teams shown by number. No progress or status. Typo "Avdisor". |
| Evaluate dialog | Pop-up listing assessment buttons for a team | An extra step. No status. |
| Grading form | Criterion + weight + a dropdown (4 levels) | No level descriptions, no running score, no comments, browser `alert()` validation. |
| All teams (admin) | Text list: "Final Report (30%): 81/100" | No table, no progress, no sorting. |
| Team × assessment detail (admin) | Accordion per reviewer with criterion scores | Plain. |
| Rubric view / edit | List of criteria; the pencil opens a raw JSON text box | Not usable by a non-developer. |
| Navbar | Title, back arrow, bell (admin), account menu | Bell items all link to the same page. |

### Proposed screens

For every screen, design: **loading** (skeletons), **empty**, **error** (a plain sentence on what went wrong and what to do, with retry), and the **mobile** layout.

#### P1. Demo landing and role picker (everyone, not signed in)
- **Purpose:** explain the product in one sentence and let a visitor enter as a persona in one click.
- **Shows:** product name and pitch; persona cards (**Coordinator, Jury member, Advisor, Student**) with the person's name and 2–3 things they can try; the note "You get a private copy of the demo data. It resets at midnight."; a small "How it's built" link (architecture overview or GitHub).
- **Actions:** "Enter as …" (signs in through the real login service, no typing); a secondary "Sign in with email".
- **States:** creating your demo copy (a few seconds); sign-in service unavailable ("The demo is starting up, try again in a minute").

#### P2. Demo banner and role switcher (all signed-in screens)
- A slim banner: "Private demo · signed in as Jane Smith (Jury)", with **Switch role** (back to the four personas, same data copy), **Reset my demo** (with an in-page confirm), and the time until the nightly reset.

#### P3. My teams (reviewer home) (jury, advisor, admin if a reviewer)
- **Purpose:** "What do I need to grade, and by when?"
- **Shows:** one card or row per assigned team: name, project title, my role, next defense date; the assessments I own for it, each with a status chip (*Not started / Draft / Submitted / Overdue*), its due date, and my score if submitted. On top: "4 of 7 evaluations submitted · 1 overdue".
- **Actions:** grade, or continue a draft.
- **By role:** jury sees 4 assessments per team; advisor sees 1.
- **Empty:** "You're not assigned to any team yet. The coordinator assigns reviewers."

#### P4. Grading form (jury, advisor)
- **Purpose:** score one team on one assessment.
- **Shows:**
  - Breadcrumb and due date.
  - For each criterion: the name (possibly long), its weight %, and **the levels 4 → 0 as clickable cards showing their descriptions**.
  - A comment box per criterion, and an overall comment.
  - A sticky panel with the **live score** (0–100), a per-criterion breakdown, the assessment's weight in the final grade, and how many reviewers have submitted.
- **Actions:**
  - Pick a level per criterion.
  - Drafts autosave.
  - **Submit** needs every criterion scored, then an in-page confirm: "Submitting locks this evaluation. You won't be able to change it."
- **States:** unscored criteria highlighted; "Draft saved 2 min ago"; overdue warning; read-only after submit (with the submitted date).
- **Mobile:** criteria stacked, levels as a vertical list, score as a bottom bar.

#### P5. Coordinator overview (admin)
- **Purpose:** "Where are we, and what's blocked?"
- **Shows:**
  - KPIs: evaluations submitted / expected, overdue, final grades computed, results released, average final grade.
  - A **team × assessment grid**. Each cell shows the grade (with its level band), "2 of 3", or an overdue mark. The last column is the final grade with its release state.
  - A live **activity feed**.
- **Actions:** open a cell to see reviewer breakdowns; sort and filter; export CSV; **release an assessment's results** (e.g. "Release Proposal presentation: 5 of 6 teams final"). Released cells are marked as such.

#### P6. Team detail (admin)
- Name, project title, **students**, reviewers and roles, defense slot. Per assessment: the team grade, each reviewer's score, levels per criterion and comments. A **spread indicator** shows how far apart the reviewers' scores are (informational only; the grade is always the plain average).
- **Actions:** edit team, add or remove students, assign reviewers (enforcing 4.3), set the defense slot, release results.

#### P7. Rubrics (everyone can view; admin edits)
- **View:** one tab per assessment; a criteria × levels matrix with descriptions and weights. Students see this too.
- **Edit (admin):** add, remove or reorder criteria; edit names, weights and descriptions. A running total must equal 100% before saving. Warn if evaluations were already submitted against this rubric.

#### P8. Teams and people (admin)
- Team list (create, rename, delete); students per team; reviewer assignment with the composition rules shown inline ("4 of 5 reviewers · needs at least 1 jury member").

#### P9. Schedule **[new]**
- **Admin:** set the due date per assessment; a defense calendar (day or list view) with time, room, team and jury. Show conflicts: one reviewer in two defenses at once.
- **Reviewers:** their own defenses and upcoming due dates.
- **Students:** their own defense slot and the assessment timeline.

#### P10. Notifications (everyone)
- A bell with an unread count, and a panel listing items. Each item links to the relevant place. Mark one or all as read. New items arrive live.

#### P11. Student home **[new]** (student)
- **Shows:**
  - Team, project title, teammates, advisor and jury.
  - A **timeline** of the five assessments with due dates and status: *Upcoming / Being graded / Graded*. No scores before release.
  - The defense slot.
- **Per assessment, once released:** the grade, per-criterion levels with reviewer comments, and a link to the rubric. Each assessment unlocks on its own as it is released.
- **Not yet released:** "Results will appear here once the coordinator releases them." The final grade appears once all five are released.

#### P12. Utility pages
- Not found; no permission ("This page is for coordinators. You're signed in as a student."); session expired; demo reset in progress.

---

## 6. New or improved features (none exist today; all approved)

| Feature | For whom | Why it matters in a 5-minute demo |
|---|---|---|
| One-click persona login, private demo copy, role switcher, reset | Visitors | Quick, safe to play with, and a visitor can follow one grade from jury to student. |
| Student persona with release of results | Students, admin | Completes the story from the students' side. |
| Grading with level descriptions, level 0, live score, per-criterion comments | Reviewers | The core task becomes clear and satisfying. |
| Coordinator grid, KPIs, activity feed, release | Admin | The whole session at a glance. |
| Due dates, overdue states, defense schedule | All | Makes it feel like a real academic process. |
| Personal live notifications | All | Shows the event-driven backend working. |
| Teams, students and reviewer assignment | Admin | A coordinator can actually set up a session. |
| Proper rubric editor | Admin | Replaces raw JSON. |
| Reviewer spread indicator, grade distribution chart | Admin | A small, data-aware touch. |
| Audit trail ("Jane changed Technical depth 3 → 4" while drafting) | Admin | Traceability. |
| CSV export | Admin | Practical. |

---

## 7. Demo dataset (for realistic mock content)

**People**
- 1 coordinator (also on one jury): **Rania Haddad**.
- 6 reviewers: **Jane Smith, John Doe, Michael Johnson, Emily Clark, Karim Nassar, Lea Mansour**. Each team has 1 advisor and 2–3 jury members; most reviewers sit on 2–4 teams.
- 3–4 students per team (about 20), with names typical of a Lebanese university (seed emails are `@usj.edu.lb`).
- **Student persona:** **Nour Khoury**, Team Alpha (results released, so there's something to see).

**Release state:** proposal presentation and progress report released for all teams; advisor assessment and final report released only where final (Alpha, Gamma); final presentation released for Alpha only.

**Calendar:** a spring semester. Proposal in February, progress report in March, advisor assessment and final report in May, defenses on 9–11 June.

**Teams** (a spread of progress, so every state appears):

| Team | Project title | State in demo | Final grade |
|---|---|---|---|
| Alpha | Smart irrigation controller with soil-moisture forecasting | All graded, all **released** | 88.0 |
| Beta | Clinic queue management with SMS notifications | Final report 2 of 3 submitted, defense upcoming | pending |
| Gamma | Arabic handwriting OCR for archived documents | All graded, not yet released | 92.2 |
| Delta | Campus carpool matching app | Proposal + progress done, advisor draft **overdue** | pending |
| Epsilon | Energy monitoring dashboard for university buildings | Final presentation 1 of 3 | pending |
| Zeta | Sign-language gesture recognition on a microcontroller | All jury graded, advisor missing | pending |

**Scores:**
- Individual reviewer scores mostly 50–97, with one low outlier around 35.
- Team final grades from ~70 to ~93.
- One team where two jury members are ~20 points apart.
- Comments on about half the criteria, written like real feedback ("Chapter 4 repeats chapter 2; figures lack captions.").

**Jury persona:** Jane Smith, with 3 teams to grade: one finished, one draft, one not started.

---

## 8. Constraints for the designer

- **Audience and time:** a public portfolio demo. Recruiters and senior engineers spend about 5 minutes. The first screen must say what the product is, and every persona must reach a meaningful screen in one click.
- **Devices:** desktop first (1280–1440 px), but usable on a phone (375 px), especially the grading form, My teams and the student home. The coordinator grid may scroll horizontally on mobile.
- **Themes:** light and dark, both designed, not one inverted.
- **Accessibility:**
  - Target WCAG 2.2 AA.
  - Level and score colours never carry meaning alone: always show the level name or number too.
  - Level choices work as a keyboard radio group, and the grid is keyboard navigable.
  - Visible focus states.
  - Text contrast at least 4.5:1.
  - Touch targets at least 44 px.
  - Respect reduced motion.
- **Content realities:** criterion names up to ~200 characters; level descriptions 1–3 sentences; 5–11 criteria per assessment; scores 0–100 to one decimal.
- **Tech target:** React (TypeScript).
  - **Recommended component base: shadcn/ui on Radix primitives, with Tailwind.** It gives accessible building blocks (dialogs, menus, tabs, radio groups, calendars) whose code the team owns, so the visual style is entirely open and won't look like a stock library.
  - Charts: Recharts.
- **Visual style:** open. The earlier mockups (`phase2-proposal.html`: cool neutrals, one blue accent, the levels as a green-to-red scale) are **one reference direction, not the answer**. Those mockups also used placeholder weights; the real weights are 15/0/25/30/30.
- **Brand:** none exists. Propose a name (section 1) and a simple wordmark.

---

## 9. Decisions and remaining questions

### Decided by the owner (15 Nov 2026)
| Topic | Decision |
|---|---|
| Student persona | Yes. Students see their team, timeline, released results with comments, and the rubrics. |
| Progress report | Stays at 0%, and must be submitted before the final grade can be computed. |
| Level descriptions | Write them for the final report and final presentation too. |
| Reopening submissions | Never. |
| Combining scores | Always a plain average. |
| Score floor | Add a level 0 ("Not demonstrated") so scores run 0–100. |
| Team composition | 1–5 reviewers in total, at least 1 jury member. |
| Name | Choose a friendlier name (the designer proposes options). |
| Dates | Add due dates and a defense schedule. |
| Comments | Per criterion (plus an overall comment). |
| Notifications | For coordinators, reviewers and students. |
| Demo data | A private copy per visitor (browser-held demo session ID). All copies are wiped at midnight; "Reset my demo" on demand. |

| Advisor | Every team must have at least 1 advisor (and at least 1 jury member, 1–5 reviewers in total). |
| Release of results | **Per assessment**, as soon as it's final, so teams learn from earlier assessments before the next ones. The coordinator releases one assessment for all teams whose grade is final. The final grade is visible to students once all five assessments are released. |
| Late submissions | Allowed after the due date, marked "overdue". |

Nothing is open for the design.

---

## Appendix A. Level descriptions for the final report and final presentation [Proposed]

These were written for the redesign, in the same style as the existing descriptions, and will also go into the seed data. The criteria and weights are the real ones from the data. Level 0 ("Not demonstrated") needs no description.

### Final report (13 criteria, 100%)

| # | Criterion (weight) | Exemplary (4) | Accomplished (3) | Developing (2) | Beginning (1) |
|---|---|---|---|---|---|
| 1 | Project objectives / Outcomes (10%) | All objectives are stated clearly and measurably, and each outcome is justified and traced to the results achieved. | The main objectives and outcomes are stated clearly, with partial justification. | Objectives are stated vaguely, or several outcomes are missing. | Objectives and outcomes are barely stated or unclear. |
| 2 | Background research / Related works (10%) | Recent, relevant works are critically compared, and the gap the project fills is clearly identified. | Relevant works are described and related to the project, with limited comparison. | Few works are cited, or they are described without relating them to the project. | Little or no background research is presented. |
| 3 | Develop functional requirements by analyzing desired needs (2.1) (10%) | Functional requirements are complete, testable and clearly derived from an analysis of user needs. | The main functional requirements are identified and mostly testable. | Requirements are incomplete or not clearly linked to needs. | Requirements are missing or listed without analysis. |
| 4 | Develop technical and non-technical constraints (2.2) (10%) | Technical and non-technical constraints (cost, time, ethics, regulations) are fully identified and quantified where possible. | The main technical and non-technical constraints are identified. | Only technical constraints, or only a few constraints, are identified. | Constraints are barely mentioned. |
| 5 | Problem formulation (10%) | The problem is formulated precisely, with scope, assumptions and success criteria. | The problem is formulated clearly, with minor gaps in scope or success criteria. | The problem formulation is partial or ambiguous. | The problem is not clearly formulated. |
| 6 | Incorporate appropriate engineering standards and specifications related to the engineering design (2.3) (10%) | Relevant standards are identified, cited and explicitly applied in the design. | Relevant standards are identified and partly applied. | Standards are mentioned but not applied, or are only partly relevant. | Standards are not considered. |
| 7 | Propose multiple solutions and evaluate them against functional requirements and constraints (2.4) (10%) | Several credible alternatives are evaluated systematically (e.g. with a decision matrix) against requirements and constraints. | At least two alternatives are compared against the main requirements. | Alternatives are mentioned without a structured evaluation. | A single solution is presented with no alternatives. |
| 8 | Implement, test and iteratively improve a solution satisfying the specified functional requirements and constraints, considering risks, and making trade-offs (2.5) (5%) | The solution is fully implemented, tested against the requirements, and improved over iterations, with risks and trade-offs documented. | The solution is implemented and tested against most requirements, with some iteration. | The implementation is partial or only lightly tested. | The implementation is minimal or untested. |
| 9 | Results presentation and analysis (5%) | Results are presented clearly with appropriate figures, analysed critically, and compared with the objectives. | Results are presented clearly with some analysis. | Results are presented with little analysis. | Results are missing or unclear. |
| 10 | Conclusion and perspectives (5%) | The conclusion summarises the achievements against the objectives, discusses limitations, and proposes concrete future work. | The conclusion summarises the achievements and mentions future work. | The conclusion is generic, with little reflection. | The conclusion is missing or unrelated to the work. |
| 11 | Make informed judgments by considering the impact of engineering solutions in global, economic, environmental and societal contexts (4.2) (5%) | Impacts in all four contexts are analysed and influence design decisions. | Impacts in several contexts are discussed. | Impacts are mentioned briefly. | Impacts are not considered. |
| 12 | Demonstrate written communication skills with a range of audiences by writing adequate documents using appropriate format and language (3.1) (5%) | The report is well structured, clear and nearly error-free, and follows the required template. | The report is clear and well structured, with minor errors. | The structure is inconsistent or there are frequent language errors. | The report is hard to follow and the template is not respected. |
| 13 | Scientific referencing (5%) | All sources are cited consistently in a standard style, and the references are recent and relevant. | Sources are cited with minor inconsistencies. | Citations are incomplete or inconsistent. | Sources are missing or not cited. |

### Final presentation (10 criteria, 100%)

| # | Criterion (weight) | Exemplary (4) | Accomplished (3) | Developing (2) | Beginning (1) |
|---|---|---|---|---|---|
| 1 | Project objectives / Outcomes (10%) | Students presented all the objectives clearly and showed which outcomes were achieved, with evidence. | Students presented the main objectives and outcomes achieved. | Students presented the objectives vaguely or omitted some outcomes. | Students did not clearly present the objectives or outcomes. |
| 2 | Background research / Related works (10%) | Students positioned the project against recent related work and stated what is new. | Students summarised the relevant related work. | Students mentioned related work briefly, without positioning the project. | Students presented no related work. |
| 3 | Develop functional requirements by analyzing desired needs (2.1) (10%) | Students explained how the needs led to the requirements and showed that the requirements were met. | Students presented the main requirements and how they were met. | Students listed the requirements without linking them to the needs or results. | Students did not present the requirements. |
| 4 | Develop technical and non-technical constraints (2.2) (10%) | Students explained the key constraints and how the design respected them. | Students presented the main constraints. | Students mentioned constraints superficially. | Students did not present the constraints. |
| 5 | Propose multiple solutions and evaluate them against functional requirements and constraints (2.4) (10%) | Students justified the chosen solution through a clear comparison of alternatives. | Students compared the main alternatives briefly. | Students mentioned alternatives without evaluating them. | Students presented only one solution. |
| 6 | Implement, test and iteratively improve a solution satisfying the specified functional requirements and constraints, considering risks, and making trade-offs (2.5) (10%) | Students demonstrated a working solution (live or recorded), explained the tests and iterations, and discussed the trade-offs. | Students demonstrated a working solution and the main tests. | Students showed a partial solution or limited testing. | Students showed no working solution. |
| 7 | Results and analysis (10%) | Results were shown clearly, analysed critically, and linked to the objectives. | Results were shown clearly, with some analysis. | Results were shown with little analysis. | Results were missing or unclear. |
| 8 | Conclusion and perspectives (10%) | Students concluded with achievements, limitations and concrete next steps. | Students concluded with achievements and next steps. | The conclusion was generic. | There was no real conclusion. |
| 9 | Demonstrate oral communication skills with a range of audiences by using appropriate verbal and non-verbal language, adopting the appropriate formatting and supporting material (3.2) (10%) | The delivery was confident, clear and well timed, every member contributed, and questions were answered precisely. | The delivery was clear and mostly on time, and most questions were answered well. | The delivery was hesitant or over time, or questions were answered partially. | The delivery was hard to follow, and questions were not answered. |
| 10 | Slides quality (10%) | Slides are clear, consistent and visual, with readable figures and minimal text. | Slides are clear, with minor layout or density issues. | Slides are text-heavy or inconsistent. | Slides are hard to read or poorly organised. |
