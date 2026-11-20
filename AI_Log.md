# Veloxa CXO Cockpit — AI-Assisted Engineering Log

This document records material AI-assisted engineering activities undertaken during the development of the Veloxa CXO Cockpit assessment.

AI tools were used to accelerate design exploration, implementation, debugging, test planning, and documentation. They were treated as engineering assistants, not as authorities on company data or substitutes for technical judgement.

The developer retains ownership of all implementation decisions, source reconciliation, generated code, testing, and final system behaviour.

---

## 1. Architecture and technical design

**Objective:** Translate the assessment requirements into a maintainable architecture covering ingestion, structured storage, document retrieval, employee agents, executive intelligence, risk monitoring, and evaluation.

**AI assistance:**

- Decomposing assessment requirements into implementation workstreams.
- Exploring service boundaries and data flows.
- Evaluating SQL, RAG, and hybrid retrieval approaches.
- Reviewing the interaction between ingestion, persistence, retrieval, and answer generation.

**Engineering judgement:**
AI-generated architectural suggestions were evaluated against the assessment requirements, source data, existing repository, and implementation constraints. Recommendations were not automatically accepted as design decisions.

Significant decisions and their rationale were recorded in `DECISIONS.md`. The implemented architecture was documented in `ARCHITECTURE.md`.

**Outcome:** AI supported architecture exploration and implementation planning. Final design ownership remained with the developer.

---

## 2. Data ingestion, parsing, and data modelling

**Objective:** Build an ingestion pipeline capable of processing the assessment's structured and unstructured data sources while retaining source traceability.

**AI assistance:**

- Parser implementation and debugging.
- Spreadsheet and document extraction.
- Data validation and integrity checks.
- Duplicate handling and source-location reasoning.
- Data-model design and persistence workflows.

**Issues encountered:**

- Spreadsheet extraction required investigation where expected rows were not being parsed.
- Successful file processing did not necessarily establish extraction completeness.
- Parser output needed to be checked against original source content.

**Engineering response:**
Extraction results were reviewed against source files, and targeted validation was used to check the resulting records. Source references were retained so extracted information could be traced back to its origin.

**Outcome:** AI assisted implementation and debugging. Ingestion correctness was evaluated against original data and validation results rather than processing status alone.

---

## 3. SQL, RAG, and hybrid retrieval

**Objective:** Enable the system to answer questions using structured records, unstructured documents, or both.

**AI assistance:**

- SQL query implementation and debugging.
- RAG retrieval and evidence selection.
- Question-routing logic.
- Hybrid retrieval reasoning.
- Answer-generation and citation handling.

**Issues encountered:**

- Relevant evidence could be incomplete or conflicting.
- A successful retrieval operation did not guarantee a correct answer.
- Internal JSON payloads and evidence identifiers were unsuitable for executive-facing presentation.
- Generated answers needed to distinguish established facts from uncertainty.

**Engineering response:**
Retrieved information was checked against original records. SQL, RAG, and hybrid retrieval were retained as distinct retrieval strategies. Evidence validation was not globally bypassed to force answer generation.

**Outcome:** AI supported retrieval development and debugging. Original company records remained the basis for factual answers.

---

## 4. Employee identity and profile correctness

**Objective:** Establish 14 employee agents with consistent identities, designations, departments, and employee-specific context.

**AI assistance:**

- Employee-agent profile construction.
- Identity and context handling.
- Prompt and response behaviour.
- Profile-question handling.

**Issues encountered during testing:**

- Canonical employee names were occasionally misspelled in generated answers.
- Employee-to-department associations were inconsistent.
- Some profile questions failed because they entered the normal evidence-retrieval path.
- Follow-up questions did not always use the selected employee's context.

**Engineering response:**
Canonical employee records and identity mappings were used as the basis for employee names, IDs, and departments. Agent introductions and follow-up conversations were tested against the selected employee.

Corrections were made to profile-question handling and employee-context usage.

**Verification:** The developer manually tested the relevant conversations and confirmed that the corrections were working.

**Outcome:** Employee identity and profile behaviour were corrected and manually verified.

---

## 5. Employee-agent knowledge and question routing

**Objective:** Ensure agents behave like knowledgeable employees rather than simple profile-response bots.

The intended context combines:

- Individual employee identity.
- Shared company knowledge.
- Department-specific expertise.
- Relevant colleague and project awareness.
- Conversation context.

**Issues encountered during testing:**

An identity-focused correction caused agents to repeat their introductions when asked unrelated questions about the company or its technical operations. Some follow-up questions also returned evidence-citation errors.

**AI assistance:**

- Analysing question-intent handling.
- Reviewing identity and company-context separation.
- Improving routing between profile, company, technical, departmental, and cross-department questions.

**Engineering response:**
Actual agent conversations were used to identify the incorrect behaviour. Targeted corrections were preferred over rebuilding the entire agent architecture.

The intended behaviour was clarified:

- Identity determines who is speaking.
- Shared company knowledge enables company-wide answers.
- Department expertise determines the depth of specialist responses.
- Cross-department questions use available supporting evidence.

**Verification:** The developer manually tested the agent conversations and used observed failures to guide subsequent corrections.

**Outcome:** Agent behaviour was iteratively refined and manually verified.

---

## 6. Answer generation and evidence presentation

**Objective:** Present useful, concise, professional answers to executive users.

**Issues encountered:**

- Answers were excessively long.
- File names appeared inside answer prose.
- Raw JSON and internal retrieval identifiers were exposed.
- Supporting evidence was not clearly separated from the answer.

