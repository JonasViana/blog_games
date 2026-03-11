from google import genai
import feedparser
import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configurações ---
RSS_URL = "https://br.ign.com/feed.xml"
PASTA_POSTS = r"C:\Users\jonas\Desktop\blog-games\content\posts"
CHAVE_GEMINI = os.getenv("CHAVE_GEMINI")

# Inicializa o cliente de forma simples
client = genai.Client(api_key=CHAVE_GEMINI)

# MUDANÇA AQUI: Algumas chaves exigem o prefixo 'models/' no novo SDK
MODELO = "gemini-2.5-flash" 

def obter_imagem(noticia):
    if 'media_thumbnail' in noticia and len(noticia.media_thumbnail) > 0:
        return noticia.media_thumbnail[0]['url']
    elif 'media_content' in noticia and len(noticia.media_content) > 0:
        return noticia.media_content[0]['url']
    match = re.search(r'<img[^>]+src="([^">]+)"', noticia.summary)
    return match.group(1) if match else ""

def reescrever_com_ia(titulo_original, resumo_original):
    prompt = f"""
    Atue como redator sênior do portal 'Foco Games'. 
    Reescreva a notícia abaixo com tom profissional, gamer e otimizado para SEO.
    
    Notícia: {titulo_original}
    Resumo: {resumo_original}
    
    Retorne EXATAMENTE neste formato:
    TITULO: [Título Chamativo]
    DESCRICAO: [Resumo de 160 caracteres para o Google]
    CONTEUDO: [Texto de 3 a 4 parágrafos em Markdown]
    """
    
    # Lista de nomes para tentar caso o primeiro dê 404
    modelos_para_tentar = [MODELO, "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    
    for nome_modelo in modelos_para_tentar:
        try:
            response = client.models.generate_content(model=nome_modelo, contents=prompt)
            t = response.text
            
            novo_titulo = re.search(r'TITULO:\s*(.+)', t).group(1).strip()
            nova_desc = re.search(r'DESCRICAO:\s*(.+)', t).group(1).strip()
            novo_cont = re.search(r'CONTEUDO:\s*(.+)', t, re.DOTALL).group(1).strip()
            
            return novo_titulo, nova_desc, novo_cont
        except Exception as e:
            if "404" in str(e):
                print(f"⚠️ Modelo {nome_modelo} não encontrado, tentando o próximo...")
                continue
            elif "429" in str(e):
                print(f"⏳ Cota atingida. Esperando 10 segundos...")
                time.sleep(10)
            else:
                print(f"❌ Erro na IA: {e}")
                break
    return None, None, None

def limpar_nome_arquivo(titulo):
    nome = re.sub(r'[^\w\s-]', '', titulo.lower())
    return re.sub(r'[-\s]+', '-', nome).strip('-') + ".md"

def criar_post_hugo(noticia):
    nome_arquivo = limpar_nome_arquivo(noticia.title)
    caminho_completo = os.path.join(PASTA_POSTS, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        return False

    img = obter_imagem(noticia)
    titulo, desc, conteudo = reescrever_com_ia(noticia.title, noticia.summary)
    
    if not titulo: return False

    data_atual = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00')

    post_template = f"""---
title: "{titulo.replace('"', "'")}"
date: {data_atual}
description: "{desc.replace('"', "'")}"
draft: false
categories: ["Notícias"]
tags: ["games", "news"]
cover:
    image: "{img}"
    alt: "{titulo.replace('"', "'")}"
---

{conteudo}

---
*Fonte: [IGN Brasil]({noticia.link})*
"""
    with open(caminho_completo, "w", encoding="utf-8") as f:
        f.write(post_template)
    
    print(f"✅ Post SEO Criado: {nome_arquivo}")
    return True

def rodar_bot():
    print("🤖 Bot Iniciado (Modo de Compatibilidade)...")
    feed = feedparser.parse(RSS_URL)
    for entrada in feed.entries[:3]:
        sucesso = criar_post_hugo(entrada)
        if sucesso:
            print("⏳ Aguardando 10 segundos...")
            time.sleep(10)

if __name__ == "__main__":
    os.makedirs(PASTA_POSTS, exist_ok=True)
    rodar_bot()