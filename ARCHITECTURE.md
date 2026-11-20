# Veloxa CXO Cockpit — System Architecture

**Project:** Veloxa CXO Cockpit  
**Purpose:** AI-powered executive decision-support platform  
**Architecture:** Modular application with separate frontend, core backend, ingestion service, and AI service  
**Primary Database:** PostgreSQL  
**Status:** Hackathon implementation

---

# 1. Project Overview

## 1.1 Introduction

Veloxa CXO Cockpit is an AI-powered decision-support platform designed to give the leadership team of Veloxa Technologies a unified view of company information.

Company information is distributed across multiple sources, including:

- Employee master records
- Financial and payroll reports
- Emails and internal communications
- Engineering and project-management exports
- Incident reports
- Meeting transcripts
- PDF, Word, Excel, CSV, and text documents
- CEO voice notes and other business updates

The purpose of the application is to ingest these different data sources, organise their information, establish relationships between relevant records, and make the information accessible through an intelligent executive interface.

Instead of manually searching through multiple files, the CEO can ask questions in natural language and receive answers supported by company records.

## 1.2 Primary Objectives

The application is designed to:

1. Centralise information from different company data sources.
2. Support automated ingestion of different file formats.
3. Extract and organise structured and unstructured information.
4. Provide 14 employee-specific AI agents.
5. Support natural-language questions about company operations.
6. Retrieve evidence from structured records and documents.
7. Combine SQL-based retrieval and Retrieval-Augmented Generation (RAG).
8. Identify important business risks and operational concerns.
9. Handle conflicting, incomplete, and uncertain information.
10. Support historical questions based on information available at a particular point in time.
11. Maintain traceability between answers and their original sources.
12. Prevent unsupported conclusions and fabricated information.

## 1.3 Core Design Principle

**The application must prioritise evidence over generated answers.**

The language model is responsible for interpreting questions and explaining retrieved information. It must not independently invent company facts.

When sufficient evidence is unavailable, the system should explicitly communicate the limitation instead of generating an unsupported answer.

---

# 2. Technology Stack

The system uses different technologies for different responsibilities.

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite | Executive dashboard and user interaction |
| Core Backend | Java 25, Spring Boot 3.5.16 | REST APIs, business logic, data access and orchestration |
| AI Service | Python, FastAPI | AI orchestration, retrieval and answer generation |
| Ingestion Service | Python, file-processing libraries | File discovery, parsing, validation and data ingestion |
| Database | PostgreSQL | Centralised application and company data storage |
| ORM / Data Access | Spring Data JPA, SQLAlchemy | Database interaction |
| Containerisation | Docker, Docker Compose | Local database and service environment |
| Testing | JUnit, pytest | Backend, ingestion and AI service testing |
| Frontend Build | npm, Vite | Frontend dependency management and production builds |
| Version Control | Git, GitHub | Source-code management and project history |

## 2.1 Frontend

**React + TypeScript + Vite**

The frontend provides the executive-facing interface.

Its responsibilities include:

- Displaying the CXO dashboard.
- Providing the natural-language question interface.
- Displaying AI-generated responses.
- Showing supporting evidence and source references.
- Displaying risk information.
- Providing access to employee-specific agents.
- Presenting relevant company information in a readable format.

The frontend communicates with the Java backend through REST APIs.

It does not directly access PostgreSQL or independently perform business-data processing.

## 2.2 Core Backend

**Java 25 + Spring Boot 3.5.16**

The Spring Boot application acts as the central application backend.

It is responsible for:

- Exposing REST APIs.
- Managing company-related entities.
- Handling database operations.
- Managing application-level business rules.
- Coordinating ingestion and AI-related workflows.
- Managing employee-agent information and conversations.
- Providing risk-related functionality.
- Returning structured responses to the frontend.

The backend separates responsibilities using controllers, services, repositories, entities, and DTOs.

## 2.3 AI Service

**Python + FastAPI**

The AI service is maintained separately from the Spring Boot application.

Its purpose is to handle AI-related processing without placing all AI orchestration logic inside the Java backend.

