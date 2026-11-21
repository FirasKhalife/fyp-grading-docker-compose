#!/usr/bin/env python3
"""API-level checks of the Assay rules on a running stack, through the gateway with real Keycloak tokens.

It covers what the smoke test doesn't: copy isolation, the grade maths, late submissions, a submit racing an
autosave, reviewer editing, release, what a reviewer may see before a grade is final, the CSV export, the schedule
and rubric editors, and the session and rate-limit rules. Each check prints ok or FAIL; the exit code is the number
of failures (0 = all passed).

Usage: e2e/api-checks.py [gateway-url] [keycloak-url]   (defaults: http://localhost:9191 http://localhost:7080)
       Against the production compose both are its edge: e2e/api-checks.py http://localhost:8080 http://localhost:8080
Env:   DEMO_PASSWORD (default assay-demo, the public personas' password)
Needs: Python 3.9+ (standard library only), and a stack started from the seed (it reads the seed's teams and grades).
"""
import csv
import datetime
import io
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zoneinfo
from decimal import Decimal, ROUND_HALF_UP

GW = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9191").rstrip("/")
KC = (sys.argv[2] if len(sys.argv) > 2 else "http://localhost:7080").rstrip("/")
PASSWORD = os.environ.get("DEMO_PASSWORD", "assay-demo")
USERS = {"rania": "rania.haddad", "jane": "jane.smith", "karim": "karim.nassar", "nour": "nour.khoury",
         "john": "john.doe", "michael": "michael.johnson", "emily": "emily.clark", "lea": "lea.mansour"}


# ---------------------------------------------------------------- client
_tokens = {}
# A named User-Agent on every request: Cloudflare refuses Python-urllib's default one (error 1010) in front of the
# live demo.
UA = {"User-Agent": "assay-api-checks"}


