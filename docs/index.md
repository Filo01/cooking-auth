# cooking_auth

[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

A user authentication microservice for an online cooking forum. Check out the project's [documentation](http://Filo01.github.io/cooking_auth/).

# Prerequisites

- [Docker](https://docs.docker.com/docker-for-mac/install/)

# Initialize the project

Start the dev server for local development:

```bash
docker-compose up
```

Create a superuser to login to the admin:

```bash
docker-compose run --rm web ./manage.py createsuperuser
```

# Swagger-ui

You can find the swagger ui at [http://localhost:7070/api/v1/schema/swagger-ui](http://localhost:7070/api/v1/schema/swagger-ui)