Its responsibilities include:

- Receiving natural-language questions.
- Understanding the information required by a question.
- Selecting an appropriate retrieval approach.
- Retrieving relevant structured or unstructured information.
- Supporting hybrid SQL and RAG workflows.
- Preparing evidence for the language model.
- Generating structured responses.
- Handling uncertainty and insufficient evidence.
- Returning answer and evidence information to the application.

The AI service uses the shared PostgreSQL data store for the relevant application data and retrieval operations.

## 2.4 Ingestion Service

**Python-based ingestion application**

The ingestion service is responsible for processing the different files supplied with the assessment.

It is maintained separately from the core Java application and AI service because file parsing and data extraction have different responsibilities from API management and question answering.

Its responsibilities include:

- Discovering input files.
- Identifying file formats.
- Parsing supported formats.
- Extracting structured and unstructured information.
- Validating extracted records.
- Identifying duplicate or previously processed files.
- Tracking ingestion progress.
- Storing extracted information and document chunks.
- Recording ingestion errors and processing results.

The ingestion service is designed to process multiple source formats through a common pipeline.

---

# 3. High-Level System Architecture

The application follows a multi-service architecture with PostgreSQL acting as the shared persistence layer.

The frontend communicates with the Spring Boot backend. The backend coordinates application functionality and communicates with the AI and ingestion-related components where required.

```text
                         CEO / Executive
                                |
                                v
                     React + TypeScript
                         Frontend
                                |
                         HTTP / REST
                                |
                                v
                    Java Spring Boot Backend
                         Core Application
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
       Employee Agent      Executive Query      Risk Analysis
         Management          Management           Module
             |                  |
             |                  v
             |             AI Service
             |              FastAPI
             |                  |
             |          +-------+-------+
             |          |               |
             |          v               v
             |      SQL Retrieval    RAG Retrieval
             |          |               |
             +----------+---------------+
                                |
                                v
                         PostgreSQL
                                ^
                                |
                    Ingestion Service
                         Python
                                |
                  +-------------+-------------+
                  |             |             |
                  v             v             v
               Excel/CSV     PDF/Word      Email/Text
                  |             |             |
                  +-------------+-------------+
                                |
                                v
                       Validation and
                      Normalisation
                                |
                                v
                         PostgreSQL
```

The diagram represents logical responsibilities. The individual services are independently implemented components; not every internal module necessarily communicates directly with every other module.

---

# 4. Project Directory and Component Organisation

The project is organised into separate application areas.

```text
veloxa-cockpit/
│
├── src/
│   └── main/
│       ├── java/
│       │   └── .../
│       │       ├── controller/
│       │       ├── service/
│       │       ├── repository/
│       │       ├── entity/
│       │       ├── dto/
│       │       ├── config/
│       │       └── ...
│       │
│       └── resources/
│           └── application.yml
│
├── ai-service/
│   └── app/
│       ├── ...
│       └── ...
│
├── ingestion-service/
│   └── app/
│       ├── database/
│       ├── ingestion/
│       ├── parsers/
│       ├── validators/
│       └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── agent_evaluation/
│
├── data/
│
├── ASSUMPTIONS.md
├── TRANSCRIPT_NOTES.md
├── DECISIONS.md
├── README.md
├── ARCHITECTURE.md
└── pom.xml
```

The directory structure illustrates the major project areas. Individual package and module names should be kept consistent with the actual repository.

---

# 5. Data Ingestion Architecture

## 5.1 Purpose

The ingestion service is responsible for converting heterogeneous company files into information that can be stored, searched, and used by the application.

The supplied files do not follow a single format or structure. Therefore, the ingestion process must identify the file type and select an appropriate parser.

## 5.2 Supported File Categories

The assessment dataset contains the following file types:

| File format | Quantity | Processing purpose |
|---|---:|---|
| XLSX | 11 | Extract tabular company information |
| CSV | 1 | Extract structured records |
| PDF | 7 | Extract document text |
| DOCX | 10 | Extract Word document content |
| EML | 11 | Extract email content and metadata |
| TXT | 1 | Extract plain-text information |
| **Total** | **41** | |

