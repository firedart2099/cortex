import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env (usado para testes locais)
load_dotenv()

app = Flask(__name__)
# O CORS é obrigatório para permitir que o seu frontend (Netlify/Canvas) converse com este backend (Render)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").replace('"', '').replace("'", "").strip()

# --- ROTAS DO FRONTEND ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

# --- ROTA DA INTELIGÊNCIA ---
@app.route('/oraculo', methods=['POST'])
def oraculo():
    data = request.json or {}
    budget = data.get('budget', '0')
    market_status = data.get('status', 'Sem dados base.')

    if not GEMINI_API_KEY:
        return jsonify({
            "title": "ERRO DE AUTENTICAÇÃO", 
            "body": "A chave de API do Gemini não foi encontrada nas variáveis de ambiente do servidor."
        }), 500

    prompt = f"""Você é o consultor financeiro do sistema CORTEX. O usuário tem EXATAMENTE R$ {budget} para investir. Sugira um ativo adequado para esse valor. Escreva de forma natural, clara e profissional, como um analista humano conversando com o cliente. Diga o motivo da escolha, o retorno esperado, os riscos e como ele deve fazer a compra. Retorne EXCLUSIVAMENTE um objeto JSON neste formato: {{"title": "Nome do Ativo", "body": "Explicação natural em texto limpo com quebras de linha."}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": f"Capital do usuário: R$ {budget}. Status: {market_status}"}]}],
        "systemInstruction": {"parts": [{"text": prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=20)
        
        if res.status_code == 200:
            ai_data = res.json()
            raw_text = ai_data['candidates'][0]['content']['parts'][0]['text']
            # Valida e limpa o retorno para garantir que o frontend receba um JSON perfeito
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
    # O Render exige que a porta seja definida dinamicamente pela variável de ambiente PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
