import pymysql
import os
from dotenv import load_dotenv
load_dotenv()
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
conn = pymysql.connect(host='localhost', port=3306, user='root', password=DB_PASSWORD, database='university_management_system', cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4')
cursor = conn.cursor()
cursor.execute('SELECT * FROM audit_log WHERE Table_Name = %s AND Event_Type = %s ORDER BY Audit_ID DESC LIMIT 10', ('students', 'INSERT'))
results = cursor.fetchall()
for row in results:
    print(row)
cursor.close()
conn.close()