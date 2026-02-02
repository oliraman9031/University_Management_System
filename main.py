from flask import Flask, request, render_template, redirect, url_for, session,render_template_string,send_from_directory
import datetime
app = Flask(__name__)
app.secret_key = '1234'
import database_prerequisite  as setup
from flask import Flask
from flask_mail import Mail, Message
import re
import ast
import threading
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)
print("TIMEOUT =", os.getenv("TIMEOUT"))

def send_email(app, to_email, subject, body):
    mail = Mail(app)
    msg = Message(subject, recipients=[to_email], body=body)
    mail.send(msg)

# Database connection
try:
    mydb = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=int(os.getenv("TIMEOUT")),
        cursorclass=pymysql.cursors.DictCursor,
        db=os.getenv("DATABASE_NAME"),
        host=os.getenv("DB_HOST"),
        password=os.getenv("DB_PASSWORD"),
        read_timeout=int(os.getenv("TIMEOUT")),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        write_timeout=int(os.getenv("TIMEOUT")),
    )
except pymysql.err.OperationalError as err:
    if "Unknown database" in str(err):
        setup.create_database()
        mydb = pymysql.connect(
            charset="utf8mb4",
            connect_timeout=int(os.getenv("TIMEOUT")),
            cursorclass=pymysql.cursors.DictCursor,
            db=os.getenv("DATABASE_NAME"),
            host=os.getenv("DB_HOST"),
            password=os.getenv("DB_PASSWORD"),
            read_timeout=int(os.getenv("TIMEOUT")),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            write_timeout=int(os.getenv("TIMEOUT")),
        )
        setup.create_tables()
        setup.insert_initial_data()
    else:
        raise


mycursor = mydb.cursor()

def generateIDPass(UserType,FirstName,LastName,digits=60):
    if UserType=='student':
        mycursor.execute("SELECT MAX(Student_ID) FROM students")

        result = tuple((mycursor.fetchone()).values())[0]
        
        if result is None:
            result = 102367001
        else:
            result =int(result)+ 1
        mail = FirstName[0] + LastName + str(digits)+'_be'+str(datetime.datetime.now().date().year)[-2:]+'@thapar.edu'
        mycursor.execute("select * from students where College_Email=%s", (mail,))
        if mycursor.fetchone():
            return generateIDPass(UserType,FirstName,LastName,int(digits)+1)
            
    elif UserType=='faculty':
        mycursor.execute("SELECT MAX(Faculty_ID) FROM faculty")
        result = tuple((mycursor.fetchone()).values())[0]
        if result is None:
            result = 1
        else:
            result =int(result)+ 1
        mail = FirstName[0] + LastName + str(digits) + '@thapar.edu'
        mycursor.execute("select * from faculty where official_mail=%s", (mail,))
        if mycursor.fetchone():
            return generateIDPass(UserType,FirstName,LastName,digits+1)
            
    password = FirstName[:3] + LastName[-3:] + str(result)[-2:] + '@tiet'
    return mail, password, result


def getFacultyCourses():
    mycursor.execute("SELECT  Course_ID,Course_Name FROM courses")
    courses = tuple(tuple(course.values()) for course in mycursor.fetchall())
    return courses



def getFacultyDepartments():
    mycursor.execute("SELECT  Department_ID,Department_Name FROM department")
    departments = tuple(tuple(department.values()) for department in mycursor.fetchall())
    return departments

def querymaker(query,values):
    display_query=query
    if values:
        for value in values:
            display_query = display_query.replace('%s', f"'{value}'", 1)
    return display_query
        

@app.route('/')
def main():
    session.clear()
    return render_template('index.html')

