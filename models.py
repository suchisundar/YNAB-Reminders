from db import db

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