## 5.3 Ingestion Workflow

The ingestion process follows these stages:

### Stage 1: File Discovery

The service scans the configured input location and identifies files available for processing.

For every discovered file, the system identifies:

- File name
- File extension
- File location
- File type
- File checksum, where applicable

### Stage 2: File Identification

The system identifies the appropriate parser based on the file format.

For example:

- XLSX files are handled by spreadsheet parsers.
- CSV files are handled by CSV parsers.
- PDF files are handled by PDF text extraction.
- DOCX files are handled by Word document parsers.
- EML files are handled by email parsers.
- TXT files are handled by plain-text processing.

### Stage 3: Parsing

The selected parser extracts information from the source file.

For structured files, the service extracts rows, columns, headers, and cell values.

For unstructured files, the service extracts document text and relevant metadata.

### Stage 4: Normalisation

Extracted information is converted into a consistent internal representation.

Normalisation helps the application handle differences in:

- Date formats
- Numeric values
- Text formatting
- Column names
- Missing values
- Whitespace and encoding
- File-specific structures

Normalisation must preserve the original source information so that the extracted data can be traced back to its source.

### Stage 5: Validation

The validation layer checks whether extracted information is suitable for ingestion.

Validation may include:

- Required-field checks
- Data-type checks
- Date validation
- Numeric-range validation
- Record consistency checks
- Duplicate detection
- Source-specific validation rules

Invalid records should not silently become valid company facts.

### Stage 6: Persistence

Validated information is stored in PostgreSQL.

The service records processing details, source information, and ingestion status so that the system can track what was processed.

### Stage 7: Ingestion Reporting

The ingestion process maintains information about:

- Total files discovered
- Files successfully processed
- Failed files
- Records extracted
- Records accepted
- Records rejected
- Duplicate records
- Processing errors

## 5.4 Ingestion Tracking

The ingestion pipeline uses database tracking to maintain visibility into processing operations.

Important tracking entities include:

### Pipeline Runs

A pipeline run represents an execution of the ingestion workflow.

It allows the application to track an ingestion execution and its overall result.

### Batch Files

The batch-files tracking records maintain file-level processing information.

Important fields include:

- `batch_file_id`
- `run_id`
- `source_file`
- `file_checksum`
- `file_status`
- `input_count`
- `accepted_count`
- `rejected_count`
- `duplicate_count`
- `started_at`
- `completed_at`
- `error_message`

These fields help identify whether a particular file was processed successfully and how many records were accepted or rejected.

The file-processing status and pipeline-run status should remain distinct because a single ingestion run can process multiple files.

## 5.5 Duplicate Handling and Idempotency

Repeated ingestion should not silently create duplicate records.

The pipeline uses file-level identification and checksum information to support duplicate detection.

The purpose is to make repeated processing safer and easier to audit.

File-level duplicate detection should not be confused with business-record duplicate detection. Two different files may contain the same business record, so additional validation may be needed at the record level.

---

# 6. Data Storage Architecture

## 6.1 PostgreSQL

PostgreSQL is the central persistence layer.

It stores the information required by the core backend, ingestion pipeline, and AI service.

The database is used for:

- Company records
- Employee information
- Operational and engineering records
- Financial information
- Ingestion tracking
- Extracted document information
- Evidence references
- Document chunks and embeddings
- Agent-related information
- Application results

The shared database allows different services to work with a consistent data store without maintaining independent copies of the entire company dataset.

## 6.2 Data Organisation

The database contains different categories of information.

| Category | Purpose |
|---|---|
| Company entities | Store employees, departments, projects and other business entities |
| Structured records | Store extracted spreadsheet and CSV information |
| Document records | Store extracted information from unstructured files |
| Evidence information | Preserve source references and provenance |
| Ingestion tracking | Record pipeline runs and file-processing results |
| Operational records | Store relevant engineering, incident and business information |
| Agent information | Support employee-agent context and conversations |
| Evaluation records | Support testing and evaluation of AI responses |

The exact table structure is determined by the implemented database entities and source-data requirements.

