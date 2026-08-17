# Social Campaign Publisher

> **Capstone Project — FlyRank Backend AI Engineering Internship**

A production-style backend for creating, scheduling, and publishing social media campaign posts. Built with FastAPI, PostgreSQL, SQLAlchemy, and Alembic, with reliability and security features such as encrypted credentials, idempotency, retries, failure handling, stale-worker recovery, and signed webhooks.

## Features

- Campaign and social post management
- Instagram and X platform adapters
- Scheduled publishing
- Reliable publisher worker
- Idempotent publishing
- HTTP 429 retry handling
- Encrypted platform credentials
- HMAC-SHA256 signed webhooks
- Publishing failure tracking
- Stale-worker recovery
- PostgreSQL persistence
- Alembic database migrations
- FastAPI Swagger/OpenAPI documentation
- Automated test suite

## Architecture

```text
                         FastAPI
                            |
          +-----------------+-----------------+
          |                 |                 |
     Campaign API      Social Post API    Worker API
          |                 |                 |
          +-----------------+-----------------+
                            |
                     Publisher Worker
                            |
               +------------+------------+
               |                         |
       Credential Service         Platform Adapters
               |                   /           \
       Encrypted Tokens       Instagram         X
               |                   \           /
               +-------------------+-----------+
                                   |
                         Fake Social Platform
                                   |
                            Signed Webhook
                                   |
                              PUBLISHED
```

## Publishing Lifecycle

```text
DRAFT → READY → PUBLISHING → QUEUED → PUBLISHED
                         \
                          → FAILED
```

Stale publishing jobs can be recovered:

```text
PUBLISHING → READY → PUBLISHING
```

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Alembic
- HTTPX
- Pytest
- Docker
- Docker Compose

## Project Structure

```text
social-campaign-publisher/
├── app/
│   ├── adapters/        # Social platform adapters
│   ├── api/             # FastAPI routes
│   ├── content/         # Caption and image processing
│   ├── core/            # Database configuration
│   ├── models/          # SQLAlchemy models
│   ├── platforms/       # Platform specifications
│   ├── schemas/         # Pydantic schemas
│   ├── security/        # Token encryption
│   ├── services/        # Credential services
│   ├── workers/         # Publishing worker
│   └── main.py
├── fake_server/         # Fake social platform
├── migrations/          # Alembic migrations
├── tests/               # Automated tests
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Simi268/social-campaign-publisher.git
cd social-campaign-publisher
```

### 2. Create a virtual environment

Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```cmd
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+psycopg2://publisher:publisher@localhost:5433/social_publisher
TOKEN_ENCRYPTION_KEY=<your-fernet-key>
FAKE_WEBHOOK_SECRET=local-webhook-secret
```

Never commit real secrets.

### 5. Start PostgreSQL

```bash
docker compose up -d
```

### 6. Run database migrations

```bash
alembic upgrade head
```

## Running the Application

Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Start the fake social platform:

```bash
uvicorn fake_server.main:app --port 9000
```

## API Endpoints

### Campaigns

```text
POST /campaigns
GET  /campaigns/{campaign_id}
POST /campaigns/{campaign_id}/publish
```

### Social Posts

```text
POST /campaigns/{campaign_id}/posts
POST /campaigns/posts/{post_id}/ready
```

### Worker

```text
POST /worker/publish-due
```

### Webhooks

```text
POST /webhook/social-delivery
```

### Health

```text
GET /
GET /health
```

## End-to-End Workflow

```text
Create Campaign
      ↓
Create Social Post
      ↓
DRAFT
      ↓
Mark READY
      ↓
Publisher Worker
      ↓
Platform Adapter
      ↓
Fake Social Platform
      ↓
QUEUED
      ↓
Signed Webhook
      ↓
PUBLISHED
```

## Reliability & Security

### Idempotency

Every social post has a unique idempotency key. Repeating the same publishing request returns the original external post instead of creating a duplicate.

### Retry Handling

The publisher handles HTTP `429 Too Many Requests` responses and respects the `Retry-After` header.

### Failure Handling

If publishing fails, the post is marked as:

```text
FAILED
```

The failure reason is stored in the `error_message` field.

### Stale Worker Recovery

Posts stuck in `PUBLISHING` beyond the configured threshold can be returned to `READY` and retried.

### Credential Encryption

Platform access tokens are encrypted before being stored in PostgreSQL.

### Signed Webhooks

Webhook requests are verified using HMAC-SHA256 signatures. Invalid signatures are rejected before the post is modified.

## Testing

Run the complete test suite:

```bash
pytest -q
```

Current verified test result:

```text
48 passed, 1 warning
```

The test suite covers:

- Campaign APIs
- Social post APIs
- Platform specifications
- Platform adapters
- Credential encryption
- Credential persistence
- Signed webhooks
- Publisher worker
- Retry handling
- Idempotency
- Failure handling
- Stale-worker recovery
- Worker API

## Verified Scenarios

### Successful Publishing

```text
READY → PUBLISHING → QUEUED → PUBLISHED
```

### Failed Publishing

```text
PUBLISHING → FAILED
```

The failure reason is persisted in the database.

### Invalid Webhook

```text
Invalid Signature → 400 Bad Request
```

The post remains unchanged.

### Idempotency

```text
Request 1 → external_post_id: instagram-xxxx

Request 2 → same idempotency key
          → same external_post_id
```

No duplicate external post is created.

## Project Status

The core publishing workflow is implemented and verified end-to-end.

```text
Campaign API            ✅
Social Post API         ✅
Platform Adapters       ✅
Scheduling              ✅
Publisher Worker        ✅
Idempotency             ✅
Retry Handling          ✅
Credential Encryption   ✅
Signed Webhooks         ✅
Failure Handling        ✅
Stale Recovery          ✅
Worker API              ✅
PostgreSQL              ✅
Alembic Migrations      ✅
Automated Tests         ✅
End-to-End Demo         ✅
```

## Future Improvements

- Real Instagram and X API integrations
- OAuth-based platform authentication
- Background job queue
- Redis-backed scheduling
- Per-user platform credentials
- Structured logging and metrics
- Distributed worker scaling
- Dead-letter queue for permanently failed posts
