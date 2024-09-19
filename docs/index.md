# cooking_auth

<!-- [![Build Status](https://travis-ci.org/Filo01/cooking_auth.svg?branch=master)](https://travis-ci.org/Filo01/cooking_auth) -->
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/6b9e815fe0e94069bbe6d36879d91772)](https://app.codacy.com/gh/Filo01/cooking_auth/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

A user authentication microservice for an online cooking forum. Check out the project's [documentation](http://Filo01.github.io/cooking_auth/).

## Prerequisites

- [Docker](https://docs.docker.com/docker-for-mac/install/)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

## Local Development with VSCode and Devcontainers

In VSCode press `F1` to bring up the `Command Palette`, type in `>Dev Containers: Rebuild and Reopen in Container`.

Then you can debug django from VSCode from the `Run and Debug` panel.

When using git inside the Devcontainer you are going to need to configure it to use the git credentials on host your machine [as described here](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials)

To install pre-commit hooks, just run from the VSCode integrated terminal `pre-commit install` the first time you open the project. It will install the pre-commit hooks automatically.

## Run locally without VSCode

Start the dev server for local development:
```bash
docker-compose up
```

Run a command inside the docker container:

```bash
docker-compose run --rm web [command]
```

## Accessing the development server

The django admin page is located at [http://localhost:7070/admin/](http://localhost:7070/admin/)

Documentation is at [http://localhost:7071/api/users/](http://localhost:7071/api/users/) or you can find the hosted version [here](https://filo01.github.io/cooking_auth/)

Swagger ui is at [http://localhost:7070/api/v1/schema/swagger-ui/#/](http://localhost:7070/api/v1/schema/swagger-ui/#/)

## Quick curl examples

### Create a user:
Request:
```bash
curl -X 'POST' \
  'http://localhost:7070/api/v1/users/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFTOKEN: wGtmTApd89fKOx1mraf7DzPAYEEDz2fqaHVJMeLJlhlnMbApuTo7y1jNsGXWy2yX' \
  -d '{
  "username": "test",
  "password": "test1234",
  "first_name": "prova",
  "last_name": "provata",
  "email": "user@example.com",
  "has_2fa": true
}'
```
Response:
```json
{
  "id": "1bde4e38-968e-4853-865b-2395ceb3a587",
  "username": "test",
  "first_name": "prova",
  "last_name": "provata",
  "email": "user@example.com",
  "has_2fa": true
}
```

### Login as user:
Request:
```bash
curl -X 'POST' \
  'http://localhost:7070/api/v1/login/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "password": "test1234",
    "email": "user@example.com"
    }'
```
Response:
```json
{
  "body": "Login via email OTP",
  "_links": [
    {
      "href": "/api/v1/login/1bde4e38-968e-4853-865b-2395ceb3a587/otp/",
      "method": "POST",
      "body": {
        "code": {
          "type": "str"
        }
      }
    }
  ]
}
```

### Login via OTP

Use OTP (which you can find in stdout) and the `_links[0].href` from the previous response.

Request:
```bash
curl -X 'POST' \
  'http://localhost:7070/api/v1/login/1bde4e38-968e-4853-865b-2395ceb3a587/otp' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "code": "hvu1j1"
    }'
```
Response:
```json
{
  "message": "Login successful",
  "token": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNjgyOTY3MiwiaWF0IjoxNzI2NzQzMjcyLCJqdGkiOiIyYzgyMmE4MzFkNmI0OWU0Yjg5NzkxYTJjOTFkNDdiMiIsInVzZXJfaWQiOiIxYmRlNGUzOC05NjhlLTQ4NTMtODY1Yi0yMzk1Y2ViM2E1ODcifQ.SSb2EFGOWIJfRUqE_rkTvw76rdP2XWJCrRGCixA80YA",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI2NzQzNTcyLCJpYXQiOjE3MjY3NDMyNzIsImp0aSI6ImRiMTNlNWMyYWJkMzQ1NGM4ZmQ5NWIzMDMyMWM1YzU1IiwidXNlcl9pZCI6IjFiZGU0ZTM4LTk2OGUtNDg1My04NjViLTIzOTVjZWIzYTU4NyJ9.x6zoYVqHwFHLYUqeY_wSVtODQhXpChsKioEjznv7VlQ"
  }
}
```

### Use the token to access user info:

Request:
```bash
curl -X 'GET' \
  'http://localhost:7070/api/v1/users/1bde4e38-968e-4853-865b-2395ceb3a587/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI2NzQzNTcyLCJpYXQiOjE3MjY3NDMyNzIsImp0aSI6ImRiMTNlNWMyYWJkMzQ1NGM4ZmQ5NWIzMDMyMWM1YzU1IiwidXNlcl9pZCI6IjFiZGU0ZTM4LTk2OGUtNDg1My04NjViLTIzOTVjZWIzYTU4NyJ9.x6zoYVqHwFHLYUqeY_wSVtODQhXpChsKioEjznv7VlQ'
```
Response:
```json
{
  "id": "1bde4e38-968e-4853-865b-2395ceb3a587",
  "username": "test",
  "first_name": "prova",
  "last_name": "provata",
  "has_2fa": true
}
```