@app.route('/signin')
def signin_page():
    return render_template('SignIn.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('registration.html')

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        firstname_error = None
        middlename_error = None
        lastname_error = None
        email_error = None
        phone_error = None
        gender_error = None
        street_error = None
        district_error = None
        state_error = None
        country_error = None
        dob_error = None

        FirstName = request.form.get('firstname', '').capitalize().strip()
        if not FirstName:
            firstname_error = "First name cannot be empty"
        elif len(FirstName) < 3:
            firstname_error = "First name should be at least 3 characters long"
        elif not re.match("^[a-zA-Z]*$", FirstName):
            firstname_error = "First name should contain only alphabets"
        
        MiddleName = request.form.get('middlename', '').capitalize().strip()
        if MiddleName and not re.match("^[a-zA-Z]*$", MiddleName):
            middlename_error = "Middle name should contain only alphabets"

        LastName = request.form.get('lastname', '').capitalize().strip()
        if not LastName:
            lastname_error = "Last name cannot be empty"
        elif not re.match("^[a-zA-Z]*$", LastName):
            lastname_error = "Last name should contain only alphabets"

        dob = request.form.get('dob', '')
        if not dob:
            dob_error = "Please select date of birth"
        elif dob > str(datetime.datetime.now().date()):
            dob_error = "Date of birth cannot be in the future"

        gender = request.form.get('gender', '')
        if not gender:
            gender_error = "Please select gender"

        email = request.form.get('email', '').lower().strip()

        street = request.form.get('street', '').capitalize().strip()
        if not street:
            street_error = "Street cannot be empty"
        
        district = request.form.get('district', '').capitalize().strip()
        if not district:
            district_error = "District cannot be empty"
        
        state = request.form.get('state', '').capitalize().strip()
        if not state:
            state_error = "State cannot be empty"
        
        country = request.form.get('country', '').capitalize().strip()
        if not country:
            country_error = "Country cannot be empty"

        if not email:
            email_error = "Email cannot be empty"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            email_error = "Invalid email"
        else:
            mycursor.execute("SELECT * FROM students WHERE email=%s", (email,))
            if mycursor.fetchone():
                email_error = "Email already exists"
        
        phone_input = request.form.get('phone', '').strip()
        phones = [p.strip() for p in phone_input.split(',') if p.strip()]
        
        if not phones:
            phone_error = "At least one phone number is required"
        else:
            for phone in phones:
                if not re.match(r"^\+?\d{1,3}[-\s]?\d{10}$", phone) and not re.match(r"^\d{10}$", phone):
                    phone_error = "Invalid phone number format"
                    break

        try:
            courses={"courses":getFacultyCourses()}
            departments={"departments":getFacultyDepartments()}
        except:
            courses={"courses":[]}
            departments={"departments":[]}

        if any([email_error, phone_error, firstname_error, middlename_error, lastname_error, state_error, district_error, street_error, country_error, gender_error, dob_error]):
            return render_template('registration.html',**courses,**departments, email_error=email_error, phone_error=phone_error, firstname_error=firstname_error, middlename_error=middlename_error, lastname_error=lastname_error, state_error=state_error, district_error=district_error, street_error=street_error, country_error=country_error, gender_error=gender_error, dob_error=dob_error,firstname=FirstName,middlename=MiddleName,lastname=LastName,dob=dob,gender=gender,phone=(',').join(phones),street=street,district=district,state=state,country=country,userType='student',email=email)
        
        mail, password, result = generateIDPass('student', FirstName.lower(), LastName.lower())
        query = """
            INSERT INTO students (Student_ID, First_Name, Middle_Name, Last_Name, Street, District, State, Country, Gender, Date_of_Birth, Email, College_Email, Password, Enrollment_Year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        queries=dict()
        values = (result, FirstName, MiddleName, LastName, street, district, state, country, gender, dob, email, mail.lower(), password, datetime.datetime.now().year)
        queries['insert_student']=querymaker(query,values)
        
        try:
            mycursor.execute(query, values)
            mydb.commit()
            
            for phone in phones:
                sql = "INSERT INTO student_phone_no (Student_ID, Phone) VALUES (%s, %s)"
                queries[f'{phone}']=querymaker(sql,(result, phone))
                mycursor.execute(sql, (result, phone))
            mydb.commit()
            
            query = "INSERT INTO fees (Student_ID, Amount, Type) VALUES (%s, %s, %s)"
            mycursor.execute(query, (result, 1500, 'Registration Fees'))
            queries['insert_fees']=querymaker(query,(result, 1500, 'Registration Fees'))
            mydb.commit()
            
            return render_template('index.html', message_success="Application has been submitted successfully. Your credentials are Email: " + mail.lower() + " Password: " + password + " You will receive an email confirmation if accepted.",queries=queries)
        except Exception as e:
            mydb.rollback()
            return render_template('index.html', message_error="Registration failed: " + str(e))
    
    return render_template('registration.html')


@app.route('/register/faculty', methods=['GET', 'POST'])
def register_faculty():
    if request.method == 'POST':
        firstname_error = None
        middlename_error = None
        lastname_error = None
        email_error = None
        phone_error = None
        course_id_error = None
        department_id_error = None
        designation_error = None

        firstname = request.form.get('firstname', '').capitalize().strip()
        middlename = request.form.get('middlename', '').capitalize().strip()
        lastname = request.form.get('lastname', '').capitalize().strip()
        email = request.form.get('email', '').lower().strip()
        phone_input = request.form.get('phone', '').strip()
        phones = [p.strip() for p in phone_input.split(',') if p.strip()]
        
        facultyCourseID = request.form.get('facultyCourseID')
        facultyCourseName = request.form.get('facultyCourseName')
        facultyDepartmentID = request.form.get('facultyDepartmentID')
        facultyDepartmentName = request.form.get('facultyDepartmentName')
        facultyDesignation = request.form.get('Designation')
        
        if not firstname:
            firstname_error = "First name cannot be empty"
        elif len(firstname) < 3:
            firstname_error = "First name should be at least 3 characters long"
        elif not re.match("^[a-zA-Z]*$", firstname):
            firstname_error = "First name should contain only alphabets"
        
        if middlename and not re.match("^[a-zA-Z ]*$", middlename):
            middlename_error = "Middle name should contain only alphabets and spaces"
        
        if lastname and not re.match("^[a-zA-Z]*$", lastname):
            lastname_error = "Last name should contain only alphabets"
        
        if not email:
            email_error = "Email cannot be empty"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            email_error = "Invalid email"
        else:
            mycursor.execute("SELECT * FROM faculty WHERE Mail=%s", (email,))
            if mycursor.fetchone():
                email_error = "Email already exists"
        
        if not phones:
            phone_error = "At least one phone number is required"
        else:
            for phone in phones:
                if not re.match(r"^\+?\d{1,3}[-\s]?\d{10}$", phone) and not re.match(r"^\d{10}$", phone):
                    phone_error = "Invalid phone number format"
                    break
        
        if not facultyCourseID:
            course_id_error = "Please select course"
        if not facultyDepartmentID:
            department_id_error = "Please select department"
        if not facultyDesignation:
            designation_error = "Please select designation"
        
        try:
            courses={"courses":getFacultyCourses()}
            departments={"departments":getFacultyDepartments()}
        except:
            courses={"courses":[]}
            departments={"departments":[]}
        
        if any([email_error, phone_error, firstname_error,middlename_error,lastname_error, course_id_error, department_id_error, designation_error]):
            return render_template('registration.html',**courses,**departments, email_error=email_error, phone_error=phone_error, firstname_error=firstname_error,lastname_error=lastname_error,middlename_error=middlename_error, course_id_error=course_id_error, department_id_error=department_id_error, designation_error=designation_error,firstname=firstname,middlename=middlename,lastname=lastname,email=email,phone=(',').join(phones),userType='faculty',facultyCourseID=facultyCourseID,facultyDepartmentID=facultyDepartmentID,facultyDesignation=facultyDesignation,facultyCourseName=facultyCourseName,facultyDepartmentName=facultyDepartmentName)
        
        mail, password, result = generateIDPass('faculty', firstname.lower(), "")
        query = "INSERT INTO faculty (Faculty_ID, First_Name, Middle_Name, Last_Name, Date_of_Joining, Designation, Mail, Official_Mail, Password, Course_ID, Department_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (result, firstname, middlename, lastname, datetime.datetime.now().date(), facultyDesignation, email, mail.lower(), password, facultyCourseID, facultyDepartmentID)
        
        try:
            mycursor.execute(query, values)
            mydb.commit()
            
            for phone in phones:
                sql = "INSERT INTO faculty_phone_no (Faculty_ID, Phone) VALUES (%s, %s)"
                mycursor.execute(sql, (result, phone))
            mydb.commit()
            
            query_display=querymaker(query,values)
            print(query_display)
            print("-"*100)
            return render_template('index.html', message_success="Faculty registration successful. Your credentials are Email: " + mail.lower() + " Password: " + password,query=query_display)
        except Exception as e:
            mydb.rollback()
            return render_template('index.html', message_error="Faculty registration failed: " + str(e))
    
    return render_template('registration.html')

@app.route('/signup')
def signup():
    try:
        
        courses={"courses":getFacultyCourses()}
        departments={"departments":getFacultyDepartments()}
    except:
        courses={"courses":[]}
        departments={"departments":[]}
    courses
    return render_template('registration.html',**courses,**departments)





@app.route('/faculty/dashboard')
def facultyDashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    print(session['user'])
    print("*"*100)
    queries={}
    message = request.args.get('message', None)
    error = request.args.get('error', None)
    query = "SELECT faculty.Faculty_ID, CONCAT(faculty.First_Name,' ',faculty.Middle_Name,' ',faculty.Last_Name) AS Name, faculty.Date_of_Joining, faculty.Designation, faculty.Mail, faculty.Official_Mail, faculty.Password, courses.Course_Name ,department.Department_Name, department.Department_ID FROM faculty INNER JOIN courses on courses.Course_ID = faculty.Course_ID INNER JOIN department on department.Department_ID =faculty.Department_ID WHERE faculty.Faculty_ID=%s;" 
    mycursor.execute(query, (session['user'][0],))
    faculty = (tuple(tuple(exam.values()) for exam in mycursor.fetchall()))[0]
    print(faculty)
    queries['faculty']=querymaker(query,(session['user'][0],))
    query = "select phone from faculty_phone_no where Faculty_ID=%s"
    mycursor.execute(query, (session['user'][0],))
    phones = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['phones']=querymaker(query,(session['user'][0],))
    query = "SELECT courses.Course_Name,exams.Exam_Type,exams.Exam_Date FROM exams INNER JOIN courses on courses.Course_ID=exams.Course_ID WHERE exams.Course_ID=%s AND exams.Exam_Date>=CURRENT_DATE ORDER BY exams.Exam_Date ASC;"
    mycursor.execute(query, (session['user'][9],))
    upcoming_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['upcoming_exams']=querymaker(query,(session['user'][9],))

    query = "SELECT courses.Course_Name,exams.Exam_Type,exams.Exam_Date FROM exams INNER JOIN courses on courses.Course_ID=exams.Course_ID WHERE exams.Course_ID=%s AND exams.Exam_Date<CURRENT_DATE AND exams.Status='Unevaluated' ORDER BY exams.Exam_Date ASC;"
    mycursor.execute(query, (session['user'][9],))
    recent_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['recent_exams']=querymaker(query,(session['user'][9],))

    query = "SELECT courses.Course_Name,exams.Exam_Type,exams.Exam_Date FROM exams INNER JOIN courses on courses.Course_ID=exams.Course_ID WHERE exams.Course_ID=%s AND exams.Status='Locked' ORDER BY exams.Exam_Date DESC LIMIT 3;"
    mycursor.execute(query, (session['user'][9],))
    locked_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['locked_exams']=querymaker(query,(session['user'][9],))
    new_queries=request.args.get('queries',None)
    if new_queries:
        queries=ast.literal_eval(new_queries)
    return render_template('FacultyDashboard.html', faculty=faculty, phones=phones, upcoming_exams=upcoming_exams, recent_exams=recent_exams, locked_exams=locked_exams, message=message, error=error,queries=queries)

@app.route('/faculty/update/<string:phones>', methods=['POST'])
def update_faculty(phones):
    if 'user' not in session:
        return redirect(url_for('login'))
    if(request.method=='POST'):
        queries={}
        Name=request.form.get('faculty_name')
        names=Name.split(' ')
        if(len(names)==1):
            FirstName=names[0]
            LastName=''
            MiddleName=''
        elif(len(names)==2):
            FirstName=names[0]
            LastName=names[1]
            MiddleName=''
        else:
            FirstName=names[0]
            MiddleName=' '.join(names[1:-1])
            LastName=names[-1]
        phones=ast.literal_eval(phones)
        phones=tuple(x[0] for x in phones )
        valid_phones = []
        invalid_phones = []
        for i in phones:
            temp=[]
            current_phone = i
            new_phones = request.form.get(f'faculty_phone_{current_phone}').split(',')
            for new_phone in new_phones:
                new_phone=new_phone.strip()
                if new_phone and new_phone != current_phone:
                    # Define valid phone patterns
                    phone_patterns = [
                        r'^\+\d{1,3}\d{10}$',      # International format with no space: +1234567890, +911234567890
                        r'^\+\d{1,3}\s\d{10}$',    # International format with space: +123 4567890, +91 1234567890
                        r'^\d{10}$'                # Local format: 1234567890
                    ]
                    
                    # Check if the phone number is valid
                    is_valid = any(re.match(pattern, new_phone) for pattern in phone_patterns)
                    
                    if is_valid:
                        temp.append((current_phone, new_phone))
                    else:
                        invalid_phones.append(new_phone)
                elif new_phone == current_phone:
                    # No change, keep the current phone number
                    temp.append((current_phone, current_phone))
                elif not new_phone:
                    # Mark for deletion
                    temp.append((current_phone, None))
                # If unchanged, do nothing
            valid_phones.extend(temp)
        if invalid_phones:
            errors['phone_error'] = f"Invalid phone number format: {', '.join(invalid_phones)}"
        
        personal_mail=request.form.get('faculty_personal_mail')
        password=request.form.get('faculty_password')
        session['user'] = (session['user'][0], FirstName, MiddleName, LastName, session['user'][4], session['user'][5], session['user'][6], session['user'][7], session['user'][8], session['user'][9])
        query="UPDATE faculty SET First_Name=%s, Middle_Name=%s, Last_Name=%s, Mail=%s, Password=%s WHERE Faculty_ID=%s"
        values=(FirstName,MiddleName,LastName,personal_mail,password,session['user'][0])
        mycursor.execute(query,values)
        mydb.commit()
        queries['faculty']=querymaker(query,(FirstName,MiddleName,LastName,personal_mail,password,session['user'][0]))


        remaining_phones = valid_phones.copy()


        # for current_phone, new_phone in valid_phones:
        for i in range(len(phones)):
            current_phone = valid_phones[i][0]
            new_phone = valid_phones[i][1]
            if new_phone is None:
                # Delete the phone number
                query = "DELETE FROM faculty_phone_no WHERE Phone=%s AND Faculty_ID=%s"
                values = (current_phone, session['user'][0])
                mycursor.execute(query, values)
                queries['delete_phone']=querymaker(query,values)
                remaining_phones.remove((current_phone, new_phone))

            elif new_phone != current_phone:
                # Update the phone number
                query = "UPDATE faculty_phone_no SET Phone=%s WHERE Phone=%s AND Faculty_ID=%s"
                values = (new_phone, current_phone, session['user'][0])
                mycursor.execute(query, values)
                queries['update_phone']=querymaker(query,values)
                remaining_phones.remove((current_phone, new_phone))
            else:
                # No change, keep the current phone number
                remaining_phones.remove((current_phone, new_phone))
        # Get the current phone numbers after updates
        query = "SELECT Phone FROM faculty_phone_no WHERE Faculty_ID=%s"
        mycursor.execute(query, (session['user'][0],))
        x=list(tuple(x.values())[0]for x in mycursor.fetchall())

        current_phones = [phone[0] for phone in x]
        queries['current_phones']=querymaker(query,(session['user'][0],))

        # Add any new phone numbers that weren't updates
        for _, new_phone in remaining_phones:
            if new_phone:
                query = "INSERT INTO faculty_phone_no (Faculty_ID, Phone) VALUES (%s, %s)"
                mycursor.execute(query, (session['user'][0], new_phone))
                current_phones.append(new_phone)
                queries['insert_phone']=querymaker(query,(session['user'][0],new_phone))

        return redirect(url_for('facultyDashboard', message="Updated", queries=queries))
    return redirect(url_for('facultyDashboard', error="Failed to update"))  # Redirect to dashboard with error message




@app.route('/faculty')
def faculty():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('facultyDashboard'))


@app.route('/faculty/students')
def facultyStudents():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = f"""
        SELECT CONCAT(s.first_name, ' ', s.Middle_Name, ' ', s.Last_Name) AS Full_Name,s.Gender , c.Course_Name,e.Enrolled_IN , 
       s.College_Email,s.student_id
       FROM students s
       JOIN enrollment e ON s.Student_ID = e.Student_ID
       JOIN faculty f ON f.Course_ID = e.Course_ID
       JOIN courses c ON c.Course_ID = e.Course_ID
       WHERE f.Faculty_ID = {session['user'][0]}
"""
    message_danger= request.args.get('message_danger', None)
    mycursor.execute(query)
    students = tuple(tuple(student.values()) for student in mycursor.fetchall())

    return render_template('students.html', students=students,message_danger=message_danger,query=request.args.get('query',querymaker(query,None)))

@app.route('/faculty/students/unenroll/<int:student_id>')
def faculty_unenroll_student(student_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM enrollment WHERE Student_ID=%s and Course_ID=%s"
    mycursor.execute(query, (student_id, session['user'][9]))
    mydb.commit()
    return redirect(url_for('facultyStudents',message_danger="Student Unenrolled From The Course",query=querymaker(query,(student_id,session['user'][9]))))
@app.route('/faculty/exams/add', methods=['GET', 'POST'])
def add_exam():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        exam_date = request.form.get('exam_date')
        date_error = None
        duration_error = None
        type_error = None
        venue_error = None
        charge_error = None
        exist_error=None
        if not exam_date:
            date_error = "Exam date cannot be empty"
        elif exam_date < str(datetime.datetime.now().date()):
            date_error = "Exam date cannot be in the past"
        exam_duration = request.form.get('exam_duration')
        if not exam_duration:
            duration_error = "Exam duration cannot be empty"
        elif float(exam_duration) < 0:
            duration_error = "Exam duration cannot be negative"
        
        exam_charge = float(request.form.get('exam_charge') or 0)
        if exam_charge < 0:
            charge_error = "Exam charge cannot be negative"
        exam_type = request.form.get('exam_type')
        if not exam_type:
            type_error = "Exam type cannot be empty"
        venue = request.form.get('venue')
        if not venue:
            venue_error = "Venue cannot be empty"
        query = "select count(*) from exams where course_id=%s and exam_type=%s"
        mycursor.execute(query,(course_id,exam_type))
        count=tuple((mycursor.fetchone()).values())[0]
        if count>0:
            exist_error="Exam with this type already exists"
        if date_error or duration_error or type_error or venue_error or charge_error or exist_error:
            return redirect(url_for('facultyExams', exist_error=exist_error, date_error=date_error, duration_error=duration_error, type_error=type_error, venue_error=venue_error, charge_error=charge_error, exam_date=exam_date, exam_duration=exam_duration, exam_charge=exam_charge, exam_type=exam_type, venue=venue))

        query = """
            INSERT INTO exams (Course_ID, Exam_Date, Exam_Duration, Exam_Type, Venue) 
            VALUES (%s, %s, %s, %s, %s)
        """
        values = (course_id, exam_date, exam_duration, exam_type, venue)
        mycursor.execute(query, values)
        mydb.commit()
        
        query = """
            INSERT IGNORE INTO takes_exams (Student_ID, Exam_ID) 
            SELECT enrollment.Student_ID, exams.Exam_ID 
            FROM enrollment 
            INNER JOIN exams ON exams.Course_ID = enrollment.Course_ID 
            WHERE exams.Course_ID = %s AND exams.Exam_Type = %s
        """
        mycursor.execute(query, (course_id, exam_type))
        mydb.commit()
        if(exam_charge>0):
            query = """
                INSERT IGNORE INTO fees (Student_ID, Exam_ID, Amount, Type) 
                SELECT enrollment.Student_ID, exams.Exam_ID,  %s, 'Exam Fee' 
                FROM enrollment 
                INNER JOIN exams ON exams.Course_ID = enrollment.Course_ID 
                WHERE exams.Course_ID = %s AND exams.Exam_Type = %s
            """
            mycursor.execute(query, (exam_charge,course_id, exam_type))
            mydb.commit()
        
        return redirect(url_for('facultyExams',message="Exam scheduled"))
    return render_template('exams.html', courses=getFacultyCourses())
@app.route('/faculty/exams/update/<int:exam_id>', methods=['POST'])
def update_exam(exam_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        errors_update={}
        current_exam_type=None
        course_id = request.form.get(f'course_id_{exam_id}')
        exam_date = request.form.get(f'exam_date_{exam_id}')
        if exam_date < str(datetime.datetime.now().date()):
            errors_update['date_error_update'] = "Exam date cannot be in the past"
        exam_duration = request.form.get(f'exam_duration_{exam_id}')
        if float(exam_duration) < 0:
            errors_update['duration_error_update'] = "Exam duration cannot be negative"
        exam_type = request.form.get(f'exam_type_{exam_id}')
        if not exam_type:
            query = "SELECT Exam_Type FROM exams WHERE Exam_ID=%s"
            mycursor.execute(query, (exam_id,))
            current_exam_type = tuple((mycursor.fetchone()).values())
            if current_exam_type:
                exam_type = current_exam_type[0]
        venue = request.form.get(f'exam_venue_{exam_id}')
        if not venue:
            errors_update['venue_error_update'] = "Venue cannot be empty"
        query = "SELECT count(*) FROM exams WHERE course_id=%s AND exam_type=%s"
        mycursor.execute(query, (course_id, exam_type))
        count = tuple((mycursor.fetchone()).values())[0]
        if count > 0 and current_exam_type[0]!=exam_type:
            errors_update['exist_error_update'] = "Exam with this type already exists"
        if errors_update:
            return redirect(url_for('facultyExams',errors_update=errors_update))
        query = """
            UPDATE exams 
            SET Exam_Date=%s, Exam_Duration=%s, Exam_Type=%s, Venue=%s
            WHERE Exam_ID=%s
        """
        values = (exam_date, exam_duration, exam_type, venue, exam_id)
        mycursor.execute(query, values)
        mydb.commit()
        return redirect(url_for('facultyExams', message_success="Exam Updated", query=querymaker(query, values)))
@app.route('/faculty/exams/delete/<int:exam_id>')
def delete_exam(exam_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM exams WHERE Exam_ID=%s"
    mycursor.execute(query, (exam_id,))
    mydb.commit()
    return redirect(url_for('facultyExams', message_danger="Exam Deleted",query=querymaker(query,(exam_id,))))

@app.route('/faculty/exams')
def facultyExams():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries = {}
    date_error = request.args.get('date_error', None)
    duration_error = request.args.get('duration_error', None)
    type_error = request.args.get('type_error', None)
    venue_error = request.args.get('venue_error', None)
    charge_error = request.args.get('charge_error', None)
    exist_error = request.args.get('exist_error', None)
    exam_date = request.args.get('exam_date', None)
    exam_duration = request.args.get('exam_duration', None)
    exam_charge = request.args.get('exam_charge', None)
    exam_type = request.args.get('exam_type', None)
    venue = request.args.get('venue', None)
    errors_update = ast.literal_eval(request.args.get('errors_update', '{}'))
    query = "SELECT * FROM exams WHERE Exam_Date>=CURRENT_DATE AND Course_ID=%s;"
    mycursor.execute(query, (session['user'][9],))
    upcoming_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['upcoming_exams'] = querymaker(query, (session['user'][9],))
    
    
    query = "SELECT * FROM exams WHERE Exam_Date<CURRENT_DATE AND Course_ID=%s;"
    mycursor.execute(query, (session['user'][9],))
    recent_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['recent_exams'] = querymaker(query, (session['user'][9],))
    
    
    query = "SELECT count(*) FROM enrollment INNER JOIN faculty ON enrollment.Course_ID=faculty.Course_ID WHERE faculty.Course_ID=%s;"
    mycursor.execute(query, (session['user'][9],))
    queries['no_enrollment'] = querymaker(query, (session['user'][9],))
    
    
    no_enrollment = None
    if tuple((mycursor.fetchone()).values())[0] == 0:
        no_enrollment = "No students enrolled in this course"
    
    
    if errors_update:
        queries = None
    
    
    query = request.args.get('query', None)
    if query:
        queries = None
    return render_template('exams.html', upcoming_exams=upcoming_exams, recent_exams=recent_exams, date_error=date_error, duration_error=duration_error, type_error=type_error, venue_error=venue_error, charge_error=charge_error, exist_error=exist_error,   exam_date=exam_date, exam_duration=exam_duration, exam_charge=exam_charge, exam_type=exam_type, venue=venue, no_enrollment=no_enrollment, queries=queries,query=query,message_danger=request.args.get('message_danger',None),message_success=request.args.get('message_success',None),errors_update=errors_update)

@app.route('/faculty/results/<int:exam_id>/evaluate', methods=['GET', 'POST'])
def evaluate(exam_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    message=request.args.get('message_success',None)
    error=request.args.get('message_danger',None)
    queries={}
    query = "SELECT Student_ID, CONCAT(First_Name, ' ', Middle_Name, ' ', Last_Name) AS Full_Name FROM students WHERE Student_ID IN ( SELECT takes_exams.Student_ID FROM takes_exams INNER JOIN exams ON exams.Exam_ID = takes_exams.Exam_ID WHERE exams.Exam_ID = %s ) AND Student_ID NOT IN ( SELECT results.Student_ID FROM results INNER JOIN exams ON results.Exam_ID = exams.Exam_ID WHERE exams.Exam_ID = %s );"
    mycursor.execute(query, (exam_id,exam_id))
    students_to_be_evaluted = tuple(tuple(student.values()) for student in mycursor.fetchall())
    queries['students_to_be_evaluted']=querymaker(query,(exam_id,exam_id))
    query = """ SELECT students.Student_ID, CONCAT(students.First_Name, ' ', students.Middle_Name, ' ', students.Last_Name) AS Full_Name, results.Marks_Obtained, results.Grade FROM students INNER JOIN results ON results.Student_ID = students.Student_ID WHERE students.Student_ID IN ( SELECT takes_exams.Student_ID FROM takes_exams INNER JOIN exams ON exams.Exam_ID = takes_exams.Exam_ID WHERE exams.Exam_ID = %s ) AND results.Exam_ID = %s; """
    mycursor.execute(query, (exam_id,exam_id))
    students_evaluted = tuple(tuple(student.values()) for student in mycursor.fetchall())
    queries['students_evaluted']=querymaker(query,(exam_id,exam_id))
    query=request.args.get('query',None)
    if query:
        queries=None
    return render_template('result_evaluation.html', students_to_be_evaluted=students_to_be_evaluted, students_evaluted=students_evaluted,exam_id=exam_id,message_success=message,message_danger=error,queries=queries,query=query)



@app.route('/faculty/results/<int:exam_id>/evaluate/<int:student_id>', methods=['POST'])
def evaluate_student(exam_id, student_id):
    if (request.method=='POST'):
        
        if 'user' not in session:
            return redirect(url_for('login'))
        obtained_marks=request.form.get(f'obtained_marks_{student_id}')
        query="SELECT Result_ID from results WHERE Exam_ID=%s AND Student_ID=%s"
        mycursor.execute(query,(exam_id,student_id))
        result=mycursor.fetchone()
        values=None
        if (result):
            result=tuple(result.values())
            query="UPDATE results SET Marks_Obtained=%s WHERE Result_ID=%s"
            values=(obtained_marks,result[0])
            mycursor.execute(query,values)
            message="Result updated"
        else:
            
            query = "INSERT INTO `results`(`Exam_ID`, `Student_ID`, `Course_ID`, `Marks_Obtained`) VALUES (%s, %s, %s, %s)"
            values = (exam_id, student_id, session['user'][9], obtained_marks)
            mycursor.execute(query, values)
            message="Result added"
        mydb.commit()
        return redirect(url_for('evaluate', exam_id=exam_id,message_success=message,message_danger=None,query=querymaker(query,values)))
    
@app.route('/faculty/results/<int:exam_id>/evaluateall/<string:student_ids>', methods=['POST'])
def evaluate_students(exam_id, student_ids):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    student_ids = student_ids.split(',')
    for student_id in student_ids:
        obtained_marks = request.form.get(f'obtained_marks_{student_id}')
        # INSERT INTO `results`(`Exam_ID`, `Student_ID`, `Course_ID`, `Marks_Obtained`)
        query="SELECT Result_ID from results WHERE Exam_ID=%s AND Student_ID=%s"
        mycursor.execute(query,(exam_id,student_id))
        result=mycursor.fetchone()
        if (result):
            result=tuple(result.values())
            query="UPDATE results SET Marks_Obtained=%s WHERE Result_ID=%s"
            values=(obtained_marks,result[0])
            mycursor.execute(query,values)
        else:
            
            query = "INSERT INTO `results`(`Exam_ID`, `Student_ID`, `Course_ID`, `Marks_Obtained`) VALUES (%s, %s, %s, %s)"
            values = (exam_id, student_id, session['user'][9], obtained_marks)
            mycursor.execute(query, values)
        mydb.commit()
        message="all marks have been uploaded"
    return redirect(url_for('evaluate', exam_id=exam_id,message=message,error=None))

def calculate_percentile(data, percentile):
    index = (percentile / 100) * (len(data) - 1)
    lower = int(index)
    upper = lower + 1
    weight = index - lower
    if upper < len(data):
        return data[lower] * (1 - weight) + data[upper] * weight
    else:
        return data[lower]

@app.route('/faculty/results/<int:exam_id>/grade/<string:student_ids>', methods=['POST'])
def result_grade(exam_id, student_ids):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    student_ids = student_ids.split(',')
    query = "SELECT Marks_Obtained FROM results WHERE Exam_ID=%s"
    mycursor.execute(query, (exam_id,))
    obtained_marks = [float(value) for row in mycursor.fetchall() for value in row.values()]
    obtained_marks.sort()
    grade=None
    percentiles = {p: calculate_percentile(obtained_marks, p) for p in range(30, 100, 10)}
    grade_map = {
        90: 'A', 80: 'A-', 70: 'B', 60: 'B-', 50: 'C', 40: 'C-', 30: 'D', 0: 'E'
    }

    for student_id in student_ids:
        obtained_marks = float(request.form.get(f'obtained_marks_{student_id}', 0))
        grade = next(grade for p, grade in grade_map.items() if obtained_marks >= percentiles.get(p, 0))
        
        query = "UPDATE results SET Grade=%s, Status='Evaluated' WHERE Exam_ID=%s AND Student_ID=%s"
        mycursor.execute(query, (grade, exam_id, student_id))
    
    mydb.commit()
    Message="Grades have been uploaded"
    return redirect(url_for('evaluate', exam_id=exam_id,message_success=Message,messaage_danger=None,query=querymaker(query,(grade,exam_id,student_id))))

@app.route('/faculty/results/<int:exam_id>/lock', methods=['POST'])
def lock(exam_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "UPDATE exams SET Status='Locked' WHERE Exam_ID=%s"
    mycursor.execute(query, (exam_id,))
    query = "UPDATE results SET Status='Locked' WHERE Exam_ID=%s"
    mycursor.execute(query, (exam_id,))
    mydb.commit()
    
    return redirect(url_for('facultyResults',message_success="Result Locked",query=querymaker(query,(exam_id,))))


@app.route('/faculty/results/<int:exam_id>/delete/<int:student_id>', methods=['POST'])
def delete_student_result(exam_id, student_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    if (request.method=='POST'):
        obtained_marks=request.form.get(f'obtained_marks_{student_id}')
        query="SELECT Result_ID from results WHERE Exam_ID=%s AND Student_ID=%s"
        mycursor.execute(query,(exam_id,student_id))
        result=tuple((mycursor.fetchone()).values())
        message=None
        error=None
        if (result):
            try:
                query="DELETE FROM results WHERE Result_ID=%s"
                values=(result[0],)
                mycursor.execute(query,values)
                mydb.commit()
                message_danger="Result deleted"
            except Exception as e:
                error=e
        else:
            message_danger= "Student not evaluated"
        return redirect(url_for('evaluate', exam_id=exam_id,message_danger=message_danger,query=querymaker(query,(result[0],))))
    return redirect(url_for('evaluate', exam_id=exam_id,message=message,error="Failed to delete"))

@app.route('/faculty/results/<int:exam_id>/view', methods=['GET', 'POST'])
def view_results(exam_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT results.Result_ID,results.Student_ID,CONCAT(students.First_Name,' ',students.Middle_Name,' ',students.Last_Name) AS Name,results.Marks_Obtained,results.Grade from results INNER JOIN students ON results.Student_ID=students.Student_ID INNER JOIN courses on results.Course_ID=courses.Course_ID WHERE results.Exam_ID=%s;"
    mycursor.execute(query, (exam_id,))
    results = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['results']=querymaker(query,(exam_id,))
    query="SELECT DISTINCT courses.Course_Name, courses.Credits FROM courses INNER JOIN results ON results.Course_ID=courses.Course_ID WHERE results.Exam_ID=%s;"
    mycursor.execute(query,(exam_id,))  
    course=(tuple(tuple(course.values()) for course in mycursor.fetchall()))[0]
    queries['course']=querymaker(query,(exam_id,))
    return render_template('view_result.html', results=results, exam_id=exam_id,course=course,queries=queries)



@app.route('/faculty/results')
def facultyResults():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    queries = {}
    message_success = request.args.get('message_success', None)
    message_danger = request.args.get('message_danger', None)
    
    def fetch_exams(query, params):
        mycursor.execute(query, params)
        return tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    
    exams_about_To_held_query = "SELECT * FROM exams WHERE Course_ID=%s  AND Exam_Date>CURRENT_DATE"
    exams_about_To_held = fetch_exams(exams_about_To_held_query, (session['user'][9],))
    queries['Exams_about_To_held'] = querymaker(exams_about_To_held_query, (session['user'][9],))
    
    exams_to_evaluate_query = "SELECT * FROM exams WHERE Course_ID=%s AND Status='Unevaluated' AND Exam_Date<=CURRENT_DATE"
    Exams_toEvaluate = fetch_exams(exams_to_evaluate_query, (session['user'][9],))
    queries['Exams_to_Evaluate'] = querymaker(exams_to_evaluate_query, (session['user'][9],))
    
    evaluated_query = "SELECT * FROM exams WHERE Course_ID=%s AND Status='Evaluated';"
    Evaluated = fetch_exams(evaluated_query, (session['user'][9],))
    queries['Evaluated'] = querymaker(evaluated_query, (session['user'][9],))
    
    locked_result_query = "SELECT * FROM exams WHERE Course_ID=%s AND Status='Locked';"
    Locked_Result = fetch_exams(locked_result_query, (session['user'][9],))
    queries['Locked_result'] = querymaker(locked_result_query, (session['user'][9],))
    query=request.args.get('query',None)
    if query:
        queries=None
    return render_template('results.html',exams_about_To_held=exams_about_To_held, Exams_toEvaluate=Exams_toEvaluate, Evaluated=Evaluated, Locked_Result=Locked_Result, message_success=message_success, message_danger=message_danger, queries=queries,query=query)

@app.route('/student/dashboard')
@app.route('/student')
def student():
    
    if 'user' not in session:
        return redirect(url_for('login'))
    errors = {}
    try:
        errors_str = request.args.get('errors', '{}')
        if errors_str and isinstance(errors_str, str):
            errors = ast.literal_eval(errors_str)
    except (ValueError, SyntaxError):
        errors = {}
    queries = {}
    message=request.args.get('message',None)
    query="SELECT `Student_ID`, CONCAT(`First_Name`, ' ', COALESCE(`Middle_Name`, ''), ' ', `Last_Name`) AS `Full_Name`, CONCAT( COALESCE(`Street`, ''), ', ', COALESCE(`District`, ''), ', ', COALESCE(`State`, ''), ', ', COALESCE(`Country`, '') ) AS `Full_Address`, `Gender`, `Date_of_Birth`, `Email`, `College_Email`, `Password`, `Enrollment_Year`, `Graduation_Year`, `Status` FROM `students` WHERE Student_ID=%s;"
    mycursor.execute(query,(session['user'][0],))
    student=tuple(tuple(student.values())for student in mycursor.fetchall())[0]
    queries['student']=querymaker(query,(session['user'][0],))
    query="SELECT Phone FROM student_phone_no WHERE Student_ID=%s;"
    mycursor.execute(query,(session['user'][0],))
    phones=tuple(tuple(phone.values()) for phone in mycursor.fetchall())
    queries['phones']=querymaker(query,(session['user'][0],))
    upcoming_exams_query = "SELECT courses.Course_Name,exams.Course_ID,exams.Exam_Type,exams.Exam_Duration,exams.Exam_Date,exams.Venue FROM exams INNER JOIN courses ON courses.Course_ID=exams.Course_ID WHERE exams.Exam_ID IN ( SELECT takes_exams.Exam_ID FROM takes_exams WHERE takes_exams.Student_ID = %s ) AND exams.Exam_Date >= CURRENT_DATE ORDER BY exams.Exam_Date ASC;"
    mycursor.execute(upcoming_exams_query,(session['user'][0],))
    upcoming_exams=tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['upcoming_exams']=querymaker(upcoming_exams_query,(session['user'][0],))
    recent_exams_query = "SELECT courses.Course_Name,exams.Course_ID,exams.Exam_Type,exams.Exam_Duration,exams.Exam_Date,exams.Venue FROM exams INNER JOIN courses ON courses.Course_ID=exams.Course_ID WHERE exams.Exam_ID IN ( SELECT takes_exams.Exam_ID FROM takes_exams WHERE takes_exams.Student_ID = %s ) AND exams.Exam_Date < CURRENT_DATE ORDER BY exams.Exam_Date ASC;"
    mycursor.execute(recent_exams_query,(session['user'][0],))
    recent_exams=tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['recent_exams']=querymaker(recent_exams_query,(session['user'][0],))
    query="SELECT  courses.Course_Name,courses.Course_ID,exams.Exam_Type,exams.Exam_Duration,exams.Exam_Date,exams.Venue FROM exams INNER JOIN courses ON exams.Course_ID = courses.Course_ID WHERE exams.Exam_ID IN ( SELECT takes_exams.Exam_ID FROM results INNER JOIN exams ON results.Exam_ID = exams.Exam_ID INNER JOIN takes_exams ON results.Exam_ID = takes_exams.Exam_ID WHERE results.Status = 'Locked' AND takes_exams.Student_ID = %s ) ORDER BY exams.Exam_Date ASC;"
    mycursor.execute(query,(session['user'][0],))
    locked_results=tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['locked_results']=querymaker(query,(session['user'][0],))
    
    query="SELECT  courses.Course_Name,courses.Course_ID,exams.Exam_Type,exams.Exam_Duration,exams.Exam_Date,exams.Venue FROM exams INNER JOIN courses ON exams.Course_ID = courses.Course_ID WHERE exams.Exam_ID IN ( SELECT takes_exams.Exam_ID FROM results INNER JOIN exams ON results.Exam_ID = exams.Exam_ID INNER JOIN takes_exams ON results.Exam_ID = takes_exams.Exam_ID WHERE results.Status = 'Evaluated' AND takes_exams.Student_ID = %s ) ORDER BY exams.Exam_Date ASC;"
    mycursor.execute(query,(session['user'][0],))
    evaluated_results=tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['evaluated_results']=querymaker(query,(session['user'][0],))
    session['phones']=phones
    query=request.args.get('query',None)
    if query:
        queries=None
    if request.args.get('queries'):
        queries = ast.literal_eval(request.args.get('queries', '{}'))
    return render_template('studentDashboard.html',student=student,phones=phones,upcoming_exams=upcoming_exams,recent_exams=recent_exams,locked_results=locked_results,evaluated_results=evaluated_results,message=message,errors=errors,queries=queries)

@app.route('/student/update/<int:student_id>/', methods=['POST'])
def update_student(student_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        queries={}
        # Initialize error flags
        errors = {}
        valid_data = {}
        # Validate name
        name = request.form.get('studentName')
        if not name:
            errors['name_error'] = "Name cannot be empty"
        elif len(name) < 3:
            errors['name_error'] = "Name should be at least 3 characters"
        else:
            names = name.split(' ')
            if len(names) == 1:
                valid_data['FirstName'] = names[0]
                valid_data['LastName'] = ''
                valid_data['MiddleName'] = ''
            elif len(names) == 2:
                valid_data['FirstName'] = names[0]
                valid_data['LastName'] = names[1]
                valid_data['MiddleName'] = ''
            else:
                valid_data['FirstName'] = names[0]
                valid_data['MiddleName'] = ' '.join(names[1:-1])
                valid_data['LastName'] = names[-1]
        
        # Validate address
        address = request.form.get('Address')
        if not address:
            errors['address_error'] = "Address cannot be empty"
        else:
            address_parts = address.split(',')
            if len(address_parts) < 4:
                errors['address_error'] = "Please enter a valid address (street,district,state,country)"
            else:
                valid_data['street'] = address_parts[0].strip()
                valid_data['district'] = address_parts[1].strip()
                valid_data['state'] = address_parts[2].strip()
                valid_data['country'] = address_parts[3].strip()
        
        # Validate gender
        gender = request.form.get('gender')
        if not gender:
            query="SELECT gender from students where Student_ID=%s LIMIT 1"
            mycursor.execute(query,(student_id,))
            valid_data['gender']=tuple((mycursor.fetchone()).values())[0]
        else:
            valid_data['gender'] = gender
        
        # Validate date of birth
        dob = request.form.get('DOB')
        if not dob:
            errors['dob_error'] = "Date of birth is required"
        elif dob > str(datetime.datetime.now().date()):
            errors['dob_error'] = "Date of birth cannot be in future"
        else:
            valid_data['dob'] = dob
        
        # Validate email
        email = request.form.get('studentEmail')
        if not email:
            errors['email_error'] = "Email is required"
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['email_error'] = "Invalid email format"
        else:
            valid_data['email'] = email
            
        # Validate work email
        work_mail = request.form.get('WorkMail')
        if not work_mail:
            errors['work_mail_error'] = "Work email is required"
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', work_mail):
            errors['work_mail_error'] = "Invalid work email format"
        else:
            valid_data['workMail'] = work_mail
        
        # Validate password
        password = request.form.get('password')
        if not password:
            errors['password_error'] = "Password is required"
        elif len(password) < 8:
            errors['password_error'] = "Password should be at least 8 characters"
        else:
            valid_data['password'] = password
        
        # Validate phone numbers
        valid_phones = []
        invalid_phones = []
        for i in session['phones']:
            temp=[]
            current_phone = i[0]
            new_phones = request.form.get(f'phone_{current_phone}').split(',')
            for new_phone in new_phones:
                new_phone=new_phone.strip()
                if new_phone and new_phone != current_phone:
                    # Define valid phone patterns
                    phone_patterns = [
                        r'^\+\d{1,3}\d{10}$',      # International format with no space: +1234567890, +911234567890
                        r'^\+\d{1,3}\s\d{10}$',    # International format with space: +123 4567890, +91 1234567890
                        r'^\d{10}$'                # Local format: 1234567890
                    ]
                    
                    # Check if the phone number is valid
                    is_valid = any(re.match(pattern, new_phone) for pattern in phone_patterns)
                    
                    if is_valid:
                        temp.append((current_phone, new_phone))
                    else:
                        invalid_phones.append(new_phone)
                elif new_phone == current_phone:
                    # No change, keep the current phone number
                    temp.append((current_phone, current_phone))
                elif not new_phone:
                    # Mark for deletion
                    temp.append((current_phone, None))
                # If unchanged, do nothing
            valid_phones.extend(temp)
        if invalid_phones:
            errors['phone_error'] = f"Invalid phone number format: {', '.join(invalid_phones)}"
        
        # If there are validation errors, return with error messages
        if errors:
            # Here you would typically render the form again with error messages
            # For demonstration, returning error messages
            return redirect(url_for('student',errors=errors))
        
        # Validation passed, proceed with update
        query = """
            UPDATE students 
            SET First_Name=%s, Middle_Name=%s, Last_Name=%s, Street=%s, District=%s, State=%s, Country=%s, Gender=%s, Date_of_Birth=%s, Email=%s, College_Email=%s, Password=%s 
            WHERE Student_ID=%s
        """
        values = (
            valid_data['FirstName'], 
            valid_data['MiddleName'], 
            valid_data['LastName'], 
            valid_data['street'], 
            valid_data['district'], 
            valid_data['state'], 
            valid_data['country'], 
            valid_data['gender'], 
            valid_data['dob'], 
            valid_data['email'], 
            valid_data['workMail'], 
            valid_data['password'], 
            student_id
        )
        mycursor.execute(query, values)
        mydb.commit()
        queries['student']=querymaker(query,values)
        # Process phone numbers (only valid ones)
        # First, handle updates and deletions for existing phone numbers
        remaining_phones = valid_phones.copy()

        # for current_phone, new_phone in valid_phones:
        for i in range(len(session['phones'])):
            current_phone = valid_phones[i][0]
            new_phone = valid_phones[i][1]
            if new_phone is None:
                # Delete the phone number
                query = "DELETE FROM student_phone_no WHERE Phone=%s AND Student_ID=%s"
                values = (current_phone, student_id)
                mycursor.execute(query, values)
                queries['delete_phone']=querymaker(query,values)
                remaining_phones.remove((current_phone, new_phone))

            elif new_phone != current_phone:
                # Update the phone number
                query = "UPDATE student_phone_no SET Phone=%s WHERE Phone=%s AND Student_ID=%s"
                values = (new_phone, current_phone, student_id)
                mycursor.execute(query, values)
                queries['update_phone']=querymaker(query,values)
                remaining_phones.remove((current_phone, new_phone))
            else:
                # No change, keep the current phone number
                remaining_phones.remove((current_phone, new_phone))
        # Get the current phone numbers after updates
        query = "SELECT Phone FROM student_phone_no WHERE Student_ID=%s"
        mycursor.execute(query, (student_id,))
        x=list(tuple(x.values())[0]for x in mycursor.fetchall())
        current_phones = [phone[0] for phone in x]
        queries['current_phones']=querymaker(query,(student_id,))
        # Add any new phone numbers that weren't updates
        for _, new_phone in remaining_phones:
            if new_phone:
                query = "INSERT INTO student_phone_no (Student_ID, Phone) VALUES (%s, %s)"
                mycursor.execute(query, (student_id, new_phone))
                current_phones.append(new_phone)
                queries['insert_phone']=querymaker(query,(student_id,new_phone))
        
        mydb.commit()
        # Update the session with new student data
        query = "SELECT * FROM students WHERE Student_ID=%s"
        mycursor.execute(query, (student_id,))
        updated_student = tuple((mycursor.fetchone()).values())
        session['user'] = updated_student
        # Update phone numbers in session
        query = "SELECT Phone FROM student_phone_no WHERE Student_ID=%s"
        mycursor.execute(query, (student_id,))
        session['phones'] = tuple(tuple(phone.values()) for phone in mycursor.fetchall())
        queries['phones']=querymaker(query,(student_id,))
        
        return redirect(url_for('student', message="Profile updated successfully",errors=errors,queries=queries))

@app.route('/student/fees')
def studentFees():
    
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    student_id = session['user'][0]
    def fetch_fees(query, params):
        mycursor.execute(query, params)
        return tuple(tuple(fee.values()) for fee in mycursor.fetchall())
    course_registration_fees_pending_query = """
        SELECT fees.Fee_ID, fees.Course_ID, courses.Course_Name, fees.Amount, fees.Issued_Date, fees.Type
        FROM fees
        INNER JOIN courses ON courses.Course_ID = fees.Course_ID
        WHERE fees.student_id = %s AND fees.Status = 'Pending'
    """
    course_registration_fees_pending = fetch_fees(course_registration_fees_pending_query, (student_id,))
    queries['course_registration_fees_pending']=querymaker(course_registration_fees_pending_query,(student_id,))
    course_registration_fees_paid_query = """
        SELECT fees.Fee_ID, fees.Course_ID, courses.Course_Name, fees.Amount, fees.Issued_Date, fees.Payment_Date, fees.Type, fees.Payment_ID
        FROM fees
        INNER JOIN courses ON courses.Course_ID = fees.Course_ID
        WHERE fees.student_id = %s AND fees.Status != 'Pending'
    """
    course_registration_fees_paid = fetch_fees(course_registration_fees_paid_query, (student_id,))
    queries['course_registration_fees_paid']=querymaker(course_registration_fees_paid_query,(student_id,))
    exam_fees_query_pending = """
        SELECT fees.Fee_ID, fees.Student_ID, fees.Exam_Id, fees.Amount, fees.Issued_Date, fees.Status, exams_with_courses.Exam_Type, exams_with_courses.Course_Name, exams_with_courses.Course_ID
        FROM fees
        INNER JOIN (
            SELECT exams.Exam_ID, courses.Course_Name, exams.Exam_Type, courses.Course_ID
            FROM exams
            INNER JOIN courses ON exams.Course_ID = courses.Course_ID
        ) AS exams_with_courses ON fees.Exam_ID = exams_with_courses.Exam_ID
        WHERE fees.student_id = %s AND fees.Status = 'Pending'
    """
    exam_fees_pending = fetch_fees(exam_fees_query_pending, (student_id,))
    queries['exam_fees_pending']=querymaker(exam_fees_query_pending,(student_id,))
    exam_fees_query_paid = """
        SELECT fees.Fee_ID, fees.Student_ID, fees.Exam_Id, fees.Amount, fees.Issued_Date, fees.Payment_Date, fees.Payment_ID, exams_with_courses.Exam_Type, exams_with_courses.Course_Name, exams_with_courses.Course_ID
        FROM fees
        INNER JOIN (
            SELECT exams.Exam_ID, courses.Course_Name, exams.Exam_Type, courses.Course_ID
            FROM exams
            INNER JOIN courses ON exams.Course_ID = courses.Course_ID
        ) AS exams_with_courses ON fees.Exam_ID = exams_with_courses.Exam_ID
        WHERE fees.student_id = %s AND fees.Status != 'Pending'
    """

    exam_fees_paid = fetch_fees(exam_fees_query_paid, (student_id,))
    queries['exam_fees_paid']=querymaker(exam_fees_query_paid,(student_id,))
    registration_fees_pending_query = """
        SELECT Fee_ID, Student_ID, Amount, Issued_Date, Type, Status
        FROM fees
        WHERE Student_ID = %s AND Type = 'Registration Fees' AND Status = 'Pending'
    """
    registration_fees_pending = fetch_fees(registration_fees_pending_query, (student_id,))
    queries['registration_fees_pending']=querymaker(registration_fees_pending_query,(student_id,))
    registration_fees_paid_query = """
        SELECT Fee_ID, Student_ID, Amount, Issued_Date, Type, Payment_Date, Payment_ID
        FROM fees
        WHERE Student_ID = %s AND Type = 'Registration Fees' AND Status != 'Pending'
    """
    registration_fees_paid = fetch_fees(registration_fees_paid_query, (student_id,))
    queries['registration_fees_paid']=querymaker(registration_fees_paid_query,(student_id,))
    query=request.args.get('query',None)
    if query:
        queries=None
    return render_template(
        'fees.html',
        course_registration_fees_pending=course_registration_fees_pending,
        course_registration_fees_paid=course_registration_fees_paid,
        exam_fees_pending=exam_fees_pending,
        exam_fees_paid=exam_fees_paid,
        registration_fees_pending=registration_fees_pending,
        registration_fees_paid=registration_fees_paid,
        message_success=request.args.get('message_success', None),
        message_error=request.args.get('message_error', None),
        queries=queries,
        query=query
    )


@app.route('/student/fees/pay/<int:fee_id>', methods=['POST'])
def pay_fee(fee_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        payment_ID=request.form.get(f'payment_id_{fee_id}')
        query="select count(*) from fees where Payment_ID=%s"
        mycursor.execute(query,(payment_ID,))
        if tuple((mycursor.fetchone()).values())[0]>0:
            return redirect(url_for('studentFees',message_error="Payment ID already exists",query=querymaker(query,(payment_ID,))))
        query = "UPDATE fees SET Status='Paid', Payment_Date=%s, payment_ID=%s WHERE Fee_ID=%s"
        values = (datetime.datetime.now().date(),payment_ID,fee_id)
        mycursor.execute(query, values)
        mydb.commit()
        return redirect(url_for('studentFees',message_success="Payment Successful",query=querymaker(query,values)))

@app.route('/student/register', methods=['GET', 'POST'])
def course_register():
    
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        queries={}
        student_id = request.form.get('studentId').strip()
        course_codes = request.form.get('courseCode').strip().split(',')

        mycursor.execute("SELECT Course_ID FROM enrollment WHERE Student_ID=%s", (student_id,))
        registered_courses = [x[0] for x in tuple(tuple(course.values()) for course in mycursor.fetchall())]

        new_course_codes = [code for code in course_codes if code not in registered_courses]
        if not new_course_codes:
            return "<script>alert('Already Registered for the course')</script>"

        for course_code in new_course_codes:
            mycursor.execute("SELECT Course_ID,Price FROM courses WHERE Course_ID=%s", (course_code,))
            course_id,price = tuple((mycursor.fetchone()).values())

            query = "INSERT INTO `enrollment`(`Student_ID`, `Course_ID`, `Enrolled_IN`) VALUES (%s, %s, %s)"
            values = (student_id, course_id, datetime.datetime.now().date())
            mycursor.execute(query, values)
            queries[f'course_{course_code}']=querymaker(query,values)
            query = "INSERT INTO `fees`(`Student_ID`, `Course_ID`, `Amount`, `Type`) VALUES (%s, %s, %s, %s)"
            values = (student_id, course_id, price, 'Course Registration')
            mycursor.execute(query, values)
            queries[f"fee_{course_code}"]=querymaker(query,values)
        mydb.commit()
        return redirect(url_for('studentCourses',message_enrolled="Courses Registered Successfully",queries=queries))
    return render_template('studentDashboard.html')



@app.route('/student/courses/<int:student_id>/unenroll/<string:course_id>')
def unenroll(student_id,course_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    student_id = session['user'][0]
    query = "DELETE FROM enrollment WHERE Student_ID=%s AND Course_ID=%s"
    mycursor.execute(query, (student_id, course_id))
    mydb.commit()
    message_deleted="Course Unenrolled Successfully"
    query=querymaker(query,(student_id,course_id))
    return redirect(url_for('studentCourses',message_deleted=message_deleted,query=query))

@app.route('/student/courses')
def studentCourses():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    queries={}
    # Get messages from query parameters
    message_deleted = request.args.get('message_deleted', None)
    message_enrolled = request.args.get('message_enrolled', None)
    
    # Get student ID from session
    student_id = session['user'][0]
    
    # Get available courses (not enrolled)
    available_courses_query = """
        SELECT * FROM courses 
        WHERE Course_ID NOT IN (
            SELECT Course_ID FROM enrollment WHERE Student_ID = %s
        );
    """
    mycursor.execute(available_courses_query, (student_id,))
    queries['available_courses']=querymaker(available_courses_query,(student_id,))
    # Organize available courses by semester
    available_courses = {}
    for course in tuple(tuple(course.values()) for course in mycursor.fetchall()):
        semester = course[2]
        if semester not in available_courses:
            available_courses[semester] = []
        
        available_courses[semester].append({
            "code": course[0],
            "name": course[1],
            "credits": course[3]
        })
    
    # Get enrolled courses
    enrolled_courses_query = """
        SELECT Course_ID, Course_Name, Semester, Credits 
        FROM courses 
        WHERE Course_ID IN (
            SELECT Course_ID FROM enrollment WHERE Student_ID = %s
        );
    """
    mycursor.execute(enrolled_courses_query, (student_id,))
    enrolled_courses = tuple(tuple(course.values()) for course in mycursor.fetchall())
    queries['enrolled_courses']=querymaker(enrolled_courses_query,(student_id,))
    # Render template with data
    query=request.args.get('query',None)
    new_qeuries=request.args.get('queries',None)
    if new_qeuries:
        queries=ast.literal_eval(new_qeuries)
    elif query:
        queries=None
    return render_template(
        'coursesRegistration.html',
        courses=available_courses,
        regeistered_courses=enrolled_courses,
        message_deleted=message_deleted,
        message_enrolled=message_enrolled,
        queries=queries,
        query=query
    )

@app.route('/student/results')
def studentResults():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT results.Result_ID,results.Course_ID,courses.Course_Name,exams.Exam_Date,exams.Exam_Type,results.Marks_Obtained,results.Grade,results.Status FROM results INNER JOIN courses on courses.Course_ID=results.Course_ID INNER JOIN exams ON exams.Exam_ID=results.Exam_ID WHERE Student_ID=%s AND results.Status='Unevaluated'"
    mycursor.execute(query, (session['user'][0],))
    Unevaluated_results = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['Unevaluated_results']=querymaker(query,(session['user'][0],))
    query = "SELECT results.Result_ID,results.Course_ID,courses.Course_Name,exams.Exam_Date,exams.Exam_Type,results.Marks_Obtained,results.Grade,results.Status FROM results INNER JOIN courses on courses.Course_ID=results.Course_ID INNER JOIN exams ON exams.Exam_ID=results.Exam_ID WHERE Student_ID=%s AND results.Status='Evaluated'"
    mycursor.execute(query, (session['user'][0],))
    Evaluated_results = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['Evaluated_results']=querymaker(query,(session['user'][0],))
    query = "SELECT results.Result_ID,results.Course_ID,courses.Course_Name,exams.Exam_Date,exams.Exam_Type,results.Marks_Obtained,results.Grade,results.Status FROM results INNER JOIN courses on courses.Course_ID=results.Course_ID INNER JOIN exams ON exams.Exam_ID=results.Exam_ID WHERE Student_ID=%s AND results.Status='Locked'"
    mycursor.execute(query, (session['user'][0],))
    Locked_results = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['Locked_results']=querymaker(query,(session['user'][0],))
    return render_template('student_result.html', Unevaluated_results=Unevaluated_results, Evaluated_results=Evaluated_results, Locked_results=Locked_results,queries=queries)

@app.route('/admin/approve_student/<int:student_id>')
def approve_student(student_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "UPDATE students SET Status='enrolled' WHERE Student_ID=%s"
    mycursor.execute(query, (student_id,))
    mydb.commit()
    display_query=querymaker(query,(student_id,))
    query="select `Email`, `college_email`,`password` from students where Student_ID=%s"
    mycursor.execute(query,(student_id,))
    student=tuple(mycursor.fetchone().values())
    subject = "Approval and Credentials"
    body = f"Dear Student,\n\nYour registration has been approved. Here are your credentials:\n\nEmail: {student[1]}\nPassword: {student[2]}\n\nPlease use these credentials to log in to the University Management System.\n\nBest regards,\nUniversity Management System"
    send_email(app, student[0], subject, body)
    return redirect(url_for('adminStudents',query=display_query,message_success="Application Approved"))


@app.route('/admin/remove_restriction/<int:student_id>')
def remove_restirction(student_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "UPDATE students SET Status='enrolled' WHERE Student_ID=%s"
    mycursor.execute(query, (student_id,))
    mydb.commit()
    display_query=querymaker(query,(student_id,))
    query="select `Email`, `college_email`,`password` from students where Student_ID=%s"
    mycursor.execute(query,(student_id,))
    student=tuple(mycursor.fetchone().values())
    subject = "Restriction Removed"
    body = f"Dear Student,\n\nYour account restriction has been removed. You can now access all the features of the University Management System.\n\nBest regards,\nUniversity Management System"
    send_email(app, student[0], subject, body)
    return redirect(url_for('adminStudents',message_success="Restriction Removed",query=display_query))

@app.route('/admin/restrict_student/<int:student_id>')
def restrict_student(student_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "UPDATE students SET Status='restricted' WHERE Student_ID=%s"
    mycursor.execute(query, (student_id,))
    mydb.commit()
    display_query=querymaker(query,(student_id,))
    query="select `Email` from students where Student_ID=%s"
    mycursor.execute(query,(student_id,))
    student=tuple(mycursor.fetchone().values())
    subject = "Account Restricted"
    body = f"Dear Student,\n\nYour account has been restricted for an undefined period. Please contact the administration for further details.\n\nBest regards,\nUniversity Management System"
    send_email(app, student[0], subject, body)

    return redirect(url_for('adminStudents',message_danger="Student Restricted",query=display_query))

@app.route('/admin/graduate_student/<int:student_id>')
def graduate_student(student_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "UPDATE students SET Status='graduated' WHERE Student_ID=%s"
    mycursor.execute(query, (student_id,))
    mydb.commit()

    return redirect(url_for('adminStudents',message_success="Student Graduated",query=querymaker(query,(student_id,))))

@app.route('/admin/reject_student/<int:student_id>')
def reject_student(student_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    query="select `Email` from students where Student_ID=%s"
    mycursor.execute(query,(student_id,))
    student=tuple(mycursor.fetchone().values())
    query = "DELETE FROM `students` WHERE Student_ID=%s"
    mycursor.execute(query, (student_id,))
    mydb.commit()
    subject = "Application Rejected"
    body = f"Dear Student,\n\nWe regret to inform you that your application has been rejected. Please contact the administration for further details.\n\nBest regards,\nUniversity Management System"
    send_email(app, student[0], subject, body)

    return redirect(url_for('adminStudents',message_danger="Student Discarded",query=querymaker(query,(student_id,))))


@app.route('/admin/students')
def adminStudents():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT Student_ID,CONCAT(First_Name, ' ', Middle_Name, ' ', Last_Name) AS Name, CONCAT(street, ', ', District, ', ', State, ', ', Country) AS Address, Gender, TIMESTAMPDIFF(YEAR, Date_of_Birth, CURRENT_DATE) AS Age, Email, Enrollment_Year, Graduation_Year FROM students WHERE Status='Pending';"
    mycursor.execute(query)
    pending_students = tuple(tuple(student.values()) for student in mycursor.fetchall())
    queries['pending_students']=querymaker(query,None)
    query = "SELECT Student_ID,CONCAT(First_Name, ' ', Middle_Name, ' ', Last_Name) AS Name, CONCAT(street, ', ', District, ', ', State, ', ', Country) AS Address, Gender, TIMESTAMPDIFF(YEAR, Date_of_Birth, CURRENT_DATE) AS Age, Email, Enrollment_Year, Graduation_Year FROM students WHERE Status='Enrolled';"
    mycursor.execute(query)
    enrolled_students = tuple(tuple(student.values()) for student in mycursor.fetchall())
    queries['enrolled_students']=querymaker(query,None)
    
    query = "SELECT Student_ID,CONCAT(First_Name, ' ', Middle_Name, ' ', Last_Name) AS Name, CONCAT(street, ', ', District, ', ', State, ', ', Country) AS Address, Gender, TIMESTAMPDIFF(YEAR, Date_of_Birth, CURRENT_DATE) AS Age, Email, Enrollment_Year, Graduation_Year FROM students WHERE Status='Graduated';"
    mycursor.execute(query)
    graduted_students = tuple(tuple(student.values()) for student in mycursor.fetchall())
    queries['graduted_students']=querymaker(query,None)


    query = "SELECT Student_ID,CONCAT(First_Name, ' ', Middle_Name, ' ', Last_Name) AS Name, CONCAT(street, ', ', District, ', ', State, ', ', Country) AS Address, Gender, TIMESTAMPDIFF(YEAR, Date_of_Birth, CURRENT_DATE) AS Age, Email, Enrollment_Year, Graduation_Year FROM students WHERE Status='Restricted';"
    mycursor.execute(query)
    restricated_students = tuple(tuple(student.values()) for student in mycursor.fetchall())
    queries['restricated_students']=querymaker(query,None)

    query=request.args.get('query',None)
    if query:
        queries=None
    return render_template('manage_students.html', pending_students=pending_students, enrolled_students=enrolled_students, graduted_students=graduted_students, restricated_students=restricated_students,queries=queries,query=query,message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None))

@app.route('/admin/view_student/<int:student_id>')
def view_student(student_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    details={}
    query = "SELECT * FROM students WHERE Student_ID=%s"
    mycursor.execute(query, (student_id,))
    details["student"] = tuple(mycursor.fetchone().values())
    queries['student']=querymaker(query,(student_id,))
    query="select c.Course_ID,c.Course_Name,c.Credits,c.Semester,e.Enrolled_IN from courses c INNER JOIN enrollment e on e.Course_ID=c.Course_ID WHERE e.Student_ID=%s;"
    mycursor.execute(query,(student_id,))
    details["courses"]=tuple(tuple(course.values()) for course in mycursor.fetchall())
    queries['courses']=querymaker(query,(student_id,))
    query="select Phone from student_phone_no where Student_ID=%s;"
    mycursor.execute(query,(student_id,))
    details["contacts"]=tuple(tuple(contact.values()) for contact in mycursor.fetchall())
    queries['contacts']=querymaker(query,(student_id,))
    
    query=request.args.get('query',None)
    if query:
        queries=None
    return render_template('view_student.html', **details,queries=queries,message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None),query=query)


@app.route('/admin/view_student/<int:student_id>/UnEnroll/<string:course_id>')
def UnEnroll(student_id, course_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM `enrollment` WHERE Student_ID=%s AND Course_ID=%s"
    mycursor.execute(query, (student_id, course_id))
    mydb.commit()
    
    return redirect(url_for('view_student', student_id=student_id,query=querymaker(query,(student_id,course_id)),message_danger="Course Unenrolled"))


@app.route('/admin/courses/filter_sorted',methods=['POST'])
def filter_sorted():
    if 'user' not in session:
        return redirect(url_for('login'))
    filters={}
    sorted_by={}
    if request.method == 'POST':
        # Extract filter values from form
        if request.form.get('course_id_check'):
            filters['Course_ID'] = request.form.get('course_id')
        if request.form.get('course_name_check'):
            filters['Course_Name'] = request.form.get('course_name')
        if request.form.get('semester_check'):
            filters['Semester'] = request.form.get('semester')
        if request.form.get('credits_check'):
            filters['Credits'] = request.form.get('credits')
        if request.form.get('price_check'):
            filters['Price'] = request.form.get('price_id')
        # Extract sorting parameters
        if request.form.get('sort_by_course_id_check'):
            sorted_by['Course_ID'] = request.form.get('sort_by_course_id')
        if request.form.get('sort_by_course_name_check'):
            sorted_by['Course_Name'] = request.form.get('sort_by_course_id_name')

        if request.form.get('sort_by_semester_check'):
            sorted_by['Semester'] = request.form.get('sort_by_semester')
        if request.form.get('sort_by_credits_check'):
            sorted_by['Credits'] = request.form.get('sort_by_credits')
        if request.form.get('sort_by_price_check'):
            sorted_by['Price'] = request.form.get('sort_by_price')



        order_clauses = []
        for field, direction in sorted_by.items():
            if direction == 'Ascending':
                order_clauses.append(f"{field} ASC")
            elif direction == 'Descending':
                order_clauses.append(f"{field} DESC")
        # Build query with filters
        query = "SELECT * FROM courses"
        
        # Add WHERE clause if filters exist
        if filters:
            query += " WHERE " + " AND ".join([f"{key} LIKE %s" for key in filters.keys()])
            # Add wildcard for partial matches
            values = tuple([f"%{value}%" for value in filters.values()])
        else:
            values = ()
            
        # Add ORDER BY clause if sorting parameters exist
        if order_clauses:
            query += " ORDER BY " + ", ".join(order_clauses)
        # Execute query with filter values
        mycursor.execute(query, values)
        # Execute query with filter values
        courses = tuple(tuple(course.values()) for course in mycursor.fetchall())
        
        # Create a display version of the query with actual values for debugging
        display_query = querymaker(query, values)
        
        return render_template('manage_courses.html', courses=courses, query=display_query, message="Filtered and Sorted")
    query = "SELECT * FROM courses"
    mycursor.execute(query)
    courses = tuple(tuple(course.values()) for course in mycursor.fetchall())    
    return render_template('manage_courses.html', courses=courses)



@app.route('/admin/courses')
def adminCourses():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "SELECT * FROM courses"
    mycursor.execute(query)
    display_query = request.args.get('query', querymaker(query,None))
    message = request.args.get('message', None)
    courses = tuple(tuple(course.values()) for course in mycursor.fetchall())
    return render_template('manage_courses.html', courses=courses, query=display_query, message=message)

@app.route('/admin/courses/add_course',methods=['POST'])
def add_course():
    if 'user' not in session:
        return redirect(url_for('login'))
    id = request.form.get('course_id')
    name = request.form.get('course_name')
    credits = request.form.get('credits')
    price = request.form.get('price')
    semester = request.form.get('semester')
    mycursor.execute("SELECT * FROM courses WHERE Course_ID=%s", (id,))
    values=mycursor.fetchone()
    if values:
        return "Course ID already exists"
    query = "INSERT INTO `courses`(`Course_ID`, `Course_Name`, `Credits`, `Semester`,`Price`) VALUES (%s, %s, %s, %s,%s)"
    values = (id, name, credits, semester, price)
    mycursor.execute(query, values)
    mydb.commit()
    return redirect(url_for('adminCourses'))

@app.route('/admin/course/update/<string:course_id>', methods=['GET', 'POST'])
def update_course(course_id):
    
    if 'user' not in session:
        return redirect(url_for('login'))
    new_course_id = request.form.get(f"course_id_{course_id}")
    new_course_name = request.form.get(f"course_name_{course_id}")
    new_course_credits = request.form.get(f"credits_{course_id}")
    new_course_semester = request.form.get(f"semester_{course_id}")
    new_course_price = request.form.get(f"price_{course_id}")
    query=None
    if(new_course_id!=course_id):
        query="SELECT * FROM courses WHERE Course_ID=%s"
        mycursor.execute(query,(new_course_id,))
        
        course=tuple((mycursor.fetchone()).values())
        if course:
            return "can't update course id as it already exists"
        else:
            query="UPDATE courses SET  Course_ID=%s,Course_Name=%s, Credits=%s, Semester=%s,price=%s WHERE Course_ID=%s"
            values=(new_course_id,new_course_name,new_course_credits,new_course_semester,new_course_price,course_id)
            mycursor.execute(query,values)
            mydb.commit()
    else:
        query="UPDATE courses SET  Course_Name=%s, Credits=%s, Semester=%s,price=%s WHERE Course_ID=%s"
        values=(new_course_name,float(new_course_credits),new_course_semester,new_course_price,course_id)
        mycursor.execute(query,values)
        mydb.commit()
    display_query=querymaker(query,values)    
    return redirect(url_for('adminCourses',query=display_query,message="Course Updated Successfully"))
        
@app.route('/admin/course/delete/<string:course_id>')
def delete_course(course_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM `courses` WHERE Course_ID=%s"
    mycursor.execute(query, (course_id,))
    display_query=querymaker(query,(course_id,))
    mydb.commit()
    return redirect(url_for('adminCourses',query=display_query,message="Course Deleted Successfully"))

@app.route('/admin/faculty')
def adminFaculty():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query="SELECT faculty.Faculty_ID, CONCAT(faculty.First_Name, ' ', COALESCE(faculty.Middle_Name, ''), ' ', faculty.Last_Name) AS Name, faculty.Date_of_Joining, faculty.Designation, faculty.Mail, faculty.Official_Mail, courses.Course_Name, department.Department_Name FROM faculty INNER JOIN courses ON courses.Course_ID = faculty.Course_ID INNER JOIN department ON department.Department_ID = faculty.Department_ID WHERE faculty.Status = 'Pending';"
    mycursor.execute(query)
    pending_faculty=tuple(tuple(faculty.values()) for faculty in mycursor.fetchall())
    queries['pending_query']=querymaker(query,None)
    query="SELECT faculty.Faculty_ID, CONCAT(faculty.First_Name, ' ', COALESCE(faculty.Middle_Name, ''), ' ', faculty.Last_Name) AS Name, faculty.Date_of_Joining, faculty.Designation, faculty.Mail, faculty.Official_Mail, courses.Course_Name, department.Department_Name FROM faculty INNER JOIN courses ON courses.Course_ID = faculty.Course_ID INNER JOIN department ON department.Department_ID = faculty.Department_ID WHERE faculty.Status = 'Active';"
    mycursor.execute(query)
    active_faculty=tuple(tuple(faculty.values()) for faculty in mycursor.fetchall())
    queries['active_query']=querymaker(query,None)
    display_query=request.args.get('query',None)
    message_success=request.args.get('message_success',None)
    message_danger=request.args.get('message_danger',None)
    if display_query:
        queries=None
    return render_template('manage_faculty.html', pending=pending_faculty, active=active_faculty, query=display_query,queries=queries,message_danger=message_danger,message_success=message_success)


@app.route('/admin/faculty/view_faculty/<int:faculty_id>')
def view_faculty(faculty_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "SELECT faculty.Faculty_ID, CONCAT(faculty.First_Name,' ', faculty.Middle_Name, ' ', faculty.Last_Name) AS Name, faculty.Date_of_Joining, faculty.Designation, faculty.Mail, faculty.Official_Mail, faculty.Course_ID, courses.Course_Name,faculty.Department_ID,department.Department_Name,faculty.Status FROM faculty INNER JOIN courses ON courses.Course_ID =faculty.Course_ID INNER JOIN department ON department.Department_ID=faculty.Department_ID WHERE faculty.Faculty_ID=%s;"
    mycursor.execute(query, (faculty_id,))
    display_query=querymaker(query,(faculty_id,))
    result = tuple(tuple(result.values()) for result in mycursor.fetchall())
    if not result:
        return "Faculty not found", 404
    faculty = result[0]
    query = "SELECT Phone FROM faculty_phone_no WHERE Faculty_ID=%s"
    mycursor.execute(query, (faculty_id,))
    phones = tuple(tuple(phone.values()) for phone in mycursor.fetchall())
    return render_template('view_faculty.html', faculty=faculty, phones=phones,query=display_query)


@app.route('/admin/faculty/approve_faculty/<int:faculty_id>')
def approve_faculty(faculty_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "UPDATE faculty SET Status='Active' WHERE Faculty_ID=%s"
    mycursor.execute(query, (faculty_id,))
    mydb.commit()
    display_query=querymaker(query,(faculty_id,))
    query="select `Mail`,`Official_Mail`,`Password` from faculty where Faculty_ID=%s"
    mycursor.execute(query,(faculty_id,))
    faculty=tuple((mycursor.fetchone()).values())
    subject = "Approval and Credentials"
    body = f"Dear Faculty,\n\nYour registration has been approved. Here are your credentials:\n\nEmail: {faculty[1]}\nPassword: {faculty[2]}\n\nPlease use these credentials to log in to the University Management System.\n\nBest regards,\nUniversity Management System"
    send_email(app, faculty[0], subject, body)
    return redirect(url_for('adminFaculty',query=display_query,message_success="Faculty Approved"))


@app.route('/admin/faculty/reject_faculty/<int:faculty_id>')
def reject_faculty(faculty_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query="select `Mail` from faculty where Faculty_ID=%s"
    mycursor.execute(query,(faculty_id,))
    faculty=tuple((mycursor.fetchone()).values())

    query = "DELETE FROM faculty WHERE Faculty_ID=%s"
    mycursor.execute(query, (faculty_id,))
    mydb.commit()
    subject = "Application Rejected"
    body = f"Dear Faculty,\n\nWe regret to inform you that your application has been rejected. Please contact the administration for further details.\n\nBest regards,\nUniversity Management System"
    send_email(app, faculty[0], subject, body)
    return redirect(url_for('adminFaculty',query=querymaker(query,(faculty_id,)),message_danger="Faculty Rejected"))

@app.route('/admin/faculty/delete_faculty/<int:faculty_id>')
def delete_faculty(faculty_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM faculty WHERE Faculty_ID=%s"
    mycursor.execute(query, (faculty_id,))
    mydb.commit()

    return redirect(url_for('adminFaculty',query=querymaker(query,(faculty_id,)),message_danger="Faculty Deleted"))

@app.route('/admin/departments')
def adminDepartments():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT department.Department_ID, department.Department_Name, department.Head_of_Department AS HOD_ID, CONCAT(hod.First_Name, ' ', COALESCE(hod.Middle_Name, ''), ' ', hod.Last_Name) AS HOD_Name, COUNT(faculty.Faculty_ID) AS FacultyCount FROM department INNER JOIN faculty ON faculty.Department_ID = department.Department_ID LEFT JOIN faculty AS hod ON department.Head_of_Department = hod.Faculty_ID WHERE faculty.Status != 'Pending' GROUP BY department.Department_ID, department.Department_Name, department.Head_of_Department, hod.First_Name, hod.Middle_Name, hod.Last_Name;"
    mycursor.execute(query)
    active_departments = tuple(tuple(department.values()) for department in mycursor.fetchall())
    queries['active_query']=querymaker(query,None)
    query = "SELECT Department_ID,Department_Name FROM `department` WHERE Department_ID NOT IN (SELECT department.Department_ID FROM department INNER JOIN faculty ON faculty.Department_ID = department.Department_ID WHERE faculty.Status != 'Pending' GROUP BY department.Department_ID, department.Department_Name, department.Head_of_Department);"
    mycursor.execute(query)
    inactive_departments = tuple(tuple(department.values()) for department in mycursor.fetchall())
    queries['inctive_query']=querymaker(query,None)
    query=request.args.get('query',None)
    if query:
        queries=None      
    return render_template('manage_department.html', active_departments=active_departments, inactive_departments=inactive_departments,queries=queries,query=query,message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None),department_id_error=request.args.get('department_id_error',None),department_name_error=request.args.get('department_name_error',None),department_id_error_form=request.args.get('department_id_error_form',None),department_name_error_form=request.args.get('department_name_error_form',None),message_danger_form=request.args.get('message_danger_form',None),department_id_form=request.args.get('department_id_form',None),department_name_form=request.args.get('department_name_form',None))     


@app.route('/admin/departments/add_department', methods=['POST'])
def add_department():
    if 'user' not in session:
        return redirect(url_for('login'))
    department_id = request.form.get('department_id')
    department_name_error_form=None
    department_id_error_form=None
    if not department_id:
        department_id_error_form = "Department ID cannot be empty"
    department_name = request.form.get('department_name')
    if not department_name:
        department_name_error_form = "Department Name cannot be empty"
    if department_id_error_form or department_name_error_form:
        return redirect(url_for('adminDepartments',department_id_error_form=department_id_error_form,department_name_error_form=department_name_error_form,department_id_form=department_id,department_name_form=department_name))


    mycursor.execute("SELECT * FROM department WHERE Department_ID=%s", (department_id,))
    if mycursor.fetchone():
        return redirect(url_for('adminDepartments',department_id_error_form="Department ID already exists",department_id_form=department_id,department_name_form=department_name))
    
    mycursor.execute("SELECT * FROM department WHERE Department_Name=%s", (department_name,))
    if mycursor.fetchone():
        return redirect(url_for('adminDepartments',department_name_error_form="Department Name already exists",department_id_form=department_id,department_name_form=department_name))
    
    query = "INSERT INTO `department`(`Department_ID`, `Department_Name`) VALUES (%s, %s)"
    values = (department_id, department_name)
    mycursor.execute(query, values)
    mydb.commit()
    return redirect(url_for('adminDepartments',query=querymaker(query,values),message_success="Department Added Successfully"))

@app.route('/admin/departments/update/<string:department_id>', methods=['POST'])
def update_department(department_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query="SELECT Department_Name FROM department WHERE Department_ID=%s"
    mycursor.execute(query,(department_id,))
    department_name=tuple((mycursor.fetchone()).values())[0] 
    # Get form data
    new_department_id = request.form.get("department_id", "").strip()
    new_department_name = request.form.get("department_name", "").strip()
    
    message_success = None
    message_danger = None
    query = None
    values = None
    department_id_error = None
    department_name_error= None    
    # Validate inputs
    if not new_department_id:
        department_id_error = "Department ID cannot be empty"
    if not new_department_name:
        department_name_error = "Department Name cannot be empty"
    
    # If validation passes, proceed with update
    if not department_id_error and not department_name_error:
        flag = False
        
        # Check if the department ID is being changed
        if new_department_id != department_id:
            # Check if new ID already exists
            mycursor.execute("SELECT count(*) FROM department WHERE Department_ID=%s", (new_department_id,))
            if tuple((mycursor.fetchone()).values())[0] > 0:
                message_danger = "Department ID already exists"
                flag = True
        
        # Check if the department name is being changed and if it already exists
        if new_department_name != department_name:
            mycursor.execute("SELECT count(*) FROM department WHERE Department_Name=%s AND Department_ID!=%s", (new_department_name, department_id))
            if tuple((mycursor.fetchone()).values())[0] > 0:
                message_danger = "Department Name already exists"
                flag = True
        
        if not flag:
            if new_department_id != department_id:
                # Update both ID and name
                query = "UPDATE department SET Department_ID=%s, Department_Name=%s WHERE Department_ID=%s"
                values = (new_department_id, new_department_name, department_id)
            else:
                # Update name only
                query = "UPDATE department SET Department_Name=%s WHERE Department_ID=%s"
                values = (new_department_name, department_id)
                
            mycursor.execute(query, values)
            mydb.commit()
            message_success = "Department updated successfully"
    
        query=querymaker(query,values)
        return redirect(url_for('adminDepartments',query=query,message_success=message_success,message_danger=message_danger,department_id_error=department_id_error,department_name_error=department_name_error))
    
    return redirect(url_for('adminDepartments',query=query,message_success=message_success,message_danger=message_danger,department_id_error=department_id_error,department_name_error=department_name_error))





@app.route('/admin/departments/delete/<string:department_id>')
def delete_department(department_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM `department` WHERE Department_ID=%s"
    mycursor.execute(query, (department_id,))
    mydb.commit()
    query=querymaker(query,(department_id,))
    return redirect(url_for('adminDepartments',query=query,message_danger="Department Deleted Successfully"))



@app.route('/admin/view_department/<string:department_id>', methods=['GET', 'POST'])
def view_department(department_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query="SELECT department.Department_ID, department.Department_Name, department.Head_of_Department AS HOD_ID, CONCAT(hod.First_Name, ' ', COALESCE(hod.Middle_Name, ''), ' ', hod.Last_Name) AS HOD_Name, COUNT(faculty.Faculty_ID) AS Faculty_Count FROM department INNER JOIN faculty ON department.Department_ID = faculty.Department_ID LEFT JOIN faculty AS hod ON department.Head_of_Department = hod.Faculty_ID WHERE department.Department_ID = %s AND faculty.Status='Active' GROUP BY department.Department_ID, department.Department_Name, department.Head_of_Department, hod.First_Name, hod.Middle_Name, hod.Last_Name;"
    mycursor.execute(query, (department_id,))
    queries['department_query']=querymaker(query,(department_id,))
    try:
        department = (tuple(tuple(department.values()) for department in mycursor.fetchall()))[0]
    except :
        department=mycursor.fetchone()
    query = "SELECT Faculty_ID, CONCAT(First_Name, ' ', COALESCE(Middle_Name, ''), ' ', Last_Name) AS Name, Designation, Mail, Official_Mail FROM faculty WHERE Department_ID=%s AND Status='Active'"
    mycursor.execute(query, (department_id,))
    faculties= tuple(tuple(faculty.values()) for faculty in mycursor.fetchall())
    queries['faculty_query']=querymaker(query,(department_id,))
    query=request.args.get('query',None)
    if query:
        queries=None
    faculty_name_error=request.args.get('faculty_name_error',None)
    faculty_id_error=request.args.get('faculty_id_error',None)
    faculty_mail_error=request.args.get('faculty_mail_error',None)
    if faculty_id_error or faculty_name_error or faculty_mail_error:
        query=None
    return render_template('view_department.html', department=department, faculties=faculties,queries=queries,query=query,department_id_error=request.args.get('department_id_error',None),faculty_name_error=faculty_name_error,faculty_id_error=faculty_id_error,faculty_mail_error=faculty_mail_error,message_danger=request.args.get('message_danger',None),message_success=request.args.get('message_success',None),message_success_hod=request.args.get('message_success_hod',None))


@app.route('/admin/view_department/<string:department_id>/appoint_HOD', methods=['GET', 'POST'])
def appoint_HOD(department_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    faculty_id = request.form.get('hod_id')
    query = "UPDATE department SET Head_of_Department=%s WHERE Department_ID=%s"
    mycursor.execute(query, (faculty_id, department_id))
    mydb.commit()
    query=querymaker(query,(faculty_id,department_id))
    return redirect(url_for('view_department', department_id=department_id,message_success_hod="HOD Appointed Successfully",query=query))


@app.route('/admin/view_department/<string:department_id>/update_faculty/<string:faculty_id>', methods=['GET', 'POST'])
def update_faculty_(department_id, faculty_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    new_faculty_id = request.form.get(f"faculty_id_{faculty_id}")
    new_faculty_name = request.form.get(f"faculty_name_{faculty_id}")
    new_faculty_mail = request.form.get(f"faculty_mail_{faculty_id}")

    faculty_name_error = None
    faculty_id_error = None
    faculty_mail_error = None

    # Validate faculty name
    new_faculty_name_parts = new_faculty_name.strip().split(' ')
    if len(new_faculty_name_parts) == 0:
        faculty_name_error = "Faculty Name cannot be empty"
    elif len(new_faculty_name_parts[0]) < 3:
        faculty_name_error = "Faculty Name should be at least 3 characters"
    else:
        FirstName = new_faculty_name_parts[0]
        MiddleName = ' '.join(new_faculty_name_parts[1:-1]) if len(new_faculty_name_parts) > 2 else ''
        LastName = new_faculty_name_parts[-1] if len(new_faculty_name_parts) > 1 else ''

    # Validate faculty email
    if not new_faculty_mail:
        faculty_mail_error = "Faculty Mail cannot be empty"
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_faculty_mail):
        faculty_mail_error = "Invalid email format"

    if faculty_name_error or faculty_id_error or faculty_mail_error:
        return redirect(url_for('view_department', department_id=department_id, faculty_name_error=faculty_name_error, faculty_id_error=faculty_id_error, faculty_mail_error=faculty_mail_error))

    if new_faculty_id != faculty_id:
        mycursor.execute("SELECT * FROM faculty WHERE Faculty_ID=%s", (new_faculty_id,))
        if tuple((mycursor.fetchone()).values()):
            return redirect(url_for('view_department', department_id=department_id, faculty_id_error="Faculty ID already exists"))
        query = "UPDATE faculty SET Faculty_ID=%s, First_Name=%s, Middle_Name=%s, Last_Name=%s, Mail=%s WHERE Faculty_ID=%s"
        values = (new_faculty_id, FirstName, MiddleName, LastName, new_faculty_mail, faculty_id)
    else:
        query = "UPDATE faculty SET First_Name=%s, Middle_Name=%s, Last_Name=%s, Mail=%s WHERE Faculty_ID=%s"
        values = (FirstName, MiddleName, LastName, new_faculty_mail, faculty_id)

    mycursor.execute(query, values)
    mydb.commit()

    return redirect(url_for('view_department', department_id=department_id,query=querymaker(query,values),message_success="Faculty Updated Successfully"))



@app.route('/admin/view_department/<string:department_id>/delete_faculty/<int:faculty_id>', methods=['GET', 'POST'])
def delete_faculty_(department_id, faculty_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    # Delete the specified faculty
    query = "DELETE FROM faculty WHERE Faculty_ID=%s"
    mycursor.execute(query, (faculty_id,))
    mydb.commit()

    # Check if there are any faculty left in the department
    check_query = "SELECT COUNT(*) FROM faculty WHERE Department_ID=%s"
    mycursor.execute(check_query, (department_id,))
    count = tuple((mycursor.fetchone()).values())[0]  # Fetch the count value

    if count == 0:
        # If no faculty are left, redirect to adminDepartments
        return redirect(url_for('adminDepartments'))

    # Otherwise, redirect back to the view_department page
    return redirect(url_for('view_department', department_id=department_id,query=querymaker(query,(faculty_id,)),message_danger="Faculty Deleted Successfully"))

@app.route('/admin/fees/delete/<int:fee_id>')
def delete_fee(fee_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM fees WHERE Fee_ID=%s"
    mycursor.execute(query, (fee_id,))
    mydb.commit()
    return redirect(url_for('adminFees'))

@app.route('/admin/fees/update/<int:fee_id>', methods=['POST'])
def update_fee(fee_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        amount = request.form.get(f'amount_{fee_id}')
        issued_date = request.form.get(f'issued_date_{fee_id}')
        fee_type = request.form.get(f'type_{fee_id}')
        payment_date = request.form.get(f'payment_date_{fee_id}')
        status = request.form.get(f'status_{fee_id}')
        if status not in ['Pending', 'Paid']:
            return "Invalid status value"
        payment_id = request.form.get(f'payment_id_{fee_id}')

        query = """
            UPDATE fees 
            SET  Amount=%s, Issued_Date=%s, Type=%s, Payment_Date=%s, Status=%s, Payment_ID=%s 
            WHERE Fee_ID=%s
        """
        values = (amount, issued_date, fee_type, payment_date, status, payment_id, fee_id)
        mycursor.execute(query, values)
        mydb.commit()
        return redirect(url_for('adminFees'))
    

@app.route('/admin/fees/filter/', methods=['POST'])
def filter_fees():
    if 'user' not in session:
        return redirect(url_for('login'))
    filters = {}
    sorted_by = {}
    if request.method == 'POST':
        # Extract filter values from form
        if request.form.get('fee_id_check'):
            filters['Fee_ID'] = request.form.get('fee_id')
        if request.form.get('student_id_check'):
            filters['Student_ID'] = request.form.get('student_id')
        if request.form.get('exam_id_check'):
            filters['Exam_ID'] = request.form.get('exam_id')
        if request.form.get('course_id_check'):
            filters['Course_ID'] = request.form.get('course_id')
        if request.form.get('amount_check'):
            filters['Amount'] = request.form.get('amount')
        if request.form.get('issued_date_check'):
            filters['Issued_Date'] = request.form.get('issued_date')
        if request.form.get('type_check'):
            filters['Type'] = request.form.get('type')
        if request.form.get('payment_date_check'):
            filters['Payment_Date'] = request.form.get('payment_date')
        if request.form.get('status_check'):
            filters['Status'] = request.form.get('status')
        if request.form.get('payment_id_check'):
            filters['Payment_ID'] = request.form.get('payment_id')
            
        # Extract sorting parameters
        if request.form.get('sort_by_fee_id_check'):
            sorted_by['Fee_ID'] = request.form.get('sort_by_fee_id')
        if request.form.get('sort_by_student_id_check'):
            sorted_by['Student_ID'] = request.form.get('sort_by_student_id')
        if request.form.get('sort_by_amount_check'):
            sorted_by['Amount'] = request.form.get('sort_by_amount')
        if request.form.get('sort_by_issued_date_check'):
            sorted_by['Issued_Date'] = request.form.get('sort_by_issued_date')
        if request.form.get('sort_by_type_check'):
            sorted_by['Type'] = request.form.get('sort_by_type')
        if request.form.get('sort_by_status_check'):
            sorted_by['Status'] = request.form.get('sort_by_status')
            
        # Add order by clause if sorting is specified
        order_clauses = []
        for field, direction in sorted_by.items():
            if direction == 'Ascending':
                order_clauses.append(f"{field} ASC")
            elif direction == 'Descending':
                order_clauses.append(f"{field} DESC")
                
        # Build query with filters
        query = "SELECT * FROM fees"
        
        # Add WHERE clause if filters exist
        if filters:
            query += " WHERE " + " AND ".join([f"{key} LIKE %s" for key in filters.keys()])
            # Add wildcard for partial matches
            values = tuple([f"%{value}%" for value in filters.values()])
        else:
            values = ()
            
        # Add ORDER BY clause if sorting parameters exist
        if order_clauses:
            query += " ORDER BY " + ", ".join(order_clauses)
            
        # Execute query with filter values
        mycursor.execute(query, values)
        fees = tuple(tuple(fee.values()) for fee in mycursor.fetchall())
        
        # Create a display version of the query with actual values for debugging
        display_query = querymaker(query, values)
        
        return render_template('manage_fees.html', fees=fees, query=display_query, message="Filtered and Sorted")
    
    query = "SELECT * FROM fees"
    mycursor.execute(query)
    fees = tuple(tuple(fee.values()) for fee in mycursor.fetchall())
    return render_template('manage_fees.html', fees=fees)
    



@app.route('/admin/fees')
def adminFees():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "SELECT * FROM fees"
    mycursor.execute(query)
    fees = tuple(tuple(fee.values()) for fee in mycursor.fetchall())
    display_query = request.args.get('query', querymaker(query, None))
    return render_template('manage_fees.html', fees=fees, query=display_query)
@app.route('/admin/exams')
def adminExams():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT exams.Exam_ID, exams.Course_ID, exams.Exam_Date, exams.Exam_Duration, exams.Exam_Type, exams.Venue, exams.Status,courses.Course_Name,courses.Credits FROM exams INNER JOIN courses ON exams.Course_ID=courses.Course_ID WHERE exams.Exam_Date>=CURRENT_DATE ;"
    mycursor.execute(query)
    upcoming_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['upcoming_exams_query']=querymaker(query,None)
    query = "SELECT exams.Exam_ID, exams.Course_ID, exams.Exam_Date, exams.Exam_Duration, exams.Exam_Type, exams.Venue, exams.Status,courses.Course_Name,courses.Credits FROM exams INNER JOIN courses ON exams.Course_ID=courses.Course_ID WHERE exams.Exam_Date<CURRENT_DATE AND exams.Status!='Locked';"
    mycursor.execute(query)
    recent_Unevaluated_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['recent_Unevaluated_exams_query']=querymaker(query,None)
    query = "SELECT exams.Exam_ID, exams.Course_ID, exams.Exam_Date, exams.Exam_Duration, exams.Exam_Type, exams.Venue, exams.Status,courses.Course_Name,courses.Credits FROM exams INNER JOIN courses ON exams.Course_ID=courses.Course_ID WHERE exams.Exam_Date<CURRENT_DATE AND exams.Status='Locked';"
    mycursor.execute(query)
    recent_Evaluated_exams = tuple(tuple(exam.values()) for exam in mycursor.fetchall())
    queries['recent_Evaluated_exams_query']=querymaker(query,None)
    display_query=request.args.get('query',None)
    if  display_query:
        queries=None
    errors = ast.literal_eval(request.args.get('errors', '{}'))
    if errors:
        queries=None
    return render_template('manage_exams.html', upcoming_exams=upcoming_exams, recent_Unevaluated_exams=recent_Unevaluated_exams, recent_Evaluated_exams=recent_Evaluated_exams,queries=queries,query=display_query,errors=errors,message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None))

@app.route('/admin/exams/update_exam/<int:exam_id>/', methods=['POST'])
def update_exam_admin(exam_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    errors={}
    new_exam_id = int(request.form.get(f'exam_id_{exam_id}'))
    new_exam_date = request.form.get(f'exam_date_{exam_id}')
    new_exam_duration = request.form.get(f'exam_duration_{exam_id}')
    if float(new_exam_duration)<=0:
        errors['exam_duration_error']="Exam Duration cannot be less than or equal to 0"
    new_exam_type = request.form.get(f'exam_type_{exam_id}')
    if new_exam_date<datetime.datetime.now().strftime('%Y-%m-%d'):
        errors['exam_date_error']="Exam Date cannot be in the past"
    if not new_exam_type:
        query = "SELECT Exam_Type FROM exams WHERE Exam_ID=%s"
        mycursor.execute(query, (exam_id,))
        current_exam_type = tuple((mycursor.fetchone()).values())
        if current_exam_type:
            new_exam_type = current_exam_type[0]
    new_venue = request.form.get(f'venue_{exam_id}')
    if not new_venue:
        errors['venue_error'] = "Venue cannot be empty"
    course_id = request.form.get(f'course_id_{exam_id}')
    if new_exam_id != exam_id:
        if exam_exists(new_exam_id):
            errors['exam_id_error'] = "Exam ID already exists"
        if exam_type_exists(course_id, new_exam_type, new_exam_id):
            errors['exam_type_error'] = "Exam Type already exists"
        update_exam(new_exam_id, new_exam_date, new_exam_duration, new_exam_type, new_venue, exam_id)
    else:
        if exam_type_exists(course_id, new_exam_type, exam_id):
            errors['exam_type_error'] = "Exam Type already exists"
        if errors:
            return redirect(url_for('adminExams',errors=errors))
        query=update_exam(None, new_exam_date, new_exam_duration, new_exam_type, new_venue, exam_id)

    return redirect(url_for('adminExams',message_success="Exam Updated Successfully",query=query))

def exam_exists(exam_id):
    query = "SELECT * FROM exams WHERE Exam_ID=%s"
    mycursor.execute(query, (exam_id,))
    return tuple((mycursor.fetchone()).values()) is not None

def exam_type_exists(course_id, exam_type, exam_id):
    query = "SELECT COUNT(*) FROM exams WHERE Course_ID=%s AND Exam_Type=%s AND Exam_ID!=%s"
    mycursor.execute(query, (course_id, exam_type, exam_id))
    return tuple((mycursor.fetchone()).values())[0] > 0

def update_exam(new_exam_id, new_exam_date, new_exam_duration, new_exam_type, new_venue, exam_id):
    if new_exam_id:
        query = "UPDATE exams SET Exam_ID=%s, Exam_Date=%s, Exam_Duration=%s, Exam_Type=%s, Venue=%s WHERE Exam_ID=%s"
        values = (new_exam_id, new_exam_date, new_exam_duration, new_exam_type, new_venue, exam_id)
    else:
        query = "UPDATE exams SET Exam_Date=%s, Exam_Duration=%s, Exam_Type=%s, Venue=%s WHERE Exam_ID=%s"
        values = (new_exam_date, new_exam_duration, new_exam_type, new_venue, exam_id)
    mycursor.execute(query, values)
    mydb.commit()
    return querymaker(query, values)


@app.route('/admin/exams/delete_exam/<int:exam_id>/')
def delete_exam_admin(exam_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "DELETE FROM exams WHERE Exam_ID=%s"
    mycursor.execute(query, (exam_id,))
    mydb.commit()
    
    return redirect(url_for('adminResults',query=querymaker(query,(exam_id,)),message_danger="Exam Deleted Successfully"))

@app.route('/admin/results/<int:exam_id>/view', methods=['GET', 'POST'])
def view_results_admin(exam_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT results.Result_ID,results.Student_ID,CONCAT(students.First_Name,' ',students.Middle_Name,' ',students.Last_Name) AS Name,results.Marks_Obtained,results.Grade from results INNER JOIN students ON results.Student_ID=students.Student_ID INNER JOIN courses on results.Course_ID=courses.Course_ID WHERE results.Exam_ID=%s;"
    mycursor.execute(query, (exam_id,))
    results = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['results_query']=querymaker(query,(exam_id,))
    query="SELECT DISTINCT courses.Course_Name, courses.Credits FROM courses INNER JOIN results ON results.Course_ID=courses.Course_ID WHERE results.Exam_ID=%s;"
    mycursor.execute(query,(exam_id,))  
    course=(tuple(tuple(course.values()) for course in mycursor.fetchall()))[0]
    queries['course_query']=querymaker(query,(exam_id,))
    return render_template('view_result_admin.html', results=results, exam_id=exam_id,course=course,queries=queries)

@app.route('/admin/results/')
def adminResults():
    if 'user' not in session:
        return redirect(url_for('login'))
    queries={}
    query = "SELECT exams.Exam_ID, exams.Course_ID, exams.Exam_Date, exams.Exam_Duration, exams.Exam_Type, exams.Venue, exams.Status,courses.Course_Name,courses.Credits FROM exams INNER JOIN courses ON exams.Course_ID=courses.Course_ID WHERE exams.Exam_Date<CURRENT_DATE AND exams.Status!='Locked';"
    mycursor.execute(query)
    Unevaluated_Result = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['Unevaluated_Result']=querymaker(query,None)
    query = "SELECT exams.Exam_ID, exams.Course_ID, exams.Exam_Date, exams.Exam_Duration, exams.Exam_Type, exams.Venue, exams.Status,courses.Course_Name,courses.Credits FROM exams INNER JOIN courses ON exams.Course_ID=courses.Course_ID WHERE exams.Exam_Date<CURRENT_DATE AND exams.Status='Locked';"
    mycursor.execute(query)
    Evautated_Result = tuple(tuple(result.values()) for result in mycursor.fetchall())
    queries['Evautated_Result']=querymaker(query,None)
    query=request.args.get('query',None)
    if query:
        queries=None
    return render_template('manage_results.html', Evautated_Result=Evautated_Result, Unevaluated_Result=Unevaluated_Result,query=query,queries=queries,message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None)) 

@app.route('/admin/<int:admin_id>/delete')
def delete_admin(admin_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query="DELETE FROM admin WHERE Admin_ID=%s"
    mycursor.execute(query, (admin_id,))
    mydb.commit()
    return redirect(url_for('view_admin',admin_id=session['user'][0],query=querymaker(query,(admin_id,)),message_danger="Admin Deleted Successfully"))
@app.route('/admin/<int:admin_id>/update', methods=['POST'])
def update_admin(admin_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    errors={}
    new_name = request.form.get('admin_name')
    if not new_name:
        errors['name_error'] = "Name cannot be empty"
    elif len(new_name) < 3:
        errors['name_error'] = "Name should be at least 3 characters"
    
    new_email = request.form.get('admin_email')
    if not new_email:
        errors['email_error'] = "Email cannot be empty"
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@thapar.edu$', new_email):
        errors['email_error'] = "Invalid email format"
    new_password = request.form.get('admin_password')
    if not new_password:
        errors['password_error'] = "Password cannot be empty"
    elif len(new_password) < 8:
        errors['password_error'] = "Password should be at least 8 characters"
    if errors:
        return redirect(url_for('view_admin', admin_id=admin_id, errors=errors,admin_name=new_name,admin_email=new_email,admin_password=new_password))
    query ="""
    UPDATE admin
    SET User_Name=%s, Email=%s, Password=%s
    WHERE Admin_ID=%s
    """ 
    values = (new_name, new_email, new_password, admin_id)
    mycursor.execute(query, values)
    mydb.commit()
    session['user'] = (admin_id, new_name, new_email, new_password)
    return redirect(url_for('view_admin', admin_id=admin_id, message_success="Admin Updated Successfully",query=querymaker(query,values)))


@app.route('/admin/<int:admin_id>/add', methods=['POST'])
def add_admin(admin_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    errors = {}
    new_admin_name = request.form.get('adminName')
    if not new_admin_name:
        errors['new_name_error'] = "Name cannot be empty"
    elif len(new_admin_name) < 3:
        errors['new_name_error'] = "Name should be at least 3 characters"
    
    new_admin_email = request.form.get('adminEmail')
    if not new_admin_email:
        errors['new_email_error'] = "Email cannot be empty"
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@thapar.edu$', new_admin_email):
        errors['new_email_error'] = "Invalid email format"
    
    new_admin_password = request.form.get('adminPassword')
    if not new_admin_password:
        errors['new_password_error'] = "Password cannot be empty"
    elif len(new_admin_password) < 8:
        errors['new_password_error'] = "Password should be at least 8 characters"
    
    if errors:
        return redirect(url_for('view_admin', admin_id=admin_id, errors=errors, admin_name=new_admin_name, admin_email=new_admin_email, admin_password=new_admin_password))
    
    query = """
    INSERT INTO admin (User_Name, Email, Password)
    VALUES (%s, %s, %s)
    """
    values = (new_admin_name, new_admin_email, new_admin_password)
    mycursor.execute(query, values)
    mydb.commit()
    
    return redirect(url_for('view_admin', admin_id=admin_id, message_success="Admin Added Successfully", query=querymaker(query, values)))

@app.route('/admin/<int:admin_id>')
def view_admin(admin_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    query="SELECT * FROM admin WHERE Admin_ID=%s"
    mycursor.execute(query,(admin_id,))
    admin=tuple((mycursor.fetchone()).values())
    errors=ast.literal_eval(request.args.get('errors', '{}'))
    if errors:
        query=None
    all_admins = "SELECT `Admin_ID`, `User_Name`, `Email` FROM admin where admin_id not in (%s)"
    mycursor.execute(all_admins,(admin_id,))
    admins=tuple(tuple(admin.values()) for admin in mycursor.fetchall())
    display_query=request.args.get('query',None)
    if  display_query:
        query=querymaker(query,(admin_id,))
    else:
        query=display_query
    return render_template('admin_view.html',admin=admin,admins=admins,errors=errors,message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None),query=query,admin_name=request.args.get('admin_name',None),admin_email=request.args.get('admin_email',None),admin_password=request.args.get('admin_password',None))

@app.route('/admin/create_tables')
def create_tables():
    if 'user' not in session:
        return redirect(url_for('login'))
    setup.create_tables()
    return redirect(url_for('admin', message_success="Tables Created Successfully"))

@app.route('/admin/insert_initial_data')
def insert_initial_data():
    if 'user' not in session:
        return redirect(url_for('login'))
    def run_with_timeout(func, timeout):
        thread = threading.Thread(target=func)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            raise TimeoutError("Function call timed out")
    try:
        run_with_timeout(setup.insert_initial_data, 10)  # 10 seconds timeout
    except TimeoutError:
        return redirect(url_for('admin', message_danger="Initial Data Insertion Timed Out"))
    return redirect(url_for('admin', message_success="Initial Data Inserted Successfully"))
@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['user'][0]!=1:
        return redirect(url_for('main'))
    query = "SELECT * FROM admin WHERE Admin_ID=%s"
    mycursor.execute(query, (session['user'][0],))
    admin = tuple((mycursor.fetchone()).values())
    return render_template('AdminDashboard.html',message_success=request.args.get('message_success',None),message_danger=request.args.get('message_danger',None))


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main'))    

@app.route('/login_user', methods=['POST'])
def signin():
    if request.method == 'POST':
        errors={}
        email = request.form.get('email').lower().strip()
        if not email:
            errors['email_error'] = "Email cannot be empty"
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@thapar.edu$', email):
            errors['email_error'] = "Invalid email format"
        password = request.form.get('password').strip()
        if not password:
            errors['password_error'] = "Password cannot be empty"
        elif len(password) < 8:
            errors['password_error'] = "Password should be at least 8 characters"
        userType = request.form.get('user-type')
        if not userType:
            errors['user_type_error'] = "please select a user type"
        if errors:
            return render_template('SignIn.html', **errors, email=email,  userType=userType)
        if userType == 'student':
            mycursor.execute("SELECT * FROM students WHERE College_Email=%s AND Password=%s", (email, password))
            user = mycursor.fetchone()
            if user:
                user = tuple(user.values())
                session['user'] = user
                return redirect(url_for('student'))
        elif userType == 'faculty':
            mycursor.execute("SELECT * FROM faculty WHERE official_mail=%s AND Password=%s", (email, password))
            user = mycursor.fetchone()
            if user:
                user = tuple(user.values())
                print(user)
                print("\n"*9)
                session['user'] = user
                return redirect(url_for('faculty'))
        elif userType == 'admin':
            mycursor.execute("SELECT * FROM admin WHERE Email=%s AND Password=%s", (email, password))
            user=mycursor.fetchone()
            if user:
                user = tuple(user.values())
                session['user'] = user
                return redirect(url_for('admin'))
        
        return render_template('SignIn.html', credentials_error="Invalid credentials", email=email, userType=userType)
    return render_template('SignIn.html')






@app.route('/signin')
def login():
    try:
        
        courses={"courses":getFacultyCourses()}
        departments={"departments":getFacultyDepartments()}
    except:
        courses={"courses":[]}
        departments={"departments":[]}
    return render_template('SignIn.html',**courses,**departments)




@app.route('/aboutme')
def aboutme():
    return render_template('aboutme.html')


@app.route('/documentations')
def documentations():
    documentation_files = []
    # Ensure the directory exists before trying to list its contents
    files_dir = os.path.join(app.static_folder, 'files')
    if os.path.exists(files_dir):
        for file in os.listdir(files_dir):
            file_path = os.path.join(files_dir, file)
            if os.path.isfile(file_path):
                # Get the file extension (without the dot)
                extension = os.path.splitext(file)[1][1:].lower() if os.path.splitext(file)[1] else 'N/A'
                # Append as tuple (extension, filename) - assuming filename is sufficient for linking
                # If you need the full path for linking, you might use url_for('static', filename='files/' + file)
                documentation_files.append((extension, file))

    # Render the template with the list of tuples
    return render_template('documentations.html', documentation_files=documentation_files)
@app.route('/admin/logs')
def admin_logs():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = "SELECT * FROM audit_log"
    mycursor.execute(query)
    logs = tuple(tuple(log.values()) for log in mycursor.fetchall())[::-1]
    display_query = request.args.get('query', querymaker(query, None))
    return render_template('logs.html', logs=logs, query=display_query)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
