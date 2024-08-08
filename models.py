from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()
bcrypt = Bcrypt()

# Define User model
class User(db.Model, UserMixin):
    '''User in System'''

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)

    @classmethod
    def signup(cls, username, password, email):
        '''Sign up user'''
        hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
        user = User(username=username, password=hashed_password, email=email)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def authenticate(cls, username, password):
        '''Find user with `username` and `password`'''
        user = cls.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        return False

# Define BudgetCategory model
class BudgetCategory(db.Model):
    '''Category in System'''
    __bind_key__ = 'ynab'
    __tablename__ = 'budget_category'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False, default=100)

# Define Transaction model
class Transaction(db.Model):
    '''Transaction in System'''
    __bind_key__ = 'ynab'
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    payee_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.String(100), nullable=False)
    memo = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 

def connect_db(app):
    '''Connect to database'''
    db.init_app(app)
