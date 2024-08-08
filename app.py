import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import requests
from datetime import datetime
from forms import BudgetForm, TransactionForm
from twilio.rest import Client
from models import db, User, BudgetCategory, Transaction, connect_db
from flask_migrate import Migrate



# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configure the SQLAlchemy part of the application instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = {
    'ynab': 'sqlite:///ynab.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
connect_db(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Define user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create tables if they do not exist
with app.app_context():
    db.create_all()

# Constants for YNAB API and Twilio
YNAB_API_KEY = os.getenv('YNAB_API_KEY')
BUDGET_ID = os.getenv('BUDGET_ID')
BASE_URL = f'https://api.youneedabudget.com/v1/budgets/{BUDGET_ID}'
HEADERS = {'Authorization': f'Bearer {YNAB_API_KEY}'}

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Function to send a text/WhatsApp message using Twilio
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

# Function to get categories from YNAB
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

# Function to create a transaction in YNAB
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

# Function to check balance for a specific category in YNAB
def check_balance(category_id):
    url = f"{BASE_URL}/categories/{category_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    category = response.json()['data']['category']
    balance = category['balance'] / 1000  # Convert from milliunits to units

    db_category = BudgetCategory.query.filter_by(category_id=category_id).first()
    threshold = db_category.threshold / 1000 if db_category else None

    return category['name'], balance, threshold

# Index route
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Dashboard route
@app.route('/dashboard', methods=['GET'])
@login_required
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

# Route to edit a specific category
@app.route('/edit_category/<category_id>', methods=['GET', 'POST'])
@login_required
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

# Route to manage transactions
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


# Route to edit a transaction
@app.route('/edit_transaction/<string:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first_or_404()
    categories = get_categories()  # Assuming get_categories is imported from ynab_api.py
    if request.method == 'POST':
        transaction.payee_name = request.form['payee_name']
        transaction.amount = float(request.form['amount']) * 1000  # Ensure the amount is in the correct format
        transaction.category_id = request.form['category_id']
        transaction.memo = request.form['memo']
        transaction.date = datetime.strptime(request.form['date'], '%Y-%m-%d')

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transaction_history'))

    return render_template('edit_transaction.html', transaction=transaction, categories=categories)

# Function to get transactions from YNAB
def get_transactions():
    url = f"{BASE_URL}/transactions"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data['data']['transactions']

# Function to get a dictionary of category IDs to category names
def get_category_dict():
    categories = get_categories()
    category_dict = {}
    for group in categories:
        for category in group['categories']:
            category_dict[category['id']] = category['name']
    return category_dict

# Function to delete a transaction in YNAB
def delete_ynab_transaction(transaction_id):
    url = f"{BASE_URL}/transactions/{transaction_id}"
    response = requests.delete(url, headers=HEADERS)
    response.raise_for_status()
    return response.status_code == 204

# Route to delete a transaction
@app.route('/delete_transaction/<string:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first_or_404()
    try:
        delete_ynab_transaction(transaction_id)  # Assuming delete_ynab_transaction is imported from ynab_api.py
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    except requests.exceptions.HTTPError as err:
        flash(f'Error deleting transaction: {err}', 'error')
    return redirect(url_for('transaction_history'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html')


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/transaction_history', methods=['GET'])
@login_required
def transaction_history():
    transactions = get_transactions()
    category_dict = get_category_dict()
    for transaction in transactions:
        transaction['category_name'] = category_dict.get(transaction['category_id'], 'Unknown')
    return render_template('transaction_history.html', transactions=transactions)


if __name__ == "__main__":
    app.run(debug=True)