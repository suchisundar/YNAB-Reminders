import pytest
from app import app, db
from models import User

def test_register(client):
    response = client.post('/register', data=dict(
        username='testuser',
        password='testpassword',
        email='testuser@example.com'
    ), follow_redirects=True)
    assert b'Registration successful!' in response.data

def test_login(client, init_database):
    user = User(username='testuser', email='testuser@example.com')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    assert b'Login successful!' in response.data

def test_logout(client, init_database):
    user = User(username='testuser', email='testuser@example.com')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)

    response = client.get('/logout', follow_redirects=True)
    assert b'You have been logged out.' in response.data
