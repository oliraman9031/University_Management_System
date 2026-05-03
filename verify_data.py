import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

conn = pymysql.connect(host='localhost', port=3306, user='root', password=DB_PASSWORD, database='university_management_system', cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4')
cursor = conn.cursor()

# Get all existing tables
cursor.execute('SHOW TABLES')
existing_tables = [list(row.values())[0] for row in cursor.fetchall()]

tables_to_check = [
    'admin', 'students', 'faculty', 'department', 'courses', 'events',
    'student_event_participation', 'student_phone_no', 'faculty_phone_no',
    'enrollment', 'exams', 'takes_exams', 'results', 'fees'
]

print("\n" + "="*70)
print("DATABASE TABLE RECORD COUNT VERIFICATION")
print("="*70 + "\n")

total_records = 0
for table in tables_to_check:
    if table in existing_tables:
        cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
        result = cursor.fetchone()
        count = result['count']
        total_records += count
        status = "✓ HAS DATA" if count > 0 else "✗ EMPTY"
        print(f"{table:35} | Records: {count:3} | {status}")
    else:
        print(f"{table:35} | Records:   0 | ✗ TABLE NOT CREATED")

print("\n" + "="*70)
print(f"TOTAL RECORDS ACROSS ALL TABLES: {total_records}")
print("="*70 + "\n")

cursor.close()
conn.close()
