
# Assumptions and Data Limitations

## 1. General Assumptions

- The supplied assessment data is treated as the primary source of truth.
- Structured records are queried from PostgreSQL, populated through the ingestion pipeline.
- Unstructured documents are retrieved through the document retrieval pipeline.
- Answers requiring multiple sources may combine structured SQL results and unstructured document evidence.
- Information is not assumed to exist merely because a question requests it. If supporting evidence is unavailable, the system should disclose the limitation.
- Evidence references should identify the originating file and, where available, the sheet, row, or page.

## 2. Employee and Organizational Data

- Employee identifiers are treated as the primary identifiers when matching employee records.
- Names and email addresses may be used for entity resolution, but inferred identity matches are not treated as authoritative without supporting evidence.
- An employee's employment status is distinct from whether their AI agent is enabled.
- Office location does not necessarily establish whether an employee works remotely, from an office, or in a hybrid arrangement.

## 3. Financial and Operational Data

- Financial calculations are based on the records available in the supplied exports.
- Period comparisons use the reporting periods specified in the source documents.
- Missing financial metrics are not estimated unless an explicit, documented calculation supports the estimate.
- Totals are not assumed to represent complete company-wide figures when the underlying export has incomplete coverage.

## 4. Engineering and Incident Data

- Jira statuses and story points are interpreted using the supplied Jira export.
- Employee-level story point attribution requires a reliable mapping between assignees and employee records.
- Incident analysis is limited to the incidents and timestamps present in the supplied incident export.
- Git commit attribution across multiple email identities is treated as provisional unless an authoritative identity mapping exists.

## 5. Historical and Temporal Queries

- Historical answers are based on evidence available for the requested date or reporting period.
- A document's creation date, modification date, and the date of an underlying business event are treated as distinct.
- When the exact effective date of a change cannot be established, the system should state that limitation rather than infer a date.

## 6. Missing Information and Conflicting Evidence

- Missing source records are reported as limitations rather than replaced with fabricated values.
- Conflicting records should be surfaced with their respective source references.
- A successful API response does not independently establish factual correctness.
- Confidence levels communicate evidence coverage and retrieval limitations, not a guarantee of correctness.

## 7. Assessment Data Limitations Observed

- Some requested requisition and candidate pipeline details were not present in the retrieved structured records.
- The supplied evidence did not establish all requested board-level financial metrics for July–September 2026.
- The available Jira evidence did not establish all requested epic and employee-level story point details.
- Some incident queries returned incomplete supporting details.
- Git identity resolution may involve inferred aliases that require authoritative confirmation.
- The available General Ledger export does not independently establish the completeness of all summit-related transactions.

These limitations are disclosed rather than silently filled with assumptions.
