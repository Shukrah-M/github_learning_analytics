# Behavioural Metric Validation Results

## Validation strategy

The behavioural analytics engine was evaluated at two levels.

First, controlled unit tests used in-memory datasets with manually
known expected results. These tests verified the mathematical
correctness of commit, issue and pull-request metrics independently
of PostgreSQL and the GitHub API.

Second, database integration scripts retrieved activity records from
PostgreSQL and passed them through the analytics engine. These tests
verified that the database access layer and behavioural metric
functions operated correctly together.

## Controlled unit tests

The unit tests covered:

- regular and irregular commit patterns;
- empty and single-commit repositories;
- issue closure rates and resolution times;
- repositories containing only open issues;
- pull-request merge and formal review ratios;
- pull requests without reviews;
- empty issue and pull-request collections;
- unified behavioural analytics output.

## Database integration tests

The existing PostgreSQL-based scripts validated:

- commit retrieval and calculation;
- issue and issue-comment retrieval;
- pull-request and review retrieval;
- combined behavioural analytics output.

## Result

All controlled unit tests and database integration checks completed
successfully.
