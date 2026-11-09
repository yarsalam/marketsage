# User authentication — initial single-owner boundary

**Status:** implementation candidate on branch `security/user-authentication-2026-11`; not deployed or production-approved.

## Behavior

- The first supported account is one owner account. This is not a multi-user identity system.
- Private user API routes are protected by a global NestJS guard.
- Public routes are limited to the health/root check, login and logout. `GET /auth/me` is authenticated.
- A successful login issues an eight-hour JWT in the `marketsage_session` HttpOnly cookie.
- The browser does not keep session tokens in localStorage or JavaScript-accessible storage.
- SameSite=Lax is used; Secure is enabled when `NODE_ENV=production`.
- A valid bearer token is also accepted for trusted non-browser API clients.
- If any required authentication setting is missing or invalid, login fails closed with HTTP 503 and private routes remain inaccessible.

## Required server configuration

Set these only in the host's protected environment/secret store; never commit real values:

- `MARKETSAGE_AUTH_USERNAME`
- `MARKETSAGE_AUTH_PASSWORD_SCRYPT`
- `MARKETSAGE_JWT_SECRET` (at least 32 random bytes)
- `NODE_ENV=production`

The password hash format is `scrypt$16384$8$1$<salt-hex>$<64-byte-hash-hex>`. Generate it locally without putting the password in shell history:

```bash
python3 - <<'PY'
from getpass import getpass
from hashlib import scrypt
from secrets import token_hex

password = getpass("New MarketSage password: ").encode()
salt = bytes.fromhex(token_hex(16))
digest = scrypt(password, salt=salt, n=16384, r=8, p=1, dklen=64)
print("scrypt$16384$8$1$" + salt.hex() + "$" + digest.hex())
PY
```

Generate the JWT secret with a cryptographically secure random generator and store it separately from the password hash.

## Deployment requirements still outstanding

Before enabling this in a public deployment:
1. Configure secrets outside the repository and verify TLS.
2. Configure reverse-proxy login rate limiting and request-size limits.
3. Verify the production origin/CORS/reverse-proxy path and cookie scope.
4. Run a browser-level sign-in, protected-route, expired-session and logout test against the deployed candidate.
5. Complete an independent security review.

No production secret or environment has been changed by this branch. The sample environment intentionally leaves authentication values unset, so the application remains fail-closed until an operator explicitly configures them.
