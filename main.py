from database import DatabaseManager
from chatbot import ChatbotSession
from chatbot import Agent

def main():
    db = DatabaseManager()
    db.init_db()
    agent = Agent()

    try:
        while True:
            auth_choice = db.auth_menu()
            if auth_choice == 'exit':
                break
            if auth_choice == True:
                if db.current_user:
                    bot = ChatbotSession(thread_id=db.current_user, agent=agent)
                while db.current_user:
                    app_choice = db.main_menu()
                    past_history = db.get_user_history(db.current_user)
                    if app_choice == 'chat':
                        bot.run(past_history=past_history)
                    elif app_choice == 'logout':
                        curr_history = bot.summarize_conversation(past_history=past_history)
                        if curr_history != None:
                            db.store_user_history(username=db.current_user, curr_history=curr_history)
                        else:
                            print("\n=== No conversation Happened! ===")
                        agent.reinitialize_checkpointer()
                        db.current_user = None
                        break
    finally:
        db.close_db()

if __name__=='__main__':
    main()