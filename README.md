# Veloxa CXO Cockpit

**An evidence-grounded AI decision-support platform for the leadership of Veloxa Technologies.**

Veloxa CXO Cockpit ingests scattered company records (spreadsheets, emails, documents, transcripts) into one database, then lets a CEO ask questions in plain language and get answers that are backed by traceable sources. When the evidence is missing or contradictory, the system says so instead of guessing.

Built for the five-day Hiyaku Systems Hackathon.

> **Core principle:** evidence over generated answers. The language model interprets questions and explains retrieved information. It never invents company facts.

---

## Table of Contents

- [Key Features](#key-features)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Data Ingestion](#data-ingestion)
- [How Questions Are Answered](#how-questions-are-answered)
- [Evaluation and Testing](#evaluation-and-testing)
- [Privacy and Responsible AI](#privacy-and-responsible-ai)
- [Project Status](#project-status)
- [Known Limitations](#known-limitations)
- [Documentation](#documentation)
- [Data Handling](#data-handling)

---

## Key Features

| Capability | What it does |
|---|---|
| **Multi-format ingestion** | Parses XLSX, CSV, PDF, DOCX, EML and TXT files through one validated, idempotent pipeline |
| **Hybrid retrieval** | Combines SQL (structured facts) with RAG (documents and communications) in a single answer |
| **Traceable citations** | Every answer links back to its source: file, sheet, row, page, email or transcript reference |
| **14 employee agents** | One shared agent implementation, each agent scoped to an employee's role and context |
| **Risk cockpit** | Surfaces material business risks and separates confirmed events from potential risks and unverified concerns |
| **Point-in-time queries** | Answers "what was known on date X" without leaking information that arrived later |
| **CEO voice-note tasks** | Handles the four CEO voice-note tasks, flagging ambiguities and contradictions |
| **Uncertainty handling** | Reports conflicting, incomplete or insufficient evidence explicitly |
| **Privacy guardrails** | Restricts sensitive data before it reaches the model or UI, and refuses speculative individual predictions |

---

## Architecture at a Glance

```text
React + TypeScript Frontend
            |
        REST / HTTP
            |
Java Spring Boot Backend  ---------->  Python FastAPI AI Service
            |                             |             |
            |                        SQL retrieval  RAG retrieval
            |                             |             |
            +-------------------------> PostgreSQL <----+
                                          ^
                                          |
                            Python Ingestion Service
                  (XLSX / CSV / PDF / DOCX / EML / TXT)
```

- The **frontend** only talks to the Spring Boot backend.
- The **backend** owns business rules and API contracts, and coordinates the AI service.
- The **AI service** handles retrieval, evidence preparation and answer generation.
- The **ingestion service** converts raw files into validated records and embedded document chunks.
- **PostgreSQL** is the shared persistence layer.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full design.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Core backend | Java 25, Spring Boot 3.5.16, Spring Data JPA |
| AI service | Python, FastAPI, SQLAlchemy |
| Ingestion service | Python, file-parsing libraries |
| Database | PostgreSQL (JSONB for flexible extracted records) |
| Infrastructure | Docker, Docker Compose |
| Testing | JUnit 5, Spring Boot Test, pytest |
| Build tools | Maven, npm |

---

## Repository Structure

```text
veloxa-cockpit/
├── src/                    # Spring Boot backend (controller, service, repository, entity, dto)
├── ai-service/             # FastAPI AI service (retrieval and answer generation)
├── ingestion-service/      # Python ingestion pipeline (parsers, validators, database)
├── frontend/               # React + TypeScript + Vite executive dashboard
├── agent_evaluation/       # Evaluation question suite and results
├── data/                   # Local working data (not committed, see Data Handling)
├── ARCHITECTURE.md         # System architecture
├── ASSUMPTIONS.md          # Assumptions, with confidence and what would change them
├── TRANSCRIPT_NOTES.md     # Possible transcription errors and contradictions
├── DECISIONS.md            # Technical and product decisions
├── README.md
└── pom.xml
```

---

## Getting Started

### Prerequisites

- Git
- Java 25 and Maven
- Python 3.10+
- Node.js and npm
- Docker and Docker Compose (for the local PostgreSQL database)
- An API key for the configured language model provider

### 1. Clone the repository

```bash
git clone https://github.com/Soumik2426/veloxa-cockpit-soumik.git
cd veloxa-cockpit-soumik
```

### 2. Configure the database connection

The database must be configured in **all three** backend components, using the same PostgreSQL connection details (host, port, database name, username, password):

| Component | Where to configure |
|---|---|
| `ingestion-service` | Its local configuration / environment file |
| `ai-service` | Its local configuration / environment file |
| Spring Boot backend | `src/main/resources/application.yml` |

Also add your language model provider key to the `ai-service` configuration. **Never commit credentials or API keys.**

Make sure PostgreSQL is running before the next step (for example, `docker compose up -d`).

### 3. Run the ingestion pipeline

Create a virtual environment inside `ingestion-service`, install its requirements, and run `pipeline.py`. This automatically populates the database with the supplied company data.

```bash
cd ingestion-service

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the pipeline
python pipeline.py
```

Wait for the pipeline to finish before starting the other services.

### 4. Start the AI service (FastAPI)

Use a separate virtual environment inside `ai-service`.

```bash
cd ai-service

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --port 8000
```

### 5. Start the Spring Boot backend

From the repository root, in a new terminal:

```bash
mvn spring-boot:run
```

### 6. Start the frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

### Default local addresses

| Component | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8080 |
| AI service | http://localhost:8000 |
| PostgreSQL | Local Docker container |

These are development defaults and can be changed in each service's configuration.

---

## Data Ingestion

The ingestion pipeline processes every file through the same stages:

1. **Discovery:** find files, record name, type, location and checksum
2. **Identification:** choose the right parser for the format
3. **Parsing:** extract rows and cells (structured) or text and metadata (unstructured)
4. **Normalisation:** standardise dates, numbers, text and column names while preserving source information
5. **Validation:** required fields, types, ranges, consistency and duplicates; invalid records never silently become facts
6. **Persistence:** store validated records and document chunks in PostgreSQL
7. **Reporting:** track accepted, rejected and duplicate records per file

Repeated runs are made safe through file checksums and per-file tracking (`pipeline_runs` and `batch_files`).

### Latest recorded ingestion run

| Metric | Value |
|---|---:|
| Files discovered | 41 |
| Files processed | 41 |
| Failed files | 0 |
| Extracted records | 1,761 |
| Document chunks with embeddings | 46 |

| Format | Files |
|---|---:|
| XLSX | 11 |
| DOCX | 10 |
| EML | 11 |
| PDF | 7 |
| CSV | 1 |
| TXT | 1 |

These figures describe the recorded ingestion state. They do not prove that every extracted business fact has been independently verified.

---

## How Questions Are Answered

1. Receive the question and identify entities, dates and constraints.
2. Decide whether it needs **SQL**, **RAG**, or **both**.
3. Retrieve structured records and relevant document chunks, each with its source reference.
4. Flag missing or conflicting evidence.
5. Generate the answer from the prepared evidence.
6. Validate the response and return it with citations.

A response includes the answer, supporting evidence, source references, relevant dates, conflicts, evidence limitations and a confidence assessment. An HTTP 200 does not mean a fully supported answer, and the system treats the two separately.

### Time-aware queries

The system separates **event time** (when something happened) from **availability time** (when the company learned of it). A question about what was known on 17 November will not use a report first received on 18 November.

---

## Evaluation and Testing

- **Automated evaluation suite** in `agent_evaluation/` with at least 25 questions covering factual, SQL, document, hybrid, conflicting-information, historical, insufficient-evidence, privacy, relationship and risk questions. At least five cases test missing or conflicting information.
- Evaluation looks beyond HTTP status: answer correctness, evidence relevance, source traceability, completeness, uncertainty handling and appropriate refusal.
- **Unit and integration tests** use JUnit 5 and Spring Boot Test for the backend and pytest for the Python services, with mocked model responses so core tests do not depend on live model output.

```bash
# Backend tests
mvn test

# Python service tests
pytest
```

---

## Privacy and Responsible AI

- Retrieve evidence before answering factual company questions.
- Never invent employee or business information.
- Keep confirmed facts, inferences, uncertain items and conflicts distinct.
- Restrict prohibited sensitive data **before** it reaches the model or UI. Prompt instructions alone are not treated as a security boundary.
- Refuse speculative individual predictions, such as ranking employees by likelihood of resigning, and offer evidence-based aggregate indicators instead.
- Treat conversation history as separate from company records. An agent cannot invent facts about another employee.

---

## Project Status

| Area | Status |
|---|---|
| Frontend | Implemented and confirmed working |
| Spring Boot backend | Implemented |
| Ingestion service and tracking | Implemented and reconciled for the 41 supplied files |
| AI service (SQL + RAG) | Implemented |
| Document chunks and embeddings | Implemented |
| Risk functionality | Implemented |
| Employee agents | Implemented; full requirement verification relies on the agent evaluation |
| Historical queries | Needs further verification against historical test cases |
| CEO voice-note tasks | Supported; individual outcomes should be verified |
| Production deployment | Not established; local development setup only |

---

## Known Limitations

- **Identity resolution:** names differ across spreadsheets, emails and transcripts; stronger alias mapping is needed.
- **Historical reconstruction:** a current snapshot cannot always rebuild past knowledge states; record versioning and availability timestamps would help.
- **Retrieval coverage:** some questions have relevant data that is not retrieved.
- **Evaluation:** some cases show a failed API call, low confidence or incomplete evidence, so the system should not be described as perfectly accurate.
- **Operations:** production authentication, centralised logging, monitoring and deployment automation are future work.

---

## Documentation

| Document | Purpose |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Full system architecture, modules and design principles |
| [`ASSUMPTIONS.md`](ASSUMPTIONS.md) | Assumptions with supporting sources and confidence |
| [`TRANSCRIPT_NOTES.md`](TRANSCRIPT_NOTES.md) | Possible mis-transcriptions and contradictions |
| [`DECISIONS.md`](DECISIONS.md) | Technical and product decisions and their reasoning |

The organisers' email is the governing source for the challenge requirements and schedule. Older conflicting challenge material in the release archive is not used as a requirements source.

---

## Data Handling

Do not commit confidential, sensitive or unnecessary raw source material to this public repository unless the organisers explicitly require it. Keep source files in a controlled local working directory and commit only the code and permitted artefacts needed for evaluation. Credentials and API keys belong in environment variables or local configuration files that are excluded from Git.
