import csv
import os
from datetime import datetime

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

def menu():
	while True:
		print("\n=== Personal Expense Tracker ===")
		print("1. Add record")
		print("2. View record")
		print("3. Balance summary")
		print("4. Filter by category")
		print("5. Filter by month")
		print("6. Exit")

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
			print("Exit from program successfully.")
			break
		else:
			print("Invalid selection!")

if __name__ == "__main__":
	menu()