"""Single source of truth for the Constitutional AIOps version.

Every other version surface MUST agree with the value defined here:
  - ``pyproject.toml``            (read statically via ``[tool.setuptools.dynamic]``)
  - ``src/__init__.py``          (re-exports ``__version__``)
  - ``src/main.py``              (FastAPI ``app.version`` + root endpoint)
  - ``src/validation/constants.py`` (re-exports ``__version__``)
  - ``frontend/package.json``    (kept in sync manually; asserted by tests)

Bump this constant only, then run ``pytest tests/test_version.py`` to confirm
all surfaces still agree.
"""

__version__ = "0.7.0"
