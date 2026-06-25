# Contacts REST API

A comprehensive REST API for managing contacts with user authentication, built with FastAPI, SQLAlchemy ORM, PostgreSQL, and Redis caching.

## Features

✅ **User Authentication & Authorization**

- User registration with email verification
- JWT-based login/logout
- Password reset via email
- Role-based access control (user/admin)

✅ **Contact Management (CRUD)**

- Create, Read, Update, Delete contacts
- Each user manages their own contacts

✅ **Search & Filtering**

- Search contacts by name, surname, or email
- Get contacts with upcoming birthdays

✅ **Performance & Caching**

- Redis caching for user sessions
- Cache-aside pattern to reduce DB load

✅ **File Upload**

- Avatar upload via Cloudinary (admin only)

✅ **API Documentation**

- Automatic Swagger UI at `/docs`
- ReDoc documentation at `/redoc`

✅ **Testing**

- Unit tests (repository, service, dependencies)
- Integration tests (API endpoints)
- Coverage report with pytest-cov

## Project Structure

```
├── main.py                    # FastAPI app entry point
├── db.py                      # Database & Redis configuration
├── pyproject.toml             # Dependencies and tool configs
├── alembic.ini                # Alembic migration config
├── migrations/                # Database schema migrations
│   └── versions/
├── models/                    # SQLAlchemy ORM models
│   ├── base.py
│   ├── user.py                # User model with roles
│   └── contact.py
├── schemas/                   # Pydantic validation schemas
│   ├── auth.py
│   └── contact.py
├── repository/                # Data access layer
│   ├── auth_repository.py
│   └── contacts_repository.py
├── service/                   # Business logic layer
│   ├── auth_service.py        # Auth logic + Redis cache
│   ├── auth_deps.py           # JWT & role dependencies
│   ├── cache_service.py       # Redis caching helpers
│   ├── contacts_service.py
│   ├── email_service.py
│   └── cloudinary_service.py
├── api/                       # API routers
│   ├── auth_api.py
│   └── contacts_api.py
├── tests/                     # Test suite
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_auth_repository.py
│   │   ├── test_contacts_repository.py
│   │   ├── test_auth_service.py
│   │   ├── test_cache_service.py
│   │   └── test_auth_deps.py
│   └── integration/
│       ├── test_auth_api.py
│       └── test_contacts_api.py
└── docs/                      # Sphinx documentation
    ├── conf.py
    ├── index.rst
    ├── api.rst
    ├── models.rst
    ├── repository.rst
    ├── service.rst
    └── schemas.rst
```

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Redis (for caching)
- pip

### Setup Steps

1. **Clone and navigate to project**

    ```bash
    cd rest_api
    ```

