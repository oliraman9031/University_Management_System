import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

conn = pymysql.connect(host='localhost', port=3306, user='root', password=DB_PASSWORD, database='university_management_system', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

try:
    # Create the missing student_event_participation table
    print("Creating student_event_participation table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_event_participation (
        Student_ID INT NOT NULL,
        Event_ID INT NOT NULL,
        Participation_Date DATE DEFAULT (CURRENT_DATE),
        Role ENUM('Participant', 'Organizer', 'Volunteer') DEFAULT 'Participant',
        Result VARCHAR(50),
        PRIMARY KEY (Student_ID, Event_ID),
        FOREIGN KEY (Student_ID) REFERENCES students(Student_ID)
            ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (Event_ID) REFERENCES events(Event_ID)
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)
    conn.commit()
    print("✓ student_event_participation table created successfully\n")

    # Insert student_event_participation data
    print("Inserting student_event_participation data...")
    cursor.execute("""
    INSERT IGNORE INTO student_event_participation (Student_ID, Event_ID, Role, Result) VALUES
        (1, 1, 'Participant', 'Winner'),
        (2, 1, 'Participant', NULL),
        (1, 2, 'Organizer', NULL),
        (3, 3, 'Participant', 'Runner-up'),
        (4, 4, 'Volunteer', NULL);
    """)
    conn.commit()
    print("✓ student_event_participation data inserted successfully\n")

    # Check fees data
    print("Checking fees table...")
    cursor.execute("SELECT COUNT(*) as count FROM fees")
    result = cursor.fetchone()
    fees_count = result['count']
    
    if fees_count == 0:
        print("fees table is empty, inserting data...")
        cursor.execute("""
        INSERT IGNORE INTO fees (Student_ID, Exam_ID, Course_ID, Amount, Issued_Date, Type, Payment_Date, Status, Payment_ID) VALUES
            (1, 1, 'UCS6789', 500.0, '2026-03-01', 'Exam Fee', '2026-03-05', 'Paid', 'PAY001'),
            (1, 2, 'UCS3456', 500.0, '2026-03-01', 'Exam Fee', NULL, 'Pending', NULL),
            (2, 3, 'UMA6789', 300.0, '2026-03-01', 'Exam Fee', '2026-03-10', 'Paid', 'PAY002'),
            (3, 4, 'UCS2345', 600.0, '2026-03-01', 'Exam Fee', NULL, 'Pending', NULL),
            (4, 5, 'UPH7890', 400.0, '2026-03-01', 'Exam Fee', '2026-03-15', 'Paid', 'PAY003'),
            (5, NULL, 'UCB1234', 1200.0, '2045-01-01', 'Course Registration', NULL, 'Pending', NULL),
            (6, NULL, 'UTA5678', 1500.0, '2046-01-01', 'Registration Fees', NULL, 'Pending', NULL);
        """)
        conn.commit()
        print("✓ fees data inserted successfully\n")
    else:
        print(f"✓ fees table already has {fees_count} records\n")

except pymysql.Error as err:
    print(f"Error: {err}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()

print("\nDone! Running verification...\n")
