from database import DatabaseManager
from chatbot import ChatbotSession
from chatbot import Agent

def main():
    db = DatabaseManager()
    db.init_db()
    agent = Agent().init_agent()

    try:
        while True:
            auth_choice = db.auth_menu()
            if auth_choice == 'exit':
                break
            if auth_choice == True:
                while db.current_user:
                    app_choice = db.main_menu()
                    if app_choice == 'chat':
                        bot = ChatbotSession(thread_id=db.current_user, agent=agent)
                        bot.run()
                    elif app_choice == 'logout':
                        break
    finally:
        db.close_db()

if __name__=='__main__':
    main()