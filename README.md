# wf-catalogue-service

Workflow and notebook catalogue service API.

## Running locally

```shell
docker-compose up
```

API available at `http://localhost:8000/api/v1.0`.
Swagger docs at `http://localhost:8000/api/v1.0/docs`.

## API Endpoints

| Endpoint                                  | Description                |
| ----------------------------------------- | -------------------------- |
| `GET /health`                             | Health check               |
| `GET /collections`                        | List catalogues            |
| `GET /collections/{id}`                   | Get catalogue details      |
| `GET /collections/{id}/items`             | List records               |
| `GET /collections/{id}/items/{record_id}` | Get record                 |
| `POST /register`                          | Register workflow/notebook |
| `DELETE /register/{record_id}`            | Delete record              |

All endpoints are prefixed with `/api/v1.0`.

## Getting started

Create the environment:

```shell
make env
```

Run `pre-commit` hooks:

```shell
make pc
```

## Dev LOG

See the [log](docs/dev-logs) of changes and experiment results. Best to view it via `mkdocs serve` command.

## Guides

Read more here:

- [Development env setup](docs/guides/setup-dev-env.md)
- [Contributing](docs/guides/contributing.md)
- [Makefile usage](docs/guides/makefile-usage.md)
- [Running tests](docs/guides/tests.md)

## Docs

To build project documentation run:

```shell
make docs
```

and then:

```shell
mkdocs serve
```
