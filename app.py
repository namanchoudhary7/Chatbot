import streamlit as st
from database import DatabaseManager
from chatbot import Agent, ChatbotSession

@st.cache_resource
def get_db_manager():
    db = DatabaseManager()
    db.init_db()
    return db

if "db" not in st.session_state:
    st.session_state.db = get_db_manager()

if "agent" not in st.session_state:
    st.session_state.agent = Agent()

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "past_history" not in st.session_state:
    st.session_state.past_history = None

if "bot_session" not in st.session_state:
    st.session_state.bot_session = None
    
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False


def show_auth_menu():
    st.title("AI chatbot")
    tabs = st.tabs(tabs=['Login', 'Register'])

    with tabs[0]:
        st.subheader(body="Login to your Account")
        login_user = st.text_input(label="Username", key="login_user")
        login_pass = st.text_input(label="Password", key="login_pass", type="password")

        if st.button(label="Log In", type="primary"):
            if not login_user and not login_pass:
                st.warning("Please fill in both fields.")
            else:
                with st.session_state.db.conn:
                    with st.session_state.db.conn.cursor() as cur:
                        cur.execute("SELECT password FROM user_info WHERE username = %s;", (login_user,))
                        result = cur.fetchone()

                if result:
                    from authentication import check_password
                    if check_password(plain_text_password=login_pass, stored_hash=result[0]):
                        st.session_state.current_user = login_user
                        st.session_state.db.current_user = login_user
                        st.session_state.bot_session = ChatbotSession(thread_id=login_user, agent=st.session_state.agent)
                        st.session_state.past_history = st.session_state.db.get_user_history()
                        st.success(body=f"Welcome back, {login_user}!")
                        st.rerun()
                    else:
                        st.error("Invalid Password.")
                else:
                    st.error("Account does not exist. Please Register.")

    with tabs[1]:
        st.subheader(body="Create a New Account")
        reg_user = st.text_input(label="Choose Username", key="reg_user")
        reg_pass = st.text_input(label="Choose Password", key="reg_pass", type="password")

        if st.button(label="Register", type="primary"):
            if not reg_user and not reg_pass:
                st.warning("Please fill in both fields.")
            else:
                with st.session_state.db.conn:
                    with st.session_state.db.conn.cursor() as cur:
                        cur.execute("SELECT password FROM user_info WHERE username = %s;", (reg_user,))
                        result = cur.fetchone()
                if result:
                    st.error("Username already exists. Select another one.")
                else:
                    from authentication import hash_password
                    with st.session_state.db.conn:
                        with st.session_state.db.conn.cursor() as cur:
                            cur.execute("INSERT INTO user_info(username, password) VALUES(%s, %s)", (reg_user, hash_password(reg_pass),))
                    st.success("Registration successful! Please head over to the Login tab.")

def handle_logout():
    st.info("Summarizing conversation and backing up history. Please wait...")
    bot = st.session_state.bot_session
    db = st.session_state.db

    curr_history = bot.summarize_conversation(past_history = st.session_state.past_history)
    if curr_history is not None:
        db.store_user_history(curr_history = curr_history)
        st.success("History saved successfully!")
    else:
        st.warning("No conversation happened. History not updated.")

    db.current_user = None
    st.session_state.agent.reinitialize_checkpointer()
    st.session_state.current_user = None
    st.session_state.past_history = None
    st.session_state.bot_session = None
    st.session_state.chat_started = False
    st.rerun()

def show_chat_interface():
    st.sidebar.title(body=f"User: {st.session_state.current_user}")
    if st.sidebar.button(label="Logout"):
        handle_logout()
    
    st.title("LangGraph Conversational Assistant")
 
    bot = st.session_state.bot_session

    if not st.session_state.chat_started:
        st.subheader("Session Settings")
        system_msg_input = st.text_input(label="System Prompt Configuration", value="You are a helpful assistant")
        recommended_ques = bot.questions
        if st.session_state.past_history and "questions" in st.session_state.past_history:
            recommended_ques = st.session_state.past_history["questions"]

        st.write("**Suggested starter questions based on your history:**")
        selected_ques = None
        for q in recommended_ques:
            if st.button(label=f"{q}", key=f"rec-{q}"):
                selected_ques = q
        
        if st.button("Start Chat Session", type="primary") or selected_ques:
            summary_context = ""
            if st.session_state.past_history and "summary" in st.session_state.past_history:
                summary_context = f"\nHere is the summary of the user's past conversations:\n<summary>{st.session_state.past_history['summary']}</summary>"
            
            from chatbot import SystemMessage
            bot.system_prompt = SystemMessage(content=[{'system_message': system_msg_input, 'past_conversation_summary': summary_context}])
            bot.chat_agent = st.session_state.agent.init_agent(system_prompt = bot.system_prompt)

            st.session_state.messages = []
            st.session_state.chat_started = True

            if selected_ques:
                st.session_state.prefilled_input = selected_ques
            
            st.rerun()
    
    else:
        if st.session_state.past_history and "summary" in st.session_state.past_history:
            with st.sidebar.expander(label="Past Context Summary", expanded=False):
                st.caption(st.session_state.past_history["summary"])
            
        for msg in st.session_state.messages:
            with st.chat_message(msg['role']):
                st.write(msg['content'])

        default_input = ""
        if "prefilled_input" in st.session_state:
            default_input = st.session_state.prefilled_input
            del st.session_state.prefilled_input

        user_query = st.chat_input("Message the AI...")
        if default_input and not user_query:
            user_query = default_input
        
        if user_query:
            st.session_state.messages.append({'role': 'user', 'content': user_query})
            with st.chat_message(name='user'):
                st.write(user_query)

            with st.chat_message(name='assistant'):
                with st.spinner(text="Thinking..."):
                    try:
                        response = bot.chat_agent.invoke(
                            {'messages': {'role': 'user', 'content': user_query}},
                            bot.thread_config,
                        )['messages'][-1].content

                        st.write(response)
                        st.session_state.messages.append({'role': 'assistant', 'content': response})
                    except Exception as e:
                        st.error(f"Error generating response: {e}")

def main():
    if st.session_state.current_user is None:
        show_auth_menu()
    else:
        show_chat_interface()

if __name__ == "__main__":
    main()