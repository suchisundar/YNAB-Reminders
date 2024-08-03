from db import db
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class User(db.Model):
    '''User in System'''

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key = True)
    
    username = db.Column(
            db.Text,
            nullable = False,
            unique = True
    )

    password = db.Column(
            db.Text,
            nullable = False,
    )

    email = db.Column(
            db.Text,
            nullable = False,
            unique = True
    )


    @classmethod
    def signup(cls, username, password, email):
        '''Sign up user'''

        hashed_pwd = bcrypt.generate_password_hash(password).decode('utf8')

        user = User(
            username = username,
            password = hashed_pwd,
            email = email
        )

        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        '''Find user with `username` and `password`'''

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        
        return False

class BudgetCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False, default=100)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payee_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.String(100), nullable=False)
    memo = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow) 
