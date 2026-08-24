import os
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from flask import Flask, render_template_string, request

app = Flask(__name__)

URL_BASE = "https://royalblue-turtle-204261.hostingersite.com/ws_dados.php?tipo_pesquisa=3"

def fmt(valor):
    """Auxiliar para formatar números no padrão brasileiro"""
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"

@app.route('/')
def index():
    try:
        response = requests.get(URL_BASE, timeout=15)
        dataJson = response.json()
        rawData = dataJson.get("data", [])
        rawAdmins = dataJson.get("administradoras", [])
        rawSegs = dataJson.get("segmentos", [])
    except Exception as e:
        return f"<h3>Erro na requisição dos dados: {e}</h3>", 500

    map_admin = {item['id']: item['nome'] for item in rawAdmins}
    map_seg = {item['id']: item['nome'] for item in rawSegs}

    df = pd.DataFrame(rawData)
    colunas_metricas = [
        'quantidade', 'cotas_ativas_em_dia', 'cotas_ativas_contempladas_acum',
        'cotas_ativas_credito_pendente', 'cotas_ativas_quitadas',
        'cotas_ativas_nao_contempladas_inadimplentes', 'cotas_ativas_contempladas_inadimplentes',
        'cotas_excluidas_a_comercializar', 'cotas_ativas_contempladas_mes', 'cotas_ativas_total'
    ]

    for col in colunas_metricas:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['administradora'] = df['id_administradora'].map(map_admin).fillna('Não Informada')
    df['segmento'] = df['id_segmento'].map(map_seg).fillna('Não Informado')
    df['competencia_str'] = df['competencia'].astype(str)
    df['data_referencia'] = df['competencia_str'].apply(lambda x: f"{x[4:]}/{x[:4]}" if len(x) == 6 else "Indefinido")
    df['sort_key'] = df['competencia_str'].apply(lambda x: int(x) if len(x) == 6 else 0)
    df = df.sort_values(by='sort_key')

    variavel_segmentos = sorted([s for s in df['segmento'].unique() if s])
    variavel_administradoras = sorted([a for a in df['administradora'].unique() if a])
    competencias_unicas = df[['sort_key', 'data_referencia']].drop_duplicates().sort_values('sort_key')
    variavel_competencias = competencias_unicas['data_referencia'].tolist()

    comp_sel = request.args.get('competencia', 'TODOS')
    seg_sel = request.args.get('segmento', 'TODOS')
    admin_sel = request.args.get('administradora', 'TODOS')

    df_filtrado = df.copy()
    if comp_sel != 'TODOS':
        df_filtrado = df_filtrado[df_filtrado['data_referencia'] == comp_sel]
    if seg_sel != 'TODOS':
        df_filtrado = df_filtrado[df_filtrado['segmento'] == seg_sel]
    if admin_sel != 'TODOS':
        df_filtrado = df_filtrado[df_filtrado['administradora'] == admin_sel]

    meses_unicos = df_filtrado['data_referencia'].unique()
    qtd_meses = len(meses_unicos) if len(meses_unicos) > 0 else 1

    t_vendas = int(df_filtrado['quantidade'].sum())
    t_em_dia = int(df_filtrado['cotas_ativas_em_dia'].sum())
    t_inad_nao_cont = int(df_filtrado['cotas_ativas_nao_contempladas_inadimplentes'].sum())
    t_inad_cont = int(df_filtrado['cotas_ativas_contempladas_inadimplentes'].sum())
    t_cont_acum = int(df_filtrado['cotas_ativas_contempladas_acum'].sum())
    t_cred_pend = int(df_filtrado['cotas_ativas_credito_pendente'].sum())
    t_quitadas = int(df_filtrado['cotas_ativas_quitadas'].sum())
    t_excluidas = int(df_filtrado['cotas_excluidas_a_comercializar'].sum())
    t_cont_mes = int(df_filtrado['cotas_ativas_contempladas_mes'].sum())
    t_total_ativas = int(df_filtrado['cotas_ativas_total'].sum())

    if comp_sel == "TODOS" and len(meses_unicos) > 1:
        ultimo_mes = meses_unicos[-1]
        df_ult = df_filtrado[df_filtrado['data_referencia'] == ultimo_mes]
        t_total_ativas = int(df_ult['cotas_ativas_total'].sum())
        t_em_dia = int(df_ult['cotas_ativas_em_dia'].sum())
        t_inad_nao_cont = int(df_ult['cotas_ativas_nao_contempladas_inadimplentes'].sum())
        t_inad_cont = int(df_ult['cotas_ativas_contempladas_inadimplentes'].sum())

    media_vendas = round(t_vendas / qtd_meses)
    taxa_inad = round(((t_inad_nao_cont + t_inad_cont) / t_total_ativas * 100), 1) if t_total_ativas > 0 else 0

    # 1. Funil
    fig_funil = go.Figure(go.Funnel(
        y=['1. Vendas', '2. Em Dia', '3. Cont. Acum.', '4. Créd. Pend.', '5. Quitadas'],
        x=[t_vendas, t_em_dia, t_cont_acum, t_cred_pend, t_quitadas],
        texttemplate="%{value:.0f}<br>%{percentInitial:.1%}",
        hovertemplate="<b>%{y}</b><br>Quantidade: %{value:.0f}<br><extra></extra>",
        marker={"color": ['#1A4B83', '#28A745', '#17A2B8', '#E67E22', '#8E44AD']}
    ))
    fig_funil.update_layout(
        height=330, 
        margin=dict(l=110, r=20, t=10, b=20), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    div_funil = fig_funil.to_html(full_html=False, include_plotlyjs=False)

    # 2. Pizza
    fig_pizza = go.Figure(go.Pie(
        labels=['Em Dia', 'Inad. (Não Cont.)', 'Inad. (Cont.)'],
        values=[t_em_dia, t_inad_nao_cont, t_inad_cont],
        hole=0.5,
        marker={"colors": ['#28A745', '#E67E22', '#D9534F']},
        textinfo='percent+label'
    ))
    fig_pizza.update_layout(
        height=330, 
        margin=dict(l=10, r=10, t=10, b=30), 
        showlegend=False, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    div_pizza = fig_pizza.to_html(full_html=False, include_plotlyjs=False)

    # 3. Histórico
    df_hist = df_filtrado.groupby(['sort_key', 'data_referencia']).agg({
        'quantidade': 'sum',
        'cotas_ativas_contempladas_mes': 'sum',
        'cotas_excluidas_a_comercializar': 'sum',
        'cotas_ativas_total': 'sum'
    }).reset_index().sort_values('sort_key')

    fig_hist = make_subplots(specs=[[{"secondary_y": True}]])
    fig_hist.add_trace(go.Scatter(x=df_hist['data_referencia'], y=df_hist['quantidade'], name='Vendas no Mês', line=dict(color='#1A4B83', width=3)), secondary_y=False)
    fig_hist.add_trace(go.Scatter(x=df_hist['data_referencia'], y=df_hist['cotas_ativas_contempladas_mes'], name='Contemplações', line=dict(color='#28A745', width=3)), secondary_y=False)
    fig_hist.add_trace(go.Scatter(x=df_hist['data_referencia'], y=df_hist['cotas_excluidas_a_comercializar'], name='Cancelamentos', line=dict(color='#D9534F', width=2, dash='dot')), secondary_y=False)
    fig_hist.add_trace(go.Scatter(x=df_hist['data_referencia'], y=df_hist['cotas_ativas_total'], name='Carteira Ativa', line=dict(color='#6C757D', width=2, dash='dash')), secondary_y=True)

    fig_hist.update_layout(
        height=350, hovermode='x unified', margin=dict(l=50, r=50, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=1.15, x=0)
    )
    fig_hist.update_yaxes(title_text="Fluxo Mensal", secondary_y=False, showgrid=True, gridcolor='#E0E6ED')
    fig_hist.update_yaxes(title_text="Estoque Ativo", secondary_y=True, showgrid=False)
    div_hist = fig_hist.to_html(full_html=False, include_plotlyjs=False)

    html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Painel BACEN - Python Direct</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root { --primary-blue: #1A4B83; --bg-light: #F4F7FA; --card-bg: #FFFFFF; --border-color: #E0E6ED; }
        body { background-color: var(--bg-light); font-family: 'Segoe UI', sans-serif; }
        .kpi-card { border: none; border-radius: 10px; background: var(--card-bg); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .kpi-card-primary { background-color: var(--primary-blue); color: white; }
        .kpi-title { font-size: 0.78rem; text-transform: uppercase; opacity: 0.85; font-weight: 600; }
        .kpi-value { font-size: 1.5rem; font-weight: bold; }
        .chart-card, .data-panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.2rem; min-height: 420px; }
        .filter-section { background: var(--card-bg); border-radius: 10px; padding: 1rem 1.5rem; border: 1px solid var(--border-color); margin-bottom: 1.5rem; }
        .table-data td { font-size: 0.88rem; font-weight: 600; color: #333; }

        /* Estilização da tela de carregamento (Loading) */
        #loading-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(244, 247, 250, 0.85);
            backdrop-filter: blur(4px);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }
        #loading-overlay.hidden {
            opacity: 0;
            visibility: hidden;
        }
    </style>
</head>
<body class="p-4">

    <!-- Screen Loading Overlay -->
    <div id="loading-overlay">
        <div class="spinner-border text-primary mb-3" style="width: 3.5rem; height: 3.5rem;" role="status">
            <span class="visually-hidden">Carregando...</span>
        </div>
        <h5 class="fw-bold" style="color: var(--primary-blue);">Processando dados...</h5>
        <p class="text-muted small">Aguarde a atualização das métricas e gráficos.</p>
    </div>

    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 style="color: var(--primary-blue); font-weight: bold; margin: 0;">Painel de Consórcios</h2>
            <span class="badge bg-success p-2">Execução Backend Python</span>
        </div>

        <form method="GET" action="/" class="filter-section shadow-sm" id="filter-form">
            <div class="row align-items-end g-3">
                <div class="col-md-3">
                    <label class="form-label fw-bold">Competência:</label>
                    <select name="competencia" class="form-select">
                        <option value="TODOS" {% if comp_sel == 'TODOS' %}selected{% endif %}>Todos os Meses ({{ variavel_competencias|length }})</option>
                        {% for c in variavel_competencias %}
                            <option value="{{ c }}" {% if comp_sel == c %}selected{% endif %}>{{ c }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label fw-bold">Segmento:</label>
                    <select name="segmento" class="form-select">
                        <option value="TODOS" {% if seg_sel == 'TODOS' %}selected{% endif %}>Todos os Segmentos ({{ variavel_segmentos|length }})</option>
                        {% for s in variavel_segmentos %}
                            <option value="{{ s }}" {% if seg_sel == s %}selected{% endif %}>{{ s }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label fw-bold">Administradora:</label>
                    <select name="administradora" class="form-select">
                        <option value="TODOS" {% if admin_sel == 'TODOS' %}selected{% endif %}>Todas ({{ variavel_administradoras|length }})</option>
                        {% for a in variavel_administradoras %}
                            <option value="{{ a }}" {% if admin_sel == a %}selected{% endif %}>{{ a }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2 d-flex gap-2">
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Filtrar</button>
                    <a href="/" class="btn btn-outline-secondary fw-bold" onclick="showLoading()">Limpar</a>
                </div>
            </div>
        </form>

        <div class="row mb-4 g-3">
            <div class="col-md-2"><div class="card kpi-card kpi-card-primary p-3"><div class="kpi-title">Vendas</div><div class="kpi-value">{{ fmt(t_vendas) }}</div></div></div>
            <div class="col-md-2"><div class="card kpi-card border p-3"><div class="kpi-title text-muted">Média Mensal</div><div class="kpi-value text-primary">{{ fmt(media_vendas) }}</div></div></div>
            <div class="col-md-3"><div class="card kpi-card border p-3"><div class="kpi-title text-muted">Cotas Ativas</div><div class="kpi-value text-dark">{{ fmt(t_total_ativas) }}</div></div></div>
            <div class="col-md-2"><div class="card kpi-card border p-3"><div class="kpi-title text-muted">Contemplações</div><div class="kpi-value text-success">{{ fmt(t_cont_mes) }}</div></div></div>
            <div class="col-md-3"><div class="card kpi-card border p-3"><div class="kpi-title text-muted">Taxa Inadimplência</div><div class="kpi-value text-danger">{{ taxa_inad }}%</div></div></div>
        </div>

        <div class="row mb-4">
            <div class="col-xl-8 col-lg-7">
                <div class="row g-3">
                    <div class="col-md-6"><div class="chart-card"><h6 class="fw-bold" style="color: var(--primary-blue);">1. Funil de Conversão</h6>{{ div_funil|safe }}</div></div>
                    <div class="col-md-6"><div class="chart-card"><h6 class="fw-bold" style="color: var(--primary-blue);">2. Composição da Carteira</h6>{{ div_pizza|safe }}</div></div>
                </div>
            </div>
            <div class="col-xl-4 col-lg-5">
                <div class="data-panel shadow-sm">
                    <h6 class="fw-bold mb-3 border-bottom pb-2" style="color: var(--primary-blue);">📊 Métricas Consolidadas</h6>
                    <table class="table table-sm table-hover table-borderless table-data align-middle mb-0">
                        <tbody>
                            <tr><td>Vendas Comercializadas</td><td class="text-end text-primary">{{ fmt(t_vendas) }}</td></tr>
                            <tr><td>Cotas Ativas em Dia</td><td class="text-end text-success">{{ fmt(t_em_dia) }}</td></tr>
                            <tr><td>Inadimplentes (Não Contemplados)</td><td class="text-end text-warning">{{ fmt(t_inad_nao_cont) }}</td></tr>
                            <tr><td>Inadimplentes (Contemplados)</td><td class="text-end text-danger">{{ fmt(t_inad_cont) }}</td></tr>
                            <tr class="border-top"><td>Contempladas Acumuladas</td><td class="text-end">{{ fmt(t_cont_acum) }}</td></tr>
                            <tr><td>Crédito Pendente de Resgate</td><td class="text-end">{{ fmt(t_cred_pend) }}</td></tr>
                            <tr><td>Cotas Quitadas / Concluídas</td><td class="text-end">{{ fmt(t_quitadas) }}</td></tr>
                            <tr><td>Cancelamentos / Excluídas</td><td class="text-end text-muted">{{ fmt(t_excluidas) }}</td></tr>
                            <tr class="border-top table-light fw-bold"><td>Total de Cotas Ativas</td><td class="text-end text-primary">{{ fmt(t_total_ativas) }}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="chart-card">
                    <h6 class="fw-bold" style="color: var(--primary-blue);">3. Evolução Histórica Mês a Mês</h6>
                    {{ div_hist|safe }}
                </div>
            </div>
        </div>
    </div>

    <script>
        // Oculta a tela de carregamento quando tudo estiver renderizado
        window.addEventListener('load', function () {
            document.getElementById('loading-overlay').classList.add('hidden');
        });

        // Exibe o loading manualmente
        function showLoading() {
            document.getElementById('loading-overlay').classList.remove('hidden');
        }

        // Exibe o loading ao disparar a busca do formulário
        document.getElementById('filter-form').addEventListener('submit', function () {
            showLoading();
        });
    </script>
</body>
</html>"""

    return render_template_string(
        html_template,
        fmt=fmt,
        comp_sel=comp_sel, seg_sel=seg_sel, admin_sel=admin_sel,
        variavel_competencias=variavel_competencias,
        variavel_segmentos=variavel_segmentos,
        variavel_administradoras=variavel_administradoras,
        t_vendas=t_vendas, media_vendas=media_vendas, t_total_ativas=t_total_ativas,
        t_cont_mes=t_cont_mes, taxa_inad=taxa_inad, t_em_dia=t_em_dia,
        t_inad_nao_cont=t_inad_nao_cont, t_inad_cont=t_inad_cont, t_cont_acum=t_cont_acum,
        t_cred_pend=t_cred_pend, t_quitadas=t_quitadas, t_excluidas=t_excluidas,
        div_funil=div_funil, div_pizza=div_pizza, div_hist=div_hist
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
