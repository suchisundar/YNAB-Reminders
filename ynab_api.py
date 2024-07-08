import requests
import os

API_TOKEN = os.getenv("YNAB_API_TOKEN")
BASE_URL = "https://api.youneedabudget.com/v1"

def get_category_groups(budget_id):
    url = f"{BASE_URL}/budgets/{budget_id}/categories"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        category_groups = response.json().get('data').get('category_groups')
        filtered_category_groups = [
            group for group in category_groups
            if not group.get('hidden') and
               group.get('name') != "Credit Card Payments" and
               group.get('name') != "Internal Master Category"
        ]
        return filtered_category_groups
    else:
        print(f"Error fetching category groups: {response.status_code} {response.text}")
        return []

def enter_transaction(budget_id, account_id, category_id, payee_id, amount, date, memo, cleared="cleared"):
    url = f"{BASE_URL}/budgets/{budget_id}/transactions"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    transaction_data = {
        "transaction": {
            "account_id": account_id,
            "date": date,
            "amount": -amount,
            "payee_id": payee_id,
            "category_id": category_id,
            "memo": memo,
            "cleared": cleared,
            "approved": True
        }
    }
    response = requests.post(url, headers=headers, json=transaction_data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error creating transaction: {response.status_code} {response.text}")
        return None

def get_category_balance(budget_id, category_id):
    url = f"{BASE_URL}/budgets/{budget_id}/categories/{category_id}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        category = response.json().get('data').get('category')
        return category.get('balance')
    else:
        print(f"Error fetching category balance: {response.status_code} {response.text}")
        return None
