# Evidence

## Social Campaign Publisher

This document records verification evidence for the FlyRank Backend Track capstone.

---

## 1. Campaign and Social Post APIs

### Evidence

FastAPI Swagger/OpenAPI was used to create and inspect campaigns and social posts.

The social post creation endpoint returned:

    201 Created

The created post was persisted in PostgreSQL.

---

## 2. Successful Publishing

### Evidence

Social post:

    ID: 309
    Campaign ID: 371
    Platform: instagram

Initial database state:

    status: QUEUED
    external_post_id: instagram-94ead191e137

After publisher processing:

    status: PUBLISHED
    external_post_id: instagram-94ead191e137
    published_at: 2026-08-17 07:40:01.901872+00

The same external post ID was retained through the publishing lifecycle.

---

## 3. Publisher Worker

### Evidence

The publisher worker successfully processed the social post and updated the database from:

    QUEUED

to:

    PUBLISHED

The final state was verified directly using PostgreSQL.

---

## 4. Signed Webhook Verification

### Test

A webhook request was intentionally sent with an invalid signature.

Command:

    curl -X POST http://127.0.0.1:8000/webhook/social-delivery \
      -H "Content-Type: application/json" \
      -H "X-Webhook-Signature: definitely-wrong-signature" \
      -d "{\"external_post_id\":\"instagram-94ead191e137\"}"

### Result

    {"detail":"Invalid webhook signature"}

The request was rejected.

The social post remained unchanged in PostgreSQL.

---

## 5. Idempotent Publishing

### Test

The fake social platform was reset and a publish request was sent using:

    Idempotency-Key: demo-idempotency-001

The first request returned:

    external_post_id: instagram-aac8ecf27b6f

The exact same publish request was sent again using the same idempotency key.

### Result

The second request returned the same:

    external_post_id: instagram-aac8ecf27b6f

The returned creation timestamp was also unchanged.

This demonstrates that the same idempotency key does not create a duplicate external post.

---

## 6. Automated Tests

### Command

    pytest -q

### Result

    48 passed, 1 warning

The warning is a Starlette/httpx TestClient deprecation warning and does not represent a test failure.

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

---

## 7. Failure Handling

### Verification

The publisher workflow contains failure handling that records publishing failures in the social post record.

Failure information is stored using the:

    error_message

field.

Automated tests covering publisher failure behavior pass as part of the complete test suite.

---

## 8. Stale Worker Recovery

### Verification

The publisher worker includes stale-worker recovery for posts that remain in the publishing state beyond the configured threshold.

Automated stale-worker recovery tests pass as part of:

    pytest -q

Result:

    48 passed, 1 warning

---

## 9. Retry / Rate-Limit Handling

### Verification

The publisher worker contains HTTP 429 handling and Retry-After based retry behavior.

Automated retry-handling tests pass as part of the complete test suite.

Result:

    48 passed, 1 warning

---

## 10. Credential Encryption

### Verification

Platform credentials are encrypted before persistence.

Credential encryption and credential persistence tests pass as part of the complete test suite.

Result:

    48 passed, 1 warning

---

## 11. PostgreSQL Persistence

### Evidence

The final social post state was queried directly from PostgreSQL using Docker:

    docker exec social-publisher-postgres psql ...

The database returned the persisted social post record with:

    id: 309
    campaign_id: 371
    platform: instagram
    status: PUBLISHED
    external_post_id: instagram-94ead191e137

This verifies that publishing state is persisted in PostgreSQL.

---

## 12. End-to-End Publishing Flow

### Verified lifecycle

    DRAFT
      ↓
    READY
      ↓
    PUBLISHING
      ↓
    QUEUED
      ↓
    PUBLISHED

Webhook verification is used to protect delivery-status updates.

---

## 13. Overall Verification

The project currently passes the complete automated test suite:

    48 passed, 1 warning

The core publishing workflow has also been manually verified through Swagger, curl requests, the publisher worker, and PostgreSQL inspection.
