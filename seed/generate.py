#!/usr/bin/env python3
"""Deterministic demo-seed generator for Assay (FYP grading).

Writes src/main/resources/demo/seed.json for the rubric, evaluation, admin and
notification services, then prints a verification table and asserts the
scoring rules. Standard library only. Same output on every run.

Times are relative strings:
  "D<+/-N> HH:MM"  N days from the anchor date (defense day 2, "today"), Europe/Paris.
  "N-<k>m"         k minutes before the visitor's copy is created.
"""
import json
import os
import random
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

from comments import FLAVOUR, OVERALL, TEMPLATES
from rubric import (ASSESSMENT_NAMES, ASSESSMENT_ROLE, ASSESSMENT_WEIGHTS, ASSESSMENTS,
                    RUBRICS, THEMES)

HERE = os.path.dirname(os.path.abspath(__file__))
# The service repos sit next to this one. ASSAY_WORKSPACE overrides it (CI writes to a scratch folder).
ROOT = os.environ.get("ASSAY_WORKSPACE") or os.path.dirname(os.path.dirname(HERE))

PROP, PROG, ADV, FR, FP = ASSESSMENTS

# ---------------------------------------------------------------- people
PEOPLE = {
    "rania.haddad": ("Rania Haddad", "00000000-0000-4000-a000-000000000001"),
    "jane.smith": ("Jane Smith", "00000000-0000-4000-a000-000000000002"),
    "john.doe": ("John Doe", "00000000-0000-4000-a000-000000000003"),
    "michael.johnson": ("Michael Johnson", "00000000-0000-4000-a000-000000000004"),
    "emily.clark": ("Emily Clark", "00000000-0000-4000-a000-000000000005"),
    "karim.nassar": ("Karim Nassar", "00000000-0000-4000-a000-000000000006"),
    "lea.mansour": ("Lea Mansour", "00000000-0000-4000-a000-000000000007"),
}
NOUR_ID = "00000000-0000-4000-a000-000000000101"   # student persona, Team Alpha: every result released
AHMAD_ID = "00000000-0000-4000-a000-000000000102"  # student persona, Team Beta: waiting on results


def uid(u):
    return PEOPLE[u][1]


def pname(u):
    return PEOPLE[u][0]


# ---------------------------------------------------------------- time helpers
NOW_REF = 12 * 60 + 28  # only used to order "N-" times against "D" times (design "now" ~ 12:28 today)


def D(n, hm):
    return "D%+d %s" % (n, hm)


def N(k):
    return "N-%dm" % k


def tmin(t):
    if t.startswith("N-"):
        return NOW_REF - int(t[2:-1])
    day, hm = t[1:].split(" ")
    h, m = hm.split(":")
    return int(day) * 1440 + int(h) * 60 + int(m)


def shift(t, d):
    """Move time t by d minutes (negative = earlier)."""
    if t.startswith("N-"):
        k = int(t[2:-1]) - d
        assert k > 0
        return N(k)
    m = tmin(t) + d
    day, rem = divmod(m, 1440)
    return D(day, "%02d:%02d" % divmod(rem, 60))


def is_today(t):
    return tmin(t) >= 0


# ---------------------------------------------------------------- numbers
def disp(x):
    """Display to 1 decimal, HALF_UP, from the exact value."""
    x = F(x)
    return str((Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def num(x):
    x = F(x)
    v = float(x)
    assert F(v) == x, x  # every stored score is a multiple of 1.25, exact in binary
    return v


# ---------------------------------------------------------------- teams
def student(slug, first, last, user_id=None):
    s = (first + "-" + last).lower().replace(" ", "")
    return {"key": "student:%s:%s" % (slug, s), "firstName": first, "lastName": last,
            "email": "%s.%s@usj.edu.lb" % (first.lower(), last.lower().replace(" ", "")), "userId": user_id}


TEAMS = [
    dict(slug="alpha", name="Alpha", title="Smart irrigation controller with soil-moisture forecasting",
         desc="A solar-powered field node that reads soil-moisture probes and forecasts the next 48 hours, so crops are watered only when they need it.",
         advisor="emily.clark", jury=["jane.smith", "john.doe", "lea.mansour"],
         students=[("Nour", "Khoury", NOUR_ID), ("Rami", "Saade"), ("Maya", "Aoun"), ("Joe", "Karam")],
         slot=(D(-1, "09:00"), "Amphi A")),
    dict(slug="beta", name="Beta", title="Clinic queue management with SMS notifications",
         desc="A web queue for outpatient clinics that texts patients when their turn is near, so they can wait outside the crowded waiting room.",
         advisor="emily.clark", jury=["jane.smith", "john.doe", "michael.johnson"],
         students=[("Ahmad", "Fares", AHMAD_ID), ("Christelle", "Nader"), ("Georges", "Hanna"), ("Yara", "Saliba")],
         slot=(D(1, "09:00"), "Amphi A")),
    dict(slug="gamma", name="Gamma", title="Arabic handwriting OCR for archived documents",
         desc="A recognition pipeline that turns scanned, handwritten Arabic registry pages into searchable text for a municipal archive.",
         advisor="lea.mansour", jury=["rania.haddad", "karim.nassar", "michael.johnson"],
         students=[("Hadi", "Chamoun"), ("Lara", "Rizk"), ("Elie", "Tannous"), ("Tala", "Sfeir")],
         slot=(D(-1, "11:00"), "Amphi A")),
    dict(slug="delta", name="Delta", title="Campus carpool matching app",
         desc="A mobile app that matches students and staff who drive to campus at similar times from nearby neighbourhoods.",
         advisor="karim.nassar", jury=["john.doe", "emily.clark"],
         students=[("Karl", "Mouawad"), ("Rita", "Khalil"), ("Fadi", "Azar")],
         slot=(D(1, "09:00"), "Room B-204")),
    dict(slug="epsilon", name="Epsilon", title="Energy monitoring dashboard for university buildings",
         desc="A dashboard that collects meter readings from campus buildings over Modbus and flags abnormal consumption to facility managers.",
         advisor="john.doe", jury=["jane.smith", "lea.mansour", "karim.nassar"],
         students=[("Jad", "Frem"), ("Nadine", "Moussa"), ("Charbel", "Daou"), ("Lynn", "Harb")],
         slot=(D(0, "09:00"), "Amphi A")),
    dict(slug="zeta", name="Zeta", title="Sign-language gesture recognition on a microcontroller",
         desc="A sensor glove whose microcontroller recognises Arabic sign-language letters on-device and speaks them through a paired phone.",
         advisor="michael.johnson", jury=["emily.clark", "lea.mansour", "john.doe"],
         students=[("Marc", "Chidiac"), ("Celine", "Eid"), ("Omar", "Itani")],
         slot=(D(-1, "14:00"), "Room B-204")),
]
TEAM = {t["slug"]: t for t in TEAMS}


def holders(slug, a):
    t = TEAM[slug]
    return [t["advisor"]] if ASSESSMENT_ROLE[a] == "ADVISOR" else list(t["jury"])


DUE = {PROP: D(-110, "23:59"), PROG: D(-75, "23:59"), ADV: D(-5, "23:59"), FR: D(2, "23:59"), FP: D(2, "23:59")}
RELEASES = {  # assessment -> (time, teams)
    PROP: (D(-99, "10:00"), ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]),
    PROG: (D(-63, "10:00"), ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]),
    ADV: (D(-4, "10:00"), ["alpha", "gamma"]),
    FR: (D(-2, "10:00"), ["alpha", "gamma"]),
    FP: (D(-1, "12:05"), ["alpha"]),
}

