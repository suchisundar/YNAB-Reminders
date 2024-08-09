import pytest
from models import db, User, BudgetCategory


@pytest.mark.usefixtures('init_database')
def test_set_category_threshold(client):
    # Create and login user
    user = User(username='testuser', email='testuser@example.com')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)

    # Pre-populate BudgetCategory
    category_id = '2b7aee8b-34ac-4194-822f-cfd7cdebd913'
    category = BudgetCategory(
        category_id=category_id,
        amount=50000,  # milliunits
        threshold=5000  # milliunits
    )
    db.session.add(category)
    db.session.commit()

    # Update the threshold via POST request to edit_category
    response = client.post(f'/edit_category/{category_id}', data=dict(
        budgeted=40000,  # milliunits
        threshold=10000  # milliunits (10.00 units)
    ), follow_redirects=True)

    assert b'Category updated successfully!' in response.data

    # Fetch the updated category from the database
    updated_category = BudgetCategory.query.filter_by(category_id=category_id).first()
    assert updated_category.threshold == 10000 * 1000  # Comparing in milliunits

