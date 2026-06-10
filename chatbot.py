import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class ChatbotSession:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature = 0.8,
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            max_tokens = 200,
        )
        self.messages = [SystemMessage("You are a helpful assistant")]

    def run(self):
        while True:
            user_input = str(input('User:'))

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Ending chatbot session...")
                break
                
            if not user_input.strip():
                continue

            try:
                self.messages.append(HumanMessage(user_input))
                response = self.llm.invoke(self.messages)
                self.messages.append(response)
                print('LLM:' + response.content)
            except Exception as e:
                print(f"Error generating response: {e}")