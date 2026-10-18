import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Plataforma de Estudos para Concursos")

# Inicializa o cliente do Gemini utilizando a chave salva nas variáveis de ambiente
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Redacao(BaseModel):
    banca: str
    tema: str
    texto: str

class QuestaoFilter(BaseModel):
    banca: str
    materia: str

@app.get("/", response_class=HTMLResponse)
def carregar_pagina():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/corrigir")
def corrigir_redacao(dados: Redacao):
    if len(dados.texto.strip()) < 50:
        raise HTTPException(status_code=400, detail="Sua redação precisa ter pelo menos 50 caracteres.")

    prompt_sistema = f"""
    Você é um examinador especialista em redações para concursos públicos, focado na banca {dados.banca}.
    Analise o texto considerando a norma culta, coerência, coesão, estrutura e adequação ao tema.
    
    Forneça o resultado formatado de forma clara:
    1. Nota Estimada (de 0 a 10)
    2. Avaliação por Critérios (Gramática, Estrutura e Conteúdo)
    3. Pontos de Erro Detectados
    4. Recomendações Práticas de Melhoria
    
    Tema: {dados.tema}
    Texto do Aluno:
    {dados.texto}
    """

    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_sistema,
        )
        return {"resultado": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gerar-questao")
def gerar_questao(dados: QuestaoFilter):
    prompt_questao = f"""
    Atue como uma banca de concurso público de alto nível ({dados.banca}).
    Crie uma questão inédita de múltipla escolha (com 5 alternativas: A, B, C, D, E) sobre a matéria: {dados.materia}.
    
    Retorne a resposta estritamente no seguinte formato JSON (sem marcadores de markdown como ```json, apenas a string JSON pura e válida):
    {{
      "enunciado": "Texto completo da questão...",
      "alternativas": [
        "A) ...",
        "B) ...",
        "C) ...",
        "D) ...",
        "E) ..."
      ],
      "gabarito": "Letra correta (ex: A)",
      "comentario": "Explicação detalhada do porquê a alternativa correta está certa e as outras erradas, fundamentada na doutrina/lei."
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_questao,
        )
        return {"questao": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
