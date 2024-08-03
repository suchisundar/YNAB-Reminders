from models import db, User
from app import app
import pytest

@pytest.fixture

def test_dashboard_access(client, init_database):
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login page for non-authenticated users

    user = User(username='testuser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)

    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data
