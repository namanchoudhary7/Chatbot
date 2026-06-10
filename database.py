import os
import psycopg2
from authentication import hash_password, check_password
from dotenv import load_dotenv
load_dotenv()

class DatabaseManager:
    def __init__(self, db_name = os.getenv('DB_NAME')):
        self.db_name = db_name
        self.conn = None
        self.cur = None
        self.current_user = None

    def connect(self):
        try:
            return psycopg2.connect(
                dbname=self.db_name,
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
            )
        except Exception as e:
            print(f'Database connection failed: {e}')
            return None

    def init_db(self):
        self.conn = self.connect()
        if self.conn:
            print("Connection to the PostgreSQL established successfully.")
            self.cur = self.conn.cursor()

            self.cur.execute(
                """CREATE TABLE IF NOT EXISTS user_info(
                userid SERIAL PRIMARY KEY,
                username VARCHAR(20) UNIQUE NOT NULL,
                password BYTEA NOT NULL
                )
            """
            )
            self.conn.commit()
        else:
            print("Connection to the PostgreSQL encountered and error.")
            exit()
    
    def close_db(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed gracefully.")

    def check_user(self):
        print('\n=== Login! ===')
        username = input('Username: ')
        self.cur.execute("SELECT password FROM user_info WHERE username = %s;", (username,))
        result = self.cur.fetchone()
        if result:
            stored_hash = result[0]
            retry = 3
            while retry:
                password = input('Password: ')
                retry-=1
                if check_password(plain_text_password=password, stored_hash=stored_hash):
                    print(f'Welcome back! {username}')
                    self.current_user = username
                    return True
                else:
                    print('Invalid password.'+(f'{retry} retries left' if retry else 'No retries left'))
            return self.auth_menu()
        else:
            print('Account does not exist. Create a new one.')
            return self.auth_menu()
        
    def create_new_user(self):
        print('\n=== Sign up! ===')
        while True:
            username = input('Username: ')
            self.cur.execute("SELECT password FROM user_info WHERE username = %s;", (username,))
            result = self.cur.fetchone()
            if result:
                print('Username already exist select any other.')
            else:
                password = input('Password: ')
                self.cur.execute("INSERT INTO user_info(username, password) VALUES(%s, %s)", (username, hash_password(password),))
                self.conn.commit()
                print(f'Welcome {username}! Your account has been created. Please log in.')
                break

    def auth_menu(self):
        print("\n=== WELCOME ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit Application")
        choice = input("Choose an option: ").strip()
        if choice == '1':
            return self.check_user()
        elif choice == '2':
            self.create_new_user()
            return self.auth_menu()
        elif choice == '3':
            return 'exit'
        else:
            print('Invalid option.')
            self.auth_menu()
    
    def main_menu(self):
        """Menu shown ONLY after a successful login."""
        print(f"\n=== MAIN MENU (User: {self.current_user}) ===")
        print("1. Chat with AI")
        print("2. Logout")
        choice = input("Choose an option: ").strip()
        if choice == '1':
            return 'chat'
        elif choice == '2':
            print(f"Logging out {self.current_user}...")
            self.current_user = None
            return 'logout'
        else:
            print('Invalid option.')
            return self.main_menu()