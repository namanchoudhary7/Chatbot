import os
from dotenv import load_dotenv
load_dotenv()
import textwrap

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import SystemMessage

from langchain.agents.middleware import SummarizationMiddleware

history_schema_dict = {
    "title": "HistorySchema",
    "description": "Schema for extracting conversation history and generating follow-up questions.",
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "The extracted context and summary from the conversation."
        },
        "questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3 questions based on the users past history and current conversation.",
            "maxItems": 3
        }
    },
    "required": ["summary", "questions"]
}

class Agent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv('MODEL_NAME'),
            temperature = os.getenv('MODEL_TEMPERATURE'),
            google_api_key = os.getenv('GOOGLE_API_KEY'),
        )

        self.checkpointer=InMemorySaver()

        self.summarization_middleware = SummarizationMiddleware(
            model=self.llm.bind(max_output_tokens = os.getenv('MAX_OUTPUT_TOKENS')),
            trigger=('messages', 5),
            keep=('messages', 2),
        )

    def init_agent(self, system_prompt: SystemMessage | str):
        return create_agent(
            model=self.llm.bind(max_output_tokens = os.getenv('MAX_OUTPUT_TOKENS')),
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
            middleware=[self.summarization_middleware],
        )
    
    def structured_llm(self):
        return self.llm.with_structured_output(
                schema=history_schema_dict, method='json_schema'
            )
    
    def reinitialize_checkpointer(self):
        self.checkpointer = InMemorySaver()

class ChatbotSession:
    def __init__(self, thread_id:str, agent:Agent):
        self.thread_config = {"configurable": {"thread_id": thread_id}}
        self.agent = agent
        self.chat_agent = None
        self.system_prompt : SystemMessage = SystemMessage(content="You are a helpful assistant")
        self.questions = ['what is langchain.', 'who is MS Dhoni', '2+2=?']

    def run(self, past_history):
        try:
            system_msg = input("\nEnter the System prompt for the assistant (Press enter or 'default' for default):")
            if system_msg.strip().lower() == 'default' or not system_msg.strip():
                system_msg = "You are a helpful assistant"

            summary_context = ""
            if past_history:
                summary_context = f"Here is the summary of the user's past conversations:\n{past_history['summary']}"
                self.questions = past_history['questions']

            self.system_prompt = SystemMessage(content=(system_msg + summary_context))
            self.chat_agent = self.agent.init_agent(system_prompt=self.system_prompt)
            
            print('\n')
            for i, item in enumerate(self.questions):
                print(f'Type {i+1} for:', item)
            print('Otherwise write if not from above options.')
                
            while True:
                user_input = input('\nUser:')
                if user_input.isdigit() and int(user_input) in range(len(self.questions)+1):
                    user_input = self.questions[int(user_input)-1]
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Ending chatbot session...")
                    break
                if not user_input.strip():
                    continue

                try:
                    response = self.chat_agent.invoke(
                        {"messages": [{"role":"user", "content": user_input}]},
                        self.thread_config,                   
                    )["messages"][-1].content

                except Exception as e:
                    print(f"Error generating response: {e}")
                    exit()
                    
                print("\nLLM:" + response)
        except Exception as e:
            print(f"Fatal error during agent initialization: {e}")
            exit()

    def summarize_conversation(self, past_history):
        if self.chat_agent:
            try:
                state = self.chat_agent.get_state(self.thread_config)
                messages = state.values.get('messages', [])
                if messages == []:
                    return None
                messages.append(self.system_prompt)
                
                formatted_messages = "\n".join(
                    [f"{msg.type.capitalize()}: {msg.content}" for msg in messages if hasattr(msg, 'content')]
                )

                DEFAULT_SUMMARY_PROMPT = textwrap.dedent(f'''
                <role>\n
                    Context Extraction Assistant\n
                </role>\n\n
                <primary_objective>\n
                    Your sole objective in this task is to extract the highest quality/most relevant context from the conversation history and users past history below and generate atmost 3 questions based on users past history and current conversation history.\n
                </primary_objective>\n\n
                <objective_information>\n
                    You\'re nearing the total number of input tokens you can accept, so you must extract the highest quality/most relevant pieces of information from your conversation and past history.\n
                    This context will then overwrite the users history in the database as json. Because of this, ensure the context you extract is only the most important information that defins the user chats with the model.\n
                    The questions will be recommended to the user at the start of the chat to choose from.\n
                </objective_information>\n\n
                <instructions>\n
                        The history will be replaced with the context you extract in this step.\n
                        You want to ensure that you don\'t repeat any actions you\'ve already completed, so the context you extract from the conversation history should be focused on the most important information to your overall goal.\n\n
                        You should structure your summary using the following sections. Each section acts as a checklist - you must populate it with relevant information or explicitly state "None" if there is nothing to report for that section:\n\n
                        The questions must be framed strictly based on the final summary generated.\n\n
                    ## SESSION INTENT\n\n
                        What is the user\'s primary goal or request? What overall task are you trying to accomplish? This should be concise but complete enough to understand the purpose of the entire session.\n\n
                    ## SUMMARY\n\n
                        Extract and record all of the most important context from the conversation and past history. Include important choices, conclusions, or strategies determined during this conversation and history. Include the reasoning behind key decisions. Document any rejected options and why they were not pursued. Do not repeat any point if mentioned in both histories and if past history is "None" then do not consider it.\n\n
                    ## ARTIFACTS\n\n
                        What artifacts, files, or resources were created, modified, or accessed during this conversation? For file modifications, list specific file paths and briefly describe the changes made to each. This section prevents silent loss of artifact information.\n\n
                    ## NEXT STEPS\n\n
                        What specific tasks remain to be completed to achieve the session intent? What should you do next?\n\n
                    ## QUESTIONS\n\n
                        Generate atmost 3 question based on the summary that har users interest and are sequenced based on users prefrences.\n\n
                </instructions>\n\n
                The user will message you with the full message history from which you\'ll extract context to create a replacement. Carefully read through it all and think deeply about what information is most important to your overall goal and should be saved:\n\n
                With all of this in mind, please carefully read over the entire conversation history, and extract the most important and relevant context to replace it so that you can free up space in the conversation history.\n
                Respond ONLY with the extracted context. Do not include any additional information, or text before or after the extracted context.\n\n
                <messages>\n
                    Messages to summarize:
                        \n{formatted_messages}\n
                    Past history to summarize:
                        \n{past_history if past_history else 'None'}\n
                </messages>
                ''').strip()

                new_history = self.agent.structured_llm().invoke(DEFAULT_SUMMARY_PROMPT)
                return new_history
            except Exception as e:
                print(f"Error generating response: {e}")
                exit()