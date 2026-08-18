# Evidence

## Social Campaign Publisher

This document records verification evidence for the **FlyRank Internship Backend Track Capstone Project**.

The evidence below is based on automated tests, API requests, and PostgreSQL verification performed during development.

---

## 1. Automated Test Suite

### Command

```bash
pytest -q
```

### Result

```text
49 passed, 1 warning
```

The warning is a Starlette/httpx `TestClient` deprecation warning and does not cause a test failure.

The complete test suite covers:

- Campaign APIs
- Social post APIs
- Platform specifications
- Platform adapters
- Caption composition
- Image processing
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

## 2. Idempotent Publishing

The fake social platform uses the `Idempotency-Key` header to prevent duplicate external posts.

### First Request

```text
POST /publish
Idempotency-Key: demo-idempotency-001
```

Result:

```text
external_post_id: instagram-aac8ecf27b6f
status: queued
```

### Second Request

The same request was sent again using the same idempotency key:

```text
Idempotency-Key: demo-idempotency-001
```

Result:

```text
external_post_id: instagram-aac8ecf27b6f
status: queued
```

The external post ID remained identical.

### Verified Behavior

```text
Request 1
    ↓
instagram-aac8ecf27b6f

Request 2 with same idempotency key
    ↓
instagram-aac8ecf27b6f
```

No duplicate external post was created.

---

## 3. HTTP 429 Retry Handling

The fake platform can intentionally return HTTP `429 Too Many Requests` with a `Retry-After` header.

The publisher adapter:

1. Detects HTTP 429.
2. Reads the `Retry-After` header.
3. Waits for the specified duration.
4. Retries the request.
5. Stops after the configured retry limit.

### Automated Test

```bash
pytest tests\test_publisher_worker.py -q -k "429"
```

### Result

```text
1 passed, 12 deselected
```

The dedicated test verifies that a `429` response with:

```text
Retry-After: 1
```

causes the publisher to wait for the specified duration before retrying and successfully publishing the post.

---

## 4. Stale Worker Recovery

The publisher worker uses the `PUBLISHING` state when a post is claimed.

If a post remains in `PUBLISHING` beyond the configured timeout and has no external post ID, it can be recovered back to `READY`.

### Automated Tests

```bash
pytest tests\test_publisher_worker.py -q -k "stale or recover"
```

### Result

```text
3 passed, 10 deselected
```

The tests verify:

- A stale `PUBLISHING` post is recovered.
- A fresh `PUBLISHING` post is not incorrectly recovered.
- A recovered post can subsequently be published.

### Verified Lifecycle

```text
READY
  ↓
PUBLISHING
  ↓
stale worker state
  ↓
READY
  ↓
PUBLISHING
  ↓
QUEUED
```

### Crash/Restart Note

The stale-worker recovery mechanism is verified through automated tests.

A literal process-kill-mid-flight demonstration was not manually performed because the provided fake social platform responds synchronously and does not provide an artificial in-flight publishing delay.

---

## 5. Successful Publishing

A social post was published through the application and its final state was verified directly in PostgreSQL.

### PostgreSQL Verification

```text
id:               309
campaign_id:      371
platform:         instagram
status:            PUBLISHED
external_post_id: instagram-94ead191e137
error_message:
published_at:     2026-08-17 07:40:01.901872+00
```

The post successfully reached:

```text
PUBLISHED
```

and received an external post ID.

This verifies that the publishing workflow persists its final state in PostgreSQL.

---

## 6. Signed Webhook Verification

Webhook requests are protected using HMAC-SHA256 signatures.

An intentionally invalid signature was sent:

```text
X-Webhook-Signature: definitely-wrong-signature
```

### Command

```bash
curl -X POST http://127.0.0.1:8000/webhook/social-delivery -H "Content-Type: application/json" -H "X-Webhook-Signature: definitely-wrong-signature" -d "{\"external_post_id\":\"instagram-94ead191e137\"}"
```

### Result

```json
{
  "detail": "Invalid webhook signature"
}
```

The request was rejected.

The PostgreSQL record remained unchanged:

```text
status:            PUBLISHED
external_post_id:  instagram-94ead191e137
published_at:      2026-08-17 07:40:01.901872+00
```

This verifies that an invalid webhook signature does not modify the social post.

---

## 7. Platform-Specific Image Variants

The image pipeline generates platform-specific image variants using the platform specifications.

### Automated Tests

```bash
pytest tests\test_image_pipeline.py tests\test_caption_composer.py -q
```

### Result

```text
7 passed in 0.59s
```

The image pipeline verifies:

| Platform | Required Dimensions |
|----------|---------------------|
| Instagram | 1080 × 1080 |
| X | 1600 × 900 |

The image pipeline uses center cropping and resizing to produce the required platform dimensions.

---

## 8. Platform-Specific Captions

Captions are composed using the shared brand voice and platform-specific rules.

The test suite verifies:

- Instagram captions are platform-specific.
- X captions are platform-specific.
- Instagram and X captions are different.

### Verified Tests

```text
test_instagram_caption_is_platform_specific
test_x_caption_is_platform_specific
test_platform_captions_are_different
```

These tests passed as part of:

```text
7 passed in 0.59s
```

---

## 9. Publishing Failure Handling

The publisher worker handles publishing failures by updating the post to:

```text
status → FAILED
error_message → failure reason
```

The failure-handling test verifies that when a platform publisher raises an exception:

- The social post becomes `FAILED`.
- The error message is persisted.
- No external post ID is incorrectly stored.

Verified test:

