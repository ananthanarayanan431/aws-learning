# aws-learning

## Backend (uv)

```bash
cd backend
uv sync                                   # create .venv and install deps
uv run uvicorn app.main:app --reload      # run the API
uv run pytest                             # run tests
uv add <package>                          # add a dependency
uv add --dev <package>                    # add a dev dependency
```
