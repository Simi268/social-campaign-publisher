# Build Log

## Project

**Social Campaign Publisher**

A backend capstone project for the FlyRank Internship Backend Track.

## AI-Assisted Development

AI tools were used throughout development as a coding and debugging assistant.

### Areas where AI helped

- Designing the FastAPI project structure
- Designing campaign and social post APIs
- Implementing SQLAlchemy models and PostgreSQL persistence
- Implementing social platform adapter architecture
- Implementing publisher worker logic
- Designing idempotent publishing behavior
- Implementing retry handling for HTTP 429 responses
- Implementing encrypted platform credentials
- Implementing HMAC-SHA256 webhook verification
- Implementing stale-worker recovery
- Writing automated tests
- Debugging API and database behavior
- Reviewing terminal output and test results
- Preparing project documentation and README

### Where AI-generated code required verification or changes

AI-generated implementation suggestions were not accepted blindly.

The application was tested through the automated test suite, Swagger/OpenAPI, curl requests, and direct PostgreSQL queries.

During development, API behavior and worker state transitions were checked against the actual database rather than relying only on expected code behavior.

Examples included:

- Verifying that a social post transitions to `PUBLISHED` only after successful delivery processing.
- Verifying that an invalid webhook signature is rejected.
- Verifying that repeated requests with the same idempotency key return the same external post.
- Verifying publisher worker state transitions directly in PostgreSQL.
- Verifying that the complete automated test suite passes.

### Human verification

The final implementation was manually verified using:

- FastAPI Swagger/OpenAPI
- curl requests
- PostgreSQL queries through Docker
- Publisher worker execution
- Webhook requests
- Automated pytest tests

Final test result:

    48 passed, 1 warning

The warning is related to the Starlette/httpx TestClient deprecation and does not cause test failures.

## Documentation

The README and submission files were prepared to match the FlyRank capstone submission requirements.

## Current Status

The core Social Campaign Publisher workflow is implemented and tested.

The project uses the provided fake social platform workflow rather than real social-media accounts, as required by the capstone brief.
