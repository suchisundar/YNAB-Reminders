import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from forms import BudgetForm, TransactionForm
from twilio.rest import Client
from dotenv import load_dotenv
import requests
from datetime import datetime
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configure the SQLAlchemy part of the application instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ynab.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Define models
class BudgetCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.String(80), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payee_name = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.String(80), nullable=False)
    memo = db.Column(db.String(200))

# Create tables if they do not exist
with app.app_context():
    db.create_all()

YNAB_API_KEY = os.getenv('YNAB_API_KEY')
BUDGET_ID = os.getenv('BUDGET_ID')
BASE_URL = f'https://api.youneedabudget.com/v1/budgets/{BUDGET_ID}'
HEADERS = {'Authorization': f'Bearer {YNAB_API_KEY}'}

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Function to send a text/whatsapp message
def send_text_message(message):
    try:
        client.messages.create(
            body=message,
            from_=f'whatsapp:{os.getenv("TWILIO_PHONE_NUMBER")}',
            to=f'whatsapp:{os.getenv("USER_PHONE_NUMBER")}'
        )
        print(f"Message sent: {message}")
    except Exception as e:
        print(f"Failed to send message: {e}")


# Function to get categories
def get_categories():
    url = f"{BASE_URL}/categories"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        category_groups = data['data']['category_groups']

        filtered_groups = []
        for group in category_groups:
            if group['hidden'] or 'Internal Master Category' in group['name']:
                continue

            filtered_categories = []
            for cat in group['categories']:
                if not cat['hidden'] and cat['name'] != 'Credit Card Payments':
                    filtered_categories.append(cat)

            if filtered_categories:
                group['categories'] = filtered_categories
                filtered_groups.append(group)

        return filtered_groups
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return []

# Function to create a transaction
def create_transaction(payee_name, amount, category_id, memo, date):
    transaction = {
        "transaction": {
            "account_id": os.getenv('ACCOUNT_ID'),
            "date": date,
            "amount": int(amount * -1000),  # YNAB uses milliunits
            "payee_name": payee_name,
            "category_id": category_id,
            "memo": memo,
            "cleared": "cleared",
            "approved": True,
            "flag_color": None,
            "subtransactions": []
        }
    }

    response = requests.post(f'{BASE_URL}/transactions', json=transaction, headers=HEADERS)

    if response.status_code != 201:
        print("Response status code:", response.status_code)
        print("Response text:", response.text)

    response.raise_for_status()
    return response.json()

# Function to check balance
def check_balance(category_id):
    url = f"{BASE_URL}/categories/{category_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    category = response.json()['data']['category']
    balance = category['balance'] / 1000  # Convert from milliunits to units

    db_category = BudgetCategory.query.filter_by(category_id=category_id).first()
    threshold = db_category.threshold / 1000 if db_category else None

    return category['name'], balance, threshold

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    categories = get_categories()

    category_thresholds = {}
    for category in BudgetCategory.query.all():
        category_thresholds[category.category_id] = category.threshold / 1000

    for group in categories:
        for category in group['categories']:
            if category['id'] not in category_thresholds:
                category_thresholds[category['id']] = 'N/A'

    return render_template('dashboard.html', categories=categories, category_thresholds=category_thresholds)


@app.route('/edit_category/<category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if request.method == 'POST':
        budgeted = float(request.form['budgeted']) * 1000
        threshold = float(request.form['threshold']) * 1000

        url = f"{BASE_URL}/categories/{category_id}"
        category_data = {
            "category": {
                "budgeted": budgeted
            }
        }
        response = requests.patch(url, json=category_data, headers=HEADERS)
        response.raise_for_status()

        category = BudgetCategory.query.filter_by(category_id=category_id).first()
        if category:
            category.threshold = threshold
        else:
            category = BudgetCategory(category_id=category_id, amount=budgeted, threshold=threshold)
            db.session.add(category)
        db.session.commit()

        flash('Category updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    url = f"{BASE_URL}/categories/{category_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    category = response.json()['data']['category']

    db_category = BudgetCategory.query.filter_by(category_id=category_id).first()
    threshold = db_category.threshold / 1000 if db_category else ''

    budgeted = category['budgeted'] / 1000

    return render_template('edit_category.html', category=category, budgeted=budgeted, threshold=threshold)

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    categories = get_categories()
    transaction_form = TransactionForm()
    transaction_form.populate_categories(categories)
    
    # Fetch all transactions for displaying in the transaction history
    transactions = Transaction.query.all()

    if transaction_form.validate_on_submit():
        payee_name = transaction_form.payee_name.data
        amount = transaction_form.amount.data
        category_id = transaction_form.category_id.data
        memo = transaction_form.memo.data
        date = transaction_form.date.data.strftime('%Y-%m-%d')

        category_name, balance, threshold = check_balance(category_id)
        print(f"Category: {category_name}, Balance: {balance}, Threshold: {threshold}")

        if amount > balance:
            flash(f'Insufficient balance in the selected category. Available balance: {balance}', 'error')
        else:
            try:
                create_transaction(payee_name, amount, category_id, memo, date)
                print(f"Transaction created: {payee_name}, {amount}, {category_id}, {memo}, {date}")

                # Directly compare the balance after transaction
                new_balance = balance - amount
                print(f"New balance: {new_balance}")

                if threshold is not None and new_balance < threshold:
                    message = f"Warning: The balance for category '{category_name}' is below the threshold."
                    send_text_message(message)
                    print(f"Message sent: {message}")
                    flash(message, 'error')  

                flash('Transaction created successfully!', 'success')
            except requests.exceptions.HTTPError as err:
                print(f"HTTPError: {err}")
                flash(f'Error creating transaction: {err}', 'error')

        return redirect(url_for('transactions'))

    return render_template('transactions.html', transaction_form=transaction_form, transactions=transactions)

if __name__ == "__main__":
    app.run(debug=True)
