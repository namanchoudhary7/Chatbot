import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from langgraph.checkpoint.memory import InMemorySaver

class ChatbotSession:
    def __init__(self, thread_id:str, agent):
        self.thread_config = {"configurable": {"thread_id": thread_id}}
        self.agent = agent

    def run(self):
        while True:
            user_input = str(input('User:'))
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Ending chatbot session...")
                break
            if not user_input.strip():
                continue

            try:
                # self.messages.append(HumanMessage(user_input))
                # response = self.llm.invoke(self.messages)
                # self.messages.append(response)
                # print('LLM:' + response.content)

                response = self.agent.invoke(
                    {"messages": [{"role":"user", "content": user_input}]},
                    self.thread_config,                   
                )["messages"][-1].content
                print("LLM:" + response)

            except Exception as e:
                print(f"Error generating response: {e}")

class Agent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature = 0.8,
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            max_tokens = 100,
        )

        # self.messages = [SystemMessage("You are a helpful assistant")]

        self.agent = create_agent(
            model=self.llm,
            checkpointer=InMemorySaver(),
            system_prompt="You are a helpful assistant",
        )

    def init_agent(self):
        return self.agent