**AI assistance:** Reviewed answer structure, evidence presentation, and response readability.

**Engineering response:**
The response presentation was refined around an answer-first structure, with supporting source files displayed separately. Internal retrieval structures were kept out of the normal user-facing explanation while retaining source traceability.

**Verification:** The developer inspected actual application responses and confirmed the revised presentation behaviour.

---

## 7. Risk Monitor reliability and AI-call efficiency

**Objective:** Make risk assessments persistent and prevent unnecessary generation whenever the Risk Monitor is opened.

**Issues encountered:**

- Opening the Risk Monitor triggered a new AI request.
- AI processing could outlast the frontend waiting period.
- The UI could display an error while processing was still underway.
- Repeated visits could consume unnecessary AI usage.

**AI assistance:**

- Investigating the request lifecycle.
- Reviewing persistence and retrieval behaviour.
- Reasoning about background refresh and duplicate-generation prevention.

**Engineering response:**
The Risk Monitor was changed to persist assessment snapshots and retrieve the latest saved result when the section is opened. Refresh processing was separated from ordinary page loading. Duplicate-generation protections and retention of the previous snapshot on refresh failure were also addressed.

**Verification:** The developer tested the Risk Monitor and confirmed that saved assessments were displayed without generating a new assessment simply because the section was opened.

**Outcome:** The persistent Risk Monitor workflow was implemented and manually verified.

---

## 8. Original source-file access

**Objective:** Allow users to open the original raw files from the Data section.

**Issue encountered:**

The initial Open action redirected users to another frontend page instead of the original source file.

**AI assistance:** Helped investigate the file-opening flow and formulate a targeted correction.

**Engineering response:** The Open action was corrected to target the original source file rather than an unrelated frontend route or database-table view.

**Verification:** The developer manually checked the resulting behaviour.

---

## 9. Historical-query design

**Objective:** Understand and design for the assessment's requirement to answer questions such as "What did we know on date X?"

**AI assistance:** Helped evaluate whether historical questions required a separate memory system or could use the existing database and retrieval infrastructure.

**Engineering conclusion:**

A separate duplicated historical-memory system is not inherently necessary if the existing database retains the relevant historical records and timestamps.

Historical retrieval must distinguish:

- **Event/valid time:** When an event happened or a fact applied.
- **Knowledge/recorded time:** When the information became available to the company or system.

For example, a document received in October may describe an event from August. Its contents must not automatically be treated as information available in August.

**Outcome:** The design discussion favoured date-aware retrieval using the existing data store where sufficient historical records and timestamps exist.

This entry records the design reasoning; it does not claim that every company-wide historical SQL/RAG query has been implemented or verified.

---

## 10. Frontend usability refinements

**Objective:** Improve specific UI areas without disturbing existing functionality.

**AI assistance:**

- Reviewing the employee-agent conversation layout.
- Scoping removal of the "Ask as of date" picker from employee-agent conversations while retaining historical-query functionality elsewhere.
- Reviewing the Overview KPI layout, where only the employee-agent count had a meaningful value.

**Engineering approach:**

- Keep the existing Veloxa colour palette and typography.
- Limit changes to relevant frontend components and styling.
- Avoid unnecessary backend changes for presentation-only work.
- Preserve existing navigation and functionality.

---

## 11. Documentation and assessment compliance

**Objective:** Ensure project documentation reflects the actual implementation.

**AI assistance:** Supported review of:

- `ARCHITECTURE.md`
- `ASSUMPTIONS.md`
- `DECISIONS.md`
- `README.md`
- `TRANSCRIPT_NOTES.md`

**Engineering approach:**

- Document implemented functionality rather than proposed functionality.
- Preserve historical decisions and assumptions.
- Record source conflicts with supporting evidence and the developer's reasoning.
- Avoid allowing AI to decide which conflicting company source is correct.
- Distinguish manual verification from automated test execution.
- Keep setup instructions consistent with actual repository configuration.

**Outcome:** AI supported documentation review. The developer remains responsible for source reconciliation and final assessment decisions.

---

## 12. Engineering controls for AI-assisted development

The following principles governed the use of AI throughout the project:

1. **Review before acceptance:** AI-generated code and explanations were treated as proposals, not proof of correctness.
2. **Source-grounded facts:** Company information was checked against the assessment data room and original records.
3. **Canonical identity:** Employee names and departments were checked against authoritative employee information.
4. **Evidence quality:** Retrieved information was reviewed for relevance, completeness, and contradictions.
5. **Targeted debugging:** Observed failures informed focused corrections instead of unnecessary rewrites.
6. **Regression protection:** Changes were scoped to preserve existing working functionality and project data.
7. **Resource discipline:** Limited AI usage was considered; unnecessary regeneration, repeated ingestion, broad scans, and avoidable model calls were discouraged.
8. **Developer ownership:** Final implementation decisions, source-conflict conclusions, correctness, and the ability to explain the code remain the developer's responsibility.

---

## Maintenance and audit integrity

- Record material AI-assisted engineering work, not every prompt or autocomplete suggestion.
- Add exact dates, tool names, commit references, and test identifiers from actual history. Never guess.
- Record rejected AI suggestions when they materially influenced an engineering decision.
- Update entries if later testing changes the outcome.
- Do not claim an automated test ran unless it actually ran.
- Do not claim a feature is complete merely because it appeared in a plan, prompt, or code change.
- Keep this log factual, concise, and suitable for technical review or an assessment interview.
