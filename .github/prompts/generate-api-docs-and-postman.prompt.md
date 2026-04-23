---
name: "Generate API Docs and Postman"
description: "Generate or update API contract documentation JSON and Postman collection when a new endpoint or contract change is introduced."
argument-hint: "Describe the endpoint change (path, method, auth, payload, response, errors)"
agent: "agent"
---
Update API documentation JSON and Postman collection for the provided endpoint change.

Input expected:
- Endpoint path and method
- Auth requirement and token rule
- Request payload (fields, required/optional, validation)
- Response schema and success example
- Main error cases and status/detail messages

Execution rules:
1. Locate existing documentation and collection files in repository root.
2. Preserve current structure and naming conventions.
3. Add or update endpoint entries with:
   - method, path, auth_required
   - payload schema and example
   - success response example
   - error response example
4. Add or update Postman request with runnable URL variables and headers.
5. If change is breaking, include both legacy and new version entries plus migration note.
6. Keep JSON valid and deterministic (no duplicate endpoint entries).

Quality checks before finishing:
- Endpoint data in docs matches route implementation.
- Payload and response examples match Pydantic models.
- Authorization header is present when endpoint is protected.
- Query/path params in Postman URL match route signature.

Output format:
- Summary of files changed
- List of endpoints added/updated
- Any assumptions made
