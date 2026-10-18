import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Plataforma de Estudos para Concursos")
# ERRADO (faz com que a OpenAI revogue):
# client = OpenAI(api_key="sk-proj-...")

# CORRETO e SEGURO:
client = OpenAI(api_key=os.getenv("Gemini_API_KEY="))

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
    """

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Tema: {dados.tema}\n\nTexto do Aluno:\n{dados.texto}"}
            ]
        )
        return {"resultado": resposta.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gerar-questao")
def gerar_questao(dados: QuestaoFilter):
    prompt_questao = f"""
    Atue como uma banca de concurso público de alto nível ({dados.banca}).
    Crie uma questão inédita de múltipla escolha (com 5 alternativas: A, B, C, D, E) sobre a matéria: {dados.materia}.
    
    Retorne a resposta estritamente no seguinte formato JSON (sem markdown extra, apenas o JSON válido):
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
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_questao}],
            response_format={"type": "json_object"}
        )
        return {"questao": resposta.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
