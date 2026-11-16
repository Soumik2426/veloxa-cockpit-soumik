# Veloxa CXO Cockpit --- Architecture

## 1. Project Overview

I am building **Veloxa CXO Cockpit**, an AI-powered decision-support
application for the leadership team of Veloxa Technologies.

Company information is spread across employee records, financial
reports, emails, meeting transcripts, engineering reports and other
documents. The purpose of this application is to bring that information
together so that the CEO can ask questions and get clear answers
supported by actual company records.

The application will help the CEO:

-   Ask questions about employees, projects, finance and company
    operations.
-   See which records support an answer.
-   Identify missing or conflicting information.
-   Review and prioritise important business risks.
-   Ask what the company knew on a particular date.
-   Review responses to the four CEO voice-note tasks.

The system must not make up facts. If the available records do not
support an answer, it must clearly say so.

## 2. Technology Stack

I have chosen the following technologies for this project:

  -----------------------------------------------------------------------
  Layer                   Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                React + TypeScript      Build the CEO
                                                  dashboard, question
                                                  interface, risk view
                                                  and evidence display.

  Backend                 Java + Spring Boot      Implement the REST
                                                  APIs, business logic
                                                  and application
                                                  modules.

  AI integration          Spring AI               Connect the application
                                                  to an LLM and support
                                                  structured responses
                                                  and tool calling.

  Database                PostgreSQL              Store company data,
                                                  employee information,
                                                  source records,
                                                  evidence and historical
                                                  information.

  Backend testing         JUnit 5 + Spring Boot   Test business logic,
                          Test                    APIs, data processing
                                                  and application
                                                  behaviour.

  Build tool              Maven                   Manage Java
                                                  dependencies and build
                                                  the backend
                                                  application.

  Version control         Git + GitHub            Track changes and
                                                  maintain the project
                                                  history.
  -----------------------------------------------------------------------

## 3. High-Level System Architecture

I will build the application as a **modular monolith**. This means there
will be one Spring Boot application, divided into modules with separate
responsibilities. This keeps development and deployment manageable while
keeping the code organised.

``` text
                  CEO / Executive
                         |
                         v
              React + TypeScript UI
                         |
                      REST API
                         |
                         v
                Spring Boot Backend
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
  Data Ingestion    Query & AI       Risk Analysis
      Module        Orchestration       Module
        |                |
        |          +-----+------+
        |          |            |
        |          v            v
        |    Employee Agent   Evidence
        |       Service      Retrieval
        |          |            |
        +----------+------------+
                   |
                   v
               PostgreSQL
```

The diagram shows the main parts of the application and how they
connect. The detailed responsibilities are explained below.

## 4. How the Application Will Work

The application will follow this workflow:

### Step 1: Load the company files

I will build a data-ingestion module to read the files supplied for the
hackathon, including the file formats present in the release such as
CSV, Excel, PDF, Word documents, emails and text transcripts.

The module will validate the information, convert it into a consistent
structure where needed, and store it in PostgreSQL. It will also retain
the original file name and source location so that information can be
traced later.

### Step 2: Organise and connect the information

I will store the important company information in related database
tables. This may include employees, departments, projects, financial
records, engineering work, incidents, emails and meeting records.

For example, an employee record, a leave record and an email may all
relate to the same person. I will connect these records using reliable
identifiers and reviewed identity matches rather than relying on names
alone.

The final database schema will be based on the actual contents of the
supplied files.

### Step 3: Keep track of evidence

I will maintain source details for the information stored in the
database. These details will include the source file, release folder,
sheet and row, page, email or transcript section, where available.

This will allow the application to show exactly where an answer came
from. Original source information will remain distinguishable from
extracted, normalised or inferred information.

### Step 4: Receive the CEO's question

The CEO will ask a question through the React interface. The frontend
will send that question to the Spring Boot backend through a REST API.

The backend will identify what information is needed and retrieve
relevant company records from PostgreSQL.

