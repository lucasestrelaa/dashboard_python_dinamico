# criado por Lucas Estrela - 24/08/2026
# Geração de gráficos para expressar os dados do bacen
# criação de kpis e gráficos com filtros dinâmicos

import os
import json
import requests
import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)

URL_BASE = "https://royalblue-turtle-204261.hostingersite.com/ws_dados.php?tipo_pesquisa=3"

@app.route('/')
def index():
    rawData, rawAdmins, rawSegs = [], [], []

    # Requisição única sem fixar competência
    try:
        response = requests.get(URL_BASE, timeout=15)
        dataJson = response.json()
        
        rawData = dataJson.get("data", [])
        rawAdmins = dataJson.get("administradoras", [])
        rawSegs = dataJson.get("segmentos", [])
    except Exception as e:
        return f"<h3>Erro na requisição dos dados: {e}</h3>", 500

    # Lookups em Python
    map_admin = {item['id']: item['nome'] for item in rawAdmins}
    map_seg = {item['id']: item['nome'] for item in rawSegs}

    # Tratamento dos Dados
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

    # Injeção das dimensões (Lookup)
    df['administradora'] = df['id_administradora'].map(map_admin).fillna('Não Informada')
    df['segmento'] = df['id_segmento'].map(map_seg).fillna('Não Informado')

    df['competencia_str'] = df['competencia'].astype(str)
    df['data_referencia'] = df['competencia_str'].apply(
        lambda x: f"{x[4:]}/{x[:4]}" if len(x) == 6 else "Indefinido"
    )

    # Listas ordenadas para os seletores
    variavel_segmentos = sorted([s for s in df['segmento'].unique() if s])
    variavel_administradoras = sorted([a for a in df['administradora'].unique() if a])

    # Serialização limpa em JSON para o Front-end
    dados_json_str = df.to_json(orient='records')

    # Template HTML com os gráficos
    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel da Carteira de Consórcios</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{
            --primary-blue: #1A4B83;
            --bg-light: #F4F7FA;
            --card-bg: #FFFFFF;
            --border-color: #E0E6ED;
        }}
        body {{ background-color: var(--bg-light); font-family: 'Segoe UI', sans-serif; }}
        .kpi-card {{ border: none; border-radius: 10px; background: var(--card-bg); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .kpi-card-primary {{ background-color: var(--primary-blue); color: white; }}
        .kpi-title {{ font-size: 0.8rem; text-transform: uppercase; opacity: 0.85; }}
        .kpi-value {{ font-size: 1.6rem; font-weight: bold; }}
        .kpi-hint {{ font-size: 0.75rem; opacity: 0.8; margin-top: 4px; }}
        .chart-card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.2rem; min-height: 440px; }}
        .data-panel {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.2rem; min-height: 440px; }}
        .filter-section {{ background: var(--card-bg); border-radius: 10px; padding: 1rem 1.5rem; border: 1px solid var(--border-color); margin-bottom: 1.5rem; }}
        .table-data td {{ font-size: 0.9rem; font-weight: 600; color: #333; }}
        .plot-container {{ height: 370px; width: 100%; }}
    </style>
</head>
<body class="p-4">
    <div class="container-fluid">
        <h2 class="mb-4" style="color: var(--primary-blue); font-weight: bold;">Painel da Carteira de Consórcios</h2>

        <!-- FILTROS DINÂMICOS -->
        <div class="filter-section shadow-sm">
            <div class="row align-items-end g-3">
                <div class="col-md-4">
                    <label for="selectSegmento" class="form-label fw-bold">Segmento:</label>
                    <select id="selectSegmento" class="form-select" onchange="aplicarFiltros()">
                        <option value="TODOS">Todos os Segmentos ({len(variavel_segmentos)})</option>
                        {"".join([f'<option value="{s}">{s}</option>' for s in variavel_segmentos])}
                    </select>
                </div>
                <div class="col-md-5">
                    <label for="selectAdmin" class="form-label fw-bold">Administradora:</label>
                    <select id="selectAdmin" class="form-select" onchange="aplicarFiltros()">
                        <option value="TODOS">Todas as Administradoras ({len(variavel_administradoras)})</option>
                        {"".join([f'<option value="{a}">{a}</option>' for a in variavel_administradoras])}
                    </select>
                </div>
                <div class="col-md-3">
                    <button class="btn btn-primary w-100 fw-bold" onclick="resetarFiltros()">Limpar Filtros</button>
                </div>
            </div>
        </div>

        <!-- KPIS SUPERIORES -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card kpi-card kpi-card-primary p-3">
                    <div class="kpi-title">Vendas Totais do Período</div>
                    <div class="kpi-value" id="kpiVendas">0</div>
                    <div class="kpi-hint">Volume acumulado comercializado</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card kpi-card border p-3">
                    <div class="kpi-title text-muted">Cotas Ativas na Carteira</div>
                    <div class="kpi-value text-primary" id="kpiAtivas">0</div>
                    <div class="kpi-hint text-muted">Total de cotas ativas sob gestão</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card kpi-card border p-3">
                    <div class="kpi-title text-muted">Contemplações no Mês</div>
                    <div class="kpi-value text-success" id="kpiContempladas">0</div>
                    <div class="kpi-hint text-muted">Novas cotas contempladas no período</div>
                </div>
            </div>
        </div>

        <!-- SEÇÃO PRINCIPAL: GRÁFICOS + QUADRO LATERAL DE DADOS -->
        <div class="row mb-4">
            <div class="col-xl-8 col-lg-7">
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="chart-card">
                            <h6 class="fw-bold" style="color: var(--primary-blue);">1. Funil do Ciclo do Consórcio</h6>
                            <div id="chartFunil" class="plot-container"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-card">
                            <h6 class="fw-bold" style="color: var(--primary-blue);">2. Saúde da Carteira</h6>
                            <div id="chartPizza" class="plot-container"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- QUADRO LATERAL DE DADOS -->
            <div class="col-xl-4 col-lg-5">
                <div class="data-panel shadow-sm">
                    <h6 class="fw-bold mb-3 border-bottom pb-2" style="color: var(--primary-blue);">
                        📊 Resumo de Quantidades na Carteira
                    </h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-hover table-borderless table-data align-middle mb-0">
                            <tbody>
                                <tr><td>Vendas no Mês (Quantidade)</td><td class="text-end text-primary" id="tblVendas">0</td></tr>
                                <tr><td>Cotas Ativas em Dia</td><td class="text-end text-success" id="tblEmDia">0</td></tr>
                                <tr><td>Inadimplentes (Não Contemplados)</td><td class="text-end text-warning" id="tblInadNaoCont">0</td></tr>
                                <tr><td>Inadimplentes (Contemplados)</td><td class="text-end text-danger" id="tblInadCont">0</td></tr>
                                <tr class="border-top"><td>Contempladas Acumuladas</td><td class="text-end" id="tblContAcum">0</td></tr>
                                <tr><td>Crédito Pendente de Resgate</td><td class="text-end" id="tblCredPend">0</td></tr>
                                <tr><td>Cotas Quitadas / Concluídas</td><td class="text-end" id="tblQuitadas">0</td></tr>
                                <tr><td>Cancelamentos / Excluídas</td><td class="text-end text-muted" id="tblExcluidas">0</td></tr>
                                <tr class="border-top table-light fw-bold"><td>Total de Cotas Ativas</td><td class="text-end text-primary" id="tblTotalAtivas">0</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- GRÁFICO INFERIOR TEMPORAL -->
        <div class="row">
            <div class="col-md-12">
                <div class="chart-card" style="min-height: 400px;">
                    <h6 class="fw-bold" style="color: var(--primary-blue);">3. Histórico Temporal</h6>
                    <div id="chartHistorico" class="plot-container"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const rawData = {dados_json_str};

        function aplicarFiltros() {{
            const segSelecionado = document.getElementById("selectSegmento").value;
            const adminSelecionada = document.getElementById("selectAdmin").value;

            let dadosFiltrados = rawData.filter(item => {{
                let matchSeg = (segSelecionado === "TODOS" || item.segmento === segSelecionado);
                let matchAdmin = (adminSelecionada === "TODOS" || item.administradora === adminSelecionada);
                return matchSeg && matchAdmin;
            }});

            renderizarPainel(dadosFiltrados);
        }}

        function resetarFiltros() {{
            document.getElementById("selectSegmento").value = "TODOS";
            document.getElementById("selectAdmin").value = "TODOS";
            aplicarFiltros();
        }}

        function renderizarPainel(dados) {{
            let t = {{
                vendas: dados.reduce((a, b) => a + (b.quantidade || 0), 0),
                emDia: dados.reduce((a, b) => a + (b.cotas_ativas_em_dia || 0), 0),
                inadNaoCont: dados.reduce((a, b) => a + (b.cotas_ativas_nao_contempladas_inadimplentes || 0), 0),
                inadCont: dados.reduce((a, b) => a + (b.cotas_ativas_contempladas_inadimplentes || 0), 0),
                contAcum: dados.reduce((a, b) => a + (b.cotas_ativas_contempladas_acum || 0), 0),
                credPend: dados.reduce((a, b) => a + (b.cotas_ativas_credito_pendente || 0), 0),
                quitadas: dados.reduce((a, b) => a + (b.cotas_ativas_quitadas || 0), 0),
                excluidas: dados.reduce((a, b) => a + (b.cotas_excluidas_a_comercializar || 0), 0),
                contMes: dados.reduce((a, b) => a + (b.cotas_ativas_contempladas_mes || 0), 0),
                totalAtivas: dados.reduce((a, b) => a + (b.cotas_ativas_total || 0), 0)
            }};

            // Atualização dos Cards Superiores
            document.getElementById("kpiVendas").innerText = t.vendas.toLocaleString('pt-BR');
            document.getElementById("kpiAtivas").innerText = t.totalAtivas.toLocaleString('pt-BR');
            document.getElementById("kpiContempladas").innerText = t.contMes.toLocaleString('pt-BR');

            // Atualização do Quadro Lateral
            document.getElementById("tblVendas").innerText = t.vendas.toLocaleString('pt-BR');
            document.getElementById("tblEmDia").innerText = t.emDia.toLocaleString('pt-BR');
            document.getElementById("tblInadNaoCont").innerText = t.inadNaoCont.toLocaleString('pt-BR');
            document.getElementById("tblInadCont").innerText = t.inadCont.toLocaleString('pt-BR');
            document.getElementById("tblContAcum").innerText = t.contAcum.toLocaleString('pt-BR');
            document.getElementById("tblCredPend").innerText = t.credPend.toLocaleString('pt-BR');
            document.getElementById("tblQuitadas").innerText = t.quitadas.toLocaleString('pt-BR');
            document.getElementById("tblExcluidas").innerText = t.excluidas.toLocaleString('pt-BR');
            document.getElementById("tblTotalAtivas").innerText = t.totalAtivas.toLocaleString('pt-BR');

            // 1. Plot Funil
            Plotly.react('chartFunil', [{{
                type: 'funnel',
                y: ['1. Vendas', '2. Em Dia', '3. Cont. Acum.', '4. Créd. Pend.', '5. Quitadas'],
                x: [t.vendas, t.emDia, t.contAcum, t.credPend, t.quitadas],
                textinfo: "value+percent initial",
                marker: {{ color: ['#1A4B83', '#28A745', '#17A2B8', '#E67E22', '#8E44AD'] }}
            }}], {{
                height: 350, margin: {{ l: 110, r: 20, t: 10, b: 20 }},
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent'
            }}, {{responsive: true}});

            // 2. Plot Pizza
            Plotly.react('chartPizza', [{{
                type: 'pie', hole: 0.5,
                labels: ['Em Dia', 'Inad. (Não Cont.)', 'Inad. (Cont.)'],
                values: [t.emDia, t.inadNaoCont, t.inadCont],
                marker: {{ colors: ['#28A745', '#E67E22', '#D9534F'] }},
                textinfo: 'percent'
            }}], {{
                height: 350, margin: {{ l: 10, r: 10, t: 10, b: 40 }},
                legend: {{ orientation: 'h', y: -0.15, x: 0 }},
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent'
            }}, {{responsive: true}});

            // 3. Plot Histórico Temporal
            let agrupadoHist = {{}};
            dados.forEach(d => {{
                let c = d.data_referencia;
                if(!agrupadoHist[c]) agrupadoHist[c] = {{ v:0, e:0, m:0 }};
                agrupadoHist[c].v += (d.quantidade || 0);
                agrupadoHist[c].e += (d.cotas_excluidas_a_comercializar || 0);
                agrupadoHist[c].m += (d.cotas_ativas_contempladas_mes || 0);
            }});

            let eixosX = Object.keys(agrupadoHist).sort((a, b) => {{
                let partsA = a.split('/');
                let partsB = b.split('/');
                if(partsA.length < 2 || partsB.length < 2) return 0;
                let dateA = new Date(partsA[1], partsA[0] - 1);
                let dateB = new Date(partsB[1], partsB[0] - 1);
                return dateA - dateB;
            }});

            Plotly.react('chartHistorico', [
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].v), name: 'Vendas', type: 'scatter', mode: 'lines+markers', line: {{ color: '#1A4B83', width: 3 }} }},
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].e), name: 'Cancelamentos', type: 'scatter', mode: 'lines+markers', line: {{ color: '#D9534F', width: 2, dash: 'dot' }} }},
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].m), name: 'Contemplações', type: 'scatter', mode: 'lines+markers', line: {{ color: '#28A745', width: 2 }} }}
            ], {{
                height: 350,
                hovermode: 'x unified',
                margin: {{ l: 60, r: 20, t: 20, b: 60 }},
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
                xaxis: {{ type: 'category', title: 'Competência', tickmode: 'linear' }},
                yaxis: {{ title: 'Quantidade', showgrid: true, gridcolor: '#E0E6ED' }},
                legend: {{ orientation: 'h', y: 1.15, x: 0 }}
            }}, {{responsive: true}});
        }}

        document.addEventListener("DOMContentLoaded", function() {{
            aplicarFiltros();
        }});

        window.addEventListener('resize', function() {{
            Plotly.Plots.resize(document.getElementById('chartFunil'));
            Plotly.Plots.resize(document.getElementById('chartPizza'));
            Plotly.Plots.resize(document.getElementById('chartHistorico'));
        }});
    </script>
</body>
</html>"""

    return render_template_string(html_template)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
