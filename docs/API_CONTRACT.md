# API_CONTRACT.md

## Auth (/api/v1/auth)

### POST /auth/login

- Content-Type: `application/json`
- Body:
  - `email`: string
  - `password`: string
- Resposta `200 OK`:
  - JSON `{ "access_token": string, "token_type": "bearer" }`
  - Cookies setados:
    - `access_token`: JWT de curta duração
    - `refresh_token`: JWT de longa duração
  - Flags dos cookies:
    - `HttpOnly: true`
    - `Secure:` controlado por `COOKIE_SECURE` (false em dev, true em prod)
    - `SameSite:` vindo de `COOKIE_SAMESITE` (`lax` em dev; ajustar para `none`/`strict` em prod)
    - `Path: /`
    - `Domain:` opcional (`COOKIE_DOMAIN`)

### POST /auth/logout

- Efeito:
  - Limpa cookies `access_token` e `refresh_token` (Path=/, mesmo Domain).
- Resposta:
  - `200 OK` `{ "ok": true }`

### GET /auth/me

- Requer autenticação via:
  - Cookie `access_token` **ou**
  - Header `Authorization: Bearer <token>`
- Resposta:
  - 200 OK: { "ok": true } (opcionalmente user)
  - cookies: access_token, refresh_token

### POST /auth/refresh

- Lê cookie `refresh_token` (HttpOnly).
- Se válido, gera novo `access_token` e atualiza cookie `access_token` com mesmas flags descritas em `/auth/login`.
- Resposta:
  - `200 OK` `{ "ok": true }`
  - `401 Unauthorized` se refresh ausente ou inválido.

## Frontend (Next.js)

- Todas as chamadas para `/api/v1` devem usar:
  - `axios` configurado com `withCredentials: true`
  - ou `fetch` com `credentials: 'include'`.
- **Nunca** armazenar tokens JWT em `localStorage` ou `sessionStorage`.

