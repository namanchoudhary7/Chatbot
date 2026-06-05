import os
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature = 1.1,
)

while True:
    user_input = str(input('User:')).lower()
    if user_input=='bye':
        print('Have a nice day! bye')
        break
    response = llm.invoke(user_input)
    print('LLM:' + response.content)