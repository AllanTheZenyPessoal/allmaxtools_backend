---
description: "Use when creating or changing API endpoints, payloads, response schemas, token claims, or auth behavior. Enforces contract versioning policy, backward compatibility, and explicit breaking-change handling."
name: "API Versioning and Breaking Changes Policy"
applyTo:
  - "app/routes/**/*.py"
  - "app/endpoint/**/*.py"
  - "app/token_utils/**/*.py"
  - "app/database/base_models.py"
  - "alembic/versions/*.py"
  - "*postman_collection.json"
  - "*documentation.json"
---
# API Versioning and Breaking Changes Policy

Use this policy for every API contract change.

## Compatibility baseline

- Additive changes are preferred (new optional fields, new endpoints, new query params).
- Existing required request fields, response fields, and field semantics must remain stable in the same API version.
- Keep existing endpoint paths and methods unless version migration is explicitly required.

## What is a breaking change

Treat each item below as breaking:

- Removing or renaming request or response fields.
- Changing a field type or format (example: number to string, datetime format change).
- Turning optional request fields into required fields.
- Changing authentication requirement from public to protected without versioning/migration note.
- Changing token claim names or removing claims consumed by clients.
- Changing endpoint path, HTTP method, or success/error status behavior.

## Versioning rules

- For breaking changes, create a new versioned endpoint path (example: /v2/...).
- Keep previous version active during migration unless task explicitly requests immediate replacement.
- Document migration notes: old behavior, new behavior, and sunset timeline when applicable.
- For non-breaking changes, keep same version and update examples/contracts.

## Token and auth compatibility

- If token payload changes, preserve legacy claims whenever possible for one migration cycle.
- If legacy claims cannot be preserved, treat as breaking and version dependent endpoints.
- Always update auth documentation and Postman auth examples when token rules change.

## Documentation and release notes

- Update contract documentation JSON in the same change set.
- Update at least one Postman collection with both legacy and new version requests when breaking changes occur.
- Include explicit breaking-change section with:
  - changed endpoint or schema
  - compatibility impact
  - migration examples

## Pull request checklist for API contract changes

- Compatibility classified (non-breaking or breaking)
- Versioning action applied when breaking
- Legacy behavior validated or intentionally deprecated
- Documentation updated with migration notes
- Postman collection updated for affected versions
