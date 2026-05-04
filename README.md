# University Management System (UMS)

A comprehensive web-based system designed to streamline and automate academic and administrative processes within a university, providing distinct, role-based interfaces for students, faculty, and administrators.

## Table of Contents

1.  [Introduction](#introduction)
2.  [Features](#features)
3.  [Technologies Used](#technologies-used)
4.  [System Architecture](#system-architecture)
5.  [Database Design](#database-design)
    *   [ER Diagram](#er-diagram)
    *   [Relational Schema (Table Definitions)](#relational-schema-table-definitions)
    *   [Relationships & Participation](#relationships--participation)
    *   [Database Logic (Triggers & Procedures)](#database-logic-triggers--procedures)
6.  [Setup and Installation](#setup-and-installation)
7.  [Usage](#usage)
8.  [Key Functionality & Modules](#key-functionality--modules)
9.  [Testing (Brief Overview)](#testing-brief-overview)
10. [Future Work & Enhancements](#future-work--enhancements)
11. [References](#references)
12. [About the Author](#about-the-author)


## 1. Introduction

Universities and educational institutions manage a vast amount of data and complex processes daily. Traditional manual methods are often inefficient, error-prone, and lead to difficulties in information retrieval and coordination.

This project, the University Management System (UMS), addresses these challenges by providing a centralized, automated, role-based, and secure platform for managing student records, course enrollments, faculty details, exam schedules, fee payments, and result processing.

**Objectives:**

*   Develop a centralized database system for efficient data management.
*   Automate core university processes (registration, enrollment, exams, fees, results).
*   Enhance data security through distinct role-based access.
*   Minimize manual errors and data redundancy with a well-structured relational schema and constraints.
*   Provide intuitive user interfaces for Admin, Faculty, and Students.
*   Create a scalable and maintainable system architecture.
*   Implement automated email notifications for critical events.

## 2. Features

The UMS provides the following core functionalities:

*   **Student Management:**
    *   Student registration and admin approval/rejection.
    *   Viewing and updating student profiles.
    *   Course enrollment and unenrollment.
    *   Viewing personalized dashboards (exams, results, fees).
    *   Simulated fee payment.
*   **Faculty Management:**
    *   Faculty registration and admin approval/rejection.
    *   Viewing and updating faculty profiles.
    *   Managing assigned courses and viewing enrolled students.
    *   Managing exams (add, update, delete, schedule).
    *   Evaluating and publishing exam results (mark entry, grading, locking).
*   **Admin Management:**
    *   CRUD operations for Students, Faculty, Courses, Departments, Exams, Fees, and Results.
    *   Managing user statuses (Student: Pending, Enrolled, Graduated, Restricted; Faculty: Pending, Active).
    *   Appointing Heads of Departments (HODs).
    *   Managing other Admin accounts (primary admin only).
    *   Filtering and sorting data in administrative tables.
    *   Viewing system audit logs.
    *   Database initialization scripts.
*   **Course Management:**
    *   Admin creation, modification, and deletion of courses.
    *   Managing course details (ID, name, semester, credits, price).
*   **Examination Management:**
    *   Faculty scheduling of exams (type, date, duration, venue).
    *   Admin overview and management of exams.
    *   Storing and managing exam results.
*   **Fee Management:**
    *   Generating fee records based on registration, enrollment, and exams.
    *   Admin management of fee records (view, update, delete).
    *   Tracking fee payment status (Pending/Paid).
*   **User Authentication & Authorization:**
    *   Secure login for Admin, Faculty, and Students using official university email.
    *   Role-based access control.
*   **Email Notifications:**
    *   Automated emails for registration approval/rejection, credential delivery, and account status changes.

**Limitations (Out of Scope for this Project Phase):**

*   Attendance Tracking, Hostel Management, Library Management modules.
*   Integration with external learning platforms (Moodle, Blackboard, etc.).
*   Advanced reporting, analytics, and data visualization features.
*   Real-time payment gateway integration (payments are simulated).
*   SMS notifications.

## 3. Technologies Used

*   **Backend:** Flask (Python Framework), PyMySQL (Database Connector), Flask-Mail (Email Handling), python-dotenv (Environment Variables)
*   **Frontend:** HTML5, CSS3, JavaScript, Jinja2 (Templating Engine)
*   **Database:** MySQL
*   **Deployment:** Render (Cloud Platform), Aiven (Database Hosting)
*   **Core Libraries:** `datetime`, `re`, `ast`, `threading` (Python)

## 4. System Architecture

The University Management System follows a standard **3-Tier Web Application Architecture**:

1.  **Presentation Tier (Client-Side):**
    *   Handles the user interface (HTML pages).
    *   Styled using CSS (`static/css/`).
    *   Basic client-side interactions managed by JavaScript (`static/scripts/`).
    *   Dynamic content rendering via Jinja2 templates (`templates/*.html`).
    *   Accessed via web browsers.

2.  **Application Tier (Server-Side):**
    *   Implemented using Flask (`main.py`).
    *   Processes HTTP requests and manages application logic (routing, form handling, validation, grading logic).
    *   Manages user sessions.
    *   Interacts with the database via PyMySQL.
    *   Handles email notifications via Flask-Mail.

3.  **Data Tier (Database):**
    *   Stores all persistent data in a MySQL database hosted on Aiven cloud.
    *   The schema is defined in `database_prerequisite.py`.
    *   Data integrity is enforced through database constraints (PK, FK, UNIQUE, NOT NULL, ENUM, CHECK, ON DELETE).
    *   Includes custom database logic like triggers and stored procedures.

## 5. Database Design

The database is structured to manage the various entities and their relationships within the university system.

### ER Diagram

A conceptual Entity-Relationship (ER) Diagram was designed to model the entities (Students, Faculty, Courses, Exams, Fees, Department, Admin) and their relationships.

You can view the ER Diagram [here](static/images/ER.jpg).

### Relational Schema (Table Definitions)

The database consists of the following tables with their primary attributes and key constraints:

*   **`admin`**:
    `Admin_ID` (PK, AUTO_INCREMENT), `User_Name`, `Email` (UNIQUE), `Password`
*   **`students`**:
    `Student_ID` (PK, AUTO_INCREMENT), `First_Name`, `Middle_Name`, `Last_Name`, `Street`, `District`, `State` (DEFAULT 'Nepal'), `Country`, `Gender` (ENUM), `Date_of_Birth`, `Email` (UNIQUE, CHECK), `College_Email` (UNIQUE, CHECK), `Password` (CHECK), `Enrollment_Year`, `Graduation_Year` (DEFAULT), `Status` (ENUM, DEFAULT 'Pending')
*   **`student_phone_no`**:
    `Student_ID` (PK, FK), `Phone` (PK). `FK_Student` references `students(Student_ID)` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`faculty`**:
    `Faculty_ID` (PK, AUTO_INCREMENT), `First_Name`, `Middle_Name`, `Last_Name`, `Date_of_Joining` (DEFAULT CURRENT_TIMESTAMP), `Designation`, `Mail` (Personal), `Official_Mail` (UNIQUE), `Password`, `Course_ID` (FK, SET NULL), `Department_ID` (FK), `Status` (ENUM, DEFAULT 'Pending'). `FK_Course` references `courses(Course_ID)` ON DELETE SET NULL ON UPDATE CASCADE. `FK_Department` references `department(Department_ID)` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`faculty_phone_no`**:
    `Faculty_ID` (PK, FK), `Phone` (PK). `FK_Faculty_Phone` references `faculty(Faculty_ID)` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`department`**:
    `Department_ID` (PK), `Department_Name` (UNIQUE), `Head_of_Department` (FK, SET NULL). `FK_Head_of_Department` references `faculty(Faculty_ID)` ON DELETE SET NULL ON UPDATE CASCADE.
*   **`courses`**:
    `Course_ID` (PK), `Course_Name` (UNIQUE), `Semester` (ENUM), `Credits`, `Price` (DEFAULT 0)
*   **`enrollment`**:
    `Student_ID` (PK, FK), `Course_ID` (PK, FK), `Enrolled_IN` (DEFAULT CURRENT_DATE). FKs reference `students` and `courses` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`exams`**:
    `Exam_ID` (PK, AUTO_INCREMENT), `Course_ID` (FK), `Exam_Date`, `Exam_Duration`, `Exam_Type` (ENUM), `Venue`, `Status` (ENUM). `UNIQUE` constraint on (`Course_ID`, `Exam_Type`). FK references `courses` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`takes_exams`**:
    `Student_ID` (PK, FK), `Exam_ID` (PK, FK), `Status` (ENUM, DEFAULT 'Unevaluated'). FKs reference `students` and `exams` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`results`**:
    `Result_ID` (PK, AUTO_INCREMENT), `Exam_ID` (FK), `Student_ID` (FK), `Course_ID` (FK), `Marks_Obtained`, `Grade` (ENUM), `Status` (ENUM, DEFAULT 'Unevaluated'). `UNIQUE` constraint on (`Exam_ID`, `Student_ID`, `Course_ID`). FKs reference `exams`, `students`, and `courses` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`fees`**:
    `Fee_ID` (PK, AUTO_INCREMENT), `Student_ID` (FK), `Exam_ID` (FK), `Course_ID` (FK), `Amount`, `Issued_Date` (DEFAULT CURRENT_DATE), `Type` (ENUM), `Payment_Date`, `Status` (ENUM, DEFAULT 'Pending'), `Payment_ID`. FKs reference `students`, `exams`, and `courses` ON DELETE CASCADE ON UPDATE CASCADE.
*   **`audit_log`**:
    `Audit_ID` (PK, AUTO_INCREMENT), `Event_Type` (ENUM), `Table_Name`, `Event_Time` (DEFAULT CURRENT_TIMESTAMP).

### Relationships & Participation

The key relationships and entity participation levels are designed for data integrity and business logic:

*   **Students and Courses (N:M):** Resolved by the `enrollment` table. Both entities participate partially (a student might not be enrolled, a course might have no students).
*   **Faculty and Department (1:N):** `faculty` table includes `Department_ID` FK. Faculty participates totally (must belong to a dept), Department participates partially (can exist without faculty).
*   **Faculty and Course (1:N):** `faculty` table includes `Course_ID` FK. Faculty participates totally (must teach a course), Course participates partially (can exist without a faculty assigned in the faculty table, but faculty teaches courses via assignment). *Note: The schema allows Faculty to have `Course_ID` as NULL.*
*   **Courses and Exams (1:N):** `exams` table includes `Course_ID` FK. Exams participate totally (must be for a course), Courses participate partially (may not have associated exams).
*   **Courses and Results (1:N):** `results` table includes `Course_ID` FK. Results participate totally, Courses participate partially.
*   **Students and Exams (N:M):** Resolved by the `takes_exams` table. Students participate partially (may not take all exams), Exams participate totally (must be taken by at least one student).
*   **Students and Results (1:N):** `results` table includes `Student_ID` FK. Results participate totally, Students participate partially (may not have results yet).
*   **Students and Fees (1:N):** `fees` table includes `Student_ID` FK. Fees participate totally (must be linked to a student), Students participate partially (may not have fees issued yet).
*   **Courses, Exams, and Fees (1:1 per Fee entry):** `fees` table includes `Course_ID` and `Exam_ID` FKs (both nullable). A fee entry can be related to a course, an exam, both, or neither (e.g., registration fee). Fees participate totally in *being linked to a student*, but partially regarding Course/Exam links.
*   **Admin Management (Implicit N:M / Total):** Admin entity manages all other entities. This management is handled by application logic; no explicit relationship tables (`manage_students`, etc., as seen in `queries.txt`) are implemented in the final database schema (`database_prerequisite.py`). Admin and the managed entities participate totally in the "management" concept from the application's perspective.

### Database Logic (Triggers & Procedures)

*   **Audit Triggers:** `AFTER INSERT`, `AFTER UPDATE`, and `AFTER DELETE` triggers are created on all tables (except `audit_log` itself) to log data modification events in the `audit_log` table.
*   **Stored Procedure (`insert_student`):** A stored procedure is defined to handle the insertion of new student records within a transaction, including error handling for SQLEXCEPTION.

## 6. Setup and Installation

To set up and run the project locally, follow these steps:

1.  **Prerequisites:**
    *   Python 3.6+
    *   pip (Python package installer)
    *   MySQL Server (version compatible with PyMySQL, e.g., 5.7+)
    *   Ensure you have privileges to create databases, tables, users, triggers, and procedures on your MySQL instance.

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/ramanoli-1309/University-Management-System.git
    cd University-Management-System
    ```

3.  **Create a Virtual Environment:**
    It's recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv .venv
    ```

4.  **Activate the Virtual Environment:**
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```

5.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt # Assuming a requirements.txt file exists listing Flask, PyMySQL, Flask-Mail, python-dotenv
    # If no requirements.txt, install manually:
    # pip install Flask PyMySQL Flask-Mail python-dotenv
    ```

6.  **Configure Database and Email Credentials:**
    Create a `.env` file in the root directory of the project with the following variables. **Replace the placeholder values with your actual database and email server details.**

    ```dotenv
    # Database Configuration
    DB_HOST=localhost      # Or your Aiven host
    DB_PORT=3306           # Or your Aiven port (usually different)
    DB_USER=your_mysql_user
    DB_PASSWORD=your_mysql_password
    DATABASE_NAME=university_management_system # Or your chosen database name
    TIMEOUT=10             # Connection timeout in seconds

    # Email Configuration (for Flask-Mail)
    MAIL_SERVER=smtp.your_email_provider.com # e.g., smtp.gmail.com
    MAIL_PORT=587          # Or your provider's SMTP port (e.g., 465 for SSL, 587 for TLS)
    MAIL_USE_TLS=True      # Set to True for TLS (recommended for 587)
    MAIL_USE_SSL=False     # Set to True for SSL (recommended for 465) - Only one should be True
    MAIL_USERNAME=your_email@example.com # Sender email address
    MAIL_PASSWORD=your_email_password    # Sender email password (use app passwords for Gmail etc.)
    MAIL_DEFAULT_SENDER=University Management System <your_email@example.com> # Display name and sender email
    ```
    **Security Note:** Storing credentials directly in `.env` is suitable for development. For production, consider more secure secrets management.

7.  **Set up the Database:**
    Run the `database_prerequisite.py` script to create the database, tables, constraints, triggers, procedures, and insert initial dummy data for courses and departments.

    ```bash
    python database_prerequisite.py
    ```
    This script will:
    *   Attempt to drop the database (if it exists).
    *   Create the database.
    *   Connect to the newly created database.
    *   Create all necessary tables with primary and foreign keys, unique constraints, check constraints, and enums.
    *   Add the `FK_Head_of_Department` constraint.
    *   Create the `audit_log` table and audit triggers on other tables.
    *   Create the `insert_student` stored procedure.
    *   Insert initial data into `courses` and `department` tables.
    *   Demonstrate the `insert_student` procedure with sample student data.

## 7. Usage

1.  **Run the Flask Application:**
    Make sure your virtual environment is active.
    ```bash
    python main.py
    ```
    The application will start and usually run on `http://127.0.0.1:8000/`.

2.  **Access the Application:**
    Open your web browser and go to the address provided by Flask (e.g., `http://127.0.0.1:8000/`).

3.  **Login:**
    *   Use the "Sign In" link.
    *   **Default Admin Credentials:**
        *   Email: `admin@thapar.edu`
        *   Password: `admin@tiet`
        *   User Type: `Admin`
    *   For other roles (Student, Faculty), you need to register first via the "Sign Up" link and have an admin approve your application (for Students/Faculty). The application will generate college emails and initial passwords upon approval.

4.  **Explore Features:**
    Navigate through the application based on your logged-in role (Admin Dashboard, Student Dashboard, Faculty Dashboard) to access the implemented functionalities.

## 8. Key Functionality & Modules

*   **`main.py`**: The main Flask application file. Handles routing, session management, database interactions, form processing, validation, and email sending. Contains helper functions like `generateIDPass` (generates college email and password), `querymaker` (formats SQL queries for display), and `calculate_percentile` (used in grading).
*   **`database_prerequisite.py`**: Script for database setup (DDL for tables, constraints, triggers, procedures) and initial data insertion.
*   **Templates (`templates/`)**: HTML files using Jinja2 for dynamic rendering of web pages for different roles and functionalities.
*   **Static Files (`static/`)**: Contains CSS (`static/css/`) for styling and JavaScript (`static/scripts/`) for client-side scripting. Includes the ER Diagram image (`static/images/ER.jpg`) and documentation files (`static/files/`).
*   **Credentials (`.env`)**: External file for storing sensitive database and email configuration (not committed to repository for security).

## 9. Testing (Brief Overview)

Testing was primarily conducted through manual testing of the deployed application. This included:

*   **Role-Based Access:** Verifying correct access and visibility for Admin, Faculty, and Student roles.
*   **Core Workflows:** Testing end-to-end processes like student registration -> admin approval -> student login -> course enrollment -> fee check; faculty registration -> admin approval -> faculty login -> exam scheduling -> result evaluation -> result locking.
*   **Form Submission & Validation:** Testing forms with valid and invalid inputs to check backend validation and error handling.
*   **Data Integrity:** Attempting actions that should be prevented by database constraints (e.g., duplicate IDs, invalid foreign keys, deleting referenced data with CASCADE rules).
*   **Boundary Conditions:** Testing specific scenarios like first user registration, empty lists, zero marks in evaluation.
*   **Browser Compatibility (Basic):** Checking functionality in major modern browsers.
*   **Email Notifications:** Verifying receipt of automated emails.
*   **Filtering/Sorting:** Testing implemented filtering and sorting features in admin views.

Automated testing (Unit, Integration, E2E) and formal security/load testing were not part of this project phase.

## 10. Future Work & Enhancements

Potential areas for future development include:

*   Attendance Tracking Module.
*   Library and Hostel Management Modules.
*   Advanced Reporting and Analytics features with downloadable reports.
*   Integration with a real-time payment gateway.
*   Timetable Management functionality.
*   UI/UX refinement and improved responsiveness.
*   Development of a RESTful API for external integration or mobile app support.
*   Enhanced Security (password hashing, CSRF protection, input sanitization).
*   Implementation of Automated Testing.
*   Database Performance Tuning and Caching.

## 11. References

The following resources were used during the development of this project:

*   Flask Documentation: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
*   PyMySQL Documentation: [https://pymysql.readthedocs.io/](https://pymysql.readthedocs.io/)
*   MySQL Documentation: [https://dev.mysql.com/doc/](https://dev.mysql.com/doc/)
*   Jinja2 Documentation: [https://jinja.palletsprojects.com/](https://jinja.palletsprojects.com/)
*   Flask-Mail Documentation: [https://pythonhosted.org/Flask-Mail/](https://pythonhosted.org/Flask-Mail/)
*   HTML/CSS/JavaScript References: MDN Web Docs ([https://developer.mozilla.org/](https://developer.mozilla.org/))
*   Python `datetime` Module: [https://docs.python.org/3/library/datetime.html](https://docs.python.org/3/library/datetime.html)
*   Python `re` Module: [https://docs.python.org/3/library/re.html](https://docs.python.org/3/library/re.html)
*   Aiven (Database Hosting): [https://aiven.io/](https://aiven.io/)
*   Render (Deployment Platform): [https://render.com/](https://render.com/)
*   GitHub Repository: [https://github.com/miyasajid19/University-Management-System.git](https://github.com/ramanoli-1309/University-Management-System.git)
<!-- *   Live Application URL: [https://university-management-system-xvfp.onrender.com/](https://university-management-system-xvfp.onrender.com/) -->

Additionally, various online tutorials, articles, videos, and forums were consulted for specific implementation details and troubleshooting.

## 12. About the Author

This project was developed by **Raman Oli**, a student pursuing Computer Science and Engineering at Thapar Institute of Engineering and Technology, Patiala, Punjab, India.

*   Contact: [oli.raman9031@gmail.com](mailto:oli.raman9031@gmail.com)
*   GitHub: [https://github.com/oliraman9031](https://github.com/oliraman9031)

  ## 13. LIVE AT: https://university-management-system-1-ahhk.onrender.com/


