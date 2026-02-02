import pymysql
import pymysql.cursors
import sys
import datetime # Import datetime for date and datetime objects
import os
from dotenv import load_dotenv
# --- Database Connection Configuration ---
# WARNING: Hardcoded password is a security risk.
# In a production environment, use environment variables or a secrets management system.
# Load environment variables from a .env file
load_dotenv()

# Using a name without spaces is generally better practice for database names
# DATABASE_NAME = os.getenv("DATABASE_NAME", "ums")
DATABASE_NAME = os.getenv("DATABASE_NAME", "university_management_system") # Changed name for better practice

DB_HOST = os.getenv("DB_HOST", "localhost")  # Default to localhost if not set
DB_PORT = int(os.getenv("DB_PORT", 3306))  # Default to 3306 if not set
DB_USER = os.getenv("DB_USER", "root")  # Default to root if not set
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # Default to empty password if not set
TIMEOUT = int(os.getenv("TIMEOUT", 10))  # Default to 10 seconds if not set
SSL_MODE = os.getenv("SSL_MODE", "REQUIRED") # Default to REQUIRED if not set - note: Aiven often requires TLS/SSL

def get_connection(db_name=None):
    """
    Establishes a database connection with configured parameters.

    Args:
        db_name (str, optional): The name of the database to connect to.
                                 If None, connects without specifying a database.

    Returns:
        pymysql.connections.Connection: A database connection object, or None if connection fails.
    """
    try:
        conn_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "charset": "utf8mb4",
            "connect_timeout": TIMEOUT,
            "read_timeout": TIMEOUT,
            "write_timeout": TIMEOUT,
            "cursorclass": pymysql.cursors.DictCursor,  # Use DictCursor for easy access to results
            # Add SSL configuration if required by your provider (Aiven likely does)
            # You might need certificate files depending on the SSL_MODE
            # "ssl": {'ssl_mode': SSL_MODE} # Requires specific configuration, check Aiven docs
        }
        if db_name:
            conn_params["db"] = db_name

        print(f"Connecting to database '{db_name or 'default'}' on {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(**conn_params)
        print("Connection successful.") # Added success message back for clarity
        return connection
    except pymysql.Error as err:
        print(f"Database connection error: {err}", file=sys.stderr)
        return None

def drop_database():
    """Drops the specified database if it exists."""
    connection = None
    cursor = None
    try:
        # Connect without specifying a database initially to run DROP DATABASE
        connection = get_connection()
        if connection is None:
            return # Connection failed, already printed error

        cursor = connection.cursor()
        # Use backticks around the database name in SQL
        print(f"\nDropping database `{DATABASE_NAME}` if it exists...")
        cursor.execute(f"DROP DATABASE IF EXISTS `{DATABASE_NAME}`;")
        connection.commit()
        print(f"Database `{DATABASE_NAME}` dropped successfully.")
    except pymysql.Error as err:
        print(f"Error dropping database: {err}", file=sys.stderr)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_database():
    """Creates the database and the initial admin table."""
    connection = None
    cursor = None
    try:
        # Connect without specifying a database initially to run CREATE DATABASE
        connection = get_connection()
        if connection is None:
            return # Connection failed

        cursor = connection.cursor()
        # Use backticks around the database name in SQL
        print(f"\nCreating database `{DATABASE_NAME}` if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}`;")
        print(f"Database `{DATABASE_NAME}` created or already exists.")

        # Close the initial connection, and re-connect to the specific database
        # This step is necessary because you can't generally USE a database within the same connection
        # where you just created it if you connected without a default DB.
        if cursor: cursor.close()
        if connection: connection.close()

        # Now connect to the specific database to create tables within it
        connection = get_connection(db_name=DATABASE_NAME)
        if connection is None:
             # Connection to specific DB failed, exit setup
            print("Could not connect to the newly created database. Exiting.", file=sys.stderr)
            sys.exit(1)

        cursor = connection.cursor()

        print("Creating admin table if it doesn't exist...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            Admin_ID INT PRIMARY KEY AUTO_INCREMENT,
            User_Name VARCHAR(255) NOT NULL,
            Email VARCHAR(255) NOT NULL UNIQUE,
            Password VARCHAR(255) NOT NULL
        );
        """)
        print("Admin table created or already exists.")

        # Check if admin user already exists before inserting the default one
        cursor.execute("SELECT COUNT(*) FROM admin WHERE Email = 'admin@thapar.edu'")
        count = cursor.fetchone()['COUNT(*)']

        if count == 0:
            print("Inserting initial default admin data...")
            cursor.execute("""
            INSERT INTO admin (User_Name, Email, Password) VALUES
            ('admin', 'admin@thapar.edu', 'admin@tiet');
            """)
            print("Initial default admin data inserted.")
            connection.commit() # Commit the insert if it happened
        else:
            print("Default admin user 'admin@thapar.edu' already exists, skipping insertion.")

    except pymysql.Error as err:
        print(f"Error creating database or admin table: {err}", file=sys.stderr)
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_tables():
    """Creates all necessary tables in the database."""
    connection = None
    cursor = None
    try:
        # Connect directly to the database
        connection = get_connection(db_name=DATABASE_NAME)
        if connection is None:
            return # Connection failed

        cursor = connection.cursor()
        print(f"\nCreating tables in database `{DATABASE_NAME}`...")

        tables_sql = [
            ("admin", """
                CREATE TABLE IF NOT EXISTS admin (
                    Admin_ID INT PRIMARY KEY AUTO_INCREMENT,
                    User_Name VARCHAR(255) NOT NULL,
                    Email VARCHAR(255) NOT NULL UNIQUE,
                    Password VARCHAR(255) NOT NULL
                );
            """),
            ("students", """
                CREATE TABLE IF NOT EXISTS students (
                    Student_ID INT AUTO_INCREMENT PRIMARY KEY,
                    First_Name VARCHAR(255) NOT NULL,
                    Middle_Name VARCHAR(255),
                    Last_Name VARCHAR(255) NOT NULL,
                    Street VARCHAR(255) NOT NULL,
                    District VARCHAR(255) NOT NULL,
                    State VARCHAR(255) NOT NULL DEFAULT 'Nepal',
                    Country VARCHAR(255) NOT NULL,
                    Gender ENUM('Male', 'Female', 'Others') NOT NULL,
                    Date_of_Birth DATE NOT NULL,
                    Email VARCHAR(255) UNIQUE NOT NULL CHECK (Email LIKE '%@%'),
                    College_Email VARCHAR(255) UNIQUE NOT NULL CHECK (College_Email LIKE '%@thapar.edu'),
                    Password VARCHAR(255) NOT NULL CHECK (LENGTH(Password) >= 8),
                    Enrollment_Year YEAR NOT NULL,
                    Graduation_Year YEAR NOT NULL DEFAULT (Enrollment_Year + 4),
                    Status ENUM('Pending', 'Enrolled', 'Graduated', 'Restricted') NOT NULL DEFAULT 'Pending'
                );
            """),
            ("courses", """
                CREATE TABLE IF NOT EXISTS courses (
                    Course_ID VARCHAR(13) PRIMARY KEY,
                    Course_Name VARCHAR(55) NOT NULL UNIQUE,
                    Semester ENUM('1', '2', '3', '4', '5', '6', '7', '8') NOT NULL,
                    Credits FLOAT NOT NULL,
                    Price FLOAT NOT NULL DEFAULT 0
                );
            """),
             ("department", """
                CREATE TABLE IF NOT EXISTS department (
                    Department_ID VARCHAR(7) PRIMARY KEY,
                    Department_Name VARCHAR(255) NOT NULL UNIQUE,
                    Head_of_Department INT -- This FK will be added later as it references 'faculty'
                );
            """),
            ("faculty", """
                CREATE TABLE IF NOT EXISTS faculty (
                    Faculty_ID INT PRIMARY KEY AUTO_INCREMENT,
                    First_Name VARCHAR(255) NOT NULL,
                    Middle_Name VARCHAR(255),
                    Last_Name VARCHAR(255) NOT NULL,
                    Date_of_Joining DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    Designation VARCHAR(32) NOT NULL,
                    Mail VARCHAR(255) NOT NULL, # Assuming this is a personal mail
                    Official_Mail VARCHAR(255) UNIQUE NOT NULL, # This should be unique like student email
                    Password VARCHAR(255) NOT NULL,
                    Course_ID VARCHAR(13), # Changed to SET NULL
                    Department_ID VARCHAR(7) NOT NULL,
                    Status ENUM('Pending', 'Active') DEFAULT 'Pending',
                    FOREIGN KEY (Course_ID) REFERENCES courses(Course_ID) ON DELETE SET NULL ON UPDATE CASCADE, # Changed to SET NULL
                    FOREIGN KEY (Department_ID) REFERENCES department(Department_ID) ON DELETE CASCADE ON UPDATE CASCADE
                );
            """),
            ("student_phone_no", """
                CREATE TABLE IF NOT EXISTS student_phone_no (
                    Student_ID INT NOT NULL,
                    Phone VARCHAR(14) NOT NULL,
                    CONSTRAINT PRIMARY KEY (Student_ID, Phone),
                    CONSTRAINT FK_Student FOREIGN KEY (Student_ID) REFERENCES students(Student_ID) ON DELETE CASCADE ON UPDATE CASCADE
                );
            """),
            ("faculty_phone_no", """
                CREATE TABLE IF NOT EXISTS faculty_phone_no (
                    Faculty_ID INT NOT NULL,
                    Phone VARCHAR(14) NOT NULL,
                    CONSTRAINT PRIMARY KEY (Faculty_ID, Phone),
                    CONSTRAINT FK_Faculty_Phone FOREIGN KEY (Faculty_ID) REFERENCES faculty(Faculty_ID) ON DELETE CASCADE ON UPDATE CASCADE
                );
            """),
            ("enrollment", """
                CREATE TABLE IF NOT EXISTS enrollment (
                    Student_ID INT NOT NULL,
                    Course_ID VARCHAR(13) NOT NULL,
                    Enrolled_IN DATE DEFAULT (CURRENT_DATE), -- Added default date
                    FOREIGN KEY (Student_ID) REFERENCES students(Student_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (Course_ID) REFERENCES courses(Course_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    PRIMARY KEY (Student_ID, Course_ID)
                );
            """),
            ("exams", """
                CREATE TABLE IF NOT EXISTS exams (
                    Exam_ID INT PRIMARY KEY AUTO_INCREMENT,
                    Course_ID VARCHAR(13),
                    Exam_Date DATE NOT NULL,
                    Exam_Duration FLOAT NOT NULL,
                    Exam_Type ENUM ('Mid Semester Test', 'End Semester Test', 'Quiz-1', 'Quiz-2', 'Lab Evaluation I', 'Lab Evaluation II', 'Others') NOT NULL,
                    Venue VARCHAR(61) NOT NULL,
                    Status ENUM('Unevaluated','Evaluated','Locked') NOT NULL,
                    CONSTRAINT UNIQUE(Course_ID, Exam_Type), # Ensure unique exam type per course
                    FOREIGN KEY (Course_ID) REFERENCES courses(Course_ID) ON DELETE CASCADE ON UPDATE CASCADE
                );
            """),
             ("fees", """
                CREATE TABLE IF NOT EXISTS fees (
                    Fee_ID INT PRIMARY KEY AUTO_INCREMENT,
                    Student_ID INT,
                    Exam_ID INT, -- Fee could be exam related
                    Course_ID VARCHAR(13), -- Fee could be course registration related
                    Amount FLOAT NOT NULL,
                    Issued_Date DATE NOT NULL DEFAULT (CURRENT_DATE),
                    Type ENUM('Registration Fees','Course Registration','Exam Fee','Other') NOT NULL, # Added 'Other'
                    Payment_Date DATE,
                    Status ENUM('Pending','Paid') DEFAULT 'Pending',
                    Payment_ID VARCHAR(13), -- Might need to be UNIQUE depending on requirements
                    FOREIGN KEY (Student_ID) REFERENCES students(Student_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (Exam_ID) REFERENCES exams(Exam_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (Course_ID) REFERENCES courses(Course_ID) ON DELETE CASCADE ON UPDATE CASCADE

                );
            """),
            ("takes_exams", """
                CREATE TABLE IF NOT EXISTS takes_exams (
                    Student_ID INT NOT NULL,
                    Exam_ID INT NOT NULL,
                    Status ENUM('Unevaluated','Evaluated','Locked') DEFAULT 'Unevaluated',
                    FOREIGN KEY (Student_ID) REFERENCES students(Student_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (Exam_ID) REFERENCES exams(Exam_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    PRIMARY KEY (Student_ID, Exam_ID)
                );
            """),
             ("results", """
                CREATE TABLE IF NOT EXISTS results (
                    Result_ID INT PRIMARY KEY AUTO_INCREMENT,
                    Exam_ID INT NOT NULL,
                    Student_ID INT NOT NULL,
                    Course_ID VARCHAR(13) NOT NULL, -- Result is for a specific exam *in* a specific course
                    Marks_Obtained FLOAT,
                    Grade ENUM('A', 'A-', 'B', 'B-', 'C', 'C-', 'D', 'E', 'F'), -- Added F for failing
                    Status ENUM('Unevaluated','Evaluated','Locked') DEFAULT 'Unevaluated',
                    FOREIGN KEY (Exam_ID) REFERENCES exams(Exam_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (Student_ID) REFERENCES students(Student_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (Course_ID) REFERENCES courses(Course_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                    -- Ensure the student is enrolled in the course related to the exam? This is complex and often handled by application logic.
                    -- For now, just ensure unique entry per exam/student/course combo.
                    UNIQUE (Exam_ID, Student_ID, Course_ID)
                );
            """),
            ("audit_log", """
                CREATE TABLE IF NOT EXISTS audit_log (
                    Audit_ID INT AUTO_INCREMENT PRIMARY KEY,
                    Event_Type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
                    Table_Name VARCHAR(255) NOT NULL,
                    Event_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
        ]

        # Execute table creation
        for table_name, sql in tables_sql:
            print(f"Creating table '{table_name}' if it doesn't exist...")
            cursor.execute(sql)
            print(f"Table '{table_name}' created or already exists.")

        # Add the foreign key constraint for department.Head_of_Department
        # This must be done after both 'department' and 'faculty' tables exist
        # Use ALTER TABLE IF EXISTS for slightly more robustness if running parts separately
        print("Adding FK constraint FK_Head_of_Department to department table...")
        try:
            # Check if the constraint already exists before adding
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = '{DATABASE_NAME}'
                AND TABLE_NAME = 'department'
                AND CONSTRAINT_NAME = 'FK_Head_of_Department'
                AND CONSTRAINT_TYPE = 'FOREIGN KEY';
            """)
            constraint_exists = cursor.fetchone()['COUNT(*)'] > 0

            if not constraint_exists:
                cursor.execute("""
                ALTER TABLE department
                ADD CONSTRAINT FK_Head_of_Department
                FOREIGN KEY (Head_of_Department) REFERENCES faculty(Faculty_ID)
                ON DELETE SET NULL -- Use SET NULL because the HOD might be removed
                ON UPDATE CASCADE;
                """)
                print("FK constraint for department.Head_of_Department added.")
            else:
                 print("FK constraint for department.Head_of_Department already exists.")

        except pymysql.Error as e:
             # Catch potential errors during ALTER TABLE, though the check above should prevent duplicates
             print(f"Error adding FK constraint to department table: {e}", file=sys.stderr)


        connection.commit() # Commit all table creations and FK additions
        print("\nAll table structures confirmed in the database.")

        # Optional: Show created tables
        print("\nTables currently in the database:")
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        if tables:
            # Exclude audit_log from this list if you prefer
            # tables = [t for t in tables if list(t.values())[0] != 'audit_log']
            for index, table_dict in enumerate(tables):
                # The dictionary key is like 'Tables_in_your_db_name'
                table_name = list(table_dict.values())[0] # Get the value of the first (and only) key
                print(f"{index+1}. {table_name}")
        else:
            print("No tables found in the database.")


    except pymysql.Error as err:
        print(f"Error creating tables or constraints: {err}", file=sys.stderr)
        if connection:
            connection.rollback() # Rollback in case of error
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            

def create_procedure():
    connection = None
    cursor = None
    try:
        connection = get_connection(db_name=DATABASE_NAME)
        if connection is None:
            return  
        cursor = connection.cursor()
        print("\nCreating stored procedure `insert_student` if it doesn't exist...")
        cursor.execute("""
        CREATE PROCEDURE insert_student (
            IN p_First_Name VARCHAR(255),
            IN p_Middle_Name VARCHAR(255),
            IN p_Last_Name VARCHAR(255),
            IN p_Street VARCHAR(255),
            IN p_District VARCHAR(255),
            IN p_State VARCHAR(255),
            IN p_Country VARCHAR(255),
            IN p_Gender ENUM('Male', 'Female', 'Others'),
            IN p_Date_of_Birth DATE,
            IN p_Email VARCHAR(255),
            IN p_College_Email VARCHAR(255),
            IN p_Password VARCHAR(255),
            IN p_Enrollment_Year YEAR
        )
        BEGIN
            DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
            BEGIN
                ROLLBACK;
                SELECT 'Error: Unable to insert student. Please check the input data.' AS Error;
            END;

            START TRANSACTION;

            INSERT INTO students (
                First_Name, Middle_Name, Last_Name, Street, District, State,
                Country, Gender, Date_of_Birth, Email, College_Email, Password, Enrollment_Year
            ) VALUES (
                p_First_Name, p_Middle_Name, p_Last_Name, p_Street, p_District, p_State,
                p_Country, p_Gender, p_Date_of_Birth, p_Email, p_College_Email, p_Password, p_Enrollment_Year
            );

            COMMIT;

            SELECT 'Student inserted successfully.' AS Message;
        END;
        """)
        print("Stored procedure `insert_student` created successfully.")
    except pymysql.Error as err:
        print(f"Error creating stored procedure: {err}", file=sys.stderr)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
def demonstrate_procedure(student_data):
    connection = None
    cursor = None
    try:
        connection = get_connection(db_name=DATABASE_NAME)
        if connection is None:
            return  
        cursor = connection.cursor()
        print("\nDemonstrating the use of `insert_student` stored procedure...")
        cursor.callproc('insert_student', (
            student_data['First_Name'], student_data.get('Middle_Name', ''), student_data['Last_Name'],
            student_data['Street'], student_data['District'], student_data['State'],
            student_data['Country'], student_data['Gender'], student_data['Date_of_Birth'],
            student_data['Email'], student_data['College_Email'], student_data['Password'],
            student_data['Enrollment_Year']
        ))
        result = cursor.fetchall()
        for row in result:
            print(row)
        connection.commit()
        print("Procedure executed successfully.")
    except pymysql.Error as err:
        print(f"Error demonstrating procedure: {err}", file=sys.stderr)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
def create_audit_trigger():
    connection = None
    cursor = None
    try:
        connection = get_connection(db_name=DATABASE_NAME)
        if connection is None:
            return  
        cursor = connection.cursor()

        print("\nCreating audit table if it doesn't exist...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            Audit_ID INT AUTO_INCREMENT PRIMARY KEY,
            Event_Type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
            Table_Name VARCHAR(255) NOT NULL,
            Event_Time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Audit table created or already exists.")

        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        excluded_tables = ['audit_log'] # IMPORTANT: Do not trigger on the audit table itself

        for table_dict in tables:
            table_name = list(table_dict.values())[0] # Get the table name

            if table_name in excluded_tables:
                print(f"Skipping trigger creation for '{table_name}' (excluded).")
                continue

            try:
                print(f"Creating AFTER INSERT trigger for table `{table_name}`...")
                cursor.execute(f"""
                CREATE TRIGGER `{table_name}_after_insert`
                AFTER INSERT ON `{table_name}`
                FOR EACH ROW
                INSERT INTO audit_log (Event_Type, Table_Name)
                VALUES ('INSERT', '{table_name}');
                """)
            except pymysql.Error as e:
                 if e.args[0] == 1359: 
                     print(f"AFTER INSERT trigger for `{table_name}` already exists.")
                 else:
                     print(f"Error creating AFTER INSERT trigger for `{table_name}`: {e}", file=sys.stderr)

            try:
                print(f"Creating AFTER UPDATE trigger for table `{table_name}`...")
                cursor.execute(f"""
                CREATE TRIGGER `{table_name}_after_update`
                AFTER UPDATE ON `{table_name}`
                FOR EACH ROW
                INSERT INTO audit_log (Event_Type, Table_Name)
                VALUES ('UPDATE', '{table_name}');
                """)
            except pymysql.Error as e:
                 if e.args[0] == 1359: # Error code 1359 is "Trigger already exists"
                     print(f"AFTER UPDATE trigger for `{table_name}` already exists.")
                 else:
                     print(f"Error creating AFTER UPDATE trigger for `{table_name}`: {e}", file=sys.stderr)


            try:
                print(f"Creating AFTER DELETE trigger for table `{table_name}`...")
                cursor.execute(f"""
                CREATE TRIGGER `{table_name}_after_delete`
                AFTER DELETE ON `{table_name}`
                FOR EACH ROW
                INSERT INTO audit_log (Event_Type, Table_Name)
                VALUES ('DELETE', '{table_name}');
                """)
            except pymysql.Error as e:
                 if e.args[0] == 1359: 
                     print(f"AFTER DELETE trigger for `{table_name}` already exists.")
                 else:
                     print(f"Error creating AFTER DELETE trigger for `{table_name}`: {e}", file=sys.stderr)


        connection.commit()
        print("\nAudit triggers creation process complete.") 
    except pymysql.Error as err:
        print(f"Error during audit trigger setup: {err}", file=sys.stderr)
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def view():
    connection = None
    cursor = None
    try:
        connection = get_connection(db_name=DATABASE_NAME)
        if connection is None:
            return  # Connection failed

        cursor = connection.cursor()
        print(f"\nViewing all content of tables in database `{DATABASE_NAME}`...")

        # Fetch all table names
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        for table_dict in tables:
            table_name = list(table_dict.values())[0]  # Get the table name
            print(f"\n--- Content of table `{table_name}` ---")
            cursor.execute(f"SELECT * FROM `{table_name}`;") # Use backticks for table name
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(row)
            else:
                print(f"Table `{table_name}` is empty.")

    except pymysql.Error as err:
        print(f"Error viewing table content: {err}", file=sys.stderr)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
def insert_initial_data():
    try:
        connection =   get_connection(db_name=DATABASE_NAME)
        cursor = connection.cursor()
        
        # Insert department data first
        cursor.execute("""
        INSERT INTO department (Department_ID, Department_Name, Head_of_Department) VALUES
        ('CSE', 'Computer Science and Engineering', NULL),
        ('ECE', 'Electronics and Communication Engineering', NULL),
        ('ME', 'Mechanical Engineering', NULL),
        ('CE', 'Civil Engineering', NULL),
        ('EE', 'Electrical Engineering', NULL);
        """)

        # Now insert courses data
        cursor.execute("""
        INSERT INTO courses (Course_ID, Course_Name, Semester, Credits, Price) VALUES
        ('UCB1234', 'ADVANCED CHEMISTRY', 1, 4.5, 1200),
        ('UTA5678', 'ADVANCED PROGRAMMING', 1, 4.0, 1500),
        ('UES9101', 'ELECTRICAL ENGINEERING', 1, 4.5, 1300),
        ('UEN2345', 'ENVIRONMENTAL SCIENCE', 1, 3.0, 1100),
        ('UMA6789', 'MATHEMATICS – III', 1, 3.5, 1400),
        ('UES3456', 'ENGINEERING MECHANICS', 1, 2.5, 1000),
        ('UPH7890', 'PHYSICS', 2, 4.5, 1200),
        ('UTA1234', 'DATA STRUCTURES', 2, 4.0, 1500),
        ('UTA5677', 'MANUFACTURING TECHNOLOGY', 2, 3.0, 1300),
        ('UTA9101', 'ENGINEERING GRAPHICS', 2, 4.0, 1400),
        ('UHU2345', 'COMMUNICATION SKILLS', 2, 3.0, 1100),
        ('UMA6790', 'MATHEMATICS – IV', 2, 3.5, 1200),
        ('UCS3456', 'OPERATING SYSTEMS', 3, 4.0, 1500),
        ('UCS7890', 'DISCRETE MATHEMATICS', 3, 3.5, 1300),
        ('UCS123', 'ALGORITHMS', 3, 4.0, 1400),
        ('UCS678', 'COMPUTER ARCHITECTURE', 3, 3.0, 1200),
        ('UMA9101', 'NUMERICAL METHODS', 3, 4.0, 1500),
        ('UCS2345', 'ARTIFICIAL INTELLIGENCE', 4, 4.0, 1600),
        ('UCS6789', 'DATABASE SYSTEMS', 4, 4.0, 1500),
        ('UCS3457', 'SOFTWARE ENGINEERING', 4, 4.0, 1400),
        ('UCS7891', 'NETWORKS', 4, 3.0, 1300),
        ('UMA1234', 'OPTIMIZATION', 4, 4.0, 1200),
        ('UML5678', 'MACHINE LEARNING', 5, 4.0, 1600),
        ('UCS9101', 'PROBABILITY AND STATISTICS', 5, 4.0, 1500),
        ('UCS2346', 'CLOUD COMPUTING', 5, 3.0, 1400),
        ('UCS6780', 'NETWORK PROGRAMMING', 5, 3.0, 1300),
        ('PE1234', 'ELECTIVE-I', 5, 3.0, 1200),
        ('GE5678', 'GENERIC ELECTIVE', 5, 2.0, 1100),
        ('UCS9102', 'THEORY OF COMPUTATION', 6, 3.5, 1500),
        ('UCS2347', 'COMPUTER GRAPHICS', 6, 4.0, 1600),
        ('UCS6791', 'QUANTUM COMPUTING', 6, 4.0, 1500),
        ('PE3456', 'ELECTIVE-II', 6, 3.0, 1400),
        ('PE7890', 'ELECTIVE-III', 6, 3.0, 1300),
        ('UCS1234', 'CAPSTONE PROJECT', 6, 0.0, 1200),
        ('UCS5678', 'COMPILER DESIGN', 7, 4.0, 1600),
        ('UHU9101', 'ENGINEERING ETHICS', 7, 3.0, 1500),
        ('UCS013', 'COGNITIVE COMPUTING', 7, 2.0, 1400),
        ('PE6789', 'ELECTIVE-IV', 7, 3.0, 1300),
        ('UCS345', 'PROJECT SEMESTER', 8, 15.0, 2000),
        ('UCS7892', 'SOCIAL NETWORK ANALYSIS', 8, 3.0, 1500),
        ('UCS432', 'CYBER SECURITY', 8, 4.0, 1600),
        ('UCS786', 'FINAL PROJECT', 8, 8.0, 1800),
        ('UCS9103', 'START-UP SEMESTER', 8, 15.0, 2000);
        """)

        connection.commit()
        print("Initial data inserted successfully.")
    except pymysql.Error as err:
        print(f"Error: {err}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# --- Main Execution ---
if __name__ == "__main__":
    print("--- University Management System Database Setup ---")

    # # Execute the functions in sequence
    # drop_database()
    create_database() # Creates DB and Admin table + default user
    create_tables()   # Creates other tables and FKs
    insert_initial_data() # Uncomment to insert initial data into courses and department tables
    import sys
    os.system('cls' if os.name == 'nt' else 'clear')
    create_audit_trigger() # Creates audit table and triggers (excluding audit_log)
    view() # Show contents, including audit log
    create_procedure() # Create the stored procedure
    # Demonstrate the procedure with sample data
    students = [
    {
        'First_Name': 'Obito',
        'Middle_Name': None,
        'Last_Name': 'Uchiha',
        'Street': 'Hidden Leaf Village',
        'District': 'Konoha',
        'State': 'Land of Fire',
        'Country': 'Japan',
        'Gender': 'Male',
        'Date_of_Birth': '1990-02-10',
        'Email': 'obito.uchiha@example.com',
        'College_Email': 'obito@thapar.edu',
        'Password': 'Mangekyo123',
        'Enrollment_Year': 2010
    },
    {
        'First_Name': 'Rin',
        'Middle_Name': None,
        'Last_Name': 'Nohara',
        'Street': 'Hidden Leaf Village',
        'District': 'Konoha',
        'State': 'Land of Fire',
        'Country': 'Japan',
        'Gender': 'Female',
        'Date_of_Birth': '1992-06-15',
        'Email': 'rin.nohara@example.com',
        'College_Email': 'rin@thapar.edu',
        'Password': 'HealingJutsu456',
        'Enrollment_Year': 2011
    },
    {
        'First_Name': 'Kakashi',
        'Middle_Name': None,
        'Last_Name': 'Hatake',
        'Street': 'Hidden Leaf Village',
        'District': 'Konoha',
        'State': 'Land of Fire',
        'Country': 'Japan',
        'Gender': 'Male',
        'Date_of_Birth': '1989-09-15',
        'Email': 'kakashi.hatake@example.com',
        'College_Email': 'kakashi@thapar.edu',
        'Password': 'Sharingan789',
        'Enrollment_Year': 2009
    },{
        'First_Name': 'Obito',
        'Middle_Name': None,
        'Last_Name': 'Uchiha',
        'Street': 'Hidden Leaf Village',
        'District': 'Konoha',
        'State': 'Land of Fire',
        'Country': 'Japan',
        'Gender': 'Male',
        'Date_of_Birth': '1990-02-10',
        'Email': 'obito.uchiha@example.com',
        'College_Email': 'obito@thapar.edu',
        'Password': 'Mangekyo123',
        'Enrollment_Year': 2010
    }
    ]
    for student in students:
        print(f"\nInserting student: {student['First_Name']} {student['Last_Name']}")
        demonstrate_procedure(student)
    print("\n--- Database Setup Complete ---")
    print(f"Remember to secure your connection details (using .env is better than hardcoding, but ensure .env is secure too).")