# tests/conftest.py
import pytest
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Main test database
    app.config['SQLALCHEMY_BINDS'] = {  
        'ynab': 'sqlite:///test_ynab.db'  # YNAB test database
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.test_client() as client:
        with app.app_context():
            # Create all tables in both databases
            db.create_all()  

            # Verify tables in main test database
            print("Tables in main test database:", db.get_engine(app, bind=None).table_names())

            # Verify tables in YNAB test database
            print("Tables in YNAB test database:", db.get_engine(app, bind='ynab').table_names())

            yield client
            db.drop_all()  # Clean up after tests

@pytest.fixture
def init_database(client):
    """Setup the database with initial data"""
    db.create_all()  # Ensure the database is created and clean

    # Verify tables in main test database
    print("Tables in main test database (init_database):", db.get_engine(app, bind=None).table_names())

    # Verify tables in YNAB test database
    print("Tables in YNAB test database (init_database):", db.get_engine(app, bind='ynab').table_names())

    yield  # Run the test

    db.session.remove()
    db.drop_all()  # Clean up after tests
