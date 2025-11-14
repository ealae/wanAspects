# Contributing to wanAspects

Thank you for considering contributing to wanAspects! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- [List your project's prerequisites]
- Example: Git, Python 3.10+, Poetry, etc.

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://gitlab.k8s.cloud.statcan.ca/jeanphilippe.wan/wanaspects.git
   cd wanAspects
   ```

2. **Install dependencies:**
   ```bash
   # Add your installation commands
   # Examples:
   # poetry install
   # npm install
   # cargo build
   ```

3. **Run tests to verify setup:**
   ```bash
   # Add your test commands
   # Examples:
   # poetry run pytest
   # npm test
   # cargo test
   ```

## Development Workflow

### Creating a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Making Changes

1. Make your changes in your feature branch
2. Write or update tests as needed
3. Ensure all tests pass
4. Follow code style guidelines (see below)

### Committing

Write clear, descriptive commit messages:

```
feat: add new feature X
fix: resolve issue with Y
docs: update README with Z
test: add tests for feature X
refactor: improve performance of Y
```

### Submitting Changes

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request/Merge Request:**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI pipeline passes

## Code Style

### [Your Language] Style Guide

- [Add your code style guidelines]
- Example: Follow PEP 8 for Python
- Example: Use ESLint configuration for JavaScript
- Example: Run `cargo fmt` for Rust

### Running Linters/Formatters

```bash
# Add your commands
# Examples:
# poetry run ruff format
# npm run lint
# cargo fmt --check
```

## Testing

### Running Tests

```bash
# Add your test commands
# Examples:
# poetry run pytest
# npm test
# cargo test
```

### Writing Tests

- Write tests for new features
- Ensure existing tests still pass
- Aim for good test coverage
- Test edge cases and error conditions

## Documentation

- Update README.md if adding user-facing features
- Add docstrings/comments for public APIs
- Update relevant documentation in `docs/`
- Include examples for new features

## Code Review Process

1. All changes require review before merging
2. Address review feedback promptly
3. Keep changes focused and atomic
4. Update your branch if conflicts arise

## Questions?

Feel free to:
- Open an issue for discussion
- Ask questions in pull requests
- [Add your contact method if applicable]

## License

By contributing, you agree that your contributions may be licensed under both options listed in `LICENSE.md` (GPL-3.0-or-later and the commercial license) so the project can continue dual-licensing future releases.

Thank you for contributing! 🎉
