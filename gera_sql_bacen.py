import pandas as pd

# 1. Carregar planilha
df = pd.read_excel('dados_bacen_abril.xlsx')

# 2. Dicionário de segmentos mapeados (Baseado em segmento_codigo)
segmentos = {
    1: 'Imóveis',
    2: 'Veículos Pesados',
    3: 'Veículos Leves',
    4: 'Motocicletas',
    5: 'Outros Bens',
    6: 'Serviços'
}

# 3. Mapear administradoras únicas para IDs numéricos
admin_unicas = sorted(df['administradora_nome'].dropna().unique())
admin_map = {nome: idx + 1 for idx, nome in enumerate(admin_unicas)}

# Adicionar ID da administradora no DataFrame
df['admin_id'] = df['administradora_nome'].map(admin_map)

# Função para tratar valores nulos / formatar tipos SQL
def fmt(val, is_float=False):
    if pd.isna(val):
        return "NULL"
    return f"{float(val):.6f}" if is_float else str(int(val))

# 4. Exportar comandos SQL para arquivo
with open('insert_script_bacen.sql', 'w', encoding='utf-8') as f:
    
    # --- Inserts de Segmentos ---
    f.write("-- 1. SEGMENTOS\n")
    for seg_id, seg_nome in segmentos.items():
        f.write(f"INSERT INTO segmentos (id_segmento, nome_segmento) VALUES ({seg_id}, '{seg_nome}') ON DUPLICATE KEY UPDATE nome_segmento=VALUES(nome_segmento);\n")
    
    # --- Inserts de Administradoras ---
    f.write("\n-- 2. ADMINISTRADORAS\n")
    for nome_admin, admin_id in admin_map.items():
        nome_escapado = nome_admin.replace("'", "''")
        f.write(f"INSERT INTO administradoras (id_administradora, nome_administradora) VALUES ({admin_id}, '{nome_escapado}') ON DUPLICATE KEY UPDATE nome_administradora=VALUES(nome_administradora);\n")
    
    # --- Inserts de Fato Desempenho / Registros ---
    f.write("\n-- 3. FATO DESEMPENHO CONSORCIOS\n")
    for _, row in df.iterrows():
        sql_insert = (
            f"INSERT INTO fato_desempenho_consorcios ("
            f"id_administradora, id_segmento, competencia, taxa_administracao_pct, "
            f"grupos_ativos, grupos_constituidos_mes, grupos_encerrados_mes, "
            f"cotas_comercializadas_mes, cotas_excluidas_a_comercializar, "
            f"cotas_ativas_contempladas_acum, cotas_ativas_nao_contempladas, "
            f"cotas_ativas_contempladas_mes, cotas_ativas_em_dia, "
            f"cotas_ativas_contempladas_inadimplentes, cotas_ativas_nao_contempladas_inadimplentes, "
            f"cotas_excluidas, cotas_ativas_quitadas, cotas_ativas_credito_pendente, "
            f"cotas_ativas_total, cotas_excluidas_total, cotas_comercializadas_total, "
            f"percentual_excluidas, percentual_ativas"
            f") VALUES ("
            f"{row['admin_id']}, {row['segmento_codigo']}, {row['competencia']}, {fmt(row.get('taxa_administracao_pct'), True)}, "
            f"{fmt(row.get('grupos_ativos'))}, {fmt(row.get('grupos_constituidos_mes'))}, {fmt(row.get('grupos_encerrados_mes'))}, "
            f"{fmt(row.get('cotas_comercializadas_mes'))}, {fmt(row.get('cotas_excluidas_a_comercializar'))}, "
            f"{fmt(row.get('cotas_ativas_contempladas_acum'))}, {fmt(row.get('cotas_ativas_nao_contempladas'))}, "
            f"{fmt(row.get('cotas_ativas_contempladas_mes'))}, {fmt(row.get('cotas_ativas_em_dia'))}, "
            f"{fmt(row.get('cotas_ativas_contempladas_inadimplentes'))}, {fmt(row.get('cotas_ativas_nao_contempladas_inadimplentes'))}, "
            f"{fmt(row.get('cotas_excluidas'))}, {fmt(row.get('cotas_ativas_quitadas'))}, {fmt(row.get('cotas_ativas_credito_pendente'))}, "
            f"{fmt(row.get('cotas_ativas_total'))}, {fmt(row.get('cotas_excluidas_total'))}, {fmt(row.get('cotas_comercializadas_total'))}, "
            f"{fmt(row.get('percentual_excluidas'), True)}, {fmt(row.get('percentual_ativas'), True)}"
            f");\n"
        )
        f.write(sql_insert)

print("Arquivo 'insert_script_bacen.sql' gerado com sucesso!")