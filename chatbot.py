import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature = 1.1,
)

sys_msg = SystemMessage("You are a helpful assistant")
messages = [sys_msg]

while True:
    user_input = str(input('User:')).lower()

    if user_input=='bye':
        print('Have a nice day! bye')
        break

    messages.append(HumanMessage(user_input))

    response = llm.invoke(messages)

    messages.append(response)

    print('LLM:' + response.content)