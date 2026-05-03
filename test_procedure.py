import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

conn = pymysql.connect(host='localhost', port=3306, user='root', password=DB_PASSWORD, database='university_management_system', cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4')
cursor = conn.cursor()

# Test inserting a student via the stored procedure
print("\n" + "="*70)
print("TESTING STORED PROCEDURE INSERT_STUDENT")
print("="*70 + "\n")

test_students = [
    {
        'First_Name': 'Itachi',
        'Middle_Name': '',
        'Last_Name': 'Uchiha',
        'Street': 'Hidden Leaf Village',
        'District': 'Konoha',
        'State': 'Land of Fire',
        'Country': 'Japan',
        'Gender': 'Male',
        'Date_of_Birth': '1990-06-09',
        'Email': 'itachi.test@example.com',
        'College_Email': 'itachi.test@thapar.edu',
        'Password': 'Tsukuyomi123',
        'Enrollment_Year': 2010
    },
    {
        'First_Name': 'Rin',
        'Middle_Name': '',
        'Last_Name': 'Nohara',
        'Street': 'Hidden Leaf Village',
        'District': 'Konoha',
        'State': 'Land of Fire',
        'Country': 'Japan',
        'Gender': 'Female',
        'Date_of_Birth': '1992-06-15',
        'Email': 'rin.test@example.com',
        'College_Email': 'rin.test@thapar.edu',
        'Password': 'HealingJutsu456',
        'Enrollment_Year': 2011
    }
]

for i, student in enumerate(test_students, 1):
    print(f"[{i}] Testing with: {student['First_Name']} {student['Last_Name']}")
    try:
        cursor.callproc('insert_student', (
            student['First_Name'], 
            student['Middle_Name'], 
            student['Last_Name'],
            student['Street'], 
            student['District'], 
            student['State'],
            student['Country'], 
            student['Gender'], 
            student['Date_of_Birth'],
            student['Email'], 
            student['College_Email'], 
            student['Password'],
            student['Enrollment_Year']
        ))
        result = cursor.fetchall()
        for row in result:
            print(f"    Result: {row}")
        conn.commit()
        print("    ✓ SUCCESS\n")
    except pymysql.Error as err:
        print(f"    ✗ ERROR: {err}\n")
        conn.rollback()

# Verify new students were inserted
print("\nVerifying inserted students...")
cursor.execute("SELECT COUNT(*) as count FROM students WHERE Email LIKE '%.test@example.com'")
result = cursor.fetchone()
print(f"✓ Total test students in database: {result['count']}\n")

cursor.close()
conn.close()
