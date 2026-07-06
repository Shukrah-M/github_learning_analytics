# GitHub-Based Learning Analytics System

## Overview

This project is a GitHub-based learning analytics system developed to support the analysis of entrepreneurial development behaviour through repository activity data.

The system currently extracts structured activity data from GitHub repositories through the GitHub REST API, transforms the returned data, and stores it in a PostgreSQL database for subsequent behavioural and textual analysis.

The project is being developed as part of an MSc research study.

---

## Research Aim

The broader aim of the project is to investigate how GitHub repository activity can be transformed into interpretable indicators of entrepreneurial development behaviour.

The system is intended to support the analysis of behaviours such as:

- iterative development activity;
- development regularity and persistence;
- problem identification and issue-resolution behaviour;
- collaboration and integration activity;
- pull request activity;
- reflection and learning signals contained in textual artefacts.

The current development stage focuses on building and validating the data acquisition and persistence layer required for these later analyses.

---

## Current Development Status

The GitHub data extraction and PostgreSQL persistence pipeline has been implemented and tested.

The system currently supports:

- authenticated access to the GitHub REST API;
- repository metadata extraction;
- commit history extraction;
- issue extraction;
- issue comment extraction;
- pull request extraction;
- pull request review extraction;
- pagination of GitHub API responses;
- transformation of API responses into structured records;
- storage of extracted records in PostgreSQL;
- updating of existing records during repeated pipeline runs;
- execution of the extraction workflow through a unified pipeline.

The full extraction pipeline can be run through:

```powershell
python app.py
```

---

## Current System Architecture

The currently implemented workflow is:

```text
GitHub Repository
        │
        ▼
GitHub REST API
        │
        ▼
Python Extraction Modules
        │
        ▼
Data Transformation
        │
        ▼
SQLAlchemy ORM
        │
        ▼
PostgreSQL Database
```

The planned next stages are:

```text
PostgreSQL Data
        │
        ▼
Data Quality Validation
        │
        ▼
Behavioural Analytics
        │
        ▼
NLP Analysis
        │
        ▼
Interactive Dashboard
```

---

## Technology Stack

The current implementation uses:

- Python
- GitHub REST API
- PostgreSQL
- SQLAlchemy
- Psycopg 3
- Requests
- python-dotenv
- Git
- GitHub

---

## Project Structure

```text
GitHub-Learning-Analytics-System/
│
├── analytics/
│
├── database/
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   └── repository.py
│
├── docs/
│
├── extractor/
│   ├── __init__.py
│   ├── github_api.py
│   ├── repository.py
│   ├── commits.py
│   ├── issues.py
│   └── pull_requests.py
│
├── app.py
├── config.py
├── create_tables.py
├── requirements.txt
└── README.md
```

### Main Components

| Component | Purpose |
|---|---|
| `app.py` | Runs the complete GitHub extraction pipeline |
| `extractor/github_api.py` | Handles GitHub authentication, API requests and pagination |
| `extractor/repository.py` | Extracts repository metadata |
| `extractor/commits.py` | Extracts commit histories |
| `extractor/issues.py` | Extracts issues and issue comments |
| `extractor/pull_requests.py` | Extracts pull requests and formal PR reviews |
| `database/database.py` | Creates the PostgreSQL connection and database sessions |
| `database/models.py` | Defines the SQLAlchemy database models |
| `database/repository.py` | Saves and updates extracted records in PostgreSQL |

---

## Database Design

The current PostgreSQL database contains six activity tables:

```text
repositories
    │
    ├── commits
    │
    ├── issues
    │      └── issue_comments
    │
    └── pull_requests
           └── pull_request_reviews
```

The tables are:

| `repositories` | Stores repository metadata |
| `commits` | Stores commit histories and associated metadata |
| `issues` | Stores issue records |
| `issue_comments` | Stores discussion comments associated with issues |
| `pull_requests` | Stores pull request records and merge information |
| `pull_request_reviews` | Stores formal pull request review records |

Uniqueness constraints and relational links are used to support data integrity and reduce duplicate records during repeated extraction runs.

---

## Current Controlled Test Results

The current controlled test repository produced the following extraction results:

| Repository | 1 |
| Commits | 7 |
| Issues | 1 |
| Issue Comments | 1 |
| Pull Requests | 1 |
| Pull Request Reviews | 0 |

The zero pull request review count reflects the absence of a formal submitted review in the controlled test repository and does not indicate an extraction failure.

The test process has demonstrated successful extraction and persistence of repository activity data, including changes in pull request state.

---

## Data Security

Sensitive credentials are stored using environment variables.

---

## Next Development Stage

The next development stage is data quality validation.

The planned validation checks include:

- record count checks;
- duplicate commit SHA detection;
- duplicate issue number checks within repositories;
- duplicate pull request number checks within repositories;
- missing critical identifier checks;
- foreign-key integrity checks;
- timestamp consistency checks.

Following data validation, development will proceed to:

1. commit behaviour metrics;
2. issue behaviour metrics;
3. pull request behaviour metrics;
4. temporal aggregation and trend analysis;
5. NLP analysis of textual artefacts;
6. metric validation;
7. interactive dashboard development.

---

## Development Status

This project is under active development as part of an MSc research study.

The current implementation provides the data acquisition and persistence foundation. The behavioural analytics, NLP analysis and dashboard components are planned development stages and are not yet presented as completed functionality.