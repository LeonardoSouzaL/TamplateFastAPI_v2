import pytest

pytest.skip(
    "O exemplo /cars não é exposto na Metrics API (somente leitura LastMile).",
    allow_module_level=True,
)
