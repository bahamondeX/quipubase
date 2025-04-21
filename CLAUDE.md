# Project Style Guide
This document outlines the coding style and conventions for the project. Adhering to these guidelines will help maintain consistency and readability across the codebase.

## Directory Structure

## Build Commands
- Install: `make install`
- Dev dependencies: `make dev`
- Start server: `make start` or `make dev-start` (with reload)
- Run tests: `make test`
- Run single test: `make test-file FILE=tests/test_main.py::test_function_name`
- Lint/format: `make lint` and `make format`

## Code Style
- Use type hints everywhere, leverage TypeVar for generics
- Imports: group standard library, then third-party, then local imports
- Exception handling: use the `@handle` decorator for robust error handling
- Use Pydantic models for data validation
- Collection classes must inherit from the base Collection class
- Async/await pattern preferred for I/O bound operations
- Use descriptive variable names and docstrings
- Tests should clean up after themselves (see cleanup fixture)