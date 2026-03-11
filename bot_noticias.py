import feedparser
import os
import re
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega as senhas do ficheiro .env
load_dotenv()

# --- Configurações ---
RSS_URL = "https://br.ign.com/feed.xml"
PASTA_POSTS = r"C:\Users\jonas\Desktop\blog-games\content\posts"
CHAVE_GEMINI = os.getenv("CHAVE_GEMINI")

genai.configure(api_key=CHAVE_GEMINI)
modelo_ia = genai.GenerativeModel('gemini-2.5-flash')

def obter_imagem(noticia):
    """Tenta extrair a imagem de destaque do feed RSS."""
    # Procura na tag media_thumbnail ou media_content (padrão em muitos feeds)
    if 'media_thumbnail' in noticia and len(noticia.media_thumbnail) > 0:
        return noticia.media_thumbnail[0]['url']
    elif 'media_content' in noticia and len(noticia.media_content) > 0:
        return noticia.media_content[0]['url']
    
    # Se não encontrar, tenta procurar uma tag <img> dentro do resumo
    match = re.search(r'<img[^>]+src="([^">]+)"', noticia.summary)
    if match:
        return match.group(1)
        
    return "" # Retorna vazio se não encontrar imagem

def reescrever_com_ia(titulo_original, resumo_original):
    """Pede à IA para criar um artigo completo baseado na notícia."""
    prompt = f"""
    És um redator sénior de um blog de videojogos chamado 'Foco Games'.
    Escreve um artigo completo e envolvente de 3 a 4 parágrafos baseado na informação abaixo.
    Não uses frases como "Leia a matéria completa" ou "Resumo". Escreve o teu próprio texto otimizado para SEO.
    Usa formatação Markdown (negritos, listas se fizer sentido).
    
    Informação Base:
    Título: {titulo_original}
    Resumo: {resumo_original}
    
    Retorna o resultado EXATAMENTE neste formato, separando o título do conteúdo:
    TITULO: [O Teu Novo Título Aqui]
    CONTEUDO: [O Teu Texto Completo Aqui]
    """
    try:
        resposta = modelo_ia.generate_content(prompt)
        texto_gerado = resposta.text
        
        # Usa Expressões Regulares para extrair com precisão
        titulo_match = re.search(r'TITULO:\s*(.+)', texto_gerado)
        conteudo_match = re.search(r'CONTEUDO:\s*(.+)', texto_gerado, re.DOTALL)
        
        if titulo_match and conteudo_match:
            novo_titulo = titulo_match.group(1).strip()
            novo_conteudo = conteudo_match.group(1).strip()
            return novo_titulo, novo_conteudo
        else:
            return None, None
    except Exception as e:
        print(f"Erro ao processar a IA: {e}")
        return None, None

def limpar_nome_arquivo(titulo):
    nome = re.sub(r'[^\w\s-]', '', titulo.lower())
    return re.sub(r'[-\s]+', '-', nome).strip('-') + ".md"

def criar_post_hugo(noticia):
    nome_arquivo = limpar_nome_arquivo(noticia.title)
    caminho_completo = os.path.join(PASTA_POSTS, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        return False # Ignora se já existir para não sobrescrever

    print(f"🧠 A gerar artigo (com imagem) via IA: {noticia.title}...")
    
    # 1. Puxa a imagem original
    imagem_url = obter_imagem(noticia)
    
    # 2. Puxa o texto reescrito
    novo_titulo, novo_conteudo = reescrever_com_ia(noticia.title, noticia.summary)
    
    if not novo_titulo or not novo_conteudo:
        print("⚠️ IA falhou nesta notícia. A saltar para a próxima.")
        return False

    data_publicacao = datetime(*noticia.published_parsed[:6]).strftime('%Y-%m-%dT%H:%M:%S-03:00')

    # Estrutura perfeita para o Hugo + PaperMod
    conteudo_md = f"""---
title: "{novo_titulo.replace('"', "'")}"
date: {data_publicacao}
draft: false
categories: ["Notícias"]
tags: ["atualidade", "games"]
cover:
    image: "{imagem_url}"
    alt: "Imagem de destaque: {novo_titulo.replace('"', "'")}"
---

{novo_conteudo}

---
*Fonte original: [Ver matéria completa]({noticia.link})*
"""
    with open(caminho_completo, "w", encoding="utf-8") as f:
        f.write(conteudo_md)
    
    print(f"✅ Artigo guardado com sucesso: {nome_arquivo}")
    return True

def rodar_bot():
    print("🎮 A procurar notícias no feed...")
    feed = feedparser.parse(RSS_URL)
    
    novos_posts = 0
    # Processa as 3 notícias mais recentes
    for entrada in feed.entries[:3]:
        if criar_post_hugo(entrada):
            novos_posts += 1
            
    print(f"\n🚀 Sucesso! {novos_posts} artigos publicados no blog.")

if __name__ == "__main__":
    os.makedirs(PASTA_POSTS, exist_ok=True)
    rodar_bot()