## 6.3 Flexible Data Storage

Different company files contain different fields and structures.

A rigid table structure for every possible source may become difficult to maintain.

PostgreSQL's JSONB support can be used where flexible extracted records are appropriate.

However, frequently queried business information should use suitable structured columns and relationships wherever possible.

This provides a balance between flexibility and reliable querying.

## 6.4 Important Database Relationships

Business entities should be connected using stable identifiers.

For example:

```text
Employee
   |
   +------ Employee-related records
   |
   +------ Communications
   |
   +------ Project assignments
   |
   +------ Other relevant business records
```

The application should not depend exclusively on employee names to establish relationships.

Names may appear differently across transcripts, emails, and spreadsheets. Potential identity matches should be validated before being treated as confirmed relationships.

---

# 7. Evidence and Provenance Architecture

## 7.1 Why Evidence Tracking Is Important

A generated answer is only useful when the user can understand where the information came from.

The system therefore needs to preserve the relationship between extracted information and the original source.

For example, if an answer states that an employee submitted a resignation letter on a particular date, the application should be able to identify the document supporting that statement.

## 7.2 Evidence Information

Where available, the system should retain:

- Original file name
- File type
- Source location
- Sheet name
- Row number
- Page number
- Email sender
- Email subject
- Email date
- Transcript reference
- Document section
- Related business entity
- Extraction or ingestion reference

Not every source type provides every field.

## 7.3 Source Reliability

Different sources can have different levels of reliability.

For example:

- An employee master spreadsheet may be suitable for official employee details.
- A formal HR email may provide evidence of an approved employment change.
- A meeting transcript may contain a discussion or proposal.
- An informal voice note may contain incomplete or uncertain information.

The system should distinguish between:

1. Directly supported information.
2. Information extracted from a source.
3. Information inferred from multiple sources.
4. Information that remains uncertain.
5. Conflicting information.

It should not silently convert an inference into a confirmed fact.

---

# 8. AI Service and Retrieval Architecture

## 8.1 Purpose

The AI service provides the intelligence layer of the application.

It accepts natural-language questions, retrieves relevant company information, and prepares evidence-supported responses.

The service uses a hybrid retrieval approach.

**SQL retrieval is used for structured information, while RAG is used for relevant unstructured document content.**

## 8.2 Hybrid SQL and RAG

The two retrieval approaches solve different problems.

### SQL-Based Retrieval

SQL is suitable for questions involving structured company information.

Examples:

- How many employees are in a department?
- How many incidents occurred in a given month?
- What is the status of a particular project?
- What is the total number of completed tasks?
- Which records match a specific employee or project?

The AI orchestration layer identifies the required information and uses the appropriate database retrieval process.

Structured answers should be based on database results rather than language-model estimates.

### RAG-Based Retrieval

RAG is useful when the answer depends on information contained in documents or communications.

Examples:

- What concerns did the CEO raise in a meeting?
- Why was a hiring request paused?
- What did an employee mention in an email?
- What was discussed in a project update?
- What evidence supports a particular business decision?

The RAG process retrieves relevant document content and provides it to the language model as contextual evidence.

### Hybrid Retrieval

Some questions require both structured and unstructured information.

For example:

A question about the reason for a delayed engineering release may require:

- Structured project status.
- Engineering issue information.
- Email communications.
- Meeting transcript evidence.

The system should combine the relevant evidence before preparing the response.

## 8.3 Document Chunking and Embeddings

Long documents cannot always be passed to the language model as one complete piece of text.

The RAG workflow therefore divides document content into smaller chunks.

Each chunk should retain its source reference.

The document-processing workflow is:

```text
Original Document
       |
       v
Text Extraction
       |
       v
Text Normalisation
       |
       v
Document Chunking
       |
       v
Embedding Generation
       |
       v
Embedding Storage
       |
       v
Similarity Retrieval
       |
       v
Relevant Evidence
```

The project maintains document chunks and their embeddings to support semantic retrieval.

The source reference must remain associated with the chunk so that the application can trace retrieved text back to the original document.