def token(who):
    if who not in _tokens:
        body = urllib.parse.urlencode({"grant_type": "password", "client_id": "assay-spa", "username": USERS[who],
                                       "password": PASSWORD}).encode()
        req = urllib.request.Request(KC + "/realms/assay/protocol/openid-connect/token", data=body, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            _tokens[who] = json.load(r)["access_token"]
    return _tokens[who]


class Res:
    def __init__(self, status, body, headers):
        self.status, self.body, self.headers = status, body, headers

    @property
    def code(self):
        return self.body.get("code") if isinstance(self.body, dict) else None

    def __repr__(self):
        return f"<{self.status} {str(self.body)[:200]}>"


def call(session, who, method, path, body=None, accept="application/json"):
    h = {"Accept": accept, **UA}
    if who:
        h["Authorization"] = "Bearer " + token(who)
    if session:
        h["X-Demo-Session"] = session
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(GW + path, data=None if body is None else json.dumps(body).encode(), method=method,
                                 headers=h)
    try:
        # r.headers is case-insensitive: Cloudflare sends some headers in lowercase (content-disposition).
        with urllib.request.urlopen(req, timeout=30) as r:
            raw, st, hd = r.read(), r.status, r.headers
    except urllib.error.HTTPError as e:
        raw, st, hd = e.read(), e.code, e.headers
    try:
        b = json.loads(raw) if raw else None
    except ValueError:
        b = raw.decode(errors="replace")
    return Res(st, b, hd)


def copy_call(session, who, method, path):
    """A call that makes a demo copy. The gateway allows few per visitor (429 with Retry-After), so wait it out."""
    for _ in range(10):
        r = call(session, who, method, path)
        if r.status != 429:
            return r
        wait = int(r.headers.get("Retry-After") or r.headers.get("retry-after") or 5)
        print(f"       (copy limit: 429, waiting {wait} s)")
        time.sleep(min(max(wait, 1), 70))
    return r


def header(r, name):
    return next((v for k, v in r.headers.items() if k.lower() == name.lower()), None)


def wait_for_full_allowance(session, who):
    """Waits until this client's browsing allowance (the gateway's per-IP token bucket) is full again, and returns
    its capacity. The bucket's size and refill rate come from the gateway's X-RateLimit-* headers, so a change in
    its config needs no change here."""
    r = call(session, who, "GET", "/api/me")
    try:
        capacity = int(header(r, "X-RateLimit-Burst-Capacity"))
        rate = int(header(r, "X-RateLimit-Replenish-Rate"))
        remaining = int(header(r, "X-RateLimit-Remaining"))
    except (TypeError, ValueError):
        capacity, rate, remaining = 60, 20, 0   # application.yml's rate-limit, assuming an empty bucket
    wait = (capacity - remaining) / max(rate, 1) + 1
    print(f"       (browsing allowance: {remaining} of {capacity} left, {rate}/s; waiting {wait:.1f} s to refill)")
    time.sleep(wait)
    return capacity


def new_session(who="rania"):
    s = str(uuid.uuid4())
    r = copy_call(s, who, "PUT", "/api/demo/session")
    assert r.status in (200, 201), r
    return s


def team_ids(s):
    return {t["team"]["name"]: t["team"]["id"] for t in call(s, "rania", "GET", "/api/overview").body["teams"]}


def items_of(body):
    return body if isinstance(body, list) else (body or {}).get("content", (body or {}).get("items", []))


# ---------------------------------------------------------------- checks
results = []


def check(name, cond, info=""):
    results.append((bool(cond), name, info))
    print(("  ok   " if cond else "  FAIL ") + name + (f"   [{info}]" if info and not cond else ""))


def ev(s, who, team, a):
    return call(s, who, "GET", f"/api/my-evaluations/{team}/{a}")


def draft_body(e, level_for_unscored=3):
    return {"criteria": [{"criterionId": c["criterionId"],
                          "level": c.get("level") if c.get("level") is not None else level_for_unscored,
                          "comment": c.get("comment")} for c in e["criteria"]],
            "overallComment": e.get("overallComment")}


def expected_score(e):
    sc = [c for c in e["criteria"] if c.get("level") is not None]
    if not sc:
        return None
    return float((Decimal(sum(c["level"] * c["weight"] for c in sc)) / 4).quantize(Decimal("0.1"), ROUND_HALF_UP))


def cell(s, team, a):
    for t in call(s, "rania", "GET", "/api/overview").body["teams"]:
        if t["team"]["name"] == team:
            return next(c for c in t["cells"] if c["assessment"] == a)


def main():
    print(f"Assay API checks against {GW} (Keycloak {KC})")
    for _ in range(30):   # right after a start, the gateway needs a few seconds to find the services
        if call(None, None, "GET", "/api/demo/personas").status == 200:
            break
        time.sleep(2)

    print("== copies, isolation, role switch")
    s1, s2 = new_session("jane"), new_session("jane")
    ids = team_ids(s1)
    ids2 = team_ids(s2)
    check("team ids differ per copy", ids["Beta"] != ids2["Beta"])
    r = copy_call(s1, "rania", "PUT", "/api/demo/session")
    check("role switch keeps the copy (200, same id)", r.status == 200 and r.body["id"] == s1, r)
    s1_today = r.body["today"]
    paris_today = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Paris")).date().isoformat()
    check("today = Paris date (defense day 2)", s1_today == paris_today, f"{s1_today} vs {paris_today}")
    sched = call(s1, "rania", "GET", "/api/schedule").body
    check("defense day 2 is today", len(sched["defenseDays"]) == 3 and sched["defenseDays"][1] == s1_today,
          sched["defenseDays"])
    due = {d["assessment"]: d["dueAt"] for d in sched["dueDates"]}

    def days(iso):
        d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(zoneinfo.ZoneInfo("Europe/Paris"))
        return (d.date() - datetime.date.fromisoformat(s1_today)).days
    offs = {k: days(v) for k, v in due.items()}
    check("due offsets -110/-75/-5/+2/+2", sorted(offs.values()) == [-110, -75, -5, 2, 2], offs)

    print("== grading: Jane, Beta final report (copy 1)")
    beta = ids["Beta"]
    e = ev(s1, "jane", beta, "FINAL_REPORT").body
    check("Jane's draft: DRAFT, 8 of 13", e["status"] == "DRAFT" and e["scoredCount"] == 8 and e["criteriaCount"] == 13,
          (e["status"], e["scoredCount"]))
    check("draft score = sum(level x weight) / 4 so far", e["score"] == expected_score(e), (e["score"], expected_score(e)))
    check("weights add up to 100", sum(c["weight"] for c in e["criteria"]) == 100)
    first = next(c for c in e["criteria"] if c.get("level") is None)
    body = {"criteria": [{"criterionId": c["criterionId"], "level": (2 if c is first else c.get("level")),
                          "comment": c.get("comment")} for c in e["criteria"]], "overallComment": e.get("overallComment")}
    r = call(s1, "jane", "PUT", f"/api/my-evaluations/{beta}/FINAL_REPORT", body)
    check("autosave 200, 9 scored", r.status == 200 and r.body["scoredCount"] == 9, r)
    check("autosave score recomputed", r.status == 200 and r.body["score"] == expected_score(r.body), r)
    r2 = call(s2, "jane", "GET", f"/api/my-evaluations/{ids2['Beta']}/FINAL_REPORT")
    check("other copy untouched by the autosave", r2.body["scoredCount"] == 8)
    h = call(s1, "rania", "GET", f"/api/evaluations/{e['id']}/history")
    check("draft history is coordinator-only (403 for the reviewer)",
          call(s1, "jane", "GET", f"/api/evaluations/{e['id']}/history").status == 403)
    check("draft history records the level change",
          h.status == 200 and any(x["kind"] == "LEVEL_CHANGED" for x in items_of(h.body)), h)
    r = call(s1, "jane", "PUT", f"/api/my-evaluations/{beta}/FINAL_REPORT", {})
    check("autosave with no criteria is a 400", r.status == 400, r)
    full = draft_body(ev(s1, "jane", beta, "FINAL_REPORT").body)
    r = call(s1, "jane", "POST", f"/api/my-evaluations/{beta}/FINAL_REPORT/submit", full)
    check("submit 200, SUBMITTED, score = rule",
          r.status == 200 and r.body["status"] == "SUBMITTED" and r.body["score"] == expected_score(r.body), r)
    check("submitted on time: submittedLate false",
          r.status == 200 and r.body["submittedLate"] is False and r.body["overdue"] is False, r)
    c = cell(s1, "Beta", "FINAL_REPORT")
    check("team grade final during the submit call", c["state"] == "FINAL" and c["grade"] is not None, c)
    team = call(s1, "rania", "GET", f"/api/teams/{beta}").body
    fr = next(a for a in team["assessments"] if a["assessment"] == "FINAL_REPORT")
    scores = [x["score"] for x in fr["reviewers"]]
    avg = float((Decimal(str(sum(scores))) / len(scores)).quantize(Decimal("0.1"), ROUND_HALF_UP))
    check("team grade = plain average of the 3 reviewers", fr["grade"] == avg, (fr["grade"], scores))
    r = call(s1, "jane", "POST", f"/api/my-evaluations/{beta}/FINAL_REPORT/submit", full)
    check("submit again is retry-safe (200)", r.status == 200, r)
    r = call(s1, "jane", "PUT", f"/api/my-evaluations/{beta}/FINAL_REPORT", full)
    check("autosave after submit: 409 evaluation-submitted", r.status == 409 and r.code == "evaluation-submitted", r)

    print("== late submission: Karim, Delta advisor (copy 1)")
    delta = ids["Delta"]
    k = ev(s1, "karim", delta, "ADVISOR_ASSESSMENT").body
    check("Karim's Delta advisor draft is overdue", k["overdue"] is True and k["status"] == "DRAFT",
          (k["status"], k["overdue"]))
    # Race an autosave against the submit: the autosave must lose cleanly (409) or land before it.
    kb = draft_body(k, 2)
    out = {}

    def sub():
        out["submit"] = call(s1, "karim", "POST", f"/api/my-evaluations/{delta}/ADVISOR_ASSESSMENT/submit", kb)

    def put():
        out["put"] = call(s1, "karim", "PUT", f"/api/my-evaluations/{delta}/ADVISOR_ASSESSMENT", kb)
    ts = [threading.Thread(target=sub), threading.Thread(target=put)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    check("submit wins over a concurrent autosave", out["submit"].status == 200, out)
    check("concurrent autosave: 200 before, or 409 evaluation-submitting/-submitted",
          out["put"].status == 200 or out["put"].code in ("evaluation-submitting", "evaluation-submitted"), out["put"])
    print(f"       (race outcome: autosave {out['put'].status} {out['put'].code})")
    k2 = ev(s1, "karim", delta, "ADVISOR_ASSESSMENT").body
    check("late submit: submittedLate true, overdue false", k2["submittedLate"] is True and k2["overdue"] is False,
          (k2["submittedLate"], k2["overdue"]))
    mt = call(s1, "karim", "GET", "/api/me/assignments").body
    task = next(t for tm in mt["teams"] if tm["team"]["id"] == delta for t in tm["tasks"]
                if t["assessment"] == "ADVISOR_ASSESSMENT")
    check("MyTask carries submittedLate", task["submittedLate"] is True and task["overdue"] is False, task)
    dt = call(s1, "rania", "GET", f"/api/teams/{delta}").body
    rp = next(a for a in dt["assessments"] if a["assessment"] == "ADVISOR_ASSESSMENT")["reviewers"][0]
    check("ReviewerProgress carries submittedLate", rp["submittedLate"] is True, rp)

    print("== reviewer editing: composition and final assessments (copy 1)")
    cur = call(s1, "rania", "GET", f"/api/teams/{beta}").body["reviewers"]
    assign = [{"reviewerId": x["reviewer"]["id"], "role": x["role"]} for x in cur]
    r = call(s1, "rania", "PUT", f"/api/teams/{beta}/reviewers", {"assignments": assign[:1]})
    check("one reviewer only: 422 composition-invalid with problems[]",
          r.status == 422 and r.code == "composition-invalid" and r.body.get("problems"), r)
    revs = items_of(call(s1, "rania", "GET", "/api/reviewers?size=100").body)
    onteam = {a["reviewerId"] for a in assign}
    extra = next(x for x in revs if x["id"] not in onteam)
    jury_out = [a for a in assign if a["role"] == "JURY"]
    swap = [a for a in assign if a is not jury_out[0]] + [{"reviewerId": extra["id"], "role": "JURY"}]
    r = call(s1, "rania", "PUT", f"/api/teams/{beta}/reviewers", {"assignments": swap})
    check("replacing a jury member after Beta's final report is final: 409",
          r.status == 409 and r.code in ("assessment-final", "reviewer-has-submissions"), r)

    print("== release and the student view (copy 1)")
    r = call(s1, "nour", "GET", "/api/me/team/results/FINAL_REPORT")
    check("Nour: Alpha final report released (200)", r.status == 200, r)
    check("Nour can't open Beta (403/404)", call(s1, "nour", "GET", f"/api/teams/{beta}").status in (403, 404))
    r = call(s1, "jane", "POST", "/api/assessments/FINAL_REPORT/release")
    check("a reviewer can't release (403)", r.status == 403, r)
    r = call(s1, "rania", "POST", "/api/assessments/FINAL_REPORT/release")
    check("release final report: Beta, Epsilon, Zeta",
          r.status == 200 and len(r.body["releasedTeamIds"]) == 3 and beta in r.body["releasedTeamIds"], r)
    r = call(s1, "rania", "POST", "/api/assessments/FINAL_REPORT/release")
    check("release again: 409 nothing-to-release", r.status == 409 and r.code == "nothing-to-release", r)
    check("Beta final report RELEASED", cell(s1, "Beta", "FINAL_REPORT")["state"] == "RELEASED")
    check("copy 2 still unreleased", cell(s2, "Beta", "FINAL_REPORT")["state"] == "WAITING")
    st = call(s1, "nour", "GET", "/api/me/team").body
    check("student home: final grade 88.0", st.get("finalGrade") == 88.0 or "88.0" in json.dumps(st), str(st)[:200])

    print("== reviewer view of a team, copy 2")
    b2 = ids2["Beta"]
    r = call(s2, "jane", "GET", f"/api/teams/{b2}")
    check("Jane (jury) can open Beta", r.status == 200, r)
    if r.status == 200:
        a = {x["assessment"]: x for x in r.body["assessments"]}
        others = [x for x in a["FINAL_REPORT"]["reviewers"] if x["reviewer"]["displayName"] != "Jane Smith"]
        check("before final: other reviewers' scores hidden", all(x.get("score") is None for x in others), others)
        check("before final: no spread or disagreement shown",
              a["FINAL_REPORT"].get("spread") is None and a["FINAL_REPORT"]["disagreement"] is False, a["FINAL_REPORT"])
        prop = a["PROPOSAL_PRESENTATION"]
        check("final assessment: every score visible", all(x.get("score") is not None for x in prop["reviewers"]),
              prop["reviewers"])
    r = call(s2, "jane", "GET", f"/api/teams/{ids2['Delta']}")
    check("Jane can't open a team she doesn't review", r.status in (403, 404), r)
    r = call(s2, "jane", "GET", f"/api/evaluations?teamId={b2}&assessment=FINAL_REPORT")
    check("Jane can't read other reviewers' levels before final",
          r.status in (403, 404) or all(x["reviewer"]["displayName"] == "Jane Smith" for x in items_of(r.body)), r)

    print("== overview: CSV, history, disagreement, insights (copy 2)")
    r = call(s2, "rania", "GET", "/api/overview/export", accept="text/csv, */*;q=0.1")
    rows = list(csv.reader(io.StringIO(r.body))) if isinstance(r.body, str) else []
    check("CSV export 200 text/csv, header + 6 teams",
          r.status == 200 and "text/csv" in r.headers.get("Content-Type", "") and len(rows) >= 7,
          (r.status, r.headers.get("Content-Type"), len(rows)))
    check("CSV has a download name", "attachment" in r.headers.get("Content-Disposition", ""),
          r.headers.get("Content-Disposition"))
    r = call(s2, "rania", "GET", f"/api/activity?teamId={b2}")
    items = items_of(r.body)
    check("team history: Beta entries only", r.status == 200 and items and all(b2 in json.dumps(x) for x in items),
          (r.status, len(items)))
    o = call(s2, "rania", "GET", "/api/overview").body
    check("Delta progress report flagged (spread 50)", cell(s2, "Delta", "PROGRESS_REPORT")["disagreement"] is True)
    ins = o["insights"]
    check("insights: threshold 15, 10 bands, disagreements largest first",
          ins["disagreementThreshold"] == 15 and len(ins["finalGradeDistribution"]) == 10
          and ins["disagreements"][0]["spread"] >= ins["disagreements"][-1]["spread"], ins["disagreementThreshold"])
    check("KPI resultsReleasable from server", o["kpis"]["resultsReleasable"] == 6, o["kpis"])

    print("== schedule conflict fix and rubric editor (copy 2)")
    sc = call(s2, "rania", "GET", "/api/schedule").body
    check("seed has one jury conflict", len(sc["conflicts"]) >= 1, sc["conflicts"])
    if sc["conflicts"]:
        tid = sc["conflicts"][0]["teams"][-1]["id"]
        slot = next(x for x in sc["slots"] if x["team"]["id"] == tid)
        busy = {x["startsAt"] for x in sc["slots"]}
        start = datetime.datetime.fromisoformat(slot["startsAt"].replace("Z", "+00:00"))
        new = next(start + datetime.timedelta(hours=h) for h in range(1, 9)
                   if (start + datetime.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ") not in busy)
        when = new.strftime("%Y-%m-%dT%H:%M:%SZ")
        r = call(s2, "rania", "PUT", f"/api/teams/{tid}/defense-slot", {"startsAt": when, "room": slot["room"]})
        check("moving the slot keeps its room", r.status == 200 and r.body["room"] == slot["room"], r)
        check("conflict gone after the move", not call(s2, "rania", "GET", "/api/schedule").body["conflicts"], r)
        r = call(s2, "rania", "PUT", f"/api/teams/{tid}/defense-slot", {"startsAt": when})
        check("slot without a room: 400", r.status == 400, r)
    rb = call(s2, "rania", "GET", "/api/rubrics/FINAL_PRESENTATION").body
    crit = [{"id": c["id"], "name": c["name"], "weight": c["weight"], "descriptions": c["descriptions"]}
            for c in rb["criteria"]]
    bad = json.loads(json.dumps(crit))
    bad[0]["weight"] -= 5
    r = call(s2, "rania", "PUT", "/api/rubrics/FINAL_PRESENTATION", {"criteria": bad})
    check("rubric weights != 100: 422 weights-not-100", r.status == 422 and r.code == "weights-not-100", r)
    good = json.loads(json.dumps(crit))
    good[0]["weight"] -= 5
    good[1]["weight"] += 5
    good[0]["name"] += " (edited)"
    r = call(s2, "rania", "PUT", "/api/rubrics/FINAL_PRESENTATION", {"criteria": good})
    check("rubric save 200 or 409 when locked by submissions", r.status in (200, 409), r)
    print(f"       (rubric save: {r.status} {r.code})")
    if r.status == 200:
        check("updatedBy is Rania", (r.body.get("updatedBy") or {}).get("displayName") == "Rania Haddad",
              r.body.get("updatedBy"))
    r = call(s2, "jane", "PUT", "/api/rubrics/FINAL_PRESENTATION", {"criteria": good})
    check("a reviewer can't edit a rubric (403)", r.status == 403, r)

    print("== sessions, reset, rate limits")
    r = call(str(uuid.uuid4()), "jane", "GET", "/api/me")
    check("unknown copy: 404 demo-session-not-found", r.status == 404 and r.code == "demo-session-not-found", r)
    r = call(None, "jane", "GET", "/api/me")
    check("no session header: 400 demo-session-required", r.status == 400 and r.code == "demo-session-required", r)
    r = copy_call(s2, "jane", "POST", "/api/demo/session/reset")
    check("reset: new id", r.status in (200, 201) and r.body["id"] != s2, r)
    new_id = r.body["id"] if r.status in (200, 201) else s2
    check("old id 404 after reset", call(s2, "jane", "GET", "/api/me").status == 404)
    check("new id serves the seed again (Beta FR 2 of 3)", cell(new_id, "Beta", "FINAL_REPORT")["state"] == "WAITING")
    # The browsing allowance is per client IP, and every call of this script shares one, so the checks above have
    # spent part of it. A visitor arrives with a full allowance: wait until it has refilled, as the gateway reports.
    burst_size = 40
    capacity = wait_for_full_allowance(s1, "jane")
    check(f"the browsing allowance holds a {burst_size}-call burst", capacity >= burst_size, capacity)
    codes = []

    def burst():
        codes.append(call(s1, "jane", "GET", "/api/me/assignments").status)
    th = [threading.Thread(target=burst) for _ in range(burst_size)]
    [t.start() for t in th]
    [t.join() for t in th]
    check(f"{burst_size} quick calls: no 429 (browsing allowance)", 429 not in codes, codes)
    check(f"{burst_size} quick calls: all 200", set(codes) == {200}, codes)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:   # a check that couldn't even run (missing field, stack down) counts as a failure
        import traceback
        traceback.print_exc()
        check(f"the checks ran to the end ({type(e).__name__})", False, e)
    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed")
    for _, name, info in failed:
        print("FAILED:", name, info)
    sys.exit(min(len(failed), 100))
