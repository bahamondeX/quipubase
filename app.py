from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)


messages = []

def chat(prompt):
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gemini-2.5-flash-preview-05-20",
        messages=messages,
    )
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    return response.choices[0].message.content

    
def main():
    while True:
        prompt = input("User: ")
        print("Gemini: ", chat(prompt))
    

if __name__ == "__main__":
    main()
    