"""Test user"""
from tests.rest_api.conftest import assert_status_code


def test_user(client, init_user, token):
    """Test user"""
    response = client.get('/users', headers={'www-authenticate': f'Bearer {token}'})
    assert_status_code(response)
    assert response.json().get('message') == 'ok'
