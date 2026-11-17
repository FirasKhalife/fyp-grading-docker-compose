# Assay demo seed

`generate.py` writes the demo data each service loads into a visitor's private copy:

- `fyp-grading-rubric-service/src/main/resources/demo/seed.json`: 5 rubrics
- `fyp-grading-evaluation-service/src/main/resources/demo/seed.json`: 62 submitted evaluations and 2 drafts
- `fyp-grading-admin-service/src/main/resources/demo/seed.json`: due dates, teams, students, reviewers, slots, grades, releases
- `fyp-grading-notification-service/src/main/resources/demo/seed.json`: notifications and the activity feed

Run it (standard library only, same output on every run):

```
wsl -d Ubuntu -- python3 "/mnt/c/src/0. personal/fyp-grading/fyp-grading-docker-compose/seed/generate.py"
```

It prints a verification table and stops with an error if a scoring rule breaks.
`rubric.py` holds the criteria, weights and level descriptions. `comments.py` holds the feedback text.

## Conventions

- Times: `D<+/-N> HH:MM` is N days from the anchor date (defense day 2, "today"), Europe/Paris. `N-<k>m` is k minutes before the visitor's copy is created.
- Keys such as `team:alpha` and `evaluation:beta:FINAL_REPORT:jane.smith` are strings. The services hash them per visitor. People use their fixed Keycloak ids.
- Notification and activity texts give no calendar dates ("tomorrow", "day 1 of the defense week"), because the anchor moves with the real date.

## Deviations from the design numbers

The seed weights win. Some design numbers can't be reached with them, so the nearest reachable value is used. On a tie the higher value is used.

| Where | Design | Seed | Why |
|---|---|---|---|
| Alpha Progress report (team) | 84.0 | 83.3 | Averages of three multiples of 5 |
| Beta Progress report, John Doe / Jane Smith | 72.5 / 72.5 | 75.0 / 70.0 | Step of 5. The team grade stays 70.0 |
| Beta Advisor assessment | 78.8 | 80.0 | Step of 5 |
| Gamma Proposal presentation | 90.0 | 89.6 | Needed for the final grade to show 92.2 (the search finds the closest combination) |
| Gamma Progress report | 88.8 | 88.3 | Step of 5/3 |
| Gamma Final presentation | 91.5 | 91.7 | Step of 2.5/3 |
| Delta Progress report | 58.8 (spread 47.5) | 60.0 (35.0 and 85.0, spread 50.0) | Step of 2.5 for two reviewers |
| Epsilon Progress report, Jane Smith | 76.3 | 75.0 | Step of 5. The team grade stays 75.0 |
| Epsilon Advisor assessment | 82.5 | 85.0 | Step of 5, tie goes up |
| Zeta Progress report | 77.5 | 78.3 | Step of 5/3, tie goes up |

Other changes:
- **Beta proposal levels:** P6 used placeholder weights, so the levels were re-solved for the seed weights. The three reviewer scores and the commented levels stay.
- **Alpha Final presentation timing:** it is final at D-1 11:40, before the 12:05 release. P10 showed "Yesterday 15:10", which came after the release.
- **SQL description typos fixed:** "developped", "apporpriate", "adpated", and "They had Self-initiated/Regular/No".
