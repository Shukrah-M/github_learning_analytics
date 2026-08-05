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
- execution of the extraction workflow through a unified pipeline;
- behavioural metric calculation (commit, issue, pull-request);
- an experimental composite experimentation-intensity score;
- an NLP classifier for repository text (see `docs/nlp_classifier_validation.md`);
- a responsive web dashboard for browsing repositories and results.

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
- scikit-learn (NLP classifier)
- Flask (dashboard)
- Git
- GitHub

---

## Project Structure

```text
GitHub-Learning-Analytics-System/
│
├── analytics/
│   ├── nlp/
│   │   ├── classifier.py
│   │   └── repository_texts.py
│   ├── commit_metrics.py
│   ├── issue_metrics.py
│   ├── pull_request_metrics.py
│   ├── experimentation_score.py
│   └── repository_analysis.py
│
├── dashboard/
│   ├── app.py
│   ├── csrf.py
│   ├── charts.py
│   ├── templates/
│   └── static/css/style.css
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
│   ├── pull_requests.py
│   └── pipeline.py
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
| `extractor/pipeline.py` | Shared extract-and-save sequence, used by `app.py` and the dashboard's "Add repository" form |
| `dashboard/csrf.py` | CSRF token helpers for the "Add repository" form |

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

## Running the Dashboard

The dashboard is a Flask web app that reads directly from the same
PostgreSQL database as the extraction pipeline. It is a **responsive
web app**, not separate native builds: run it once on a Windows or
macOS machine that has Python and Postgres access, then open it from
any browser — the same machine, or another device (iPhone, iPad,
another laptop) on the same network.

1. Install dependencies (once):

   ```powershell
   pip install -r requirements.txt
   ```

2. Add `FLASK_SECRET_KEY` to `.env` if it isn't already there:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   and put the output in `.env` as `FLASK_SECRET_KEY=<value>`.

3. Optionally train the NLP model
   (`python -m scripts.train_nlp_classifier` — the dashboard still
   works without this, it just skips the NLP section).

4. Optionally enable HTTPS (see "HTTPS" below). If skipped, the
   dashboard serves plain HTTP.

5. Start the dashboard:

   **Windows (PowerShell):**

   ```powershell
   python dashboard/app.py
   ```

   **macOS / Linux:**

   ```bash
   python3 dashboard/app.py
   ```

6. Open it:

   - On the same machine: `http://127.0.0.1:5000` (or `https://` if
     HTTPS is enabled)
   - From another device on the same Wi-Fi (e.g. a phone): find this
     machine's local IP address (`ipconfig` on Windows, `ifconfig`
     or `ipconfig getifaddr en0` on macOS) and open
     `http://<that IP>:5000` (or `https://`) in the device's browser.

### HTTPS

The dashboard can serve HTTPS using a locally trusted certificate
generated with [mkcert](https://github.com/FiloSottile/mkcert),
rather than a self-signed one that triggers browser warnings.

1. Install mkcert (once):

   ```powershell
   winget install --id FiloSottile.mkcert -e
   ```

2. Install its local certificate authority — **this changes your
   system's trusted-certificate store, so run it yourself**:

   ```powershell
   mkcert -install
   ```

3. Generate a certificate covering this machine and its LAN IP
   (replace `10.124.184.253` with the output of `ipconfig`
   /`ifconfig`):

   ```powershell
   mkdir dashboard\certs
   cd dashboard\certs
   mkcert -cert-file dashboard.pem -key-file dashboard-key.pem localhost 127.0.0.1 ::1 10.124.184.253
   cd ..\..
   ```

`dashboard/app.py` automatically serves HTTPS if
`dashboard/certs/dashboard.pem` and `dashboard-key.pem` exist, and
falls back to plain HTTP otherwise. These files are machine-specific
(bound to your LAN IP) and gitignored — regenerate them if you move
to a different machine or network.

#### Trusting it on other devices (phone, tablet, another laptop)

Without this step, other devices on your Wi-Fi can still reach the
dashboard over HTTPS, they'll just see a one-time certificate
warning. To get a clean padlock everywhere, copy
`mkcert -CAROOT`'s `rootCA.pem` (the CA's **public** certificate only
— never share `rootCA-key.pem`) to each device and install it as a
trusted root certificate:

- **iOS**: AirDrop or email `rootCA.pem` to the device, open it (installs
  a profile), then go to Settings → General → VPN & Device Management
  and install the profile, then Settings → General → About →
  Certificate Trust Settings and enable full trust for it.
- **Android**: send the file to the device, open Settings → Security
  → Encryption & credentials → Install a certificate → CA certificate,
  and select the file.
- **macOS**: double-click `rootCA.pem` to add it to Keychain Access,
  then open it in Keychain Access and set "Always Trust" under the
  Trust section.
