import csv
import os
from datetime import datetime

FILE_NAME = "expenses.csv"

#Check if file exists, otherwise create it with header
if not os.path.exists(FILE_NAME):
	with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
		writer = csv.writer(file)
		writer.writerow(["date", "type", "category", "amount", "description"])


def menu():
	while True:
		print("\n=== Personal Expense Tracker ===")
		print("1. Add record")
		print("2. View record")
		print("3. Balance")
		print("4. Exit")
		break

if __name__ == "__main__":
	menu()