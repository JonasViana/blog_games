from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
CHAVE_GEMINI = os.getenv("CHAVE_GEMINI")
client = genai.Client(api_key=CHAVE_GEMINI)

print("--- LISTANDO MODELOS DISPONÍVEIS ---")
try:
    for m in client.models.list():
        print(f"Disponível: {m.name}")
except Exception as e:
    print(f"ERRO CRÍTICO NA CHAVE: {e}")