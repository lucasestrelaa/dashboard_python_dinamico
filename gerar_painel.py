import os
import pandas as pd
import requests
import plotly.graph_objects as go
from flask import Flask, render_template_string

app = Flask(__name__)

URL_BASE = "https://royalblue-turtle-204261.hostingersite.com/ws_dados.php?tipo_pesquisa=3"

@app.route('/')
def index():
    try:
        response = requests.get(URL_BASE, timeout=15)
        dataJson = response.json()
        df = pd.DataFrame(dataJson.get("data", []))
        map_admin = {item['id']: item['nome'] for item in dataJson.get("administradoras", [])}
        map_seg = {item['id']: item['nome'] for item in dataJson.get("segmentos", [])}
        
        colunas_metricas = [
            'quantidade', 'cotas_ativas_em_dia', 'cotas_ativas_contempladas_acum',
            'cotas_ativas_credito_pendente', 'cotas_ativas_quitadas',
            'cotas_ativas_nao_contempladas_inadimplentes',
            'cotas_ativas_contempladas_inadimplentes', 'cotas_excluidas_a_comercializar',
            'cotas_ativas_contempladas_mes', 'cotas_ativas_total'
        ]
        
        for col in colunas_metricas:
            df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0).astype(int)

        df['administradora'] = df['id_administradora'].map(map_admin).fillna('Não Informada')
        df['segmento'] = df['id_segmento'].map(map_seg).fillna('Não Informado')
        df['competencia_str'] = df['competencia'].astype(str)
        df['data_referencia'] = df['competencia_str'].apply(lambda x: f"{x[4:]}/{x[:4]}" if len(x) == 6 else "Indefinido")

        # Gráfico Funil
        fig_funil = go.Figure(go.Funnel(
            y=['1. Vendas', '2. Em Dia', '3. Cont. Acum.', '4. Créd. Pend.', '5. Quitadas'],
            x=[
                df['quantidade'].sum(),
                df['cotas_ativas_em_dia'].sum(),
                df['cotas_ativas_contempladas_acum'].sum(),
                df['cotas_ativas_credito_pendente'].sum(),
                df['cotas_ativas_quitadas'].sum()
            ],
            marker={"color": ['#1A4B83', '#28A745', '#17A2B8', '#E67E22', '#8E44AD']}
        ))
        fig_funil.update_layout(height=350, margin=dict(l=110, r=20, t=10, b=20))

        html_funil = fig_funil.to_html(full_html=False, include_plotlyjs=False)

        html_final = f"""<!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Painel</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body class="p-4">
            <div class="container">
                <h2>Painel da Carteira (Processado no Render)</h2>
                <div>{html_funil}</div>
            </div>
        </body>
        </html>"""

        return render_template_string(html_final)

    except Exception as e:
        return f"<h3>Erro no processamento Python: {e}</h3>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
