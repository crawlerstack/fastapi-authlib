"""rest api"""
from fastapi import Response


def assert_status_code(response: Response, code=200) -> None:
    """Check state code is ok."""
    assert response.status_code == code