## 8.4 Question-Answering Workflow

The question-answering process follows this logical sequence:

1. Receive the user's question.
2. Understand the requested information.
3. Identify the relevant entities, dates, and constraints.
4. Determine whether structured retrieval, RAG, or both are required.
5. Retrieve relevant company information.
6. Collect supporting source references.
7. Identify missing or conflicting information.
8. Prepare the evidence context.
9. Generate the response using the configured language model.
10. Validate the response structure and supporting evidence.
11. Return the answer to the application.

The exact retrieval route depends on the question.

## 8.5 Response Structure

An AI response should provide more than a paragraph of generated text.

Where supported by the implementation, the response should contain:

- Answer
- Supporting evidence
- Source references
- Relevant dates
- Conflicting information
- Evidence limitations
- Confidence or evidence-strength assessment

The application should distinguish between a successful API request and a fully supported answer. An HTTP success response does not automatically mean the evidence is complete or the conclusion is correct.

---

# 9. Employee-Specific AI Agents

## 9.1 Requirement

The application must support 14 employee-specific AI agents.

These agents provide an employee-oriented interface for retrieving and discussing relevant company information.

## 9.2 Shared Agent Architecture

Instead of implementing 14 completely separate AI systems, the application uses a shared agent implementation.

Each agent can be associated with:

- Employee identity
- Employee role
- Relevant organisational context
- Relevant company records
- Conversation history

The shared implementation reduces code duplication and makes it easier to maintain consistent retrieval and response behaviour.

## 9.3 Agent Workflow

```text
User Selects Employee Agent
          |
          v
Load Employee Context
          |
          v
Receive User Question
          |
          v
AI Orchestration
          |
          v
Retrieve Relevant Records
          |
          v
Generate Evidence-Based Response
          |
          v
Return Response
```

## 9.4 Agent Memory and Conversations

Agent conversation history can be maintained separately from the shared company knowledge base.

This distinction is important:

- Company knowledge represents information from company records.
- Conversation history represents the interaction between the user and an agent.

Conversation history should not automatically become an authoritative company record.

The system should avoid allowing one employee agent to invent information about another employee.

---

# 10. Executive Query and Orchestration Module

The executive query functionality coordinates the question-answering workflow.

Its responsibilities include:

1. Accept questions from the frontend.
2. Communicate with the AI service.
3. Manage the application-level request and response flow.
4. Return structured results.
5. Handle unavailable or failed AI responses.
6. Preserve relevant source references.
7. Ensure that unsupported information is not presented as established fact.

The Java backend acts as the central application entry point, while the Python AI service handles the dedicated AI processing workflow.

This separation keeps the core application logic independent of the underlying AI provider and retrieval implementation.

---

# 11. Risk Analysis and Executive Cockpit

## 11.1 Purpose

The risk-analysis functionality helps leadership identify important business concerns.

It should bring together relevant company information and highlight issues that may require executive attention.

## 11.2 Risk Sources

Potential risk indicators can come from:

- Employee and organisational records
- Project status
- Engineering issues
- Production incidents
- Hiring and resource constraints
- Financial information
- Emails and meeting discussions
- Leadership updates

## 11.3 Risk Evaluation

Each risk should be evaluated using available evidence.

A risk record or risk assessment should ideally communicate:

- Risk title
- Risk category
- Description
- Supporting evidence
- Potential impact
- Urgency
- Relevant dates
- Confidence or evidence strength
- Recommended follow-up, where justified

## 11.4 Risk Presentation

The cockpit should prioritise risks that require executive attention.

For example, a production incident, a critical employee departure, or a delayed launch may require different levels of attention.

However, a risk indicator should not be presented as a confirmed event unless the underlying evidence supports that conclusion.

The system should clearly distinguish between:

- Confirmed events
- Identified risks
- Potential risks
- Unverified concerns

---

# 12. Historical and Time-Aware Queries

Historical questions require more than storing the date on which an event occurred.

The application must distinguish between two concepts.

## 12.1 Event Time

The time at which an event actually happened.

Example:

An incident occurred on 16 November.

