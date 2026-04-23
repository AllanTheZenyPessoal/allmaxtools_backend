---
description: "Use when creating or changing FastAPI endpoints, auth/token behavior, request payloads, response formats, or database-backed API history. Enforces security checks and mandatory documentation/Postman updates."
name: "API Contract and Documentation Rules"
applyTo:
  - "app/routes/**/*.py"
  - "app/endpoint/**/*.py"
  - "app/token_utils/**/*.py"
  - "app/database/base_models.py"
  - "alembic/versions/*.py"
  - "*postman_collection.json"
  - "*documentation.json"
---
# API Contract and Documentation Rules

Apply these rules for every API change.

## Security and token rules

- Protected operations must require token validation using dependency injection with verify_token.
- Read-only endpoints can be public only if explicitly intended; otherwise require authentication.
- Never remove or weaken existing auth checks unless the task explicitly requests it.
- If token payload/claims change, update token generation, validation, and affected endpoint docs in the same task.

## Endpoint and payload rules

- Keep endpoint naming consistent with existing patterns under app/routes.
- Validate domain constraints at API boundary, including symbol allowlists, numeric bounds, and date range consistency.
- Request payloads and response formats must be defined in app/database/base_models.py.
- Do not return ad-hoc shapes for new endpoints when a typed response model is expected.
- For date range endpoints, enforce start_date <= end_date with clear 400 detail messages.

## Response format rules

- Prefer stable JSON contracts with explicit fields and predictable naming.
- Keep error responses consistent using detail messages that explain validation failures.
- When extending response models, preserve backward compatibility whenever possible.

## Documentation and Postman are mandatory

- Any endpoint, payload, token rule, or response contract change must update documentation files in the same change set.
- Update API documentation JSON with:
  - endpoint path and method
  - auth requirement
  - payload schema and example
  - success response example
  - error response example
- Update at least one relevant Postman collection with runnable requests for changed endpoints.
- If existing docs are stale or conflicting, correct them as part of the same task.

## Required completion checklist for API tasks

- Endpoint implementation updated
- Pydantic request/response models updated
- Auth/token enforcement reviewed
- Documentation JSON updated
- Postman collection updated
- Validation or error checks verified
