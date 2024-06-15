import sqlite3
import csv
import time

def create_connection():
    connection = sqlite3.connect('budget.db')
    return connection

def create_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    connection.commit()
    connection.close()

def execute_query(query, params=(), retry_count=5):
    for _ in range(retry_count):
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            connection.close()
            return
        except sqlite3.OperationalError as e:
            if 'locked' in str(e):
                time.sleep(0.1)
            else:
                raise e

def fetch_query(query, params=(), retry_count=5):
    for _ in range(retry_count):
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            connection.close()
            return result
        except sqlite3.OperationalError as e:
            if 'locked' in str(e):
                time.sleep(0.1)
            else:
                raise e

def insert_expense(user_id, month, category, amount):
    execute_query('INSERT INTO budget (user_id, month, category, amount) VALUES (?, ?, ?, ?)', (user_id, month, category, amount))

def insert_income(user_id, month, amount):
    execute_query('INSERT INTO income (user_id, month, amount) VALUES (?, ?, ?)', (user_id, month, amount))

def delete_data(user_id, month):
    execute_query('DELETE FROM budget WHERE user_id = ? AND month = ?', (user_id, month))
    execute_query('DELETE FROM income WHERE user_id = ? AND month = ?', (user_id, month))

def get_expenses(user_id, month):
    expenses = fetch_query('SELECT category, amount FROM budget WHERE user_id = ? AND month = ?', (user_id, month))
    income = fetch_query('SELECT amount FROM income WHERE user_id = ? AND month = ?', (user_id, month))
    return expenses, income[0][0] if income else 0

def get_distinct_months(user_id):
    months = fetch_query('SELECT DISTINCT month FROM budget WHERE user_id = ?', (user_id,))
    return [month[0] for month in months]

def export_to_csv(user_id, filename='budget_export.csv'):
    rows_budget = fetch_query('SELECT * FROM budget WHERE user_id = ?', (user_id,))
    rows_income = fetch_query('SELECT * FROM income WHERE user_id = ?', (user_id,))

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'User ID', 'Month', 'Category', 'Amount'])
        writer.writerows(rows_budget)
        writer.writerow([])
        writer.writerow(['ID', 'User ID', 'Month', 'Income Amount'])
        writer.writerows(rows_income)

create_table()
