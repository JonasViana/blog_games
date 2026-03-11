import feedparser
import os
import re
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv # <-- Nova importação

# Carrega as senhas ocultas do arquivo .env
load_dotenv()

# --- Configurações ---
RSS_URL = "https://br.ign.com/feed.xml"
PASTA_POSTS = r"C:\Users\jonas\Desktop\blog-games\content\posts"
# Puxa a chave do arquivo .env de forma segura:
CHAVE_GEMINI = os.getenv("CHAVE_GEMINI") 

# Configura a IA
genai.configure(api_key=CHAVE_GEMINI)
modelo_ia = genai.GenerativeModel('gemini-1.5-flash')

def reescrever_com_ia(titulo_original, resumo_original):
    """Pede para a IA reescrever a notícia focada em SEO para games."""
    prompt = f"""
    Você é um redator sênior de um blog de games chamado 'Foco Games'.
    Reescreva a seguinte notícia de forma original, engajadora e otimizada para SEO.
    Não copie o texto original. Crie um novo título chamativo e um texto de 2 a 3 parágrafos.
    Use formatação Markdown (negritos, listas se necessário).
    
    Notícia Original: {titulo_original}
    Resumo Original: {resumo_original}
    
    Retorne o resultado EXATAMENTE neste formato:
    TITULO: [Seu Novo Título Aqui]
    CONTEUDO: [Seu Texto Reescrito Aqui]
    """
    try:
        resposta = modelo_ia.generate_content(prompt)
        texto_gerado = resposta.text
        
        # Separa o título do conteúdo usando as tags que pedimos no prompt
        novo_titulo = re.search(r'TITULO:\s*(.+)', texto_gerado).group(1).strip()
        novo_conteudo = re.search(r'CONTEUDO:\s*(.+)', texto_gerado, re.DOTALL).group(1).strip()
        
        return novo_titulo, novo_conteudo
    except Exception as e:
        print(f"Erro ao gerar IA para '{titulo_original}': {e}")
        return None, None

def limpar_nome_arquivo(titulo):
    nome = re.sub(r'[^\w\s-]', '', titulo.lower())
    return re.sub(r'[-\s]+', '-', nome).strip('-') + ".md"

def criar_post_hugo(noticia):
    nome_arquivo = limpar_nome_arquivo(noticia.title)
    caminho_completo = os.path.join(PASTA_POSTS, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        return False # Pula se já existir

    print(f"🧠 Reescrevendo com IA: {noticia.title}...")
    novo_titulo, novo_conteudo = reescrever_com_ia(noticia.title, noticia.summary)
    
    if not novo_titulo:
        return False # Pula se a IA falhar

    data_publicacao = datetime(*noticia.published_parsed[:6]).strftime('%Y-%m-%dT%H:%M:%S-03:00')

    conteudo_md = f"""---
title: "{novo_titulo.replace('"', "'")}"
date: {data_publicacao}
draft: false
categories: ["Notícias"]
tags: ["games", "novidade"]
cover:
    image: "" 
---

{novo_conteudo}

*Fonte: [IGN Brasil]({noticia.link})*
"""
    with open(caminho_completo, "w", encoding="utf-8") as f:
        f.write(conteudo_md)
    
    print(f"✅ Post gerado e salvo: {nome_arquivo}")
    return True

def rodar_bot():
    print("🎮 Buscando as últimas notícias no feed RSS...")
    feed = feedparser.parse(RSS_URL)
    
    novos_posts = 0
    # Limitei a 3 para não estourar a cota gratuita da API muito rápido nos testes
    for entrada in feed.entries[:3]:
        if criar_post_hugo(entrada):
            novos_posts += 1
            
    print(f"\n🚀 Sucesso! {novos_posts} novas notícias exclusivas adicionadas ao seu blog.")

if __name__ == "__main__":
    os.makedirs(PASTA_POSTS, exist_ok=True)
    rodar_bot()