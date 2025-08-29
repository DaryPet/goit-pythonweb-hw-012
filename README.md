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

