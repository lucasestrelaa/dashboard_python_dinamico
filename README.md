<div align="center">
  <h1>📊 Dashboard de Análise de Dados - Consórcios BACEN</h1>
  <p><i>Painel interativo para monitoramento de vendas, carteira ativa e inadimplência usando Python, Flask e Plotly.</i></p>

  Com base em dados disponíveis no [Dados do Sistema de Consórcios — ABAC](https://abac.org.br/downloads/dados-do-sistema-de-consorcios/?utm_source=chatgpt.com)

  <!-- Badges indicando as tecnologias -->
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly" />
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas" />
  <img src="https://img.shields.io/badge/PHP-777BB4?style=for-the-badge&logo=php&logoColor=white" alt="PHP" />
  <img src="https://img.shields.io/badge/MySQL-000000?style=for-the-badge&logo=mysql&logoColor=4479A1" alt="MySQL" />
  <img src="https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap" />
</div>

<hr />

<h2>📌 Sobre o Projeto</h2>
<p>
  Este projeto foi desenvolvido para consolidar e visualizar dados operacionais de consórcios consumidos diretamente de uma API REST. 
  A aplicação processa as métricas em tempo real, permite filtragem dinâmica por competência, segmento e administradora, e renderiza os gráficos e KPIs em uma interface web.
</p>

<hr />

<h2>🎯 O que foi realizado</h2>

<ul>
  <li><b>Consumo e Tratamento de Dados:</b> Integração com webservice PHP/MySQL e higienização/mapeamento de dados com Pandas.</li>
  <li><b>Gráfico de Funil:</b> Visualização das etapas de conversão e ciclo de vida das cotas.</li>
  <li><b>Gráfico de Rosca:</b> Composição da carteira dividida entre cotas em dia e inadimplentes.</li>
  <li><b>Evolução Histórica:</b> Gráfico combinado de linhas e eixo secundário para acompanhar o fluxo mensal vs. estoque ativo.</li>
  <li><b>Arquitetura Web & Renderização:</b>
    <ul>
      <li>Script para um servidor web em **Flask**.</li>
      <li>Injeção direta dos gráficos Plotly convertidos em HTML/Divs no template do Flask via Jinja2 (`render_template_string`).</li>
      <li>Tratamento de compatibilidade de transparência e leiaute no Python (`rgba(0,0,0,0)` para evitar quebras de propriedades nativas da biblioteca Plotly).</li>
    </ul>
  </li>
</ul>

<hr />

<h2>🛠️ Tecnologias Utilizadas</h2>

<table>
  <tr>
    <th>Tecnologia</th>
    <th>Descrição / Função</th>
  </tr>
  <tr>
    <td><b>Python 3</b></td>
    <td>Linguagem principal responsável pela regra de negócio e servidor backend.</td>
  </tr>
  <tr>
    <td><b>Flask</b></td>
    <td>Microframework web para subir a aplicação localmente e gerenciar rotas/filtros.</td>
  </tr>
  <tr>
    <td><b>Pandas</b></td>
    <td>Manipulação, agrupamento e filtragem rápida dos DataFrames.</td>
  </tr>
  <tr>
    <td><b>Plotly (Graph Objects)</b></td>
    <td>Geração dos gráficos interativos (Funil, Rosca e Linhas com eixo duplo).</td>
  </tr>
  <tr>
    <td><b>PHP / MySQL</b></td>
    <td>API externa responsável por fornecer o JSON com a base de dados.</td>
  </tr>
  <tr>
    <td><b>Bootstrap 5</b></td>
    <td>Estilização responsiva do painel de controle e tabelas de métricas.</td>
  </tr>
</table>

<hr />

<h2>🚀 Como Executar o Projeto</h2>

<pre><code># 1. Clone o repositório
git clone https://github.com/seu-usuario/seu-repositorio.git

# 2. Acesse a pasta do projeto
cd seu-repositorio

# 3. Instale as dependências
pip install flask pandas plotly requests

# 4. Execute o servidor local
python app.py

# 5.1. Acesse no seu navegador
http://127.0.0.1:5000

# 5.2. Acesse via web
https://royalblue-turtle-204261.hostingersite.com/dash_dinamico.html
</code></pre>

<hr />

<div align="center">
  <p>Desenvolvido por Lucas Estrela.</p>
</div>
