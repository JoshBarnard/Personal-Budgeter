import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
from database import create_table, insert_expense, insert_income, delete_data, get_expenses, get_distinct_months, export_to_csv

def run_app(user_id):
    create_table()

    def calculate_remaining_budget():
        try:
            total_budget = validate_numeric_input(total_budget_entry.get(), "Total Budget")

            # Validate and gather expense entries
            expenses = []
            expense_labels = []
            month = month_entry.get()
            validate_date_input(month)

            for label, entry in zip(labels, expense_entries):
                if entry.get():
                    expense = validate_numeric_input(entry.get(), label)
                    expenses.append(expense)
                    expense_labels.append(label)
                    insert_expense(user_id, month, label, expense)  # Save each expense to the database

            insert_income(user_id, month, total_budget)  # Save monthly income to the database

            total_expenses = sum(expenses)
            remaining = total_budget - total_expenses

            spent_var.set(f"Total Spent: ${total_expenses:.2f}")
            remaining_var.set(f"Remaining Budget: ${remaining:.2f}")

            # Clear line graph if exists
            if hasattr(display_line_graph, 'canvas_widget'):
                display_line_graph.canvas_widget.destroy()

            # Display bar graph
            display_bar_graph(expense_labels, expenses, month)

            # Update month selection
            update_month_selection()

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except sqlite3.OperationalError as e:
            messagebox.showerror("Database Error", f"Database error: {e}")

    def validate_numeric_input(value, field_name):
        try:
            float_value = float(value)
            if float_value < 0:
                raise ValueError
            return float_value
        except ValueError:
            raise ValueError(f"Please enter a valid positive number for {field_name}.")

    def validate_date_input(value):
        try:
            datetime.strptime(value, "%m/%Y")
        except ValueError:
            raise ValueError("Please enter a valid month in the format MM/YYYY.")

    def display_bar_graph(labels, values, month):
        fig, ax = plt.subplots()
        ax.bar(labels, values, color='blue')
        ax.set_title(f'{spent_var.get()}   Expenses for {month}   {remaining_var.get()}')
        ax.set_ylabel('Amount ($)')
        ax.set_xlabel('Categories')

        # Clear previous graph if exists
        if hasattr(display_bar_graph, 'canvas_widget'):
            display_bar_graph.canvas_widget.destroy()

        # Embedding the graph in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=app)  # A tk.DrawingArea.
        display_bar_graph.canvas_widget = canvas.get_tk_widget()
        display_bar_graph.canvas_widget.grid(row=10, column=0, columnspan=2, sticky="nsew")
        canvas.draw()

        # Adjust window size after plotting
        app.after(100, lambda: app.geometry(''))  # Reset geometry to adjust to new content

    def reset_fields():
        total_budget_entry.delete(0, tk.END)
        for entry in expense_entries:
            entry.delete(0, tk.END)
        month_entry.delete(0, tk.END)
        spent_var.set("Total Spent: $0.00")
        remaining_var.set("Remaining Budget: $0.00")
        if hasattr(display_bar_graph, 'canvas_widget'):
            display_bar_graph.canvas_widget.destroy()
        if hasattr(display_line_graph, 'canvas_widget'):
            display_line_graph.canvas_widget.destroy()

    def export_data():
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            export_to_csv(user_id, filename)
            messagebox.showinfo("Export Successful", f"Data exported to {filename}")

    def fetch_data():
        try:
            month = selected_month.get()
            if not month or month == "No data yet":
                messagebox.showerror("Invalid Input", "Please select a valid month to view data.")
                return

            expenses, income = get_expenses(user_id, month)
            if not expenses:
                messagebox.showinfo("No Data", f"No data found for {month}.")
                return

            expense_labels = [expense[0] for expense in expenses]
            expense_values = [expense[1] for expense in expenses]

            total_expenses = sum(expense_values)
            spent_var.set(f"Total Spent: ${total_expenses:.2f}")
            remaining_var.set(f"Remaining Budget: ${income - total_expenses:.2f}")

            # Clear line graph if exists
            if hasattr(display_line_graph, 'canvas_widget'):
                display_line_graph.canvas_widget.destroy()

            display_bar_graph(expense_labels, expense_values, month)
        except sqlite3.OperationalError as e:
            messagebox.showerror("Database Error", f"Database error: {e}")

    def update_month_selection():
        months = get_distinct_months(user_id)
        if not months:
            months = ["No data yet"]
        selected_month.set('')
        start_month_var.set('')
        end_month_var.set('')
        month_menu['values'] = months
        start_month_menu['values'] = months
        end_month_menu['values'] = months

    def delete_selected_month():
        try:
            month = selected_month.get()
            if not month or month == "No data yet":
                messagebox.showerror("Invalid Input", "Please select a valid month to delete data.")
                return

            delete_data(user_id, month)
            messagebox.showinfo("Delete Successful", f"Data for {month} has been deleted.")
            update_month_selection()
        except sqlite3.OperationalError as e:
            messagebox.showerror("Database Error", f"Database error: {e}")

    def fetch_data_for_line_graph():
        try:
            start_month = start_month_var.get()
            end_month = end_month_var.get()
            if not start_month or not end_month or start_month == "No data yet" or end_month == "No data yet":
                messagebox.showerror("Invalid Input", "Please select valid start and end months to view data.")
                return

            start_date = datetime.strptime(start_month, "%m/%Y")
            end_date = datetime.strptime(end_month, "%m/%Y")

            if start_date > end_date:
                messagebox.showerror("Invalid Input", "Start month should be earlier than end month.")
                return

            months, expenses, incomes = fetch_monthly_data(user_id, start_month, end_month)

            if not months:
                messagebox.showinfo("No Data", "No data found between the selected months.")
                return

            # Clear bar graph if exists
            if hasattr(display_bar_graph, 'canvas_widget'):
                display_bar_graph.canvas_widget.destroy()

            display_line_graph(months, expenses, incomes)
        except sqlite3.OperationalError as e:
            messagebox.showerror("Database Error", f"Database error: {e}")

    def fetch_monthly_data(user_id, start_month, end_month):
        months = []
        expenses = []
        incomes = []

        start_date = datetime.strptime(start_month, "%m/%Y")
        end_date = datetime.strptime(end_month, "%m/%Y")

        current_date = start_date
        while current_date <= end_date:
            month_str = current_date.strftime("%m/%Y")
            month_expenses, month_income = get_expenses(user_id, month_str)
            total_expense = sum(exp[1] for exp in month_expenses)
            months.append(month_str)
            expenses.append(total_expense)
            incomes.append(month_income)
            current_date = datetime(current_date.year + (current_date.month // 12), (current_date.month % 12) + 1, 1)

        return months, expenses, incomes

    def display_line_graph(months, expenses, incomes):
        fig, ax = plt.subplots()
        ax.plot(months, expenses, 'r', label='Spending')
        ax.plot(months, incomes, 'g', label='Income')
        ax.set_title('Spending and Income Over Time')
        ax.set_ylabel('Amount ($)')
        ax.set_xlabel('Months')
        ax.legend()

        # Remove previous graph if exists
        if hasattr(display_line_graph, 'canvas_widget'):
            display_line_graph.canvas_widget.destroy()

        # Embedding the graph in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=app)
        display_line_graph.canvas_widget = canvas.get_tk_widget()
        display_line_graph.canvas_widget.grid(row=12, column=0, columnspan=2, sticky="nsew")
        canvas.draw()

        # Adjust window size after plotting
        app.after(100, lambda: app.geometry(''))

    def clear_line_graph():
        if hasattr(display_line_graph, 'canvas_widget'):
            display_line_graph.canvas_widget.destroy()

    app = tk.Tk()
    app.title("Personal Budgeter")

    large_font = ('Verdana', 14)

    app.grid_rowconfigure(10, weight=1)
    app.grid_columnconfigure(1, weight=1)

    # Entries for expenses
    labels = ["Rent", "Groceries", "Utilities", "Transportation", "Misc"]
    expense_entries = []
    for i, label in enumerate(labels):
        tk.Label(app, text=label, font=large_font).grid(row=i, column=0)
        entry = tk.Entry(app, font=large_font, width=25)
        entry.grid(row=i, column=1)
        expense_entries.append(entry)

    # Month and budget entries
    tk.Label(app, text="Enter Month (MM/YYYY)", font=large_font).grid(row=len(labels), column=0)
    month_entry = tk.Entry(app, font=large_font, width=25)
    month_entry.grid(row=len(labels), column=1)

    tk.Label(app, text="Enter Monthly Income", font=large_font).grid(row=len(labels) + 1, column=0)
    total_budget_entry = tk.Entry(app, font=large_font, width=25)
    total_budget_entry.grid(row=len(labels) + 1, column=1)

    # Buttons
    calculate_button = tk.Button(app, text="Calculate and Save", command=calculate_remaining_budget, font=large_font,
                                 height=2, width=15)
    calculate_button.grid(row=len(labels) + 2, column=0)

    reset_button = tk.Button(app, text="Clear Bar Graph", command=reset_fields, font=large_font, height=2, width=15)
    reset_button.grid(row=len(labels) + 2, column=1)

    export_button = tk.Button(app, text="Export to CSV", command=export_data, font=large_font, height=2, width=15)
    export_button.grid(row=len(labels) + 2, column=2, columnspan=2)

    # Month selection for fetching data
    selected_month = tk.StringVar(app)
    tk.Label(app, text="Select Month to View", font=large_font).grid(row=len(labels) + 4, column=0)
    month_menu = ttk.Combobox(app, textvariable=selected_month, font=large_font, width=22)
    month_menu.grid(row=len(labels) + 4, column=1)

    fetch_button = tk.Button(app, text="Show Month", command=fetch_data, font=large_font, height=2, width=15)
    fetch_button.grid(row=len(labels) + 5, column=0, columnspan=1)

    # Delete button for removing selected month's data
    delete_button = tk.Button(app, text="Delete Month", command=delete_selected_month, font=large_font, height=2, width=15)
    delete_button.grid(row=len(labels) + 5, column=1)

    # Labels for displaying results
    spent_var = tk.StringVar(app, value="Total Spent: $0.00")
    remaining_var = tk.StringVar(app, value="Remaining Budget: $0.00")
    tk.Label(app, textvariable=spent_var, font=large_font).grid(row=len(labels) + 7, column=0)
    tk.Label(app, textvariable=remaining_var, font=large_font).grid(row=len(labels) + 7, column=1)

    start_month_var = tk.StringVar(app)
    end_month_var = tk.StringVar(app)

    tk.Label(app, text="Select Start Month", font=large_font).grid(row=len(labels) + 8, column=0)
    start_month_menu = ttk.Combobox(app, textvariable=start_month_var, font=large_font, width=22)
    start_month_menu.grid(row=len(labels) + 8, column=1)

    tk.Label(app, text="Select End Month", font=large_font).grid(row=len(labels) + 9, column=0)
    end_month_menu = ttk.Combobox(app, textvariable=end_month_var, font=large_font, width=22)
    end_month_menu.grid(row=len(labels) + 9, column=1)

    graph_button = tk.Button(app, text="Show Line Graph", command=fetch_data_for_line_graph, font=large_font, height=2, width=15)
    graph_button.grid(row=len(labels) + 10, column=0, columnspan=2)

    clear_graph_button = tk.Button(app, text="Clear Line Graph", command=clear_line_graph, font=large_font, height=2, width=15)
    clear_graph_button.grid(row=len(labels) + 11, column=0, columnspan=2)

    update_month_selection()

    app.mainloop()

if __name__ == "__main__":
    create_table()