```text
test_publish_failure_marks_post_failed
```

This test passes as part of the complete test suite.

---

## 10. Encrypted Platform Credentials

Platform access tokens are encrypted before being stored in PostgreSQL.

### Automated Test

```bash
pytest tests\test_credentials_db.py -q
```

### Result

```text
1 passed in 1.13s
```

Verified test:

```text
test_platform_credential_is_stored_encrypted
```

This confirms that platform credentials are not stored as plaintext values.

---

## 11. PostgreSQL Persistence

PostgreSQL is used as the persistent database for campaigns, social posts, and platform credentials.

A published social post was queried directly using Docker:

```bash
docker exec social-publisher-postgres psql -U publisher -d social_publisher -c "SELECT id, campaign_id, platform, status, external_post_id, error_message, published_at FROM social_posts WHERE id = 309;"
```

The resulting record contained:

```text
id               | 309
campaign_id      | 371
platform         | instagram
status           | PUBLISHED
external_post_id | instagram-94ead191e137
error_message    |
published_at     | 2026-08-17 07:40:01.901872+00
```

This verifies that the publishing state is persisted in PostgreSQL.

---

## 12. Publisher Worker

The publisher worker is responsible for:

- Finding due posts.
- Claiming posts.
- Moving claimed posts to `PUBLISHING`.
- Publishing through the platform adapter.
- Recording the external post ID.
- Updating the final publishing state.
- Handling failures.
- Recovering stale publishing jobs.

### Worker Tests

```bash
pytest tests\test_publisher_worker.py -q
```

The worker test suite contains:

```text
test_publish_instagram_post
test_already_published_post_is_rejected
test_unsupported_platform_is_rejected
test_get_due_posts
test_future_post_is_not_due
test_draft_post_is_not_due
test_already_published_post_is_not_due
test_publish_due_posts
test_publish_failure_marks_post_failed
test_recover_stale_publishing_post
test_fresh_publishing_post_is_not_recovered
test_stale_post_is_recovered_and_published
```

The additional HTTP 429 retry test is verified separately.

---

## 13. Durable Job Claiming

Due posts are claimed using database row-level locking:

```text
FOR UPDATE SKIP LOCKED
```

Claimed posts are marked:

```text
PUBLISHING
```

before publishing.

This helps prevent multiple workers from simultaneously claiming the same ready post.

Stale publishing recovery provides a mechanism for returning abandoned jobs to:

```text
READY
```

for another attempt.

---

## 14. API Verification

The application exposes FastAPI endpoints for campaign management, social posts, publishing, workers, and webhooks.

### Campaigns

```text
POST /campaigns
GET /campaigns/{campaign_id}
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

FastAPI Swagger/OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## 15. End-to-End Publishing Lifecycle

The verified publishing workflow is:

```text
Campaign
   ↓
Social Post
   ↓
DRAFT
   ↓
READY
   ↓
PUBLISHING
   ↓
Platform Adapter
   ↓
Fake Social Platform
   ↓
QUEUED
   ↓
Signed Delivery Webhook
   ↓
PUBLISHED
```

### Failure Path

```text
PUBLISHING
   ↓
FAILED
```

### Recovery Path

```text
PUBLISHING
   ↓
stale
   ↓
READY
   ↓
PUBLISHING
```

---

## 16. Database Migrations

The project uses Alembic for database schema management.

Database migrations are applied using:

```bash
alembic upgrade head
```

The PostgreSQL database contains the persistence required for:

- Campaigns
- Social posts
- Platform credentials
- Publishing status
- External post IDs
- Error messages
- Scheduling timestamps
- Idempotency keys

---

## 17. Overall Verification

### Complete Test Suite

```text
49 passed, 1 warning
```

### Focused Verification

```text
HTTP 429 Retry:
1 passed, 12 deselected

Stale Worker Recovery:
3 passed, 10 deselected

Image + Caption Tests:
7 passed

Credential Encryption:
1 passed
```

### Manual Verification

```text
Idempotent publishing        ✓
Signed webhook rejection     ✓
PostgreSQL persistence        ✓
Successful publishing        ✓
```

---

## 18. Verification Summary

| Requirement | Status |
|-------------|--------|
| Campaign API | ✅ Verified |
| Social Post API | ✅ Verified |
| Platform Adapters | ✅ Verified |
| Scheduled Publishing | ✅ Verified |
| Publisher Worker | ✅ Verified |
| Idempotent Publishing | ✅ Verified |
| HTTP 429 Retry Handling | ✅ Verified |
| Retry-After Handling | ✅ Verified |
| Credential Encryption | ✅ Verified |
| Signed Webhooks | ✅ Verified |
| Failure Handling | ✅ Verified |
| Stale Worker Recovery | ✅ Verified |
| PostgreSQL Persistence | ✅ Verified |
| Alembic Migrations | ✅ Verified |
| Image Variants | ✅ Verified |
| Platform-Specific Captions | ✅ Verified |
| Worker API | ✅ Verified |
| Automated Test Suite | ✅ 49 passed |
| End-to-End Publishing | ✅ Verified |

---

## Conclusion

The core Social Campaign Publisher workflow has been implemented and verified using:

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Platform adapters
- Publisher worker
- Fake social platform
- Pytest
- Docker
- HMAC-SHA256 webhook verification
- Encrypted credentials
- Idempotent publishing
- Retry handling
- Stale-worker recovery

The project has **49 passing automated tests** and additional manual verification covering idempotency, signed webhooks, successful publishing, and PostgreSQL persistence.
