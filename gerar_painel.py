# Criado por Lucas Estrela
# Geração de gráficos para expressar os dados do BACEN
# Atualizado para análise multi-mês com filtros dinâmicos de competência, segmento e administradora

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

    # Requisição única dos dados BACEN
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

    # Ordenação temporal real
    df['sort_key'] = df['competencia_str'].apply(lambda x: int(x) if len(x) == 6 else 0)
    df = df.sort_values(by='sort_key')

    # Listas ordenadas para os seletores
    variavel_segmentos = sorted([s for s in df['segmento'].unique() if s])
    variavel_administradoras = sorted([a for a in df['administradora'].unique() if a])
    
    # Lista de competências ordenadas
    competencias_unicas = df[['sort_key', 'data_referencia']].drop_duplicates().sort_values('sort_key')
    variavel_competencias = competencias_unicas['data_referencia'].tolist()

    # Serialização em JSON
    dados_json_str = df.to_json(orient='records')

    # Template HTML
    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel da Carteira de Consórcios BACEN</title>
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
        .kpi-title {{ font-size: 0.78rem; text-transform: uppercase; opacity: 0.85; font-weight: 600; }}
        .kpi-value {{ font-size: 1.5rem; font-weight: bold; }}
        .kpi-hint {{ font-size: 0.75rem; opacity: 0.8; margin-top: 4px; }}
        .chart-card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.2rem; min-height: 420px; }}
        .data-panel {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.2rem; min-height: 420px; }}
        .filter-section {{ background: var(--card-bg); border-radius: 10px; padding: 1rem 1.5rem; border: 1px solid var(--border-color); margin-bottom: 1.5rem; }}
        .table-data td {{ font-size: 0.88rem; font-weight: 600; color: #333; }}
        .plot-container {{ height: 350px; width: 100%; }}
    </style>
</head>
<body class="p-4">
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 style="color: var(--primary-blue); font-weight: bold; margin: 0;">Painel da Carteira de Consórcios</h2>
            <span class="badge bg-secondary p-2">Série Temporal Expandida</span>
        </div>

        <div class="filter-section shadow-sm">
            <div class="row align-items-end g-3">
                <div class="col-md-3">
                    <label for="selectCompetencia" class="form-label fw-bold">Competência (Mês/Ano):</label>
                    <select id="selectCompetencia" class="form-select" onchange="aplicarFiltros()">
                        <option value="TODOS">Todos os Meses ({len(variavel_competencias)})</option>
                        {"".join([f'<option value="{c}">{c}</option>' for c in variavel_competencias])}
                    </select>
                </div>
                <div class="col-md-3">
                    <label for="selectSegmento" class="form-label fw-bold">Segmento:</label>
                    <select id="selectSegmento" class="form-select" onchange="aplicarFiltros()">
                        <option value="TODOS">Todos os Segmentos ({len(variavel_segmentos)})</option>
                        {"".join([f'<option value="{s}">{s}</option>' for s in variavel_segmentos])}
                    </select>
                </div>
                <div class="col-md-4">
                    <label for="selectAdmin" class="form-label fw-bold">Administradora:</label>
                    <select id="selectAdmin" class="form-select" onchange="aplicarFiltros()">
                        <option value="TODOS">Todas as Administradoras ({len(variavel_administradoras)})</option>
                        {"".join([f'<option value="{a}">{a}</option>' for a in variavel_administradoras])}
                    </select>
                </div>
                <div class="col-md-2">
                    <button class="btn btn-outline-primary w-100 fw-bold" onclick="resetarFiltros()">Limpar Filtros</button>
                </div>
            </div>
        </div>

        <div class="row mb-4 g-3">
            <div class="col-md-2">
                <div class="card kpi-card kpi-card-primary p-3">
                    <div class="kpi-title">Vendas Acumuladas</div>
                    <div class="kpi-value" id="kpiVendas">0</div>
                    <div class="kpi-hint">Total comercializado</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card kpi-card border p-3">
                    <div class="kpi-title text-muted">Média Mensal Vendas</div>
                    <div class="kpi-value text-primary" id="kpiMediaVendas">0</div>
                    <div class="kpi-hint text-muted">Média / mês no período</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card kpi-card border p-3">
                    <div class="kpi-title text-muted">Cotas Ativas (Base Gestão)</div>
                    <div class="kpi-value text-dark" id="kpiAtivas">0</div>
                    <div class="kpi-hint text-muted">Base sob gestão atual</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card kpi-card border p-3">
                    <div class="kpi-title text-muted">Contemplações</div>
                    <div class="kpi-value text-success" id="kpiContempladas">0</div>
                    <div class="kpi-hint text-muted">Cotas contempladas</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card kpi-card border p-3">
                    <div class="kpi-title text-muted">Taxa Inadimplência</div>
                    <div class="kpi-value text-danger" id="kpiTaxaInad">0%</div>
                    <div class="kpi-hint text-muted">% Inadimplentes na base</div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-xl-8 col-lg-7">
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="chart-card">
                            <h6 class="fw-bold" style="color: var(--primary-blue);">1. Funil de Conversão do Consórcio</h6>
                            <div id="chartFunil" class="plot-container"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-card">
                            <h6 class="fw-bold" style="color: var(--primary-blue);">2. Composição da Carteira de Ativos</h6>
                            <div id="chartPizza" class="plot-container"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-xl-4 col-lg-5">
                <div class="data-panel shadow-sm">
                    <h6 class="fw-bold mb-3 border-bottom pb-2" style="color: var(--primary-blue);">
                        📊 Resumo de Métricas Consolidadas
                    </h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-hover table-borderless table-data align-middle mb-0">
                            <tbody>
                                <tr><td>Vendas Comercializadas</td><td class="text-end text-primary" id="tblVendas">0</td></tr>
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

        <div class="row">
            <div class="col-md-12">
                <div class="chart-card" style="min-height: 420px;">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold" style="color: var(--primary-blue); margin:0;">3. Evolução Histórica Mês a Mês</h6>
                        <small class="text-muted">Acompanhamento contínuo dos meses disponíveis</small>
                    </div>
                    <div id="chartHistorico" class="plot-container" style="height: 370px;"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const rawData = {dados_json_str};

        function aplicarFiltros() {{
            const compSelecionada = document.getElementById("selectCompetencia").value;
            const segSelecionado = document.getElementById("selectSegmento").value;
            const adminSelecionada = document.getElementById("selectAdmin").value;

            let dadosFiltrados = rawData.filter(item => {{
                let matchComp = (compSelecionada === "TODOS" || item.data_referencia === compSelecionada);
                let matchSeg = (segSelecionado === "TODOS" || item.segmento === segSelecionado);
                let matchAdmin = (adminSelecionada === "TODOS" || item.administradora === adminSelecionada);
                return matchComp && matchSeg && matchAdmin;
            }});

            renderizarPainel(dadosFiltrados, compSelecionada);
        }}

        function resetarFiltros() {{
            document.getElementById("selectCompetencia").value = "TODOS";
            document.getElementById("selectSegmento").value = "TODOS";
            document.getElementById("selectAdmin").value = "TODOS";
            aplicarFiltros();
        }}

        function renderizarPainel(dados, compSelecionada) {{
            let mesesUnicos = [...new Set(dados.map(d => d.data_referencia))];
            let qtdMeses = mesesUnicos.length || 1;

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

            if(compSelecionada === "TODOS" && mesesUnicos.length > 1) {{
                let ultimoMes = mesesUnicos[mesesUnicos.length - 1];
                let dadosUltimoMes = dados.filter(d => d.data_referencia === ultimoMes);
                t.totalAtivas = dadosUltimoMes.reduce((a, b) => a + (b.cotas_ativas_total || 0), 0);
                t.emDia = dadosUltimoMes.reduce((a, b) => a + (b.cotas_ativas_em_dia || 0), 0);
                t.inadNaoCont = dadosUltimoMes.reduce((a, b) => a + (b.cotas_ativas_nao_contempladas_inadimplentes || 0), 0);
                t.inadCont = dadosUltimoMes.reduce((a, b) => a + (b.cotas_ativas_contempladas_inadimplentes || 0), 0);
            }}

            let mediaVendasMensal = Math.round(t.vendas / qtdMeses);
            let taxaInadimplencia = t.totalAtivas > 0 ? (((t.inadNaoCont + t.inadCont) / t.totalAtivas) * 100).toFixed(1) : 0;

            document.getElementById("kpiVendas").innerText = t.vendas.toLocaleString('pt-BR');
            document.getElementById("kpiMediaVendas").innerText = mediaVendasMensal.toLocaleString('pt-BR');
            document.getElementById("kpiAtivas").innerText = t.totalAtivas.toLocaleString('pt-BR');
            document.getElementById("kpiContempladas").innerText = t.contMes.toLocaleString('pt-BR');
            document.getElementById("kpiTaxaInad").innerText = taxaInadimplencia.replace('.', ',') + "%";

            document.getElementById("tblVendas").innerText = t.vendas.toLocaleString('pt-BR');
            document.getElementById("tblEmDia").innerText = t.emDia.toLocaleString('pt-BR');
            document.getElementById("tblInadNaoCont").innerText = t.inadNaoCont.toLocaleString('pt-BR');
            document.getElementById("tblInadCont").innerText = t.inadCont.toLocaleString('pt-BR');
            document.getElementById("tblContAcum").innerText = t.contAcum.toLocaleString('pt-BR');
            document.getElementById("tblCredPend").innerText = t.credPend.toLocaleString('pt-BR');
            document.getElementById("tblQuitadas").innerText = t.quitadas.toLocaleString('pt-BR');
            document.getElementById("tblExcluidas").innerText = t.excluidas.toLocaleString('pt-BR');
            document.getElementById("tblTotalAtivas").innerText = t.totalAtivas.toLocaleString('pt-BR');

            // 1. Plot Funil com textos traduzidos e formatados
            Plotly.react('chartFunil', [{{
                type: 'funnel',
                y: ['1. Vendas', '2. Em Dia', '3. Cont. Acum.', '4. Créd. Pend.', '5. Quitadas'],
                x: [t.vendas, t.emDia, t.contAcum, t.credPend, t.quitadas],
                texttemplate: "%{{value:,.0f}}<br>%{{percentInitial:.1%}}",
                hovertemplate: 
                    "<b>%{{y}}</b><br>" +
                    "Quantidade: %{{value:,.0f}}<br>" +
                    "%{{percentInitial:.1%}} do inicial<br>" +
                    "%{{percentPrevious:.1%}} do anterior<br>" +
                    "%{{percentTotal:.1%}} do total" +
                    "<extra></extra>",
                marker: {{ color: ['#1A4B83', '#28A745', '#17A2B8', '#E67E22', '#8E44AD'] }}
            }}], {{
                height: 330, 
                margin: {{ l: 110, r: 20, t: 10, b: 20 }},
                paper_bgcolor: 'transparent', 
                plot_bgcolor: 'transparent'
            }}, {{
                responsive: true,
                locale: 'pt-BR',
                locales: {{
                    'pt-BR': {{
                        format: {{
                            thousands: '.',
                            grouping: [3]
                        }}
                    }}
                }}
            }});

            // 2. Plot Pizza
            Plotly.react('chartPizza', [{{
                type: 'pie', hole: 0.5,
                labels: ['Em Dia', 'Inad. (Não Cont.)', 'Inad. (Cont.)'],
                values: [t.emDia, t.inadNaoCont, t.inadCont],
                marker: {{ colors: ['#28A745', '#E67E22', '#D9534F'] }},
                textinfo: 'percent+label'
            }}], {{
                height: 330, margin: {{ l: 10, r: 10, t: 10, b: 30 }},
                showlegend: false,
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent'
            }}, {{responsive: true}});

            // 3. Agrupamento para o Gráfico Histórico Multi-Mês
            let agrupadoHist = {{}};
            dados.forEach(d => {{
                let c = d.data_referencia;
                let sortKey = d.sort_key;
                if(!agrupadoHist[c]) agrupadoHist[c] = {{ sortKey: sortKey, v:0, e:0, m:0, a:0 }};
                agrupadoHist[c].v += (d.quantidade || 0);
                agrupadoHist[c].e += (d.cotas_excluidas_a_comercializar || 0);
                agrupadoHist[c].m += (d.cotas_ativas_contempladas_mes || 0);
                agrupadoHist[c].a += (d.cotas_ativas_total || 0);
            }});

            let eixosX = Object.keys(agrupadoHist).sort((a, b) => agrupadoHist[a].sortKey - agrupadoHist[b].sortKey);

            Plotly.react('chartHistorico', [
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].v), name: 'Vendas no Mês', type: 'scatter', mode: 'lines+markers', line: {{ color: '#1A4B83', width: 3 }} }},
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].m), name: 'Contemplações no Mês', type: 'scatter', mode: 'lines+markers', line: {{ color: '#28A745', width: 3 }} }},
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].e), name: 'Cancelamentos', type: 'scatter', mode: 'lines+markers', line: {{ color: '#D9534F', width: 2, dash: 'dot' }} }},
                {{ x: eixosX, y: eixosX.map(k => agrupadoHist[k].a), name: 'Evolução Carteira Ativa', type: 'scatter', mode: 'lines+markers', yaxis: 'y2', line: {{ color: '#6C757D', width: 2, dash: 'dash' }} }}
            ], {{
                height: 350,
                hovermode: 'x unified',
                margin: {{ l: 50, r: 50, t: 20, b: 40 }},
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
                xaxis: {{ type: 'category', title: 'Competência' }},
                yaxis: {{ title: 'Fluxo Mensal (Cotas)', showgrid: true, gridcolor: '#E0E6ED' }},
                yaxis2: {{ title: 'Estoque de Ativas', overlaying: 'y', side: 'right', showgrid: false }},
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