### Step 5: Prepare an evidence-based answer

The query service will provide the retrieved records to Spring AI, which
will use the configured language model to prepare a structured response.

Before returning the response, the backend will check that it follows
the application's rules. The answer will include supporting source
references, relevant disagreements, and an explanation of the strength
of the available evidence.

If the records do not provide enough information, the application will
say that it cannot determine the answer rather than guessing.

### Step 6: Show the result

The React interface will display the answer, its supporting evidence,
any source disagreement and the confidence or evidence-strength
assessment. The CEO will be able to inspect the referenced records.

## 5. Main Backend Modules

### 5.1 Data Ingestion Module

This module will:

-   Read the supplied company files.
-   Validate and normalise extracted information.
-   Store the information in PostgreSQL.
-   Preserve the original source file and location.
-   Report invalid, unclear or duplicate records for review.

Ingestion should be repeatable without silently creating duplicate
records.

### 5.2 Company Data Module

This module will manage the main company entities and their
relationships, such as:

-   Employees and departments.
-   Projects and engineering work.
-   Financial and payroll records.
-   Emails and meeting records.
-   Incidents and company activities.

The database design will be finalised after reviewing all relevant
source files.

### 5.3 Evidence Retrieval Module

This module will find the company records relevant to a question and
provide their source details.

Each evidence record should retain, where available:

-   Source file and release folder.
-   Source type and exact location.
-   Event date.
-   Date the information became available.
-   Related employee, project or other entity.
-   Verification status and conflict notes.

### 5.4 Employee Agent Module

The application must provide **14 employee-specific AI agents**.

I will use one shared implementation for all 14 agents. Each agent will
have the relevant employee's identity and role context, but all agents
will retrieve information from the same company database and evidence
store.

This avoids maintaining separate copies of company information and helps
keep the agents consistent. The exact 14 people will be identified from
the supplied records and the hackathon requirements before
implementation.

Agents will not invent personal details, work history or activities that
are not supported by the available information.

### 5.5 Executive Query Module

This module will coordinate the question-answering process:

1.  Receive the CEO's question.
2.  Retrieve relevant records.
3.  Check whether the evidence supports an answer.
4.  Use Spring AI to prepare a structured response.
5.  Validate the response before returning it.

The response will contain the answer, source references, any important
conflicts, and an explanation of evidence strength. If evidence is
insufficient, the module will return an explicit unknown or
insufficient-evidence response.

### 5.6 Risk Analysis Module

This module will identify possible company risks and arrange them by
importance.

It will use available company records and defined rules, with AI helping
to explain the findings. Each risk will include its reason, supporting
evidence, potential impact or urgency, and any uncertainty.

A possible risk will not be presented as a confirmed event unless the
records support that conclusion.

### 5.7 Historical Query Module

This module will answer questions about what was known by a particular
date and time.

I will keep two dates separate:

-   **Event date:** when something happened.
-   **Availability date:** when the information became available to the
    company or system.

For example, an incident may have happened on 16 November but only been
reported on 18 November. A question about what was known on 17 November
must not use the later report.

The database must preserve enough history to reconstruct the information
available at the requested cutoff, including when records are later
updated or corrected.

### 5.8 CEO Voice-note Module

This module will support the four CEO voice-note tasks. For each task, I
will record:

-   The voice-note task and release date.
-   The information available at that time.
-   The relevant evidence.
-   The response or action proposed.
-   The reasoning behind the response.

I will follow the deadlines specified in the organiser's email. Where
transcripts are supplied, I will use them as source material and check
uncertain details against other records where possible.

## 6. Database Design Approach