# ---------------------------------------------------------------- Gamma search
GAMMA_TARGET = {PROP: "90.0", ADV: "95.0", FR: "91.7", FP: "91.5"}


def multiples(lo, hi, step):
    k = -(-F(lo) // step)
    out = []
    while k * step <= hi:
        out.append(k * step)
        k += 1
    return out


def gamma_search():
    best = None
    for p in multiples(86, 94, F(5, 12)):           # avg of 3 proposal scores (step 1.25)
        for a in (85, 90, 95, 100):                 # 1 advisor score (step 5)
            for r in multiples(88, 95, F(5, 12)):   # avg of 3 final report scores
                for f in multiples(88, 95, F(5, 6)):  # avg of 3 final presentation scores (step 2.5)
                    fin = (15 * p + 25 * a + 30 * r + 30 * f) / 100
                    if disp(fin) != "92.2" or abs(fin - F(9215, 100)) < F(1, 100) or abs(fin - F(9225, 100)) < F(1, 100):
                        continue
                    vals = {PROP: p, ADV: F(a), FR: r, FP: f}
                    cost = sum(abs(Decimal(disp(vals[k])) - Decimal(GAMMA_TARGET[k])) for k in vals)
                    changed = sum(disp(vals[k]) != GAMMA_TARGET[k] for k in vals)
                    key = (cost, changed, abs(fin - F(922, 10)))
                    if best is None or key < best[0]:
                        best = (key, vals, fin)
    return best[1]


def split(total, n, step, offsets):
    """Split a team total into n reviewer scores (multiples of step) around the mean."""
    base = round(F(total) / n / step) * step
    vals = [base + o * step for o in offsets[: n - 1]]
    vals.append(F(total) - sum(vals))
    assert all(v % step == 0 and 25 <= v <= 100 for v in vals), vals
    return vals


GAMMA = gamma_search()

# ---------------------------------------------------------------- submitted scores and times
# (slug, assessment) -> list of (reviewer, score, submittedAt) in roster order. Not-started ones are absent.
f = F
SUB = {
    ("alpha", PROP): [("jane.smith", f(8875, 100), D(-113, "10:35")), ("john.doe", f(85), D(-113, "10:52")), ("lea.mansour", f(8625, 100), D(-113, "11:20"))],
    ("alpha", PROG): [("jane.smith", f(85), D(-79, "18:20")), ("john.doe", f(85), D(-78, "09:10")), ("lea.mansour", f(80), D(-77, "21:05"))],
    ("alpha", ADV): [("emily.clark", f(90), D(-7, "16:30"))],
    ("alpha", FR): [("jane.smith", f(875, 10), D(-6, "20:15")), ("john.doe", f(8625, 100), D(-5, "17:40")), ("lea.mansour", f(8875, 100), D(-4, "09:30"))],
    ("alpha", FP): [("jane.smith", None, D(-1, "10:05")), ("john.doe", None, D(-1, "10:50")), ("lea.mansour", None, D(-1, "11:40"))],

    ("beta", PROP): [("jane.smith", f(7375, 100), D(-113, "16:05")), ("john.doe", f(85), D(-113, "14:48")), ("michael.johnson", f(6375, 100), D(-113, "15:10"))],
    ("beta", PROG): [("jane.smith", f(70), D(-76, "22:10")), ("john.doe", f(75), D(-78, "17:45")), ("michael.johnson", f(65), D(-77, "11:30"))],
    ("beta", ADV): [("emily.clark", f(80), D(-6, "11:20"))],
    ("beta", FR): [("john.doe", f(775, 10), D(-2, "17:20")), ("michael.johnson", f(75), D(-1, "19:05"))],

    ("delta", PROP): [("john.doe", f(6625, 100), D(-112, "14:55")), ("emily.clark", f(5875, 100), D(-112, "15:30"))],
    ("delta", PROG): [("john.doe", f(85), D(-77, "20:15")), ("emily.clark", f(35), D(-76, "08:50"))],

    ("epsilon", PROP): [("jane.smith", f(80), D(-111, "10:20")), ("lea.mansour", f(7625, 100), D(-111, "10:45")), ("karim.nassar", f(825, 10), D(-111, "12:10"))],
    ("epsilon", PROG): [("jane.smith", f(75), D(-79, "19:30")), ("lea.mansour", f(70), D(-77, "16:10")), ("karim.nassar", f(80), D(-76, "09:40"))],
    ("epsilon", ADV): [("john.doe", f(85), D(-5, "21:40"))],
    ("epsilon", FR): [("jane.smith", f(7875, 100), D(-4, "21:30")), ("lea.mansour", f(7625, 100), D(-3, "16:45")), ("karim.nassar", f(7875, 100), D(-2, "18:30"))],
    ("epsilon", FP): [("lea.mansour", f(825, 10), N(40))],

    ("zeta", PROP): [("emily.clark", f(825, 10), D(-111, "15:05")), ("lea.mansour", f(7875, 100), D(-111, "15:40")), ("john.doe", f(825, 10), D(-111, "14:50"))],
    ("zeta", PROG): [("emily.clark", f(80), D(-78, "12:05")), ("lea.mansour", f(75), D(-76, "18:35")), ("john.doe", f(80), D(-75, "21:50"))],
    ("zeta", FR): [("emily.clark", f(825, 10), D(-6, "11:15")), ("lea.mansour", f(775, 10), D(-5, "20:40")), ("john.doe", f(8125, 100), D(-3, "08:55"))],
    ("zeta", FP): [("emily.clark", f(85), D(-1, "15:05")), ("lea.mansour", f(80), D(-1, "16:30")), ("john.doe", f(85), D(-1, "17:15"))],
}
_g = lambda vals, times: list(zip(TEAM["gamma"]["jury"], vals, times))
SUB[("gamma", PROP)] = _g(split(3 * GAMMA[PROP], 3, F(5, 4), [2, -2]), [D(-112, "10:40"), D(-112, "11:05"), D(-112, "10:58")])
SUB[("gamma", PROG)] = _g(split(265, 3, 5, [0, -1]), [D(-80, "16:00"), D(-79, "10:25"), D(-78, "14:40")])
SUB[("gamma", ADV)] = [("lea.mansour", GAMMA[ADV], D(-8, "09:45"))]
SUB[("gamma", FR)] = _g(split(3 * GAMMA[FR], 3, F(5, 4), [2, -1]), [D(-5, "15:20"), D(-4, "22:05"), D(-3, "18:45")])
SUB[("gamma", FP)] = _g(split(3 * GAMMA[FP], 3, F(5, 2), [0, -1]), [D(-1, "12:15"), D(-1, "13:30"), D(-1, "16:20")])

CREATE_LEAD = {PROP: 50, PROG: 95, ADV: 70, FR: 200, FP: 60}

# Per-evaluation fixed content: levels, starting levels, pinned levels, comments {index: text}, overall.
ALPHA_FP_LEVELS = {
    "jane.smith": [4, 3, 4, 3, 3, 4, 4, 3, 4, 3],
    "john.doe": [4, 3, 3, 3, 3, 4, 3, 4, 4, 3],
    "lea.mansour": [4, 4, 4, 3, 4, 4, 3, 3, 4, 3],
}
FIXED = {
    ("alpha", PROP, "jane.smith"): dict(overall="Clear objectives and a credible plan. Tighten the constraints section before the progress report.", pins={3: 3}),
    ("alpha", PROG, "john.doe"): dict(overall="Meetings are well documented. Implementation is on track, but testing has not started yet."),
    ("alpha", ADV, "emily.clark"): dict(overall="The team met every week and kept a decision log. The forecasting model was their own initiative."),
    ("alpha", FR, "lea.mansour"): dict(overall="A well-argued alternatives chapter. Referencing style is inconsistent in chapter 5.",
                                       pins={12: 3}, comments={12: "Referencing switches between IEEE and author-year style in chapter 5."}),
    ("alpha", FP, "jane.smith"): dict(levels=ALPHA_FP_LEVELS["jane.smith"], only_fixed=True, comments={
        5: "The live demo with the soil probe worked first time, and the forecasting fallback was a nice touch.",
        8: "Everyone spoke, and the questions on sensor calibration were answered precisely."}),
    ("alpha", FP, "john.doe"): dict(levels=ALPHA_FP_LEVELS["john.doe"], only_fixed=True, comments={
        3: "The water-cost constraint was clear; the power budget for the field node was not quantified.",
        6: "Show the forecast error per week, not only the average.",
        9: "Slide 14 is dense; split the architecture diagram."}),
    ("alpha", FP, "lea.mansour"): dict(levels=ALPHA_FP_LEVELS["lea.mansour"], only_fixed=True,
                                       overall="A confident defense. The live demo made the results convincing.", comments={
        1: "Good positioning against commercial controllers; cite the 2024 FAO irrigation study you mentioned.",
        7: "Next steps are concrete; say which ones you would drop with less time."}),
    # Beta proposal: start from the P6 levels, keep the commented levels, re-solve with the seed weights.
    ("beta", PROP, "john.doe"): dict(start=[4, 3, 4, 3, 3, 3, 4, 3], pins={2: 4}, comments={2: "Requirements are specific and testable."}),
    ("beta", PROP, "michael.johnson"): dict(start=[4, 2, 3, 2, 2, 3, 1, 3], pins={6: 1},
                                            comments={6: "Hard to hear at the back; slow down and face the jury."}),
    ("beta", PROP, "jane.smith"): dict(start=[4, 2, 3, 3, 3, 2, 3, 3], pins={1: 2},
                                       comments={1: "Only two related systems; look at open-source queue tools too."}),
    ("delta", PROG, "emily.clark"): dict(overall="I could not find a working build or any test results; the report describes plans, not progress."),
}

# Drafts (in progress, not submitted).
BETA_FR_DRAFT_LEVELS = [3, 3, 4, 2, 3, 2, 3, None, None, None, None, 3, None]
BETA_FR_DRAFT_COM = {
    2: "Requirements trace cleanly to the interviews with clinic staff.",
    3: "Cost and time are covered, but nothing on patient-data privacy, which matters for an SMS system.",
    5: "GSM and SMS-gateway standards are cited but never shown shaping the design.",
    11: "Chapter 4 repeats chapter 2; figures lack captions.",
}
# history steps: (time, kind, index or None, from, to)
BETA_FR_DRAFT_HISTORY = [
    (D(-3, "20:10"), "CREATED", None, None, None),
    (D(-3, "20:16"), "LEVEL_CHANGED", 0, None, 3),
    (D(-3, "20:24"), "LEVEL_CHANGED", 1, None, 3),
    (D(-3, "20:41"), "LEVEL_CHANGED", 2, None, 4),
    (D(-3, "20:44"), "COMMENT_CHANGED", 2, None, None),
    (D(-3, "21:02"), "LEVEL_CHANGED", 3, None, 3),
    (D(-1, "21:30"), "LEVEL_CHANGED", 3, 3, 2),
    (D(-1, "21:33"), "COMMENT_CHANGED", 3, None, None),
    (D(-1, "21:48"), "LEVEL_CHANGED", 4, None, 2),
    (D(-1, "22:05"), "LEVEL_CHANGED", 5, None, 2),
    (D(-1, "22:07"), "COMMENT_CHANGED", 5, None, None),
    (D(-1, "22:20"), "LEVEL_CHANGED", 6, None, 3),
    (D(-1, "22:31"), "LEVEL_CHANGED", 11, None, 3),
    (D(-1, "22:33"), "COMMENT_CHANGED", 11, None, None),
    (N(133), "LEVEL_CHANGED", 4, 2, 3),   # feed: "Today 10:15" Problem formulation 2 -> 3
]
DELTA_ADV_DRAFT_LEVELS = [3, 2, 2, None, None]
DELTA_ADV_DRAFT_COM = {1: "Two members carry most of the work; the task board shows little from the other two."}
DELTA_ADV_DRAFT_HISTORY = [
    (D(-8, "17:10"), "CREATED", None, None, None),
    (D(-8, "17:14"), "LEVEL_CHANGED", 0, None, 3),
    (D(-8, "17:21"), "LEVEL_CHANGED", 1, None, 1),
    (N(92), "LEVEL_CHANGED", 1, 1, 2),
    (N(90), "LEVEL_CHANGED", 2, None, 2),
    (N(86), "COMMENT_CHANGED", 1, None, None),   # feed: "Today 11:02" draft saved
]

# ---------------------------------------------------------------- level vectors
def solve_levels(weights, total4, start, pins, rng):
    """Levels 1..4 with sum(level*weight) == total4, as close as possible to start."""
    noise = [[rng.random() for _ in range(5)] for _ in weights]
    dp = {0: (0.0, ())}
    for i, w in enumerate(weights):
        nd = {}
        for s, (c, lv) in sorted(dp.items()):
            for l in ([pins[i]] if i in pins else [1, 2, 3, 4]):
                ns = s + l * w
                if ns > total4:
                    continue
                nc = c + abs(l - start[i]) * 10 + noise[i][l]
                if ns not in nd or nc < nd[ns][0]:
                    nd[ns] = (nc, lv + (l,))
        dp = nd
    assert total4 in dp, (total4, start, pins)
    return list(dp[total4][1])


def gen_levels(key, a, score, start=None, pins=None):
    rng = random.Random("levels|" + key)
    weights = [c[1] for c in RUBRICS[a]]
    total4 = F(score) * 4
    assert total4.denominator == 1, (key, score)
    if start is None:
        m = float(score) / 25
        start = [min(4, max(1, int(round(m + rng.gauss(0, 0.6))))) for _ in weights]
    return solve_levels(weights, int(total4), start, pins or {}, rng)


def score_of(a, levels):
    return sum(F(l * c[1]) for l, c in zip(levels, RUBRICS[a]) if l is not None) / 4


# ---------------------------------------------------------------- comments
USED = Counter()


def band(level):
    return "hi" if level == 4 else "mid" if level == 3 else "lo"


def pick(options, fl, rng, cap):
    texts = [o.format(**fl) for o in options]
    best = min(USED[t] for t in texts)
    if best >= cap:
        return None
    choice = rng.choice([t for t in texts if USED[t] == best])
    USED[choice] += 1
    return choice


def gen_comments(key, slug, a, levels, fixed):
    rng = random.Random("comments|" + key)
    out = dict(fixed)
    for t in fixed.values():
        USED[t] += 1
    n = len(levels)
    want = max(1, round(n * 0.5) + rng.choice([-1, 0, 1])) - len(fixed)
    cands = [i for i in range(n) if i not in fixed]
    cands.sort(key=lambda i: levels[i] + rng.random() * 2.2)  # weaker criteria get feedback more often
    for i in cands:
        if want <= 0:
            break
        txt = pick(TEMPLATES[THEMES[a][i]][band(levels[i])], FLAVOUR[slug], rng, 2)
        if txt:
            out[i] = txt
            want -= 1
    return out


TEAM_OVERALL = {}


def gen_overall(key, slug, a, score):
    """Overall comment for the score's band, never repeated within one team's assessment."""
    rng = random.Random("overall|" + key)
    b = "hi" if score >= 87.5 else "mid" if score >= 70 else "lo"
    seen = TEAM_OVERALL.setdefault((slug, a), set())
    order = {"hi": ["hi", "mid"], "mid": ["mid", "hi", "lo"], "lo": ["lo", "mid"]}[b]
    for band_ in order:
        opts = [o for o in OVERALL[a][band_] if o.format(**FLAVOUR[slug]) not in seen]
        if opts:
            txt = pick(opts, FLAVOUR[slug], rng, 99)
            seen.add(txt)
            return txt
    raise AssertionError("no overall comment left for " + key)


# ---------------------------------------------------------------- build evaluations
def ckey(a, i):
    return "criterion:%s:%d" % (a, i + 1)


def ekey(slug, a, rev):
    return "evaluation:%s:%s:%s" % (slug, a, rev)


def make_eval(slug, a, rev, status, levels, comments, overall, created, updated, submitted, history):
    crit = []
    for i, (cname, w, desc) in enumerate(RUBRICS[a]):
        crit.append({"criterionKey": ckey(a, i), "position": i + 1, "name": cname, "weight": w,
                     "descriptions": desc, "level": levels[i], "comment": comments.get(i)})
    return {
        "key": ekey(slug, a, rev), "teamKey": "team:" + slug, "teamName": TEAM[slug]["name"], "assessment": a,
        "reviewerId": uid(rev), "reviewerName": pname(rev), "reviewerRole": ASSESSMENT_ROLE[a],
        "status": status, "criteria": crit, "overallComment": overall,
        "score": num(score_of(a, levels)),
        "createdAt": created, "updatedAt": updated, "submittedAt": submitted,
        "history": [{"at": t, "kind": k, "criterionKey": (ckey(a, i) if i is not None else None), "from": fr, "to": to}
                    for (t, k, i, fr, to) in history],
    }


EVALS = []
SUBMITTED = {}  # (slug, a) -> list of (rev, Fraction score, submittedAt, key)
for t in TEAMS:
    slug = t["slug"]
    for a in ASSESSMENTS:
        for idx, (rev, score, sub_at) in enumerate(SUB.get((slug, a), [])):
            assert rev in holders(slug, a), (slug, a, rev)
            key = ekey(slug, a, rev)
            fx = FIXED.get((slug, a, rev), {})
            levels = fx.get("levels") or gen_levels(key, a, score, fx.get("start"), fx.get("pins"))
            if score is None:
                score = score_of(a, levels)
            assert score_of(a, levels) == score, (key, levels, score)
            if fx.get("only_fixed"):
                comments = dict(fx.get("comments", {}))
            else:
                comments = gen_comments(key, slug, a, levels, fx.get("comments", {}))
            if fx.get("overall"):
                overall = fx["overall"]
                USED[overall] += 1
                TEAM_OVERALL.setdefault((slug, a), set()).add(overall)
            else:
                overall = gen_overall(key, slug, a, score)
            created = shift(sub_at, -CREATE_LEAD[a] - 7 * idx)
            EVALS.append(make_eval(slug, a, rev, "SUBMITTED", levels, comments, overall, created, sub_at, sub_at,
                                   [(created, "CREATED", None, None, None), (sub_at, "SUBMITTED", None, None, None)]))
            SUBMITTED.setdefault((slug, a), []).append((rev, score, sub_at, key))

EVALS.append(make_eval("beta", FR, "jane.smith", "DRAFT", BETA_FR_DRAFT_LEVELS, BETA_FR_DRAFT_COM, None,
                       BETA_FR_DRAFT_HISTORY[0][0], BETA_FR_DRAFT_HISTORY[-1][0], None, BETA_FR_DRAFT_HISTORY))
EVALS.append(make_eval("delta", ADV, "karim.nassar", "DRAFT", DELTA_ADV_DRAFT_LEVELS, DELTA_ADV_DRAFT_COM, None,
                       DELTA_ADV_DRAFT_HISTORY[0][0], DELTA_ADV_DRAFT_HISTORY[-1][0], None, DELTA_ADV_DRAFT_HISTORY))
DRAFTS = {("beta", FR): "jane.smith", ("delta", ADV): "karim.nassar"}


def team_grade(slug, a):
    subs = SUBMITTED.get((slug, a), [])
    if len(subs) != len(holders(slug, a)) or not subs:
        return None
    return sum(s[1] for s in subs) / len(subs)


def finalized_at(slug, a):
    return max((s[2] for s in SUBMITTED[(slug, a)]), key=tmin)


def final_grade(slug):
    gs = [team_grade(slug, a) for a in ASSESSMENTS]
    if any(g is None for g in gs):
        return None
    return sum(g * ASSESSMENT_WEIGHTS[a] for g, a in zip(gs, ASSESSMENTS)) / 100


def final_at(slug):
    return max((finalized_at(slug, a) for a in ASSESSMENTS), key=tmin)


# ---------------------------------------------------------------- rubric seed
rubric_seed = {"rubrics": [
    {"assessment": a, "name": ASSESSMENT_NAMES[a], "criteria": [
        {"key": ckey(a, i), "position": i + 1, "name": c[0], "weight": c[1], "descriptions": c[2]}
        for i, c in enumerate(RUBRICS[a])]}
    for a in ASSESSMENTS]}

# ---------------------------------------------------------------- admin seed
admin_teams = []
for t in TEAMS:
    slug = t["slug"]
    grades = []
    for a in ASSESSMENTS:
        for rev, score, sub_at, key in SUBMITTED.get((slug, a), []):
            grades.append({"assessment": a, "reviewerId": uid(rev), "evaluationKey": key, "score": num(score), "submittedAt": sub_at})
    releases = []
    for a in ASSESSMENTS:
        at, teams = RELEASES[a]
        if slug in teams:
            assert team_grade(slug, a) is not None and tmin(finalized_at(slug, a)) < tmin(at), (slug, a)
            releases.append({"assessment": a, "releasedAt": at})
    admin_teams.append({
        "key": "team:" + slug, "name": t["name"], "projectTitle": t["title"], "description": t["desc"],
        "students": [student(slug, *s) for s in t["students"]],
        "reviewers": [{"reviewerId": uid(t["advisor"]), "role": "ADVISOR"}] + [{"reviewerId": uid(j), "role": "JURY"} for j in t["jury"]],
        "defenseSlot": {"startsAt": t["slot"][0], "durationMinutes": 40, "room": t["slot"][1]},
        "grades": grades, "releases": releases,
    })
admin_seed = {"assessments": [{"code": a, "dueAt": DUE[a]} for a in ASSESSMENTS], "teams": admin_teams}

# ---------------------------------------------------------------- notifications
NOTES = []


def link(kind, slug=None, a=None):
    return {"kind": kind, "teamKey": ("team:" + slug) if slug else None, "assessment": a}


def note(recipient, typ, text, at, lk, read=None):
    NOTES.append({"recipientId": recipient, "type": typ, "text": text, "createdAt": at,
                  "read": (not is_today(at)) if read is None else read, "link": lk})


def an(a):
    return ASSESSMENT_NAMES[a]


def g(slug, a):
    return disp(team_grade(slug, a))


DAY_OF = {-1: "day 1", 0: "day 2", 1: "day 3"}
JANE, JOHN, MICH, EMILY, KARIM, LEA, RANIA = (uid(u) for u in
    ["jane.smith", "john.doe", "michael.johnson", "emily.clark", "karim.nassar", "lea.mansour", "rania.haddad"])
DELTA_MOVE = N(168)   # feed: "Today 09:40"
TODAY_0800 = N(268)

# Jane (P10)
note(JANE, "DUE_SOON", "Final report for Team Beta is due in 2 days. Your draft has %d of 13 criteria scored."
     % sum(l is not None for l in BETA_FR_DRAFT_LEVELS), TODAY_0800, link("EVALUATION", "beta", FR))
note(JANE, "DEFENSE_SCHEDULED", "Defense confirmed: Team Beta, tomorrow at 09:00, Amphi A.", DELTA_MOVE, link("SCHEDULE", "beta"))
note(JANE, "GRADE_FINAL", "Final presentation for Team Alpha is final: %s." % g("alpha", FP), finalized_at("alpha", FP), link("EVALUATION", "alpha", FP))
note(JANE, "FINAL_GRADE_COMPUTED", "Team Alpha's final grade is computed: %s." % disp(final_grade("alpha")), final_at("alpha"), link("MY_TEAMS", "alpha"))
note(JANE, "GRADE_FINAL", "Final report for Team Epsilon is final: %s." % g("epsilon", FR), finalized_at("epsilon", FR), link("EVALUATION", "epsilon", FR))
note(JANE, "ASSIGNED", "You were assigned to Team Epsilon as a jury member.", D(-147, "09:30"), link("MY_TEAMS", "epsilon"))

# Rania (coordinator)
for t in TEAMS:
    for a in ASSESSMENTS:
        if team_grade(t["slug"], a) is not None:
            note(RANIA, "GRADE_FINAL", "%s for Team %s is final: %s." % (an(a), t["name"], g(t["slug"], a)),
                 finalized_at(t["slug"], a), link("TEAM", t["slug"], a))
    if final_grade(t["slug"]) is not None:
        note(RANIA, "FINAL_GRADE_COMPUTED", "Team %s's final grade is computed: %s." % (t["name"], disp(final_grade(t["slug"]))),
             final_at(t["slug"]), link("TEAM", t["slug"]))
note(RANIA, "OVERDUE", "2 advisor assessments are overdue: Team Delta (Karim Nassar, draft) and Team Zeta (Michael Johnson, not started).",
     D(-4, "08:00"), link("OVERVIEW", None, ADV))


def open_at(a, at):
    expected = sum(len(holders(t["slug"], a)) for t in TEAMS)
    done = sum(1 for (s, aa), subs in SUBMITTED.items() if aa == a for x in subs if tmin(x[2]) <= tmin(at))
    return expected - done


note(RANIA, "DUE_SOON", "Final report and Final presentation are due in 2 days: %d and %d evaluations still open."
     % (open_at(FR, TODAY_0800), open_at(FP, TODAY_0800)), TODAY_0800, link("OVERVIEW"))
note(RANIA, "DEFENSE_SCHEDULED", "Team Delta's defense moved to tomorrow at 09:00, Room B-204. Conflict: John Doe is in two defenses at 09:00.",
     DELTA_MOVE, link("SCHEDULE", "delta"))

# Karim (advisor of Delta; jury of Gamma and Epsilon)
note(KARIM, "ASSIGNED", "You were assigned to Team Delta as advisor.", D(-150, "09:30"), link("MY_TEAMS", "delta"))
note(KARIM, "ASSIGNED", "You were assigned to Team Gamma as a jury member.", D(-150, "09:31"), link("MY_TEAMS", "gamma"))
note(KARIM, "ASSIGNED", "You were assigned to Team Epsilon as a jury member.", D(-147, "09:30"), link("MY_TEAMS", "epsilon"))
note(KARIM, "DEFENSE_SCHEDULED", "Defense scheduled: Team Gamma, %s of the defense week, 11:00, Amphi A." % DAY_OF[-1], D(-30, "10:00"), link("SCHEDULE", "gamma"))
note(KARIM, "DEFENSE_SCHEDULED", "Defense scheduled: Team Epsilon, %s of the defense week, 09:00, Amphi A." % DAY_OF[0], D(-30, "10:00"), link("SCHEDULE", "epsilon"))
note(KARIM, "DUE_SOON", "Advisor assessment for Team Delta is due in 3 days.", D(-8, "08:00"), link("EVALUATION", "delta", ADV))
note(KARIM, "OVERDUE", "Advisor assessment for Team Delta is overdue. Your draft has 2 of 5 criteria scored.", D(-4, "08:00"), link("EVALUATION", "delta", ADV))
note(KARIM, "FINAL_GRADE_COMPUTED", "Team Gamma's final grade is computed: %s." % disp(final_grade("gamma")), final_at("gamma"), link("MY_TEAMS", "gamma"))
note(KARIM, "DUE_SOON", "Final presentation for Team Epsilon is due in 2 days.", TODAY_0800, link("EVALUATION", "epsilon", FP))

# John
note(JOHN, "FINAL_GRADE_COMPUTED", "Team Alpha's final grade is computed: %s." % disp(final_grade("alpha")), final_at("alpha"), link("MY_TEAMS", "alpha"))
note(JOHN, "GRADE_FINAL", "Final presentation for Team Zeta is final: %s." % g("zeta", FP), finalized_at("zeta", FP), link("EVALUATION", "zeta", FP))
note(JOHN, "DUE_SOON", "Final report for Team Delta is due in 2 days.", TODAY_0800, link("EVALUATION", "delta", FR))
note(JOHN, "DEFENSE_SCHEDULED", "Team Delta's defense moved to tomorrow at 09:00, Room B-204. You are also on the Team Beta jury at 09:00.",
     DELTA_MOVE, link("SCHEDULE", "delta"))

# Emily
note(EMILY, "GRADE_FINAL", "Advisor assessment for Team Beta is final: %s." % g("beta", ADV), finalized_at("beta", ADV), link("EVALUATION", "beta", ADV))
note(EMILY, "FINAL_GRADE_COMPUTED", "Team Alpha's final grade is computed: %s." % disp(final_grade("alpha")), final_at("alpha"), link("MY_TEAMS", "alpha"))
note(EMILY, "DUE_SOON", "Final report for Team Delta is due in 2 days.", TODAY_0800, link("EVALUATION", "delta", FR))
note(EMILY, "DEFENSE_SCHEDULED", "Team Delta's defense moved to tomorrow at 09:00, Room B-204.", DELTA_MOVE, link("SCHEDULE", "delta"))

# Lea
note(LEA, "FINAL_GRADE_COMPUTED", "Team Alpha's final grade is computed: %s." % disp(final_grade("alpha")), final_at("alpha"), link("MY_TEAMS", "alpha"))
note(LEA, "FINAL_GRADE_COMPUTED", "Team Gamma's final grade is computed: %s." % disp(final_grade("gamma")), final_at("gamma"), link("MY_TEAMS", "gamma"))
note(LEA, "GRADE_FINAL", "Final presentation for Team Zeta is final: %s." % g("zeta", FP), finalized_at("zeta", FP), link("EVALUATION", "zeta", FP))

# Michael
note(MICH, "OVERDUE", "Advisor assessment for Team Zeta is overdue. You haven't started it yet.", D(-4, "08:00"), link("EVALUATION", "zeta", ADV))
note(MICH, "FINAL_GRADE_COMPUTED", "Team Gamma's final grade is computed: %s." % disp(final_grade("gamma")), final_at("gamma"), link("MY_TEAMS", "gamma"))
note(MICH, "DEFENSE_SCHEDULED", "Defense confirmed: Team Beta, tomorrow at 09:00, Amphi A.", DELTA_MOVE, link("SCHEDULE", "beta"))

# Nour (student, Team Alpha)
for a in ASSESSMENTS:
    at, teams = RELEASES[a]
    if "alpha" in teams:
        note(NOUR_ID, "RESULTS_RELEASED", "Your %s results are available." % an(a), at, link("STUDENT_RESULTS", "alpha", a),
             read=(a != FP))
note(NOUR_ID, "DEFENSE_SCHEDULED", "Your defense is scheduled: %s of the defense week, 09:00, Amphi A (40 minutes)." % DAY_OF[-1],
     D(-30, "10:00"), link("SCHEDULE", "alpha"))

# Ahmad (student, Team Beta): only the results released so far, and tomorrow's defense
for a in ASSESSMENTS:
    at, teams = RELEASES[a]
    if "beta" in teams:
        note(AHMAD_ID, "RESULTS_RELEASED", "Your %s results are available." % an(a), at, link("STUDENT_RESULTS", "beta", a), read=True)
note(AHMAD_ID, "DEFENSE_SCHEDULED", "Your defense is confirmed: tomorrow at 09:00, Amphi A (40 minutes).", DELTA_MOVE,
     link("SCHEDULE", "beta"))

NOTES.sort(key=lambda n: -tmin(n["createdAt"]))  # stable: newest first
for i, n in enumerate(NOTES, 1):
    n_key = {"key": "notification:%d" % i}
    n_key.update(n)
    NOTES[i - 1] = n_key

# ---------------------------------------------------------------- activity feed (newest first)
ACT = []


def act(kind, actor, text, at, lk):
    ACT.append({"kind": kind, "actorId": uid(actor) if actor in PEOPLE else None,
                "actorName": pname(actor) if actor in PEOPLE else actor, "text": text, "at": at, "link": lk})


eps_fp_n = len(SUBMITTED[("epsilon", FP)])
act("SUBMITTED", "lea.mansour", "submitted the Final presentation for Team Epsilon (%d of 3)." % eps_fp_n, N(40), link("TEAM", "epsilon", FP))
act("DRAFT_SAVED", "karim.nassar", "saved a draft of the Advisor assessment for Team Delta, overdue for 5 days.", N(86), link("TEAM", "delta", ADV))
act("LEVEL_CHANGED", "jane.smith", "changed Problem formulation 2 → 3 in her Team Beta final report draft.", N(133), link("TEAM", "beta", FR))
act("SCHEDULE", "Schedule", "Team Delta moved to tomorrow, 09:00, Room B-204. John Doe is now in two defenses at 09:00.", DELTA_MOVE, link("SCHEDULE", "delta"))
act("GRADE_FINAL", "Team Zeta", "Final presentation grade is final: %s." % g("zeta", FP), finalized_at("zeta", FP), link("TEAM", "zeta", FP))
act("FINAL_GRADE_COMPUTED", "Team Gamma", "final grade computed: %s." % disp(final_grade("gamma")), final_at("gamma"), link("TEAM", "gamma"))
act("GRADE_FINAL", "Team Gamma", "Final presentation grade is final: %s." % g("gamma", FP), finalized_at("gamma", FP), link("TEAM", "gamma", FP))
act("RELEASED", "rania.haddad", "released Final presentation results to Team Alpha.", RELEASES[FP][0], link("OVERVIEW", None, FP))
act("FINAL_GRADE_COMPUTED", "Team Alpha", "final grade computed: %s." % disp(final_grade("alpha")), final_at("alpha"), link("TEAM", "alpha"))
act("GRADE_FINAL", "Team Alpha", "Final presentation grade is final: %s." % g("alpha", FP), finalized_at("alpha", FP), link("TEAM", "alpha", FP))
act("GRADE_FINAL", "Team Epsilon", "Final report grade is final: %s." % g("epsilon", FR), finalized_at("epsilon", FR), link("TEAM", "epsilon", FR))
act("RELEASED", "rania.haddad", "released Final report results to Team Alpha and Team Gamma.", RELEASES[FR][0], link("OVERVIEW", None, FR))
act("GRADE_FINAL", "Team Gamma", "Final report grade is final: %s." % g("gamma", FR), finalized_at("gamma", FR), link("TEAM", "gamma", FR))
act("GRADE_FINAL", "Team Zeta", "Final report grade is final: %s." % g("zeta", FR), finalized_at("zeta", FR), link("TEAM", "zeta", FR))
act("RELEASED", "rania.haddad", "released Advisor assessment results to Team Alpha and Team Gamma.", RELEASES[ADV][0], link("OVERVIEW", None, ADV))
act("GRADE_FINAL", "Team Beta", "Advisor assessment grade is final: %s." % g("beta", ADV), finalized_at("beta", ADV), link("TEAM", "beta", ADV))
act("RELEASED", "rania.haddad", "released Progress report results to all six teams.", RELEASES[PROG][0], link("OVERVIEW", None, PROG))
act("GRADE_FINAL", "Team Delta", "Progress report grade is final: %s." % g("delta", PROG), finalized_at("delta", PROG), link("TEAM", "delta", PROG))
act("RELEASED", "rania.haddad", "released Proposal presentation results to all six teams.", RELEASES[PROP][0], link("OVERVIEW", None, PROP))
act("GRADE_FINAL", "Team Beta", "Proposal presentation grade is final: %s." % g("beta", PROP), finalized_at("beta", PROP), link("TEAM", "beta", PROP))
act("ASSIGNMENT", "rania.haddad", "assigned reviewers to all six teams.", D(-150, "09:30"), link("OVERVIEW"))

ACT.sort(key=lambda e: -tmin(e["at"]))  # stable
ACT = [dict({"key": "activity:%d" % i}, **e) for i, e in enumerate(ACT, 1)]
notif_seed = {"notifications": NOTES, "activity": ACT}

# ---------------------------------------------------------------- write
OUT = {
    "fyp-grading-rubric-service": rubric_seed,
    "fyp-grading-evaluation-service": {"evaluations": EVALS},
    "fyp-grading-admin-service": admin_seed,
    "fyp-grading-notification-service": notif_seed,
}
for svc, data in OUT.items():
    path = os.path.join(ROOT, svc, "src", "main", "resources", "demo", "seed.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

# ---------------------------------------------------------------- verification
SHORT = {PROP: "Prop", PROG: "Prog", ADV: "Adv", FR: "FR", FP: "FP"}
print("Assay demo seed written for 4 services.\n")

# weights
for a in ASSESSMENTS:
    assert sum(c[1] for c in RUBRICS[a]) == 100, a
assert sum(ASSESSMENT_WEIGHTS.values()) == 100

# every submitted evaluation: score == sum(level*weight)/4 == admin grade
admin_scores = {gr["evaluationKey"]: gr["score"] for t in admin_teams for gr in t["grades"]}
for e in EVALS:
    s = sum(F(c["level"] * c["weight"]) for c in e["criteria"] if c["level"] is not None) / 4
    assert F(e["score"]) == s, e["key"]
    assert all(c["level"] is None or 0 <= c["level"] <= 4 for c in e["criteria"])
    if e["status"] == "SUBMITTED":
        assert all(c["level"] is not None for c in e["criteria"]), e["key"]
        assert e["overallComment"], e["key"]
        assert admin_scores[e["key"]] == e["score"], e["key"]
        assert tmin(e["submittedAt"]) <= tmin(DUE[e["assessment"]]), e["key"]
    else:
        assert e["key"] not in admin_scores
assert len(admin_scores) == sum(e["status"] == "SUBMITTED" for e in EVALS)

print("%-8s %-5s %-46s %6s %6s  %s" % ("Team", "Ass.", "Reviewer scores (exact -> 1dp)", "Grade", "Spread", "State"))
print("-" * 100)
for t in TEAMS:
    slug = t["slug"]
    for a in ASSESSMENTS:
        subs = SUBMITTED.get((slug, a), [])
        hs = holders(slug, a)
        parts = ", ".join("%s %s->%s" % (pname(r).split()[0], float(s), disp(s)) for r, s, _, _ in subs)
        if (slug, a) in DRAFTS:
            dk = ekey(slug, a, DRAFTS[(slug, a)])
            de = next(e for e in EVALS if e["key"] == dk)
            parts += (", " if parts else "") + "%s DRAFT %s (%d/%d)" % (
                pname(DRAFTS[(slug, a)]).split()[0], de["score"], sum(c["level"] is not None for c in de["criteria"]), len(de["criteria"]))
        gr = team_grade(slug, a)
        spread = disp(max(s[1] for s in subs) - min(s[1] for s in subs)) if len(subs) > 1 else "-"
        rel = slug in RELEASES[a][1]
        state = ("final" + (", released" if rel else "")) if gr is not None else "waiting %d of %d" % (len(subs), len(hs))
        print("%-8s %-5s %-46s %6s %6s  %s" % (t["name"], SHORT[a], parts or "-", disp(gr) if gr is not None else "-", spread, state))
    fg = final_grade(slug)
    print("%-8s %-5s %-46s %6s" % (t["name"], "FINAL", "", disp(fg) if fg is not None else "pend."))
    print()

print("Jane Smith's My teams (P3):")
for slug in ("beta", "epsilon", "alpha"):
    row = []
    for a in (PROP, PROG, FR, FP):
        e = next((e for e in EVALS if e["key"] == ekey(slug, a, "jane.smith")), None)
        row.append("%s %s" % (SHORT[a], "not started" if e is None else disp(e["score"]) if e["status"] == "SUBMITTED"
                              else "draft %d/13 (%s)" % (sum(c["level"] is not None for c in e["criteria"]), e["score"])))
    print("  %-8s %s" % (TEAM[slug]["name"], " | ".join(row)))
print()

# required assertions
assert disp(final_grade("alpha")) == "88.0" and g("alpha", PROP) == "86.7"
assert disp(final_grade("gamma")) == "92.2"
beta_prop = [s[1] for s in SUBMITTED[("beta", PROP)]]
assert g("beta", PROP) == "74.2" and disp(max(beta_prop) - min(beta_prop)) == "21.3"
jd = next(e for e in EVALS if e["key"] == ekey("beta", FR, "jane.smith"))
assert jd["score"] == 53.75 and sum(c["level"] is not None for c in jd["criteria"]) == 8
assert F(35) in [s[1] for s in SUBMITTED[("delta", PROG)]]
for a, (at, teams) in RELEASES.items():
    for slug in TEAM:
        assert (slug in teams) == any(r["assessment"] == a for r in admin_teams[[t["slug"] for t in TEAMS].index(slug)]["releases"])
assert [tmin(e["at"]) for e in ACT] == sorted((tmin(e["at"]) for e in ACT), reverse=True)

# deviations from the design numbers
DESIGN_TEAM = {
    ("alpha", PROP): "86.7", ("alpha", PROG): "84.0", ("alpha", ADV): "90.0", ("alpha", FR): "87.5", ("alpha", FP): "87.5",
    ("beta", PROP): "74.2", ("beta", PROG): "70.0", ("beta", ADV): "78.8",
    ("gamma", PROP): "90.0", ("gamma", PROG): "88.8", ("gamma", ADV): "95.0", ("gamma", FR): "91.7", ("gamma", FP): "91.5",
    ("delta", PROP): "62.5", ("delta", PROG): "58.8",
    ("epsilon", PROP): "79.6", ("epsilon", PROG): "75.0", ("epsilon", ADV): "82.5", ("epsilon", FR): "77.9",
    ("zeta", PROP): "81.3", ("zeta", PROG): "77.5", ("zeta", FR): "80.4", ("zeta", FP): "83.3",
}
DESIGN_IND = {
    ("alpha", PROP, "jane.smith"): "88.8", ("alpha", PROP, "john.doe"): "85.0", ("alpha", PROP, "lea.mansour"): "86.3",
    ("alpha", PROG, "jane.smith"): "85.0", ("alpha", ADV, "emily.clark"): "90.0",
    ("alpha", FR, "jane.smith"): "87.5", ("alpha", FR, "john.doe"): "86.3", ("alpha", FR, "lea.mansour"): "88.8",
    ("alpha", FP, "jane.smith"): "87.5", ("alpha", FP, "john.doe"): "85.0", ("alpha", FP, "lea.mansour"): "90.0",
    ("beta", PROP, "john.doe"): "85.0", ("beta", PROP, "michael.johnson"): "63.8", ("beta", PROP, "jane.smith"): "73.8",
    ("beta", PROG, "john.doe"): "72.5", ("beta", PROG, "michael.johnson"): "65.0", ("beta", PROG, "jane.smith"): "72.5",
    ("beta", ADV, "emily.clark"): "78.8", ("beta", FR, "john.doe"): "77.5", ("beta", FR, "michael.johnson"): "75.0",
    ("epsilon", PROP, "jane.smith"): "80.0", ("epsilon", PROG, "jane.smith"): "76.3", ("epsilon", ADV, "john.doe"): "82.5",
    ("epsilon", FR, "jane.smith"): "78.8",
}
DESIGN_FINAL = {"alpha": "88.0", "gamma": "92.2"}
devs = []
for (slug, a), want in DESIGN_TEAM.items():
    got = g(slug, a)
    if got != want:
        devs.append("%s %s team grade: design %s -> seed %s" % (TEAM[slug]["name"], an(a), want, got))
for (slug, a, rev), want in DESIGN_IND.items():
    got = disp(next(s for r, s, _, _ in SUBMITTED[(slug, a)] if r == rev))
    if got != want:
        devs.append("%s %s, %s: design %s -> seed %s" % (TEAM[slug]["name"], an(a), pname(rev), want, got))
for slug, want in DESIGN_FINAL.items():
    if disp(final_grade(slug)) != want:
        devs.append("%s final grade: design %s -> seed %s" % (TEAM[slug]["name"], want, disp(final_grade(slug))))
dp_ = [s[1] for s in SUBMITTED[("delta", PROG)]]
if disp(max(dp_) - min(dp_)) != "47.5":
    devs.append("Delta Progress report spread: design 47.5 -> seed %s" % disp(max(dp_) - min(dp_)))
print("Deviations from the design numbers (seed weights win):")
for d in devs:
    print("  - " + d)
print()
n_sub = sum(e["status"] == "SUBMITTED" for e in EVALS)
n_crit = sum(len(e["criteria"]) for e in EVALS if e["status"] == "SUBMITTED")
n_com = sum(1 for e in EVALS if e["status"] == "SUBMITTED" for c in e["criteria"] if c["comment"])
print("Evaluations: %d submitted, %d drafts. Criterion comments on %d of %d submitted criteria (%.0f%%)."
      % (n_sub, len(EVALS) - n_sub, n_com, n_crit, 100.0 * n_com / n_crit))
print("Notifications: %d (%d unread). Activity entries: %d." % (len(NOTES), sum(not n["read"] for n in NOTES), len(ACT)))
print("All assertions passed.")
