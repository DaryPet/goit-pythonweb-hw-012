This is a REST API application for managing personal contacts. It is built with FastAPI and uses SQLAlchemy for database interactions. The project is containerized with Docker Compose, and it includes key features such as user authentication (JWT with access/refresh tokens), password reset, user roles, and Redis caching.


# build dokcer
`docker compose up -d --build`
or
`docker compose up --build`

# run alembic in Docker
`docker compose exec web bash`
then
`poetry run alembic revision --autogenerate -m "Create contacts table"`
then
`poetry run alembic upgrade head`

# run swagger documentation
`http://localhost:8000/docs`

# run redis
`docker compose up -d --build`
`docker compose ps`

# run black 
`poetry run black .`

# run unit tests
`poetry run pytest tests/unit/test_user_repository.py -v`
`poetry run pytest tests/unit/test_contact_repository.py -v`
`poetry run pytest tests/unit/test_auth_service.py -v`
`poetry run pytest tests/unit/test_avatar_service.py -v`
`poetry run pytest tests/unit/test_email_service.py -v`
`poetry run pytest tests/unit/test_redis_service.py -v`
`poetry run pytest tests/unit/test_password_service.py -v`
`poetry run pytest tests/unit/test_tokens_service.py -v`

# run integration tests
`poetry run pytest tests/integration/test_auth_routes.py -v`
`poetry run pytest tests/integration/test_contacts_routes.py -v`
`poetry run pytest tests/integration/test_users_routes.py -v`


# to make documentstion 
`poetry run make html`
# run documantation
`cd docs`
macOS: `open build/html/index.html`


Cloud Deployment
This project is configured for cloud deployment, utilizing free-tier services.

Web Service: Render is used for deploying the main FastAPI application.

Database: Render Postgres is used for the primary database.

Caching: Upstash provides the Redis service for caching.



Linux: `xdg-open build/html/index.html`

Windows: `start build\html\index.html`

# to check how much you cover your code by test run
`poetry run pytest --cov=./src`
