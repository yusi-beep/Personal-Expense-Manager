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
	with open(FILE_NAME, "r", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		for row in reader:
			amount = float(row["amount"])
			if row["type"] == "income":
				balance += amount
			elif row["type"] == "expense":
				balance -= amount
	print(f"Current balance: {balance:.2f} BGN")

def menu():
	while True:
		print("\n=== Personal Expense Tracker ===")
		print("1. Add record")
		print("2. View record")
		print("3. Balance")
		print("4. Exit")

		choice = input("Select: ")

		if choice == "1":
			add_record()
		elif choice == "2":
			view_records()
		elif choice == "3":
			calculate_balance()
		elif choice == "4":
			print("Exit from program successfully.")
			break
		else:
			print("Invalid selection!")

if __name__ == "__main__":
	menu()