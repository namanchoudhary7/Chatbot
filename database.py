import os
import psycopg2
from authentication import hash_password, check_password
from dotenv import load_dotenv
load_dotenv()
import json

class DatabaseManager:
    def __init__(self, db_name = os.getenv('DB_NAME')):
        self.db_name = db_name
        self.conn = None
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
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        """CREATE TABLE IF NOT EXISTS user_info(
                        userid SERIAL PRIMARY KEY,
                        username VARCHAR(20) UNIQUE NOT NULL,
                        password BYTEA NOT NULL
                        )
                    """
                    )
                    cur.execute(
                        """CREATE TABLE IF NOT EXISTS user_memory(
                        userid INT UNIQUE REFERENCES user_info(userid),
                        history JSONB
                        )
                    """
                    )
        else:
            print("Connection to the PostgreSQL encountered and error.")
            exit()
    
    def close_db(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed gracefully.")

    def check_user(self):
        print('\n=== Login! ===')
        username = input('Username: ')
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT password FROM user_info WHERE username = %s;", (username,))
                result = cur.fetchone()
        if result:
            stored_hash = result[0]
            retry = 3
            while retry:
                password = input('Password: ')
                retry-=1
                if check_password(plain_text_password=password, stored_hash=stored_hash):
                    print(f'\nWelcome back! {username}')
                    self.current_user = username
                    return True
                else:
                    print('Invalid password.'+(f'{retry} retries left' if retry else 'No retries left'))
            return False
        else:
            print('Account does not exist. Create a new one.')
            return False
        
    def create_new_user(self):
        print('\n=== Sign up! ===')
        while True:
            username = input('Username: ')
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("SELECT password FROM user_info WHERE username = %s;", (username,))
                    result = cur.fetchone()
            if result:
                print('\nUsername already exist select any other.')
            else:
                password = input('Password: ')
                with self.conn:
                    with self.conn.cursor() as cur:
                        cur.execute("INSERT INTO user_info(username, password) VALUES(%s, %s)", (username, hash_password(password),))
                print(f'\nWelcome {username}! Your account has been created. Please log in.')
                break
    
    def get_user_history(self, username):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT userid FROM user_info WHERE username = %s;", (username,))
                userid = cur.fetchone()
                if not userid:
                    return None
                userid = userid[0]
                cur.execute("SELECT history FROM user_memory WHERE userid = %s;", (userid,))
                past_history = cur.fetchone()
                return past_history[0] if past_history else None

    def store_user_history(self, username, curr_history):
        history_json = json.dumps(curr_history)
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT userid FROM user_info WHERE username = %s;", (username,))
                result = cur.fetchone()
                if not result:
                    print("User not found.")
                    return
                userid = result[0]
                cur.execute("INSERT INTO user_memory(userid, history) VALUES(%s, %s) ON CONFLICT(userid) DO UPDATE SET history = EXCLUDED.history", (userid, history_json))
        print("\n=== History stored ===")

    def auth_menu(self):
        print("\n=== WELCOME ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit Application")
        while True:
            choice = input("\nChoose an option from the menu above: ").strip()
            if choice == '1':
                if self.check_user():
                    return True
            elif choice == '2':
                self.create_new_user()
            elif choice == '3':
                return 'exit'
            else:
                print('Invalid option.')
    
    def main_menu(self):
        """Menu shown ONLY after a successful login."""
        print(f"\n=== MAIN MENU (User: {self.current_user}) ===")
        print("1. Chat with AI")
        print("2. Logout")
        while True:
            choice = input("\nChoose an option from the main menu: ").strip()
            if choice == '1':
                return 'chat'
            elif choice == '2':
                print(f"\nLogging out {self.current_user}...")
                return 'logout'
            else:
                print('Invalid option.')