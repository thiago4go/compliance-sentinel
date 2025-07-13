# Development Guide

## Dependencies

This project uses modern Python packaging with `pyproject.toml`. Dependencies are managed as follows:

- Main dependencies are in `[project.dependencies]`
- Test dependencies are in `[project.optional-dependencies.test]`
- Development dependencies are in `[project.optional-dependencies.dev]`

### Generating Requirements Files

If you need to generate requirements files (e.g., for deployment or specific environments):

```bash
# Generate requirements.txt
pip-compile pyproject.toml

# Generate dev-requirements.txt
pip-compile pyproject.toml --extra dev
```

### Installing Dependencies

```bash
# Install main package with test dependencies
pip install -e ".[test]"

# Install main package with development dependencies
pip install -e ".[dev]"

# Install main package with all optional dependencies
pip install -e ".[test,dev]"
```

## Testing

The project uses pytest for testing. To run tests:

```bash
# Run all tests
tox -e pytest

# Run specific test file
tox -e pytest tests/test_random_orchestrator.py

# Run tests with coverage
tox -e pytest --cov=dapr_agents
```

## Code Quality

The project uses several tools to maintain code quality:

```bash
# Run linting
tox -e flake8

# Run code formatting
tox -e ruff

# Run type checking
tox -e type
```

## Development Workflow

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Run tests before making changes:
   ```bash
   tox -e pytest
   ```

3. Make your changes

4. Run code quality checks:
   ```bash
   tox -e flake8
   tox -e ruff
   tox -e type
   ```

5. Run tests again:
   ```bash
   tox -e pytest
   ```

6. Submit your changes
