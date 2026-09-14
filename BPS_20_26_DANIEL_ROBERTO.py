import os
import glob
import pandas as pd

# 1. Mapear todos os arquivos CSV de 2020 a 2026
arquivos_csv = sorted(glob.glob("20*.csv"))
print(f"Arquivos localizados: {arquivos_csv}")

lista_dfs = []

# 2. Leitura e padronização inicial ano a ano
for arquivo in arquivos_csv:
    print(f"Lendo e processando: {arquivo}...")
    
    # O BPS utiliza ponto e vírgula como separador
    try:
        df_temp = pd.read_csv(arquivo, sep=';', encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        df_temp = pd.read_csv(arquivo, sep=';', encoding='latin1', low_memory=False)
        
    # Padronizar nomes de colunas (caixa baixa e sem espaços nas pontas)
    df_temp.columns = df_temp.columns.str.strip().str.lower()
    
    lista_dfs.append(df_temp)

# 3. Concatenação (Append) de todas as tabelas anuais
print("\nConcatenando as bases...")
df_consolidado = pd.concat(lista_dfs, ignore_index=True)
print(f"Total de registros brutos acumulados: {len(df_consolidado):,}")

# 4. Tratamento de Tipos e Limpeza de Dados

# A) Tratamento de Datas (Formatando para AAAA-MM-DD) e extração do Ano
print("Ajustando formatos de datas...")
df_consolidado['compra'] = pd.to_datetime(df_consolidado['compra'], errors='coerce')
df_consolidado['insercao'] = pd.to_datetime(df_consolidado['insercao'], errors='coerce')
df_consolidado['ano_compra'] = df_consolidado['compra'].dt.year

# B) Tratamento de Valores Monetários e Quantidades
cols_numericas = ['qtd_itens_comprados', 'preco_unitario', 'preco_total']
for col in cols_numericas:
    if col in df_consolidado.columns:
        if df_consolidado[col].dtype == 'object':
            df_consolidado[col] = (
                df_consolidado[col]
                .astype(str)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
        df_consolidado[col] = pd.to_numeric(df_consolidado[col], errors='coerce')

# C) Remoção de Duplicatas Exatas
linhas_antes = len(df_consolidado)
df_consolidado = df_consolidado.drop_duplicates()
duplicadas_removidas = linhas_antes - len(df_consolidado)
print(f"Registros duplicados exatos removidos: {duplicadas_removidas:,}")

# D) Remoção ou Tratamento de Inconsistências Críticas
df_limpo = df_consolidado.dropna(subset=['preco_unitario', 'qtd_itens_comprados', 'preco_total']).copy()
df_limpo = df_limpo[(df_limpo['qtd_itens_comprados'] > 0) & (df_limpo['preco_unitario'] > 0)]

# E) Recálculo de validação do preco_total para garantir integridade
df_limpo['preco_total'] = df_limpo['preco_unitario'] * df_limpo['qtd_itens_comprados']

# 5. Exportar a base final consolidada
nome_arquivo_final = "BPS_20_26_DanielRoberto.csv"
print(f"\nExportando arquivo consolidado para: {nome_arquivo_final}...")
df_limpo.to_csv(nome_arquivo_final, sep=';', index=False, encoding='utf-8-sig')

# Divisão opcional em 2 partes sem precisar ler o arquivo do disco novamente
metade = len(df_limpo) // 2
df_limpo.iloc[:metade].to_csv("BPS_Parte1.csv", sep=';', index=False, encoding='utf-8-sig')
df_limpo.iloc[metade:].to_csv("BPS_Parte2.csv", sep=';', index=False, encoding='utf-8-sig')

print("\n--- PROCESSO CONCLUÍDO COM SUCESSO! ---")
print(f"Total de registros válidos salvos: {len(df_limpo):,}")
print("Arquivos BPS_20_26_DanielRoberto.csv, BPS_Parte1.csv e BPS_Parte2.csv gerados com sucesso!")