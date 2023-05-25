"""Tests"""
from fastapi_authlib import __version__


def test_version():
    """Test version"""
    assert __version__ == '0.1.0.dev1'