## 12.2 Information Availability Time

The time at which the company or system became aware of the event.

Example:

The incident was reported to management on 18 November.

These dates are not interchangeable.

If the CEO asks what was known on 17 November, a report first received on 18 November must not be treated as information already available on 17 November.

## 12.3 Historical Query Behaviour

The historical query workflow should:

1. Identify the requested cutoff date.
2. Retrieve records relevant to the question.
3. Consider when each record became available.
4. Exclude information that became available after the cutoff.
5. Preserve the distinction between event time and reporting time.
6. Explain limitations where historical information cannot be reconstructed reliably.

This capability depends on preserving sufficient source and record history. A current database snapshot alone cannot always reconstruct what was known in the past.

---

# 13. CEO Voice-Note Requirements

The CEO voice notes form an important part of the assessment.

The application must consider these requirements when answering questions and presenting executive information.

For each voice-note task, the system should retain or identify:

- Original voice-note reference
- Transcript or extracted statement
- Date of the instruction
- Relevant company information
- Supporting evidence
- Any ambiguity or contradiction
- Proposed response or action
- Reasoning behind the conclusion

Voice-note transcripts should not automatically be treated as perfectly accurate.

Uncertain names, dates, and technical terms should be checked against other company records wherever possible.

If two sources disagree, the application should preserve and communicate the disagreement rather than silently choosing one.

---

# 14. Privacy, Security and Responsible AI

The application processes internal company information, including potentially sensitive employee and financial data.

Therefore, privacy must be considered at the application and retrieval levels.

## 14.1 Data Access

The backend should control which information is retrieved and made available for a particular request.

Sensitive information should not be exposed simply because it exists in the database.

## 14.2 Employee Privacy

The application must not expose private employee communications or generate unsupported individual resignation predictions.

For example, a request to rank individual employees by their likelihood of quitting should not be answered through speculation.

Where appropriate, the system can provide evidence-based aggregate workforce indicators instead.

## 14.3 Financial and Sensitive Information

Information that the assessment or application rules prohibit displaying must be restricted before it reaches the language model or the user interface.

Prompt instructions alone are not a sufficient security boundary.

## 14.4 AI Reliability

The AI layer must follow these principles:

- Retrieve evidence before answering factual company questions.
- Avoid inventing employee or business information.
- Distinguish confirmed information from inference.
- Identify conflicting source information.
- Communicate uncertainty.
- Preserve source traceability.
- Avoid exposing prohibited sensitive information.

---

# 15. API and Service Communication

The application uses HTTP-based service communication.

## 15.1 Frontend to Backend

The React application sends requests to the Spring Boot backend through REST APIs.

The backend returns application responses in a structured format.

The frontend is responsible for presenting the returned information, not independently deciding whether a company fact is correct.

## 15.2 Backend to AI Service

The Spring Boot backend communicates with the FastAPI AI service for AI-related processing.

This keeps AI-specific orchestration separate from the core Java application.

The Java backend remains responsible for its application-level business rules and API contracts.

## 15.3 Ingestion Service to Database

The ingestion service processes input files and persists the extracted information and ingestion tracking data in PostgreSQL.

The ingestion service does not need to send every extracted record through the AI service.

## 15.4 Shared Database

The services use PostgreSQL as the common persistence layer.

This avoids unnecessary duplication of company data.

However, shared database access requires consistent schemas, controlled ownership of data structures, and compatible data contracts between services.

---

# 16. Testing and Evaluation Architecture

Testing is required at multiple levels because the application contains independent services and an AI retrieval workflow.

## 16.1 Backend Testing

The Java backend should be tested for:

- REST API behaviour
- Business logic
- Entity and repository behaviour
- Request validation
- Response structure
- Exception handling
- Service integration

## 16.2 Ingestion Testing

The ingestion service should be tested for:

- File discovery
- File-type identification
- Parsing
- Data normalisation
- Validation
- Duplicate handling
- Database persistence
- Error handling

## 16.3 AI Service Testing

The AI service should be evaluated for:

