import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import SystemMessage

from langchain.messages import RemoveMessage
from langchain.agents.middleware import before_model, SummarizationMiddleware
from langgraph.runtime import Runtime
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from typing import Any

class Agent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature = 0.8,
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            max_tokens = 100,
        )

        self.checkpointer=InMemorySaver()

    def init_agent(self, system_prompt: SystemMessage | str):
        return create_agent(
            model=self.llm,
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
            middleware=[self.trim_messages],
        )
    
    @before_model
    def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        messages = state["messages"]
        if len(messages) <= 11:
            return None
        
        first_msg = messages[0]
        recent_msgs = messages[-4:]
        new_msgs = [first_msg] + recent_msgs

        return {
            "messages": [
                RemoveMessage(id = REMOVE_ALL_MESSAGES),
                *new_msgs
            ]
        }

class ChatbotSession:
    def __init__(self, thread_id:str, agent:Agent):
        self.thread_config = {"configurable": {"thread_id": thread_id}}
        self.agent = agent

    def run(self):
        system_prompt = input("\nEnter the System prompt for the assistant (Press enter or 'default' for default):")
        if system_prompt.strip().lower() == 'default' or not system_prompt.strip():
            system_prompt = "You are a helpful assistant" 
        chat_agent = self.agent.init_agent(system_prompt=system_prompt)

        while True:
            user_input = input('\nUser:')
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Ending chatbot session...")
                break
            if not user_input.strip():
                continue

            try:
                response = chat_agent.invoke(
                    {"messages": [{"role":"user", "content": user_input}]},
                    self.thread_config,                   
                )["messages"][-1].content

            except Exception as e:
                print(f"Error generating response: {e}")
                
            print("\nLLM:" + response)