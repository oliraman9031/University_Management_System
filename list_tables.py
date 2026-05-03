import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

conn = pymysql.connect(host='localhost', port=3306, user='root', password=DB_PASSWORD, database='university_management_system', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
tables = [list(row.values())[0] for row in cursor.fetchall()]
print('\nTables in database:')
for t in sorted(tables):
    print(f'  ✓ {t}')
print(f'\nTotal tables: {len(tables)}\n')
cursor.close()
conn.close()
