# Reference review

This restoration used three established Flask repositories as design references. No source code was copied.

## `pallets/flask`

Adopted ideas:

- application factory instead of irreversible module-level setup
- test configuration injection
- instance-relative storage for local SQLite
- blueprint registration after extensions are initialized

## `pallets-eco/flask-sqlalchemy`

Adopted ideas:

- SQLAlchemy 2 style typed models
- `db.select(...)` and session execution rather than legacy `Model.query`
- explicit application context for schema initialization

## `cookiecutter-flask/cookiecutter-flask`

Adopted ideas:

- environment-driven configuration
- application factory and blueprints
- deployable process command
- automated tests and CI as part of the baseline

## Deliberate omissions

The repository is intentionally smaller than the references. Authentication systems, migrations, background queues, caching, and frontend tooling were not added because the current product scope does not justify them yet.
