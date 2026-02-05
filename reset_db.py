import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "university_management_system")

try:
    # Connect without specifying a database
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
    )
    
    cursor = conn.cursor()
    
    # Drop the existing database
    print(f"Dropping database '{DATABASE_NAME}'...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME};")
    conn.commit()
    print(f"✓ Database '{DATABASE_NAME}' dropped successfully")
    
    cursor.close()
    conn.close()
    
    print("\nNow run 'python main.py' to recreate the database with correct schema.")
    
except Exception as e:
    print(f"Error: {e}")
