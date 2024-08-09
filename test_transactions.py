import pytest
from models import db, User, BudgetCategory, Transaction
from flask import session
from unittest.mock import patch

@pytest.mark.usefixtures('init_database')
class TestTransaction:

    @patch('app.create_transaction')
    def test_add_transaction(self, mock_create_transaction, client):
        # Mock the create_transaction function
        mock_create_transaction.return_value = None

        # Create and login user
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

        client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)

        # Pre-populate BudgetCategory with milliunits adjustment
        category = BudgetCategory(
            category_id='2b7aee8b-34ac-4194-822f-cfd7cdebd913',
            amount=5000000,  # milliunits (5000.00 units)
            threshold=500000  # milliunits (500.00 units)
        )
        db.session.add(category)
        db.session.commit()

        # Retrieve CSRF token
        response = client.get('/transactions')
        csrf_token = session.get('csrf_token')

        # Add transaction
        response = client.post('/transactions', data=dict(
            payee_name='Test Payee',
            amount=1000000,  # milliunits (1000.00 units)
            category_id='2b7aee8b-34ac-4194-822f-cfd7cdebd913',
            memo='Test Memo',
            date='2023-01-01',
            csrf_token=csrf_token
        ), follow_redirects=True)

        # Debugging to check response
        print("Response data:", response.data.decode('utf-8'))

        # Adjust the expected assertion
        assert b'Transaction created successfully!' in response.data
