
# Architecture and Product Decisions

## Purpose

This document records important technical and product decisions made while building the Veloxa CXO Cockpit, including the rationale, alternatives considered, and trade-offs.

---

## 1. Technology Stack

### Decision: Java Spring Boot for the core backend

- **Chosen approach:** Java 25 with Spring Boot 3.5.16.
- **Alternatives considered:** A Python-only backend or a different Java framework.
- **Reason:** Spring Boot provides a structured backend architecture for REST APIs, business logic, persistence, and integration with PostgreSQL.
- **Trade-off:** Requires maintaining a separate AI service for model orchestration.

### Decision: Python FastAPI for the AI service

- **Chosen approach:** FastAPI for retrieval planning, SQL/RAG orchestration, answer generation, and evidence handling.
- **Reason:** Python provides convenient integration with AI models, embedding libraries, and retrieval tooling.
- **Trade-off:** Introduces an additional service and requires reliable inter-service communication.

### Decision: React and TypeScript for the frontend

- **Chosen approach:** React, TypeScript, and Vite.
- **Reason:** Supports a modular interface for employee agents, conversations, and risk monitoring.
- **Trade-off:** Requires separate frontend API integration and state management.

---

## 2. Database and Persistence

### Decision: PostgreSQL as the shared persistence layer

- **Chosen approach:** PostgreSQL stores structured business data, ingestion metadata, document chunks, and agent conversation data.
- **Alternatives considered:** Separate databases for individual services.
- **Reason:** A shared relational database provides consistent access to ingested information and application records.
- **Trade-off:** Services must maintain clear ownership of their respective data and avoid uncontrolled cross-service writes.

### Decision: JSONB for flexible extracted records

- **Chosen approach:** Extracted spreadsheet and CSV records are stored using JSONB-backed structured records.
- **Reason:** Different source files contain different schemas. JSONB allows ingestion without creating a new relational table for every spreadsheet format.
- **Trade-off:** Queries require schema awareness, validation, and a controlled source catalogue.

---

## 3. Ingestion Architecture

### Decision: Separate ingestion from AI orchestration

- **Chosen approach:** A dedicated ingestion service discovers, classifies, extracts, validates, and persists source files.
- **Reason:** Data preparation should not be tightly coupled to question answering.
- **Trade-off:** Adds a separate service and requires job tracking and failure handling.

### Decision: Different processing paths for structured and unstructured data

- **Structured data:** CSV and Excel files are parsed and persisted as extracted records.
- **Unstructured data:** PDF, Word, text, and email documents are processed into document chunks and embeddings.
- **Reason:** Structured data is better suited to exact SQL queries, while unstructured documents require semantic retrieval.
- **Trade-off:** Two retrieval paths must be coordinated for questions requiring both numerical and narrative evidence.

### Decision: Track ingestion status and provenance

- **Chosen approach:** Maintain ingestion jobs, file-level statuses, checksums, and source metadata.
- **Reason:** Makes ingestion progress observable and supports traceability and duplicate handling.
- **Trade-off:** Requires consistent status updates and error handling across processing stages.

---

## 4. AI Retrieval and Answer Generation

### Decision: Hybrid SQL and RAG retrieval

- **Chosen approach:** Use SQL for structured information, RAG for unstructured information, and both when a question requires cross-source reasoning.
- **Alternatives considered:** RAG-only or SQL-only retrieval.
- **Reason:** Business questions may require exact numerical values as well as explanations from emails, documents, and transcripts.
- **Trade-off:** Hybrid retrieval increases orchestration complexity and requires evidence reconciliation.

### Decision: Dynamic source catalogue

- **Chosen approach:** Build retrieval plans using the available structured source catalogue rather than relying exclusively on hardcoded source assumptions.
- **Reason:** New files, sheets, and fields may be introduced during the assessment.
- **Trade-off:** The planner must validate source names and query fields before execution.

### Decision: Evidence-backed answers

- **Chosen approach:** Return source references and evidence identifiers with answers.
- **Reason:** Executives should be able to trace important statements back to the original records.
- **Trade-off:** Citation validation and evidence selection add processing overhead.

### Decision: Explicit uncertainty and limitations

- **Chosen approach:** Surface missing information, conflicting evidence, and retrieval limitations.
- **Reason:** A plausible but unsupported answer is more dangerous than an explicit statement that the evidence is incomplete.
- **Trade-off:** Some questions may receive qualified or incomplete answers rather than definitive responses.

---

## 5. Agent Conversations and Memory

### Decision: Separate employee agents and conversation history

- **Chosen approach:** Maintain individual employee agent identities and persistent conversation records.
- **Reason:** Each agent represents a distinct organizational role and provides a separate conversational context.
- **Trade-off:** Conversation history and agent identity must be managed consistently.

### Decision: Persist conversation messages

- **Chosen approach:** Store conversations and messages in PostgreSQL.
- **Reason:** Enables conversation history retrieval and continuity across sessions.
- **Trade-off:** Requires appropriate context management when constructing future prompts.

---

## 6. Product Behaviour and Safety

### Decision: Do not fabricate missing business information

- **Chosen approach:** Explicitly communicate when the supplied data does not support an answer.
- **Reason:** Executive decisions require reliable evidence.
- **Trade-off:** The system may decline to provide a precise figure when source coverage is incomplete.

### Decision: Restrict sensitive employee inferences

- **Chosen approach:** Do not expose private employee messages or present speculative individual resignation rankings as established facts.
- **Reason:** Protects employee privacy and avoids unsupported sensitive conclusions.
- **Trade-off:** Some requested employee-level insights are intentionally not provided.

### Decision: Distinguish proposals from confirmed changes

- **Chosen approach:** Treat proposed organizational changes, employee requests, and unconfirmed dates as pending until supported by authoritative evidence.
- **Reason:** Prevents tentative statements from becoming incorrect operational facts.
- **Trade-off:** Some answers must retain uncertainty until confirmation is available.

---

## 7. Evaluation and Quality Assurance

### Decision: Maintain a question-based evaluation benchmark

- **Chosen approach:** Evaluate factual retrieval, SQL aggregation, hybrid reasoning, conflicts, and temporal questions.
- **Reason:** API availability alone does not establish answer quality.
- **Trade-off:** Benchmark results require manual review of factual correctness and evidence quality.

### Decision: Preserve automated tests

- **Chosen approach:** Maintain tests across the Java backend, Python AI service, and ingestion service.
- **Reason:** Helps identify regressions when changes are made to retrieval, persistence, and API behaviour.
- **Trade-off:** Test maintenance adds development effort but reduces submission risk.

---

## 8. Future Improvements

The following are potential improvements rather than claims of completed functionality:

- More granular file-level failure recovery.
- Stronger entity resolution using authoritative identity mappings.
- Improved retrieval context management for large evidence sets.
- Expanded benchmark coverage and automated answer-quality evaluation.
- More detailed historical snapshots for reliable as-of-date queries.

---

## 9. Decision Maintenance

New decisions should be added when meaningful architectural or product trade-offs are made.

Existing decisions should be revised when new evidence or assessment requirements justify a change. The rationale and consequences of the change should remain traceable.
