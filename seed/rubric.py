"""Rubric data for the Assay demo seed.

Weights and the Proposal / Progress / Advisor level descriptions come from the
old rubric-service Liquibase seed (09-30-24-initial_data.sql), with obvious typos
fixed. Final report and Final presentation descriptions come from Appendix A of
PRODUCT-BRIEF.md. Each criterion is (name, weight, {4: ..., 3: ..., 2: ..., 1: ...}).
"""

ASSESSMENTS = [
    "PROPOSAL_PRESENTATION",
    "PROGRESS_REPORT",
    "ADVISOR_ASSESSMENT",
    "FINAL_REPORT",
    "FINAL_PRESENTATION",
]

ASSESSMENT_NAMES = {
    "PROPOSAL_PRESENTATION": "Proposal presentation",
    "PROGRESS_REPORT": "Progress report",
    "ADVISOR_ASSESSMENT": "Advisor assessment",
    "FINAL_REPORT": "Final report",
    "FINAL_PRESENTATION": "Final presentation",
}

# Weight of each assessment in the final grade (%).
ASSESSMENT_WEIGHTS = {
    "PROPOSAL_PRESENTATION": 15,
    "PROGRESS_REPORT": 0,
    "ADVISOR_ASSESSMENT": 25,
    "FINAL_REPORT": 30,
    "FINAL_PRESENTATION": 30,
}

ASSESSMENT_ROLE = {
    "PROPOSAL_PRESENTATION": "JURY",
    "PROGRESS_REPORT": "JURY",
    "ADVISOR_ASSESSMENT": "ADVISOR",
    "FINAL_REPORT": "JURY",
    "FINAL_PRESENTATION": "JURY",
}


def _d(e, a, d, b):
    return {"4": e, "3": a, "2": d, "1": b}


