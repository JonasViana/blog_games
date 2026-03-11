@echo off
echo Iniciando o Bot do Foco Games...

:: 1. Entra na pasta do teu projeto
cd C:\Users\jonas\Desktop\blog-games

:: 2. Corre o teu bot de Python
python bot_noticias.py

:: 3. Envia os novos posts para o GitHub (para o site ir para o ar)
git add content/posts/*.md
git commit -m "Auto: Novas noticias publicadas pelo Bot IA"
git push origin main

echo Processo concluido com sucesso!