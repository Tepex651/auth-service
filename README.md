# Auth service
Async authentication service with JWT-based access control, refresh token rotation, and multi-factor authentication.

## Features

- ✅ Registration & email verification  
- 🛡 JWT authentication (access & refresh tokens)  
- 🔄 Token lifecycle (rotation, revocation)  
- 🔑 MFA (TOTP / email)  
- 🔐 Password hashing (bcrypt)  
- ⚙️ Async FastAPI backend  
- 🐳 Docker support  
- 🧪 Tests (unit, integration, e2e)  

## Tech Stack

- **Backend:** Python3, FastAPI (async)
- **Database:** PostgreSQL(asyncpg), SQLAlchemy
- **Infrastructure:** Docker, Docker Compose
- **Security:** cryptography, bcrypt
- **Testing:** pytest (unit, integration, e2e)

## Installation

1. Clone repository
```sh
git clone https://github.com/Tepex651/auth-service.git
cd auth-service
cp .env.example .env
```

2. Install Dependencies (`uv` used as package manager)
```sh
# install uv
pip install uv  # see https://docs.astral.sh/uv/getting-started/installation/

uv sync
```

3. Deploy and Run

```sh
# setup db, mailhog and app
docker compose up -d

# db-migrate
uv run alembic upgrade head

# run tests
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/e2e

# to see logs
docker compose logs
```
<details>
<summary> make </summary>

```sh
# setup db, mailhog and app
make setup-local

# db-migrate
make migrate

# run tests
make e2e-tests

# to see logs
make logs
```
</details>

## Architecture & Flows

<details>
<summary>📦 Domain Boundaries Diagram</summary>

### Layers
- Orchestration: coordinates authentication flows
- Domain services: encapsulate business rules
- Infrastructure: external integrations and persistence

```mermaid
flowchart TB
    subgraph Orchestration
        AuthService
    end

    subgraph Domain Services
        UserService
        TokenService
        MFAService
        ChallengeService
    end

    subgraph Infrastructure
        EmailNotification
        Repositories
        Database[(PostgreSQL)]
    end

    AuthService --> UserService
    AuthService --> TokenService
    AuthService --> MFAService
    AuthService --> ChallengeService
    AuthService --> EmailNotification

    UserService --> Repositories
    TokenService --> Repositories
    MFAService --> Repositories
    ChallengeService --> Repositories

    Repositories --> Database
```

### Responsibilities
- **AuthService** — orchestrates authentication flows (login, refresh, MFA, reset)
- **UserService** — user lifecycle and identity state
- **TokenService** — issuing, rotating, revoking tokens
- **MFAService** — multi-factor authentication flows
- **ChallengeService** — multi-step auth continuations
- **EmailNotification** — outbound notification delivery
- **Repositories** — persistence abstraction

</details>

<details> <summary>🔐 Login Flow</summary>

### Actors
- Client - browser, mobile app or another backend service
- API - FastAPI HTTP layer
- AuthService - authentication logic (credentials validation)
- TokenService - access/refresh token lifecycle
- UserService - creating user in db
- MFAService - create mfa challenge token and verify

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthService
    participant UserService
    participant TokenService
    participant MFAService

    Client->>API: POST /login
    API->>AuthService: login(email, password)

    AuthService->>UserService: authenticate()
    UserService-->>AuthService: User | InvalidCredentials | Disabled

    alt invalid credentials
        AuthService-->>API: 401
    else disabled
        AuthService-->>API: 403
    else success
        alt MFA required
            AuthService->>MFAService: start challenge
            AuthService-->>API: 202 MFA_REQUIRED
        else no MFA
            AuthService->>TokenService: issue tokens
            TokenService-->>AuthService: access + refresh
            AuthService-->>API: 200 tokens
        end
    end
```

</details>

<details> <summary>📝 Registration Flow</summary>

### Actors
- Client - browser, mobile app or another backend service
- API - FastAPI HTTP layer
- AuthService - orchestration layer. Pass control to UserService
- UserService - create user in DB
- MFAService - create mfa challenge token and verify
- EmailNotification - send email message

```mermaid
sequenceDiagram
    participant C as Client
    participant API
    participant AuthService
    participant UserService
    participant MFAService
    participant EmailNotification

	note over C,API: :─────────────── Step 1: Create user and start email verification ───────────────
    C->>API: POST /register<br>{username, email, password, role_name}
    API->>AuthService: register(username, email, password)
    AuthService->>UserService: create_user(username, email, password_hash)
    UserService-->>AuthService: User created

    AuthService->>MFAService: start email verification challenge (user_id, email)
    MFAService->>MFAService: generate challenge_token(user_id, type=email_verification)
    MFAService->>EmailNotification: send_verification_email(email, token_link)
    EmailNotification-->>MFAService: sent
    MFAService-->>AuthService: ok

    AuthService-->>API: 202 Accepted<br>"verification email sent"
    API-->>C: 202 + "check your email"

    note over C,API: ─────────────── Step 2: Email verification ───────────────

    C->>API: GET /confirm-email?token=...
    API->>AuthService: confirm_email(token)
    AuthService->>MFAService: validate challenge_token(token)
    MFAService-->>AuthService: valid (user_id)

    AuthService->>UserService: mark_email_verified(user_id)<br>→ status = active
    UserService-->>AuthService: ok

    AuthService-->>API: 200 OK<br>"account activated"
    API-->>C: 200 + "registration completed<br>you can now log in"
```
</details> 

## Configuration

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=iam
DB_CONN_POOL_SIZE=20
DB_CONN_MAX_OVERFLOW=10

# use it for test/local development only (openssl rand -hex 32)
SECRET_KEY=7e23e1a55eea04523ec90c86554b5640d2c1f6919e89efa9bb0a56efde5e7cf3

SMTP_TOKEN=0a5e54b0d9f685a652fcae6425af58af
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
SMTP_WEB_PORT=8025

REDIS_HOST=localhost
REDIS_PORT=6379
# use it for test/local development only (openssl rand -base64 32)
ENCRYPTION_CURRENT_KEY=YADrK143ZO9TGwKAHKWr1QhRsUDqBj4_4_DtiH-QA-w=

LOG_LEVEL=DEBUG
BCRYPT_COST=4

APP_HOST=0.0.0.0
APP_PORT=8000
```

## License

MIT License © 2026