- SQL retrieval correctness
- RAG retrieval correctness
- Hybrid retrieval
- Evidence completeness
- Response generation
- Missing-information handling
- Conflict handling
- API failure handling

## 16.4 Question-and-Answer Evaluation

The project includes an evaluation suite containing questions that test different types of company information retrieval.

The benchmark should cover:

1. Direct factual questions.
2. Structured SQL questions.
3. Document-based questions.
4. Hybrid SQL and RAG questions.
5. Questions involving conflicting information.
6. Historical questions.
7. Questions with insufficient evidence.
8. Privacy-sensitive questions.
9. Questions involving employee and project relationships.
10. Operational and risk-related questions.

At least five evaluation cases should specifically test how the system handles missing or conflicting information.

Evaluation should consider more than whether the API returns HTTP 200.

Important evaluation dimensions include:

- Correctness of the answer
- Relevance of retrieved evidence
- Source traceability
- Completeness
- Handling of uncertainty
- Appropriate refusal
- API reliability

## 16.5 Test Reliability

Where possible, deterministic tests and mocked external AI responses should be used to avoid making core application tests dependent on unpredictable live model output.

---

# 17. Deployment and Runtime Environment

The development environment uses separate services.

| Component | Development address |
|---|---|
| React frontend | `http://localhost:5173` |
| Spring Boot backend | `http://localhost:8080` |
| FastAPI AI service | `http://localhost:8000` |
| PostgreSQL | Local Docker database |

The exact addresses and ports are development configuration values and may differ in another environment.

## 17.1 Docker and PostgreSQL

Docker is used to run PostgreSQL in a controlled development environment.

The database is shared by the relevant application services through configured connection details.

Database credentials should be maintained in environment variables or local configuration files and should not be committed to Git.

## 17.2 Configuration Management

Each service should maintain its own configuration for:

- Database connection
- Service ports
- External AI provider
- Model configuration
- Input directories
- Environment-specific settings

Secrets must be excluded from source control.

---

# 18. Documentation and Decision Tracking

The project maintains separate documentation for requirements, assumptions, contradictions, and technical decisions.

## 18.1 ASSUMPTIONS.md

Records assumptions made during implementation.

Each entry should include:

- Date
- Assumption
- Supporting source
- Confidence
- What evidence would change the assumption

Assumptions should be updated when new evidence proves them incorrect.

## 18.2 TRANSCRIPT_NOTES.md

Records information that may have been misheard, incorrectly transcribed, or contradicted by another source.

Each entry should include:

- Original statement
- Potential transcription issue
- Supporting evidence
- Interpretation
- Conclusion
- Remaining uncertainty

## 18.3 DECISIONS.md

Records important technical and product decisions.

Examples include:

- Database design
- Technology selection
- SQL versus RAG
- Agent architecture
- Ingestion strategy
- Evidence handling
- Privacy restrictions
- Features the cockpit refuses to provide

These documents preserve the reasoning behind the implementation rather than recording only the final code.

---

# 19. Current Implementation Status

The following table distinguishes the components developed in the project from areas that require further verification or enhancement.

| Component | Current status |
|---|---|
| React frontend | Implemented; frontend confirmed working |
| Spring Boot backend | Implemented |
| PostgreSQL integration | Implemented |
| Python ingestion service | Implemented |
| Multi-format file processing | Implemented for the supplied dataset |
| Ingestion tracking | Implemented |
| File-level processing reconciliation | Completed for the 41 supplied files |
| Document chunk storage | Implemented |
| Embedding storage | Implemented |
| AI service | Implemented |
| SQL and RAG retrieval | Implemented |
| Employee-specific agents | Application functionality developed; complete requirement verification should be based on the agent evaluation |
| Risk functionality | Implemented in the application |
| Historical query behaviour | Requires evidence-based verification against historical test cases |
| CEO voice-note requirements | Supported through the project data and application logic; individual task outcomes should be verified |
| Automated evaluation | Implemented; benchmark results require continued review |
| Production deployment | Not established by the local development setup |

## 19.1 Ingestion Snapshot

The completed ingestion reconciliation recorded:

