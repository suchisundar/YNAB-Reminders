import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
BASE_URL = "https://api.youneedabudget.com/v1"
API_KEY = os.getenv('YNAB_API_KEY')
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

# Function to get budgets
def get_budgets():
    url = f"{BASE_URL}/budgets"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
    except Exception as err:
        print(f"An error occurred: {err}")

# Fetch and print budgets
budgets = get_budgets()
if budgets:
    print(budgets)
else:
    print("Failed to fetch budgets.")