- **Windows**: double-click `rootCA.pem` → Install Certificate → Local
  Machine → place it in "Trusted Root Certification Authorities".

This only affects devices you explicitly install it on — it does not
make the dashboard reachable from anywhere it wasn't already (still
LAN-only, per the network it's running on).

### Adding repositories

The dashboard is open — no account or login is needed. Anyone who can
reach the page can browse every repository and add new ones through
the "Add repository" button rather than editing `.env` — enter a
GitHub owner and repository name, and the server extracts it using the
`GITHUB_TOKEN` already configured in `.env`. Every repository added
this way is visible to everyone who opens the dashboard.

For each repository, the dashboard shows its behavioural metrics, the
experimentation-intensity score breakdown, a commit-activity
sparkline, and the NLP category distribution with a learning-quality
indicator. All charts are rendered as inline SVG with no
external/CDN dependency, so the page looks and works the same whether
it is loaded locally or over a phone's browser.

The dashboard is open to anyone who can reach it — there's no login.
Running it locally, that means your trusted network only. If you
deploy it publicly (see below), the app has some protection against
abuse (rate limiting on adding repositories, debug mode off by
default), but it's still an unauthenticated app that anyone with the
link can use — keep that in mind before sharing it widely.

---

## Deploying Publicly

The source is public at
[github.com/Shukrah-M/github_learning_analytics](https://github.com/Shukrah-M/github_learning_analytics)
— anyone can clone or download it and run it themselves, locally,
following the steps above.

To make a *running instance* reachable from anywhere (not just your
local network), it needs real hosting. **Account creation, billing,
and clicking "Deploy" are steps only you can do** — I can prepare the
app and give you exact steps, but I can't sign up for a service or
enter payment details on your behalf.

Recommended: **[Render](https://render.com)** — free tier for the web
service, handles HTTPS automatically via Let's Encrypt (no more
manual certificates), and deploys straight from the GitHub repo.

1. **Create a Postgres database.** In the Render dashboard: New →
   PostgreSQL. Note the connection details it gives you (host, port,
   database, user, password).

2. **Migrate your local data to it** (optional — skip this if you'd
   rather start with an empty database and re-extract repositories
   there). From your own terminal, with your local Postgres running:

   ```bash
   pg_dump -h localhost -U postgres -d github_learning_analytics -F c -f backup.dump
   pg_restore -h <render-db-host> -U <render-db-user> -d <render-db-name> backup.dump
   ```

   (You'll be prompted for each database's password.)

3. **Create a Web Service.** In the Render dashboard: New → Web
   Service → connect the `github_learning_analytics` GitHub repo.
   Render will detect the `Procfile` automatically
   (`gunicorn dashboard.app:app`); no build command changes needed
   beyond the default `pip install -r requirements.txt`.

4. **Set environment variables** in the Web Service's Settings →
   Environment tab (enter these directly in Render, not to me):

   | Variable | Value |
   |---|---|
   | `GITHUB_TOKEN` | Your GitHub personal access token |
   | `GITHUB_OWNER` | Default owner for `python app.py` CLI use (optional for the dashboard itself) |
   | `GitHub_Repository` | Same, optional |
   | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | From step 1's Render Postgres |
   | `OBSERVATION_START`, `OBSERVATION_END` | Same fixed window as local, e.g. `2026-01-02T00:00:00Z` / `2026-07-01T00:00:00Z` |
   | `FLASK_SECRET_KEY` | Generate a **new** one for production — don't reuse your local one: `python -c "import secrets; print(secrets.token_hex(32))"` |

   Leave `FLASK_DEBUG` unset (it defaults to off, which is what you
   want here).

5. **Deploy.** Render builds and starts the service automatically.
   Your dashboard will be live at `https://<your-service-name>.onrender.com`
   with a trusted certificate — no browser warnings, nothing to
   install on any device.

---

## Data Security

Sensitive credentials are stored using environment variables.

---

## Next Development Stage

Data quality validation (record counts, duplicate-key detection,
foreign-key integrity, timestamp consistency) remains a planned
addition, alongside expanding the NLP gold-standard dataset — the
`reflection` category currently has only 2 labelled examples, which
caps how reliable its classifier predictions can be (see
`docs/nlp_classifier_validation.md`).

Completed so far:

1. commit behaviour metrics;
2. issue behaviour metrics;
3. pull request behaviour metrics;
4. an experimental composite experimentation-intensity score;
5. NLP classification of textual artefacts;
6. controlled-repository metric validation;
7. a responsive web dashboard.

---

## Development Status

This project is under active development as part of an MSc research study.

The current implementation provides the data acquisition and persistence foundation. The behavioural analytics, NLP analysis and dashboard components are planned development stages and are not yet presented as completed functionality.