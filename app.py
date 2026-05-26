import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").replace('"', '').replace("'", "").strip()

@app.route('/oraculo', methods=['POST'])
def oraculo():
    data = request.json or {}
    budget = data.get('budget', '0')
    market_status = data.get('status', 'Sem dados base.')
    category = data.get('category', 'Geral')

    if not GEMINI_API_KEY:
        return jsonify({
            "title": "ERRO DE AUTENTICAÇÃO", 
            "body": "A chave de API do Gemini não foi encontrada nas variáveis de ambiente do servidor."
        }), 500

    prompt = f"""Você é o CORTEX, um sistema de inteligência algorítmica de hiper-precisão. O usuário tem EXATAMENTE R$ {budget} para investir e selecionou o mercado de: {category}.
    
    Status Global das APIs: {marketDataString}

    REGRAS DO CORTEX:
    1. Aja com a frieza de Ozymandias. Sem saudações. Direto aos números.
    2. NÃO sugira ativos que exigem mais dinheiro do que o orçamento disponível. Se o valor for baixo para a categoria, sugira mercado fracionário ou tokens.
    3. Exija clareza de risco: determine um preço de entrada, um alvo de lucro e um limite de perda (Stop Loss).

    Retorne EXCLUSIVAMENTE um objeto JSON válido neste exato formato técnico:
    {{
        "asset_name": "Nome e Ticker do Ativo (ex: PETR4 ou Bitcoin)",
        "risk_level": "ALTO / MÉDIO / BAIXO",
        "thesis": "Resumo de 3 linhas da anomalia/motivo da escolha cruzando dados.",
        "execution": "Comprar a R$ X. Alvo: R$ Y (+%). Stop: R$ Z (-%)."
    }}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": f"Capital: R$ {budget}. Categoria: {category}. Status: {market_status}"}]}],
        "systemInstruction": {"parts": [{"text": prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=20)
        
        if res.status_code == 200:
            ai_data = res.json()
            raw_text = ai_data['candidates'][0]['content']['parts'][0]['text']
            json_data = json.loads(raw_text)
            return jsonify(json_data)
        else:
            return jsonify({
                "title": "FALHA NA IA", 
                "body": f"A API da IA recusou a conexão. Código: {res.status_code}"
            }), res.status_code

    except Exception as e:
        return jsonify({
            "title": "FALHA CRÍTICA NO SERVIDOR", 
            "body": f"Erro interno no processamento: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
