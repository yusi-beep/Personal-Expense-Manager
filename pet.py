import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

FILE_NAME = "expenses.csv"

#Check if file exists, otherwise create it with header
if not os.path.exists(FILE_NAME):
	with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
		writer = csv.writer(file)
		writer.writerow(["date", "type", "category", "amount", "description"])

def add_record():
	date = datetime.now().strftime("%Y-%m-%d")
	entry_type = input("Type (expense/income): ").strip().lower()
	category = input("Category:" ).strip()
	amount = float(input("Amount: "))
	description = input("Description: " ).strip()

	with open(FILE_NAME,"a", newline="", encoding="utf-8") as file:
		writer = csv.writer(file)
		writer.writerow([date, entry_type, category, amount, description])

	print("Record added successfully!")

def view_records():
	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.reader(file)
		next(reader) #skip header
		for row in reader:
			print(row)

def calculate_balance():
	balance = 0
	income = 0
	expense = 0
	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		for row in reader:
			amount = float(row["amount"])
			if row["type"] == "income":
				balance += amount
				income += amount
			elif row["type"] == "expense":
				balance -= amount
				expense += amount
	print(f"Current balance: {balance:.2f} BGN")
	print(f"Total income: {income:.2f} BGN")
	print(f"Total expense: {expense:.2f} BGN")

def filter_by_category():
	category = input("Enter category to filter: ").strip().lower()
	total = 0
	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		print(f"\n == Records in category '{category}' ===")
		for row in reader:
			if row["category"].lower() == category:
				print(row)
				total += float(row["amount"])
	print(f"Total for category '{category}': {total:.2f} BGN")

def filter_by_month():
	year_month = input("Enter month (YYYY-MM): ").strip()
	total_income = 0
	total_expense = 0
	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		print(f"\n=== Records for {year_month} ===")
		for row in reader:
		 	if row["date"].startswith(year_month):
		 		print(row)
		 		amount = float(row["amount"])
		 		if row["type"] == "income":
		 			total_income += amount
		 		elif row["type"] == "expense":
		 			total_expense += amount
	print(f"Income for {year_month}: {total_income:.2f} BGN")
	print(f"Expense for {year_month}: {total_expense:.2f} BGN")
	print(f"Net: {(total_income - total_expense):.2f} BGN")

def plot_expenses_by_category():
	categories = defaultdict(float)
	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		for row in reader:
			if row["type"] == "expense":
				categories[row["category"]] += float(row["amount"])

	if not categories:
		print("No expenses found!")
		return

	plt.figure(figsize=(6, 6))
	plt.pie(categories.values(), labels=categories.keys(), autopct="%1.1f%%", startangle=90)
	plt.title("Expenses by category")
	plt.show()

def plot_monthly_summary():
	monthly_income = defaultdict(float)
	monthly_expense = defaultdict(float)

	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		for row in reader:
			date_obj = datetime.strptime(row["date"], "%Y-%m-%d")
			year_month = date_obj.strftime("%Y-%m")

			amount = float(row["amount"])
			if row["type"] == "income":
				monthly_income[year_month] += amount
			elif row["type"] == "expense":
				monthly_expense[year_month] += amount

	if not monthly_income and not monthly_expense:
		print("No data found!")
		return

	month = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))

	income_vals = [monthly_income[m] for m in month]
	expense_vals = [monthly_expense[m] for m in month]

	x = range(len(month))
	plt.figure(figsize=(8, 5))
	plt.bar(x, income_vals, width=0.4, label="Income", align="center")
	plt.bar(x, expense_vals, width=0.4, label="Expence", align="edge")
	plt.xticks(x,month, rotation=45)
	plt.title("Monthly Income vs Expense")
	plt.xlabel("Month")
	plt.ylabel("Amount (BGN)")
	plt.legend()
	plt.tight_layout()
	plt.show()

def menu():
	while True:
		print("\n=== Personal Expense Tracker ===")
		print("1. Add record")
		print("2. View record")
		print("3. Balance summary")
		print("4. Filter by category")
		print("5. Filter by month")
		print("6. Plot expenses by category (pie chart)")
		print("7. Plot monthly summary (bar chart)")
		print("8. Exit")

		choice = input("Select: ")

		if choice == "1":
			add_record()
		elif choice == "2":
			view_records()
		elif choice == "3":
			calculate_balance()
		elif choice == "4":
			filter_by_category()
		elif choice == "5":
			filter_by_month()
		elif choice == "6":
			plot_expenses_by_category()
		elif choice == "7":
			plot_monthly_summary()
		elif choice == "8":
			print("Exit from program successfully.")
			break
		else:
			print("Invalid selection!")

if __name__ == "__main__":
	menu()