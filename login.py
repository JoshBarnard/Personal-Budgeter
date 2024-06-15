import tkinter as tk
from tkinter import messagebox
import sqlite3

# Database functions
def create_users_table():
    connection = sqlite3.connect('budget.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()

def register_user(username, password):
    connection = sqlite3.connect('budget.db')
    cursor = connection.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        connection.commit()
        messagebox.showinfo("Registration Successful", "User registered successfully.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")
    connection.close()

def validate_login(username, password):
    connection = sqlite3.connect('budget.db')
    cursor = connection.cursor()
    cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    connection.close()
    if result and result[1] == password:
        return result[0]
    return None

# Login screen
def login_screen():
    def login():
        username = username_entry.get()
        password = password_entry.get()
        user_id = validate_login(username, password)
        if user_id:
            root.destroy()
            import main
            main.run_app(user_id)  # Pass user ID to the main application
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def register():
        username = username_entry.get()
        password = password_entry.get()
        if username and password:
            register_user(username, password)
        else:
            messagebox.showerror("Error", "Please enter both username and password.")

    root = tk.Tk()
    root.title("Login")
    root.geometry("525x225")

    tk.Label(root, text="Username", font=('Helvetica', 24)).grid(row=2, column=0)
    tk.Label(root, text="Password", font=('Helvetica', 24)).grid(row=3, column=0)

    username_entry = tk.Entry(root, font=('Helvetica', 24))
    password_entry = tk.Entry(root, show="*", font=('Helvetica', 24))

    username_entry.grid(row=2, column=1)
    password_entry.grid(row=3, column=1)

    login_button = tk.Button(root, text="Login", command=login, font=('Helvetica', 24))
    login_button.grid(row=5, column=0, columnspan=4)

    register_button = tk.Button(root, text="Register", command=register, font=('Helvetica', 24))
    register_button.grid(row=6, column=0, columnspan=4)

    root.mainloop()

if __name__ == "__main__":
    create_users_table()
    login_screen()
