import requests
import os

from datetime import date

BASE = os.environ.get("API_BASE", "http://127.0.0.1:5000/api")
USERNAME = "admin"
PASSWORD = "admin"

def main():
    # === 1) LOGIN ====
    r = requests.post(f"{BASE}/login", json={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in:", r.json()["user"])

    # === 2) LIST RECORDS ===
    r = requests.get(f"{BASE}/records", headers=headers)
    print("Records count:", len(r.json().get("records", [])))

    # === 3) CREATE CATEGORY ===
    cat_data = {"name": "TestAPI"}
    r = requests.post(f"{BASE}/categories", json=cat_data, headers=headers)
    if r.status_code == 201:
        print("Created category:", r.json())
    elif r.status_code == 400 and "exists" in r.text.lower():
        print("Category 'TestAPI' already exists.")
    else:
        print("Category create failed:", r.status_code, r.text)


    # === 4) CREATE RECORD ===
    new_rec = {
        "date": "2025-08-29",
        "type": "expense",
        "category": "TestAPI",
        "amount": 12.5,
        "description": "API test expense"
    }
    r = requests.post(f"{BASE}/records", json=new_rec, headers=headers)
    assert r.status_code == 201, r.text

    data = r.json()
    if "record" in data:
        record_id = data["record"]["id"]
    else:
        record_id = data["id"]

    print("Created record ID:", record_id)

    # === 5) EDIT RECORD ===
    edit_data = {
        "date": str(date.today()),
        "type": "expense",
        "category": "TestAPI",
        "amount": 99.99,
        "description": "Edited by API test"
    }
    r = requests.put(f"{BASE}/records/{record_id}", json=edit_data, headers=headers)
    assert r.status_code == 200, r.text
    print("Edited record:", r.json())

    # === 6) FILTER RECORDS ===
    params = {
        "type": "expense",
        "category": "TestAPI",
        "date_from": "2025-01-01",
        "date_to": "2025-12-31",
        "q": "Edited"
    }
    r = requests.get(f"{BASE}/records", headers=headers, params=params)
    assert r.status_code == 200
    filtered = r.json().get("records", [])
    print(f"Filtered records ({len(filtered)} found):")
    for rec in filtered:
        print("   -", rec)

    # --- Ensure output dir exists ---
    OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(OUT_DIR, exist_ok=True)

    # === 7) EXPORT CSV ===
    r = requests.get(f"{BASE}/records/export/csv", headers=headers)
    csv_path = os.path.join(OUT_DIR, "records_test.csv")
    with open(csv_path, "wb") as f:
        f.write(r.content)
    print("Exported CSV ->", csv_path)

    # === 8) EXPORT PDF ===
    r = requests.get(f"{BASE}/records/export/pdf", headers=headers)
    pdf_path = os.path.join(OUT_DIR, "records_test.pdf")
    with open(pdf_path, "wb") as f:
        f.write(r.content)
    print("Exported PDF ->", pdf_path)

    # === 9) IMPORT CSV ===
    files = {"file": open(csv_path, "rb")}
    data = {"create_missing_categories": "on"}
    r = requests.post(f"{BASE}/records/import/csv", headers=headers, files=files, data=data)
    print("Import result:", r.text)

    # === 10) DELETE record (cleanup) ===
    r = requests.delete(f"{BASE}/records/{record_id}", headers=headers)
    print("Deleted record:", record_id, "->", r.json())

if __name__ == "__main__":
    main()
