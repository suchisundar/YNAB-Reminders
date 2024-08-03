from models import db, User, BudgetCategory, Transaction
from app import app, BASE_URL, HEADERS
from flask import session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import os
from datetime import datetime
import pytest


def test_transactions_access(client, init_database):
    response = client.get('/transactions')
    assert response.status_code == 302  # Redirect to login page for non-authenticated users

    user = User(username='testuser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)

    response = client.get('/transactions')
    assert response.status_code == 200
    assert b'Transactions' in response.data

def test_add_transaction(client, init_database):
    user = User(username='testuser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)

    response = client.post('/transactions', data=dict(
        payee_name='Test Payee',
        amount=100.00,
        category_id='some-category-id',
        memo='Test Memo',
        date='2023-01-01'
    ), follow_redirects=True)

    assert b'Transaction created successfully!' in response.data
