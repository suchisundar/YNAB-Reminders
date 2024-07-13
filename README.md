Show Me the Money

Show Me the Money is a web application that integrates with the You Need A Budget (YNAB) API to help users manage and track their budgets and save for financial goals. The application allows users to set budget categories, log transactions, and receive SMS alerts through the Twilio API when their budget categories are running low.

Features
Spending category warnings: View color coded warnings on the dashboard, receive warnings when transactions are created in categories that are low on funds.
Budget Management: Set and manage budget amount and threshold for different categories.
Transaction Logging: Log transactions with details such as payee name, amount, category, and memo.
SMS Alerts: Receive SMS alerts when the remaining budget for a category falls below a specified threshold.
API Integration: Fetch categories and log transactions using the YNAB API.

Technologies Used
Backend:
Python: The core programming language used.
Flask: Web framework for Python.
SQLAlchemy: ORM for database management.
WTForms: Form handling and validation.
dotenv: For managing environment variables.
APIs:
YNAB API: External API for budget management.
Twilio API: External API for sending SMS alerts.
Database:
SQLite: Database for storing budget and transaction data.
Frontend:
HTML/CSS: For structuring and styling the web pages.

Future Work:
To obtain the most value out of the texting feature, this app should be used with the YNAB banking integration so that transactions are recorded with more timeliness and accuracy. For travelers or those who otherwise don't have consistent internet access, this application provides an intuitive, structured, and visual solution to manage a budget.

View the deployed app at: https://shes-got-money-11438ac3dc54.herokuapp.com/