2. **Create virtual environment**

    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/macOS:
    source .venv/bin/activate
    ```

3. **Install dependencies**

    ```bash
    pip install -e .
    ```

4. **Configure environment variables**

    Create a `.env` file in the project root:

    ```env
    DATABASE_URL=postgresql://user:password@localhost:5432/contacts_db
    SECRET_KEY=your-secret-key-here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REDIS_URL=redis://localhost:6379/0

    # Cloudinary (for avatar uploads)
    CLOUDINARY_CLOUD_NAME=your-cloud-name
    CLOUDINARY_API_KEY=your-api-key
    CLOUDINARY_API_SECRET=your-api-secret

    # Email (for verification/reset)
    MAIL_USERNAME=your-email@gmail.com
    MAIL_PASSWORD=your-app-password
    MAIL_FROM=your-email@gmail.com
    MAIL_PORT=587
    MAIL_SERVER=smtp.gmail.com
    ```

5. **Run database migrations**

    ```bash
    alembic upgrade head
    ```

6. **Run the application**

    ```bash
    uvicorn main:app --reload
    ```

    The API will be available at http://localhost:8000

## API Endpoints

### Authentication

| Method | Endpoint                           | Description                | Access        |
| ------ | ---------------------------------- | -------------------------- | ------------- |
| POST   | `/api/auth/register`               | Register new user          | Public        |
| POST   | `/api/auth/login`                  | Login and get JWT token    | Public        |
| GET    | `/api/auth/confirm_email/{token}`  | Verify email address       | Public        |
| POST   | `/api/auth/request_email`          | Request verification email | Public        |
| GET    | `/api/auth/me`                     | Get current user profile   | Authenticated |
| PATCH  | `/api/auth/avatar`                 | Update avatar URL          | Admin only    |
| POST   | `/api/auth/password-reset/request` | Request password reset     | Public        |
| POST   | `/api/auth/password-reset/confirm` | Confirm password reset     | Public        |

### Contact Management

| Method | Endpoint                  | Description        | Access        |
| ------ | ------------------------- | ------------------ | ------------- |
| POST   | `/api/contacts/`          | Create contact     | Authenticated |
| GET    | `/api/contacts/`          | List user contacts | Authenticated |
| GET    | `/api/contacts/{id}`      | Get contact by ID  | Authenticated |
| PUT    | `/api/contacts/{id}`      | Update contact     | Authenticated |
| DELETE | `/api/contacts/{id}`      | Delete contact     | Authenticated |
| GET    | `/api/contacts/search`    | Search contacts    | Authenticated |
| GET    | `/api/contacts/birthdays` | Upcoming birthdays | Authenticated |

### Health Check

| Method | Endpoint  | Description             |
| ------ | --------- | ----------------------- |
| GET    | `/health` | Check API and DB health |

## User Roles

- **user**: Default role. Can manage own contacts.
- **admin**: Can manage own contacts AND update own avatar.

Role is specified during registration and defaults to `user`.

## Testing

### Run all tests

```bash
pytest tests/ -v
```

### Run with coverage report

```bash
pytest tests/ --cov=api --cov=repository --cov=service --cov=models --cov=schemas --cov=db.py --cov=main.py --cov-report=term-missing
```

### Run specific test suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test class
pytest tests/unit/test_auth_service.py::TestAuthService -v
```

### Current Coverage

Target: **>75%**

- Repository layer: ~100%
- Service layer: ~88%
- API layer: ~63%
- Overall: **~82%**

## Technical Stack

- **Framework**: FastAPI 0.138+
- **ORM**: SQLAlchemy 2.0.51+
- **Database**: PostgreSQL with asyncpg
- **Caching**: Redis 8.0+
- **Validation**: Pydantic 2.13+
- **Auth**: python-jose (JWT), passlib (bcrypt)
- **Storage**: Cloudinary
- **Email**: fastapi-mail
- **Migrations**: Alembic
- **Testing**: pytest, pytest-asyncio, pytest-cov, httpx
- **Docs**: Sphinx with ReadTheDocs theme

## Environment Variables Reference

| Variable                      | Required | Description                    |
| ----------------------------- | -------- | ------------------------------ |
| `DATABASE_URL`                | Yes      | PostgreSQL connection string   |
| `SECRET_KEY`                  | Yes      | JWT signing secret             |
| `ALGORITHM`                   | No       | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No       | Token lifetime (default: 30)   |
| `REDIS_URL`                   | No       | Redis connection URL           |
| `CLOUDINARY_CLOUD_NAME`       | No       | Cloudinary cloud name          |
| `CLOUDINARY_API_KEY`          | No       | Cloudinary API key             |
| `CLOUDINARY_API_SECRET`       | No       | Cloudinary API secret          |
| `MAIL_USERNAME`               | No       | SMTP username                  |
| `MAIL_PASSWORD`               | No       | SMTP password                  |
| `MAIL_FROM`                   | No       | Sender email address           |
| `MAIL_PORT`                   | No       | SMTP port (default: 587)       |
| `MAIL_SERVER`                 | No       | SMTP server hostname           |

## Error Handling

Standard HTTP status codes are used:

- `200 OK` - Successful request
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid JWT
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Example error response:

```json
{
    "detail": "Contact not found"
}
```

## Rate Limiting

- General endpoints: default limits via `slowapi`
- `/api/auth/me`: 5 requests per minute

## Docker Support

The project includes `Dockerfile` and `docker-compose.yml` for containerized deployment.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and coverage stays above 75%
5. Submit a pull request

## License

MIT License
