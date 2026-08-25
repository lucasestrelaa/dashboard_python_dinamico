<?php
//erros
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Origin: *"); // Permite requisições de outros domínios/front-end
header("Access-Control-Allow-Methods: GET");
//parametros para o get do banco de dados
//url: https://royalblue-turtle-204261.hostingersite.com/ws_dados.php?tipoDado=J&credential=123456&referenciaInicial=2023-01-01&referenciaFinal=2023-12-31
$_GET['tipoDado'] = isset($_GET['tipoDado']) ? $_GET['tipoDado'] : 'J';//json
$_GET['credential'] = isset($_GET['credential']) ? $_GET['credential'] : '';
$_GET['referenciaInicial'] = isset($_GET['referenciaInicial']) ? $_GET['referenciaInicial'] : '';
$_GET['referenciaFinal'] = isset($_GET['referenciaFinal']) ? $_GET['referenciaFinal'] : '';

//parâmetros de conexão com o banco de dados
$host = 'localhost';
$username = 'u856143160_dados';
$password = 'dadosWiz123';
$db_name = 'u856143160_dados';

//conexão com o banco de dados
try {
    // Instancia o PDO
    $pdo = new PDO("mysql:host={$host};dbname={$db_name};charset=utf8", $username, $password);

    // Configura o PDO para lançar exceções em caso de erros
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    // Configura para retornar os dados como array associativo por padrão
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

} catch (PDOException $e) {
    // Retorna erro 500 se não conseguir conectar
    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => "Erro na conexão com o banco de dados: " . $e->getMessage()
    ]);
    exit;
}

// 3. Captura dos Parâmetros via GET (com valores padrão/segurança)
$tipo_pesquisa = isset($_GET['tipo_pesquisa']) ? intval($_GET['tipo_pesquisa']) : 1;
$loja_id = isset($_GET['loja_id']) ? intval($_GET['loja_id']) : null;
$faixa_etaria = isset($_GET['faixa_etaria']) ? trim($_GET['faixa_etaria']) : null;
$regiao = isset($_GET['regiao']) ? trim($_GET['regiao']) : null;
$genero = isset($_GET['genero']) ? trim($_GET['genero']) : null; //M ou F
//visualização nova
$segmentoId = $_GET['segmento_id'] ?? null;
$administradoraId = $_GET['administradora_id'] ?? null;
$dataInicio = $_GET['data_inicio'] ?? null;
$dataFim = $_GET['data_fim'] ?? null;

