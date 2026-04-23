---
name: security-api-audit
description: 'Audit FastAPI security and contract consistency. Use for reviewing routes without token protection, weak input validation, and inconsistent response formats across endpoints.'
argument-hint: 'Scope of audit (all routes, crypto only, user only)'
user-invocable: true
---

# Security API Audit

## When To Use

Use this skill when you need a security-focused review of API routes and contracts, especially after adding or changing endpoints.

Typical triggers:

- New endpoint added without clear auth requirement.
- Suspected missing token validation in protected operations.
- Weak or missing input validation (dates, bounds, enums, symbols).
- Inconsistent response format between similar endpoints.

## Audit Goals

- Identify routes that should use token validation but do not.
- Find weak validation and unsafe assumptions in request processing.
- Detect inconsistent response contracts and error patterns.
- Ensure docs and Postman reflect real auth and payload behavior.

## Procedure

1. Map routes and dependencies
- Inspect files under app/routes and app/endpoint.
- List each route method/path and whether token dependency exists.

2. Validate auth and token usage
- Verify protected operations use verify_token dependency.
- Check token claim usage remains compatible with documented claims.

3. Validate input constraints
- Check allowlists (for example BTC/ETH), numeric bounds, and date range order.
- Ensure invalid inputs return clear 400 detail messages.

4. Validate response consistency
- Confirm response_model usage and schema alignment with base_models.
- Flag ad-hoc response shapes where typed models are expected.

5. Validate docs sync
- Check documentation JSON and Postman collection entries for changed endpoints.
- Ensure auth header requirements match route protection.

6. Report findings
- Report findings ordered by severity with file references and concrete fixes.
- Include residual risks and testing gaps.

## Severity Rubric

- High: Missing auth on sensitive operations, broken token assumptions, exploitable validation gaps.
- Medium: Contract inconsistencies that can break clients, weak error patterns, docs mismatch for protected routes.
- Low: Style-level inconsistencies, non-critical duplication, minor naming issues.

## Output Template

- Findings (high to low)
- Open questions/assumptions
- Suggested fixes
- Documentation/Postman sync actions

## Reference

See detailed checklist: [API Security Audit Checklist](./references/api-security-audit-checklist.md)