RUBRICS = {
    "PROPOSAL_PRESENTATION": [
        ("Project objectives / Expected outcomes", 10, _d(
            "Students presented all the objectives of the project and set out all the outcomes with justification.",
            "Students presented the main objectives of the project and identified the main outcomes.",
            "Students presented some of the objectives of the project or identified marginal outcomes.",
            "Students did not present the objectives of the project and did not identify any outcome.")),
        ("Cite recent developments pertaining to an engineering field", 20, _d(
            "Students cited recent developments pertaining to an engineering field and analysed the relation with the project topic.",
            "Students cited recent developments pertaining to an engineering field related to the project topic.",
            "Students cited recent developments irrelevant to the project topic.",
            "Students did not cite any recent developments.")),
        ("Develop functional requirements by analyzing desired needs", 20, _d(
            "Students developed functional requirements of the project and analysed their dependencies and organized them by priority.",
            "Students developed functional requirements of the project.",
            "Students developed an incomplete set of functional requirements of the project.",
            "Students did not develop any functional requirements.")),
        ("Develop technical and non-technical constraints", 10, _d(
            "Students developed non-technical and measurable technical constraints of the project and related them to functional requirements.",
            "Students developed non-technical and measurable technical constraints of the project.",
            "Students developed incomplete non-technical and technical constraints of the project.",
            "Students did not develop any constraints.")),
        ("Solution specifications", 15, _d(
            "Students provided detailed solution specification for the project supported by models and representation (flowcharts, diagrams, etc.).",
            "Students provided solution specification for the project.",
            "Students provided incomplete solution specification for the project.",
            "Students did not provide solution specification for the project.")),
        ("Future work plan", 10, _d(
            "Students presented a detailed plan for their future work, covering time and resources (software/hardware, etc.) supported by risk management.",
            "Students provided a detailed plan for their future work covering time and resources.",
            "Students provided an incomplete work plan (in terms of time, resources, risk management) for their future work.",
            "Students did not provide a plan for their future work.")),
        ("Oral expression", 10, _d(
            "Students made use of relevant semantics supported by a coherent speech and appropriate body language.",
            "Students made use of relevant semantics supported by a coherent speech.",
            "Students made use of relevant semantics.",
            "Students made use of irrelevant semantics and incoherent speech.")),
        ("Slides quality", 5, _d(
            "Slides followed a structured outline with a proper layout (density, numbering, header/footer, etc.), pertinent verbal transitions and an adapted design.",
            "Slides followed a structured outline with a proper layout (density, numbering, header/footer, etc.).",
            "Slides followed an unstructured outline, or had an improper layout (density, numbering, header/footer, etc.).",
            "Slides followed an unstructured outline and had an improper layout (density, numbering, header/footer, etc.).")),
    ],
    "PROGRESS_REPORT": [
        ("Meeting management", 20, _d(
            "Self-initiated regular meetings (minimum two per month). Minutes of meetings are regularly submitted, template is respected, and all relevant information is covered.",
            "Regular meetings (minimum two per month). Minutes of meetings are regularly submitted, template is respected, and all relevant information is covered.",
            "No regular meetings. Inappropriate minutes of meeting (template is not respected, minimum effort is done to cover meetings topics and guidelines and to submit minutes regularly).",
            "No regular meetings. Missing minutes of meeting.")),
        ("Proposal report", 20, _d(
            "Report respects template and deadline. All items are covered with a high level of relevant details.",
            "Report respects template and deadline. All items are covered.",
            "Report respects template and deadline, but minimal effort is done to cover important items.",
            "Missing or inappropriate proposal report. It does not respect template, and is not submitted on time.")),
        ("Progress report", 20, _d(
            "Report respects template and deadline. All items are covered with a high level of relevant details.",
            "Report respects template and deadline. All items are covered.",
            "Report respects template and deadline, but minimal effort is done to cover important items.",
            "Missing or inappropriate progress report. It does not respect template, and is not submitted on time.")),
        ("Proposed solution and implementation progress", 20, _d(
            "Students proposed a suitable solution incorporating appropriate engineering standards and provided an implementation respecting the solution specification and validated by tests.",
            "Students proposed a suitable solution incorporating appropriate engineering standards and provided an implementation respecting the solution specification.",
            "Students proposed a suitable solution incorporating appropriate engineering standards but did not provide any implementation.",
            "No solution was proposed.")),
        ("Motivation / initiative / creativity", 20, _d(
            "Students were motivated during the project. They took initiative, made their own decisions, and came up with new and creative ideas, propositions, and solutions.",
            "Students showed motivation for their project. They were able to take initiatives to make their work advance.",
            "Students showed little/unstable motivation. Little initiative has been taken.",
            "Students were passive with no motivation. They did not take any initiative in their work.")),
    ],
    "ADVISOR_ASSESSMENT": [
        ("Acquire and apply new knowledge as needed, using appropriate learning strategies (7.1)", 20, _d(
            "Students acquired and applied relevant new knowledge autonomously using appropriate learning strategies.",
            "Students acquired and applied relevant new knowledge with guidance.",
            "Students acquired new knowledge but were not able to apply it.",
            "Students did not acquire new knowledge.")),
        ("Function effectively on a team whose members together provide leadership, create a collaborative and inclusive environment, establish goals, plan tasks, and meet objectives (5.1)", 20, _d(
            "Students collaborated with team members of different backgrounds, in order to establish goals, plan tasks, and meet objectives by using collaborative tools.",
            "Students collaborated with team members of different backgrounds, in order to establish goals, plan tasks, and meet objectives.",
            "Students collaborated with team members of different backgrounds, in order to establish goals, plan tasks, but did not meet objectives.",
            "Students did not establish goals, plan tasks, and meet objectives.")),
        ("Skills for engineering practice", 20, _d(
            "Students showed advanced skills necessary for engineering practice (such as programming, drawing and manipulating equipment).",
            "Students showed skills necessary for engineering practice of the project (such as programming, drawing and manipulating equipment).",
            "Students showed limited skills necessary for engineering practice (such as programming, drawing and manipulating equipment).",
            "Students showed no skills necessary for engineering practice (such as programming, drawing and manipulating equipment).")),
        ("Objectives / Achievement", 20, _d(
            "Students were able to attain the expected objectives and tackled additional ones.",
            "Students attained the expected objectives.",
            "Students did not attain all expected objectives.",
            "Students failed to attain the main objectives.")),
        ("Motivation / initiative / creativity / Meeting management", 20, _d(
            "Students were motivated during the project. They took initiative, made their own decisions, and came up with new and creative ideas, propositions, and solutions. They had self-initiated regular meetings (minimum two per month). Minutes of meetings are regularly submitted, template is respected, and all relevant information is covered.",
            "Students showed motivation for their project. They were able to take initiatives to make their work advance. They had regular meetings (minimum two per month). Minutes of meetings are regularly submitted, template is respected, and all relevant information is covered.",
            "Students showed little/unstable motivation. Little initiative has been taken. They had no regular meetings. Inappropriate minutes of meeting (template is not respected, minimum effort is done to cover meetings topics and guidelines and to submit minutes regularly).",
            "Students were passive with no motivation. They did not take any initiative in their work. They had no regular meetings. Missing minutes of meeting.")),
    ],
    "FINAL_REPORT": [
        ("Project objectives / Outcomes", 10, _d(
            "All objectives are stated clearly and measurably, and each outcome is justified and traced to the results achieved.",
            "The main objectives and outcomes are stated clearly, with partial justification.",
            "Objectives are stated vaguely, or several outcomes are missing.",
            "Objectives and outcomes are barely stated or unclear.")),
        ("Background research / Related works", 10, _d(
            "Recent, relevant works are critically compared, and the gap the project fills is clearly identified.",
            "Relevant works are described and related to the project, with limited comparison.",
            "Few works are cited, or they are described without relating them to the project.",
            "Little or no background research is presented.")),
        ("Develop functional requirements by analyzing desired needs (2.1)", 10, _d(
            "Functional requirements are complete, testable and clearly derived from an analysis of user needs.",
            "The main functional requirements are identified and mostly testable.",
            "Requirements are incomplete or not clearly linked to needs.",
            "Requirements are missing or listed without analysis.")),
        ("Develop technical and non-technical constraints (2.2)", 10, _d(
            "Technical and non-technical constraints (cost, time, ethics, regulations) are fully identified and quantified where possible.",
            "The main technical and non-technical constraints are identified.",
            "Only technical constraints, or only a few constraints, are identified.",
            "Constraints are barely mentioned.")),
        ("Problem formulation", 10, _d(
            "The problem is formulated precisely, with scope, assumptions and success criteria.",
            "The problem is formulated clearly, with minor gaps in scope or success criteria.",
            "The problem formulation is partial or ambiguous.",
            "The problem is not clearly formulated.")),
        ("Incorporate appropriate engineering standards and specifications related to the engineering design (2.3)", 10, _d(
            "Relevant standards are identified, cited and explicitly applied in the design.",
            "Relevant standards are identified and partly applied.",
            "Standards are mentioned but not applied, or are only partly relevant.",
            "Standards are not considered.")),
        ("Propose multiple solutions and evaluate them against functional requirements and constraints (2.4)", 10, _d(
            "Several credible alternatives are evaluated systematically (e.g. with a decision matrix) against requirements and constraints.",
            "At least two alternatives are compared against the main requirements.",
            "Alternatives are mentioned without a structured evaluation.",
            "A single solution is presented with no alternatives.")),
        ("Implement, test and iteratively improve a solution satisfying the specified functional requirements and constraints, considering risks, and making trade-offs (2.5)", 5, _d(
            "The solution is fully implemented, tested against the requirements, and improved over iterations, with risks and trade-offs documented.",
            "The solution is implemented and tested against most requirements, with some iteration.",
            "The implementation is partial or only lightly tested.",
            "The implementation is minimal or untested.")),
        ("Results presentation and analysis", 5, _d(
            "Results are presented clearly with appropriate figures, analysed critically, and compared with the objectives.",
            "Results are presented clearly with some analysis.",
            "Results are presented with little analysis.",
            "Results are missing or unclear.")),
        ("Conclusion and perspectives", 5, _d(
            "The conclusion summarises the achievements against the objectives, discusses limitations, and proposes concrete future work.",
            "The conclusion summarises the achievements and mentions future work.",
            "The conclusion is generic, with little reflection.",
            "The conclusion is missing or unrelated to the work.")),
        ("Make informed judgments by considering the impact of engineering solutions in global, economic, environmental and societal contexts (4.2)", 5, _d(
            "Impacts in all four contexts are analysed and influence design decisions.",
            "Impacts in several contexts are discussed.",
            "Impacts are mentioned briefly.",
            "Impacts are not considered.")),
        ("Demonstrate written communication skills with a range of audiences by writing adequate documents using appropriate format and language (3.1)", 5, _d(
            "The report is well structured, clear and nearly error-free, and follows the required template.",
            "The report is clear and well structured, with minor errors.",
            "The structure is inconsistent or there are frequent language errors.",
            "The report is hard to follow and the template is not respected.")),
        ("Scientific referencing", 5, _d(
            "All sources are cited consistently in a standard style, and the references are recent and relevant.",
            "Sources are cited with minor inconsistencies.",
            "Citations are incomplete or inconsistent.",
            "Sources are missing or not cited.")),
    ],
    "FINAL_PRESENTATION": [
        ("Project objectives / Outcomes", 10, _d(
            "Students presented all the objectives clearly and showed which outcomes were achieved, with evidence.",
            "Students presented the main objectives and outcomes achieved.",
            "Students presented the objectives vaguely or omitted some outcomes.",
            "Students did not clearly present the objectives or outcomes.")),
        ("Background research / Related works", 10, _d(
            "Students positioned the project against recent related work and stated what is new.",
            "Students summarised the relevant related work.",
            "Students mentioned related work briefly, without positioning the project.",
            "Students presented no related work.")),
        ("Develop functional requirements by analyzing desired needs (2.1)", 10, _d(
            "Students explained how the needs led to the requirements and showed that the requirements were met.",
            "Students presented the main requirements and how they were met.",
            "Students listed the requirements without linking them to the needs or results.",
            "Students did not present the requirements.")),
        ("Develop technical and non-technical constraints (2.2)", 10, _d(
            "Students explained the key constraints and how the design respected them.",
            "Students presented the main constraints.",
            "Students mentioned constraints superficially.",
            "Students did not present the constraints.")),
        ("Propose multiple solutions and evaluate them against functional requirements and constraints (2.4)", 10, _d(
            "Students justified the chosen solution through a clear comparison of alternatives.",
            "Students compared the main alternatives briefly.",
            "Students mentioned alternatives without evaluating them.",
            "Students presented only one solution.")),
        ("Implement, test and iteratively improve a solution satisfying the specified functional requirements and constraints, considering risks, and making trade-offs (2.5)", 10, _d(
            "Students demonstrated a working solution (live or recorded), explained the tests and iterations, and discussed the trade-offs.",
            "Students demonstrated a working solution and the main tests.",
            "Students showed a partial solution or limited testing.",
            "Students showed no working solution.")),
        ("Results and analysis", 10, _d(
            "Results were shown clearly, analysed critically, and linked to the objectives.",
            "Results were shown clearly, with some analysis.",
            "Results were shown with little analysis.",
            "Results were missing or unclear.")),
        ("Conclusion and perspectives", 10, _d(
            "Students concluded with achievements, limitations and concrete next steps.",
            "Students concluded with achievements and next steps.",
            "The conclusion was generic.",
            "There was no real conclusion.")),
        ("Demonstrate oral communication skills with a range of audiences by using appropriate verbal and non-verbal language, adopting the appropriate formatting and supporting material (3.2)", 10, _d(
            "The delivery was confident, clear and well timed, every member contributed, and questions were answered precisely.",
            "The delivery was clear and mostly on time, and most questions were answered well.",
            "The delivery was hesitant or over time, or questions were answered partially.",
            "The delivery was hard to follow, and questions were not answered.")),
        ("Slides quality", 10, _d(
            "Slides are clear, consistent and visual, with readable figures and minimal text.",
            "Slides are clear, with minor layout or density issues.",
            "Slides are text-heavy or inconsistent.",
            "Slides are hard to read or poorly organised.")),
    ],
}

# Comment theme of each criterion (used to pick feedback templates).
THEMES = {
    "PROPOSAL_PRESENTATION": ["objectives", "related", "requirements", "constraints", "spec", "plan", "oral", "slides"],
    "PROGRESS_REPORT": ["meetings", "report", "report", "implementation", "motivation"],
    "ADVISOR_ASSESSMENT": ["learning", "teamwork", "skills", "achievement", "motivation"],
    "FINAL_REPORT": ["objectives", "related", "requirements", "constraints", "formulation", "standards",
                     "alternatives", "implementation", "results", "conclusion", "impact", "writing", "referencing"],
    "FINAL_PRESENTATION": ["objectives", "related", "requirements", "constraints", "alternatives",
                           "implementation", "results", "conclusion", "oral", "slides"],
}
