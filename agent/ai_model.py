import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_ai_model():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "your_api_key_here":
        raise ValueError("OpenAI API key is missing. Check your .env file.")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=api_key
    )

    return llm