I will design the PostgreSQL schema after inspecting the source files.
The database is expected to cover these areas:

  -----------------------------------------------------------------------
  Data area                           Information stored
  ----------------------------------- -----------------------------------
  Company entities                    Employees, departments, projects
                                      and other entities found in the
                                      data.

  Source files                        Original files and the release
                                      folder they came from.

  Imported records                    Information extracted from the
                                      source files.

  Evidence references                 Links between facts and their
                                      original source locations.

  Communications                      Emails, transcript sections and
                                      related records.

  Historical information              Event dates, availability dates and
                                      record history.

  Conflicts and assumptions           Disagreements between sources,
                                      assumptions and resolution
                                      decisions.

  Application results                 CEO questions, answers and risk
                                      assessments where retaining them is
                                      useful.
  -----------------------------------------------------------------------

I will use stable internal IDs to connect records. I will not use
employee names alone as identifiers. Possible name variations will be
reviewed before records are merged.

## 7. Privacy and Data Protection

Sensitive information must be protected by the backend before it is sent
to the AI model or displayed in the application.

For example, if the source instructions prohibit displaying individual
salary figures, the backend will prevent those figures from being
included in the AI's retrieved context and in the CEO-facing response. I
will not rely only on a prompt telling the AI to hide them.

The application will retrieve only the information needed for a
question, and logs will avoid storing unnecessary sensitive content.

## 8. AI Answer Reliability

I will follow these rules when implementing AI features:

-   Retrieve company records before generating an answer.
-   Support important factual claims with source references.
-   Say when the available information is insufficient.
-   Show conflicting records instead of silently choosing one.
-   Evaluate source quality instead of assuming every export or
    transcript is correct.
-   Verify uncertain names and figures against other available records.
-   Validate the AI's structured response in the backend.
-   Treat confidence as an assessment of the available evidence, not a
    guarantee that the answer is correct.

The language model will help interpret and explain the records. The
supplied company records will remain the source of truth.

## 9. Testing Strategy

I will create at least **25 automated question-and-answer evaluation
cases**. At least five will specifically test whether the application
handles missing or conflicting information correctly.

The tests will cover:

-   Correct retrieval of employees, projects and company records.
-   Correct source references and evidence locations.
-   Refusal to guess when evidence is missing.
-   Detection and reporting of conflicting information.
-   Historical queries that exclude information not yet available at the
    requested time.
-   Protection of sensitive information.
-   Risk assessments supported by actual records.
-   File-ingestion validation and REST API behaviour.

I will use predictable test data and mocks where possible so that the
tests do not depend on unpredictable live AI responses. The complete
test suite will be runnable with one documented command.

## 10. Implementation Plan

I will develop the application in the following order:

1.  Set up the GitHub repository and inspect all released files.
2.  Identify the important people, projects and other company entities.
3.  Design the PostgreSQL schema and source-tracking approach.
4.  Implement and test file ingestion.
5.  Implement evidence retrieval and basic executive question answering.
6.  Implement the 14 employee-specific AI agents.
7.  Implement risk analysis and historical queries.
8.  Complete the four CEO voice-note responses.
9.  Build and run the 25+ automated tests.
10. Connect the React dashboard, complete documentation and verify the
    final submission.

I will prioritise the mandatory requirements before attempting optional
stretch work.

## 11. Decisions to Finalise During Implementation

I will make the following decisions after inspecting the data and
checking the development environment:

-   The exact 14 people who will have employee agents.
-   The final database tables and identity-matching rules.
-   The file-reading libraries needed for the formats supplied.
-   Whether PostgreSQL queries and text search are sufficient or
    semantic/vector search is also needed.
-   The AI model/provider to use, based on availability and project
    requirements.
-   The authentication and deployment approach.

These decisions will be based on the actual source data and the time
available.

------------------------------------------------------------------------

## Summary

I will build a React-based CEO dashboard backed by a Java Spring Boot
application. The backend will organise the company's files in
PostgreSQL, retrieve supporting evidence for questions, use Spring AI to
prepare answers, and provide employee-specific agents, risk analysis and
historical answers.

**The central principle of the project is simple: every important answer
should be supported by company records, and the application should
clearly say when it does not know.**
