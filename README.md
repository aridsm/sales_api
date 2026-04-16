# Sales API

A FastAPI-based REST API for sales management with PostgreSQL, Redis, and JWT authentication.

## Project Structure

```
sales_api/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app initialization
│   ├── config.py                 # Configuration management
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── schemas.py            # Pydantic models for requests/responses
│   │   ├── tokens.py             # JWT token creation and verification
│   │   ├── dependencies.py       # FastAPI dependencies (auth, etc.)
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── users.py          # User endpoints
│   ├── database/                 # Database layer
│   │   ├── __init__.py
│   │   ├── engine.py             # SQLAlchemy engine and session
│   │   ├── models.py             # SQLAlchemy models
│   │   └── redis.py              # Redis client for token blacklist
│   ├── enums/                    # Enumeration classes
│   │   └── __init__.py
│   └── services/                 # Business logic layer
│       ├── __init__.py
│       ├── base.py               # BaseService with common CRUD operations
│       └── user.py               # UserService with user-specific logic
├── alembic/                      # Database migrations
│   ├── __init__.py
│   ├── env.py                    # Alembic environment configuration
│   └── versions/
│       └── 001_create_users_table.py
├── alembic.ini                   # Alembic configuration file
├── docker-compose.yml            # Docker Compose for PostgreSQL and Redis
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

## Features

- **FastAPI**: Modern async Python web framework
- **PostgreSQL**: Robust relational database
- **Redis**: In-memory cache for token blacklist
- **JWT Authentication**: Secure token-based authentication
- **Alembic**: Database schema management
- **BaseService Pattern**: Reusable service layer with common CRUD operations
- **SQLAlchemy ORM**: Object-relational mapping
- **Pydantic**: Data validation using Python type hints

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- pip (Python package manager)

## Setup Instructions

### 1. Clone or Create Project

The project structure has been created. Navigate to the project root:

```bash
cd c:\Users\arian\OneDrive\Desktop\Projects\sales_api
```

### 2. Install Dependencies

Create a virtual environment (optional but recommended):

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/macOS
source venv/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
```

### 3. Start Services with Docker Compose

Start PostgreSQL and Redis:

```bash
docker-compose up -d
```

Verify services are running:

```bash
docker-compose ps
```

### 4. Run Alembic Migrations

Apply database migrations:

```bash
alembic upgrade head
```

To create a new migration after model changes:

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### 5. Start the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### User Endpoints

#### Sign Up

- **POST** `/users/signup`
- **Request**:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword"
  }
  ```
- **Response**: User object with id, name, email, created_at, updated_at

#### Login

- **POST** `/users/login`
- **Request**:
  ```json
  {
    "email": "john@example.com",
    "password": "securepassword"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
  }
  ```

#### Get Current User (Authenticated)

- **GET** `/users/me`
- **Header**: `Authorization: Bearer <access_token>`
- **Response**: Current user object

#### Delete Account (Authenticated)

- **DELETE** `/users/me`
- **Header**: `Authorization: Bearer <access_token>`
- **Response**: 204 No Content

#### Logout (Authenticated)

- **POST** `/users/logout`
- **Header**: `Authorization: Bearer <access_token>`
- **Response**:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```

## Environment Variables

Edit `.env` file to configure:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=sales_api
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT Configuration
JWT_SECRET=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
DEBUG=True
ENVIRONMENT=development
```

**Important**: In production, change `JWT_SECRET` to a strong random string.

## BaseService Pattern

The `BaseService` class provides reusable CRUD operations:

```python
class UserService(BaseService[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)
```

Available methods:

- `get_all(skip: int, limit: int)` - Get paginated records
- `get_by_id(id)` - Get single record by ID
- `create(obj_in: dict)` - Create new record
- `update(id, obj_in: dict)` - Update existing record
- `delete(id)` - Delete record
- `exists(id)` - Check if record exists

## Adding New Models and Services

### 1. Create Model (app/database/models.py)

```python
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    # ... other fields
```

### 2. Create Service (app/services/product.py)

```python
from app.services.base import BaseService
from app.database.models import Product

class ProductService(BaseService[Product]):
    def __init__(self, db: Session):
        super().__init__(Product, db)

    # Add custom methods here
```

### 3. Create Migration

```bash
alembic revision --autogenerate -m "Add product table"
alembic upgrade head
```

### 4. Create Schemas and Routes

Add Pydantic schemas in `app/api/schemas.py` and routes in `app/api/routes/`

## Redis Token Blacklist

The application uses Redis to maintain a blacklist of tokens for logout functionality:

```python
# In app/database/redis.py
redis_client.add_token_to_blacklist(token, ttl=3600)  # Add to blacklist
redis_client.is_token_blacklisted(token)  # Check if blacklisted
```

## Testing with cURL

### Sign Up

```bash
curl -X POST "http://localhost:8000/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"password123"}'
```

### Login

```bash
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"password123"}'
```

### Get Current User

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Delete Account

```bash
curl -X DELETE "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Database Management

### View Database

Connect to PostgreSQL:

```bash
# Using Docker
docker-compose exec postgres psql -U postgres -d sales_api

# Then in psql:
\dt  # List all tables
\d users  # Describe users table
SELECT * FROM users;  # Query users
```

### Reset Database

Drop all tables and recreate:

```bash
alembic downgrade base
alembic upgrade head
```

## Redis Commands

Check Redis:

```bash
# Docker container
docker-compose exec redis redis-cli

# Check blacklist tokens
KEYS blacklist:*
GET blacklist:<token>
```

## Troubleshooting

### Port Already in Use

If ports 5432, 6379, or 8000 are already in use:

1. Change in `docker-compose.yml` (for 5432, 6379)
2. Change in `.env` (DB_PORT, REDIS_PORT)
3. Use different port when running uvicorn:

```bash
uvicorn app.main:app --reload --reload-dir app
```

### Database Connection Error

Ensure:

1. Docker containers are running: `docker-compose ps`
2. Environment variables in `.env` match docker-compose.yml
3. Database is initialized: Migrations have been run

### Authentication Issues

- Ensure token is included in `Authorization: Bearer <token>` header
- Check token hasn't expired (default 30 minutes)
- Verify Redis is running for blacklist checks

## Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET` to a strong random string
- [ ] Change `DEBUG` to `False`
- [ ] Set `ENVIRONMENT` to `production`
- [ ] Change database credentials
- [ ] Set up HTTPS/SSL
- [ ] Configure database backups
- [ ] Set up Redis persistence
- [ ] Add database connection pooling
- [ ] Enable CORS appropriately (not `["*"]`)
- [ ] Add rate limiting
- [ ] Set up logging and monitoring

## Next Steps

1. Add more models and services following the same pattern
2. Add validation and business logic in services
3. Implement pagination properly in the API routes
4. Add API documentation and examples
5. Add comprehensive unit and integration tests
6. Set up CI/CD pipeline

## License

This project is open source and available under the MIT License.
