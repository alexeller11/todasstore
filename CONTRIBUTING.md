# Contributing to Todas Store

Thank you for your interest in contributing! This project follows a simple workflow:

## How to contribute
1. **Fork** the repository.
2. **Clone** your fork locally.
3. Create a **feature branch**:
   ```bash
   git checkout -b my-feature
   ```
4. Make your changes, **add tests** if you add functionality, and ensure they pass:
   ```bash
   pytest -q
   ```
5. **Commit** with a clear message following the Conventional Commits style.
6. Push to your fork and open a **Pull Request** against `main`.

## Code style
- Follow the existing code style (PEP 8, type hints, docstrings).
- Run `flake8` locally if you have it installed.

## Testing
- All new code must include unit tests under the `tests/` directory.
- CI runs `pytest` on every PR.

## License
By contributing you agree that your contributions will be licensed under the same MIT license as the project.
