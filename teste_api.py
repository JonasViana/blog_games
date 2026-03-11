import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega a sua chave com segurança
load_dotenv()
genai.configure(api_key=os.getenv("CHAVE_GEMINI"))

print("🔍 Perguntando ao Google quais modelos estão liberados para a sua chave...\n")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            # Imprime o nome exato que o bot precisa usar
            print(f"✅ Modelo pronto para uso: {m.name.replace('models/', '')}")
except Exception as e:
    print(f"Erro ao conectar: {e}")