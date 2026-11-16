# Veloxa CXO Cockpit

An evidence-grounded AI decision-support cockpit for Veloxa Technologies, built for the five-day hackathon challenge.

## Project status

**Initial setup / architecture phase.** The architecture and implementation plan are being established before the application modules are built.

## Planned stack

- Java + Spring Boot
- Spring AI
- PostgreSQL
- React + TypeScript
- Maven
- JUnit 5 / Spring Boot Test

The organisers' email is the governing source for the challenge requirements and schedule. Older conflicting challenge material in the release archive is not used as a requirements source.

## Core goals

- Ingest and connect the supplied company records.
- Provide 14 evidence-grounded employee agents.
- Answer executive questions with traceable citations and uncertainty handling.
- Identify and explain material company risks.
- Support point-in-time questions without leaking later information.
- Respond to the four CEO voice-note tasks.
- Maintain at least 25 automated evaluation questions, including uncertainty tests.

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — proposed system architecture, modules, reliability principles, and open decisions.

Additional project documentation will be added as implementation progresses.

## Planned setup

Build and run instructions will be added once the backend and frontend project skeletons are created and their versions are pinned.

## Data handling

Do not commit confidential, sensitive, or unnecessary raw source material to the public repository unless the organisers explicitly require it. Keep source files in a controlled local working directory and commit only the code and permitted artefacts needed for evaluation.