- 41 files discovered.
- 41 files marked as processed.
- 0 failed files in the reconciled pipeline run.
- 1,761 extracted records.
- 46 document chunks with embeddings.

These figures describe the recorded ingestion state and should not be interpreted as proof that every extracted business fact has been independently verified.

## 19.2 Evaluation Considerations

The evaluation suite has identified cases requiring further attention, including:

- A failed API evaluation case.
- Low-confidence answers.
- Missing or incomplete retrieved evidence.
- Historical and identity-resolution limitations.
- Questions requiring better retrieval coverage.

The application should not be described as having perfect answer accuracy merely because the majority of evaluation requests succeeded.

---

# 20. Known Limitations and Future Improvements

The following areas are suitable for further development.

## 20.1 Stronger Identity Resolution

Improve the mapping of people and other entities across spreadsheets, emails, and transcripts.

Possible improvements:

- Explicit identity-mapping records.
- Verified aliases.
- Confidence levels for candidate matches.
- Manual review of ambiguous matches.

## 20.2 Improved Historical Data Management

Preserve sufficient historical information to reconstruct earlier company knowledge states.

This may require:

- Record versioning.
- Availability timestamps.
- Source update history.
- Historical snapshots.

## 20.3 Better Retrieval Coverage

Improve retrieval for questions where relevant information exists in the dataset but is not retrieved.

Possible improvements:

- Better metadata filtering.
- Improved document chunking.
- Better SQL query planning.
- More effective hybrid retrieval.
- Stronger evidence-ranking logic.

## 20.4 Improved Evaluation

Expand the benchmark and investigate every failed or low-confidence result.

Track:

- API failures.
- Retrieval failures.
- Incorrect SQL.
- Irrelevant document chunks.
- Unsupported generated claims.
- Missing citations.
- Incomplete answers.

## 20.5 Operational Improvements

Further improvements may include:

- Better service health monitoring.
- More granular ingestion recovery.
- Stronger database access boundaries.
- Production authentication and authorisation.
- Centralised logging.
- Deployment automation.
- Backup and recovery procedures.

These are future improvements and should not be represented as completed functionality unless implemented and tested.

---

# 21. End-to-End Application Workflow

The following sequence describes how the main components work together.

```text
       COMPANY DATA SOURCES
                |
                v
        INGESTION SERVICE
                |
                v
       FILE IDENTIFICATION
                |
                v
             PARSING
                |
                v
       NORMALISATION AND
           VALIDATION
                |
                v
          POSTGRESQL
                |
                +----------------------+
                |                      |
                v                      v
        STRUCTURED DATA          DOCUMENT DATA
                |                      |
                v                      v
          SQL RETRIEVAL          CHUNK RETRIEVAL
                |                      |
                +----------+-----------+
                           |
                           v
                      AI SERVICE
                           |
                           v
                 EVIDENCE PREPARATION
                           |
                           v
                 RESPONSE GENERATION
                           |
                           v
                 RESPONSE VALIDATION
                           |
                           v
                 SPRING BOOT BACKEND
                           |
                           v
                    REACT FRONTEND
                           |
                           v
                    CEO / EXECUTIVE
```

The ingestion workflow prepares company information before it is used by the query workflow.

The query workflow retrieves the relevant information, generates an answer, and presents the result through the executive interface.

---

# 22. Conclusion

Veloxa CXO Cockpit is designed as an evidence-driven executive decision-support platform.

Its architecture separates the responsibilities of the frontend, core Java backend, Python ingestion service, and Python AI service.

PostgreSQL provides the shared persistence layer for company information, ingestion records, and document-retrieval data.

The ingestion service converts heterogeneous files into usable information. The AI service supports SQL retrieval, RAG, and hybrid question answering. The Spring Boot backend coordinates application functionality, while the React frontend provides the executive interface.

The employee-agent functionality and risk-monitoring capabilities extend the platform beyond a basic document question-answering system.

The most important architectural principle remains:

**Every important answer should be traceable to company evidence. When the evidence is incomplete, contradictory, or unavailable, the system must communicate that limitation rather than inventing an answer.**
