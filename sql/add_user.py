import os
import sys
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://project_user:choose_a_password@localhost:5432/steam_db")

def add_user(username, password, role):
    if role not in ('viewer', 'admin'):
        print("Error: Role must be either 'viewer' or 'admin'.")
        sys.exit(1)
        
    password_hash = generate_password_hash(password)
    
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_user (username, password_hash, role) 
                VALUES (%s, %s, %s)
                RETURNING user_id;
                """,
                (username, password_hash, role)
            )
            user_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        print(f"Successfully added user '{username}' (ID: {user_id}) with role '{role}'.")
    except psycopg2.IntegrityError:
        print(f"Error: Username '{username}' already exists.")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python add_user.py <username> <password> <role>")
        print("Example: python add_user.py sam viewer_pass123 viewer")
        sys.exit(1)
        
    uname, pword, urole = sys.argv[1], sys.argv[2], sys.argv[3]
    add_user(uname, pword, urole)
