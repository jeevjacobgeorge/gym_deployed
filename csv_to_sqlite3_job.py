import csv
import sqlite3
from datetime import datetime
import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygym.settings")
django.setup()

from gym.models import Customer  # Replace `your_app` with your actual app name

# CSV file path
csv_file_path = "customers.csv"

# Step 1: Convert CSV to SQLite3
sqlite_db_path = "customers.db"
conn = sqlite3.connect(sqlite_db_path)
cursor = conn.cursor()

# Drop the existing table if you want to reset it (Optional)
cursor.execute("DROP TABLE IF EXISTS customer_data")

# Create SQLite table
cursor.execute('''
CREATE TABLE customer_data (
    admission_number INTEGER,
    name TEXT,
    phone_no TEXT,
    date_of_admission TEXT,
    blood_group TEXT,
    gender TEXT,
    height REAL,
    weight REAL,
    bmi REAL,
    health TEXT,
    email TEXT,
    date_of_birth TEXT
)
''')
conn.commit()

# Insert CSV data into SQLite
with open(csv_file_path, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cursor.execute('''
        INSERT INTO customer_data (admission_number, name, phone_no, date_of_admission, blood_group, gender, height, weight, bmi, health, email, date_of_birth)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(row['admission number']) if row['admission number'] else None,
            row['name'],
            row['phone no'],
            row['date of admission'],
            row['blood group'],
            row['gender'][0].upper() if row['gender'] else None,  # Use M/F for gender
            float(row['height']) if row['height'] else None,
            float(row['weight']) if row['weight'] else None,
            float(row['bmi']) if row['bmi'] else None,
            row['health'],
            row['email'],
            row['date of birth']
        ))
conn.commit()

# Step 2: Upload data to Django Database
cursor.execute("SELECT * FROM customer_data")
rows = cursor.fetchall()

for row in rows:
    try:
        admission_number, name, phone_no, date_of_admission, blood_group, gender, height, weight, bmi, health, email, date_of_birth = row

        # Convert dates
        date_of_admission = datetime.strptime(date_of_admission, "%m/%d/%Y").date() if date_of_admission else None
        date_of_birth = datetime.strptime(date_of_birth, "%m/%d/%Y").date() if date_of_birth else None

        # Save to Django model
        customer = Customer(
            admission_number=admission_number,
            name=name,
            phone_no=phone_no,
            date_of_admission=date_of_admission,
            blood_group=blood_group,
            gender=gender,
            height=height,
            weight=weight,
            bmi=bmi,
            health=health,
            email=email,
            date_of_birth=date_of_birth
        )
        customer.save()
        print(f"Saved: {name}")
    except Exception as e:
        print(f"Error saving {name}: {e}")

# Close SQLite connection
conn.close()