//tipo_pesquisa 1 => dashboard vendas_mensais
//tipo_pesquisa 2 => dashboard consórcios
//tipo_pesquisa 3 => dashboard bacen
if ($tipo_pesquisa == 1) {
    // Montagem da query SQL
    $sql = "
    SELECT 
        v.id_venda,
        s.nome_segmento AS segmento,
        a.nome_administradora AS administradora,
        v.data_referencia,
        v.quantidade
    FROM vendas_mensais v
    INNER JOIN segmentos s ON v.id_segmento = s.id_segmento
    INNER JOIN administradoras a ON v.id_administradora = a.id_administradora
    WHERE 1=1
";

    $params = [];

    if ($segmentoId) {
        $sql .= " AND v.id_segmento = :id_segmento";
        $params['segmento_id'] = $segmentoId;
    }

    if ($administradoraId) {
        $sql .= " AND v.id_administradora = :id_administradora";
        $params['administradora_id'] = $administradoraId;
    }

    if ($dataInicio) {
        $sql .= " AND v.data_referencia >= :data_inicio";
        $params['data_inicio'] = $dataInicio;
    }

    if ($dataFim) {
        $sql .= " AND v.data_referencia <= :data_fim";
        $params['data_fim'] = $dataFim;
    }

    $sql .= " ORDER BY v.data_referencia DESC, a.nome_administradora ASC";

} else if ($tipo_pesquisa == 2) {
    // 4. Montagem Dinâmica da Consulta SQL com JOINs
    $sql = "SELECT 
            v.id AS venda_id,
            v.data_venda,
            v.valor_total,
            v.faixa_etaria,
            v.genero,
            v.nivel_fidelidade,
            p.nome AS produto,
            p.categoria AS produto_categoria,
            l.nome AS loja,
            l.cidade,
            l.estado,
            l.regiao
        FROM vendas_publico v
        INNER JOIN produtos p ON v.produto_id = p.id
        INNER JOIN lojas l ON v.loja_id = l.id
        WHERE 1=1";

    $params = [];

    // Adiciona filtros se forem informados no GET
    if ($loja_id) {
        $sql .= " AND v.loja_id = :loja_id";
        $params[':loja_id'] = $loja_id;
    }

    if ($faixa_etaria) {
        $sql .= " AND v.faixa_etaria = :faixa_etaria";
        $params[':faixa_etaria'] = $faixa_etaria;
    }

    if ($regiao) {
        $sql .= " AND l.regiao = :regiao";
        $params[':regiao'] = $regiao;
    }

    if ($genero) {
        $sql .= " AND v.genero = :genero";
        $params[':genero'] = $genero;
    }

    $sql .= " ORDER BY v.data_venda DESC";
} else if ($tipo_pesquisa == 3) {
    // 1. Buscar Lista Única de Administradoras
    $sqlAdmins = "SELECT id_administradora AS id, nome_administradora AS nome FROM administradoras ORDER BY nome_administradora ASC";
    
    // 2. Buscar Lista Única de Segmentos
    $sqlSegs = "SELECT id_segmento AS id, nome_segmento AS nome FROM segmentos ORDER BY id_segmento ASC";
    
    // 3. Montagem da Query dos Fatos (Sem JOINs de texto)
    $sql = "
        SELECT 
            f.id AS id,
            f.id_segmento,
            f.id_administradora,
            f.competencia,
            f.taxa_administracao_pct,
            
            -- Saúde e Dinâmica dos Grupos
            f.grupos_ativos,
            f.grupos_constituidos_mes,
            f.grupos_encerrados_mes,
            
            -- Vendas e Oportunidades
            f.cotas_comercializadas_mes AS quantidade,
            f.cotas_excluidas_a_comercializar,
            f.cotas_ativas_contempladas_mes,
            
            -- Carteira Ativa / Adimplência
            f.cotas_ativas_em_dia,
            f.cotas_ativas_contempladas_acum,
            f.cotas_ativas_nao_contempladas,
            
            -- Inadimplência
            f.cotas_ativas_contempladas_inadimplentes,
            f.cotas_ativas_nao_contempladas_inadimplentes,
            
            -- Encerramento e Situações Especiais
            f.cotas_excluidas,
            f.cotas_ativas_quitadas,
            f.cotas_ativas_credito_pendente,
            
            -- Totais Consolidados
            f.cotas_ativas_total,
            f.cotas_excluidas_total,
            f.cotas_comercializadas_total,
            
            -- Percentuais do BACEN
            f.percentual_excluidas,
            f.percentual_ativas
        FROM fato_desempenho_consorcios f
        WHERE 1=1
    ";
    
    $params = [];
    
    if ($segmentoId) {
        $sql .= " AND f.id_segmento = :id_segmento";
        $params['id_segmento'] = $segmentoId;
    }
    
    if ($administradoraId) {
        $sql .= " AND f.id_administradora = :id_administradora";
        $params['id_administradora'] = $administradoraId;
    }
    
    if ($dataInicio) {
        $sql .= " AND f.competencia >= :data_inicio";
        $params['data_inicio'] = $dataInicio;
    }
    
    if ($dataFim) {
        $sql .= " AND f.competencia <= :data_fim";
        $params['data_fim'] = $dataFim;
    }
    
    $sql .= " ORDER BY f.competencia DESC, f.id_administradora ASC";
}


// 5. Execução do Query Preparado
try {
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $dados = $stmt->fetchAll();
    $administradorasList = [];
    if($sqlAdmins){
        $stmtAdmins = $pdo->prepare($sqlAdmins);
        $stmtAdmins->execute();
        $administradorasList = $stmtAdmins->fetchAll(PDO::FETCH_ASSOC);
    }   
    $segmentosList = [];
    if($sqlSegs){
        $stmtSegs = $pdo->prepare($sqlSegs);
        $stmtSegs->execute();
        $segmentosList = $stmtSegs->fetchAll(PDO::FETCH_ASSOC);
    }    


    // 6. Retorno dos Dados em Formato JSON
    http_response_code(200);
    echo json_encode([
        "codigo" => 200,
        "status" => "success",
        "total_registros" => count($dados),
        ...(!empty($administradorasList) ? ["administradoras" => $administradorasList] : []),
        ...(!empty($segmentosList) ? ["segmentos" => $segmentosList] : []),
        "data" => $dados,
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        "codigo" => 500,
        "status" => "error",
        "message" => "Erro ao executar consulta: " . $e->getMessage()
    ]);
}


?>