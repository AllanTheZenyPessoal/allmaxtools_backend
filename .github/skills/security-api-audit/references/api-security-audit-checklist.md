# API Security Audit Checklist

Use this checklist during route and contract reviews.

## Route protection

- Route has explicit auth decision: public or protected.
- Protected route includes verify_token dependency.
- Sensitive operations are never left public by default.

## Token compatibility

- Token claims used by endpoints are documented.
- Claim name changes are treated as breaking and versioned.
- Auth examples in Postman still work after changes.

## Input validation

- Enums/allowlists enforced (example: BTC/ETH).
- Numeric constraints enforced (greater than zero, limits, ranges).
- Date intervals validated (start_date <= end_date).
- Invalid input returns consistent 400 detail.

## Response consistency

- response_model declared and matches returned JSON shape.
- Similar endpoints use consistent field names.
- Error messages are clear and predictable.

## Documentation sync

- Documentation JSON updated with method/path/auth/payload/response/errors.
- Postman collection updated with headers, params, and body examples.
- Breaking changes include migration notes and versioned endpoint entries.
