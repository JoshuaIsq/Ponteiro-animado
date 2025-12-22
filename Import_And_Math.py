import pandas as pd
import numpy as np
import scipy as sp
from scipy import signal
import dearpygui.dearpygui as dpg
import random

"""Abre arquivo de medição para análise experimental de tensões
    Contém funções para carregar dados de arquivos .txt (necessário incluir outros futuramente),
    possui as funções
    load_data_converte: Carrega e converte os dados do arquivo.
    calibration_factor: Aplica um fator de calibração aos dados carregados.^
    e tambem possui a classe DataStorage para armazenar os dados importados e processados."""

class DataStorage:
    x_data = [] #Aqui guardo os dados do eixo x (tempo em segundos, posteriormente convertido em data)
    df_dados_brutos = pd.DataFrame() #Aqui guardo os dados brutos para futura calobração
    df_sensores = pd.DataFrame() #Aqui guardo os dados calibrados para serem plotados
    checkbox_tags = {} #Dicionário para armazenar as tags dos checkboxes
    colunas_disponiveis = [] #Lista das colunas disponíveis nos dados
    arquivos_acumulados = [] #Lista dos arquivos já carregados para concatenação
    df_visualizacao_atual = pd.DataFrame()


def load_data(filenames): #1. Importação de mais de um arquivo ao mesmo tempo

    import os
    if isinstance(filenames, str):
        filenames = [filenames]
        
    if filenames:
        for f in filenames:
            if f not in DataStorage.arquivos_acumulados:
                DataStorage.arquivos_acumulados.append(f)
    
    arquivos_para_processar = DataStorage.arquivos_acumulados
    lista_dfs_processados = []
    qtd_colunas_padrao = None 

    print(f"--- INICIANDO LEITURA DE {len(arquivos_para_processar)} ARQUIVOS ---")

    for arquivo in arquivos_para_processar:
        if not arquivo.endswith(".txt"):
            continue
            
        try:
            txt_file = pd.read_csv(arquivo, sep=r'[;\s]+', header=None, engine="python", on_bad_lines="skip")
            print(f"Lendo '{os.path.basename(arquivo)}': Encontradas {txt_file.shape[1]} colunas.") # confirmação visual de igualdade dos arquivos

            num_cols_atual = txt_file.shape[1] ## Verificar se todos os arquivos são do mesmo tipo e são validos-- Amei isso aqui
            if qtd_colunas_padrao is None:
                qtd_colunas_padrao = num_cols_atual
            elif num_cols_atual != qtd_colunas_padrao:
                print(f"[ERRO] Arquivo '{os.path.basename(arquivo)}' ignorado.")
                print(f"       Motivo: Tem {num_cols_atual} colunas, mas o padrão é {qtd_colunas_padrao}.")

            cols_tempo_indices = [0, 1, 2, 3, 4, 5] # Processamento do dataframe
            for col in cols_tempo_indices:
                txt_file[col] = pd.to_numeric(txt_file[col], errors='coerce')
            txt_file = txt_file.dropna(subset=cols_tempo_indices)
            txt_file[cols_tempo_indices] = txt_file[cols_tempo_indices].astype(int)
            time_cols = txt_file.iloc[:, 0:6] 
            time_cols.columns = ["day", "month", "year", "hour", "minute", "second"]
            timestamp = pd.to_datetime(time_cols)
            df_temp = pd.DataFrame({'timestamp': timestamp})
            df_temp = pd.concat([df_temp, txt_file.iloc[:, 6:]], axis=1)
            lista_dfs_processados.append(df_temp)

        except Exception as e:
            print(f"Erro ao ler arquivo {arquivo}: {e}")

    if not lista_dfs_processados:
        print("Nenhum dado válido na memória.")
        return [], pd.DataFrame()

    try:   # 3. Concatenação e Processamento Final
        df_full = pd.concat(lista_dfs_processados, ignore_index=True)
        df_sorted = df_full.sort_values(by='timestamp').reset_index(drop=True) #Mão na roda
        eixo_x_segundos = (df_sorted['timestamp'].astype('int64') / 10**9).tolist()
        dados_brutos = df_sorted.iloc[:, 1:].copy()
        
        for col in dados_brutos.columns:
            dados_brutos[col] = pd.to_numeric(dados_brutos[col], errors='coerce')
        
        DataStorage.df_dados_brutos = dados_brutos.fillna(0.0)
        return True

        print(f"Dados brutos prontos: {len(DataStorage.x_data)} pontos.")

    except Exception as e:
        print(f"Erro CRÍTICO na matemática final: {e}")
        import traceback
        traceback.print_exc() # Mostra onde foi o erro exato
        return [], pd.DataFrame()

def calibration_factor(factor):  #Criei uma função a parte para a calibração, pois agora os dados brutos são armazenados, 
    if DataStorage.df_dados_brutos.empty: #Pega os dados originalmente vazios, antes de serem importados lá no modulo de chamadas, passa uma calibração 1
        return pd.DataFrame()               #Que tambem vai ser alterada la na frente
    try:
        factor = float(factor)
    except:
        factor = 1.0
    print(f"Aplicando fator de calibração: K = {factor}")

    DataStorage.df_sensores = DataStorage.df_dados_brutos * factor
    amount_data = len(DataStorage.df_sensores.columns) #Renomeando as colunas pra manter atualizado
    new_name = [str(i + 1) for i in range(amount_data)]
    DataStorage.df_sensores.columns = new_name
    
    return DataStorage.df_sensores.round(4) 

#2. ---------------- Filtros e ajustes -------------

"""Este trecho contem todas as funções de filtros e ajustes que podem ser aplicados
    Média move: Suaviza os dados aplicando uma média móvel com janela definida pelo usuário.
    Ajuste de offset: Remove o offset inicial dos dados com base na média dos primeiros n pontos.
    Filtro passa baixa: Aplica um filtro Butterworth passa baixa para remover ruídos de alta frequência.
    Filtro passa alta: Aplica um filtro Butterworth passa alta para remover tendências de baixa frequência.
    Identificação de outliers: Detecta pontos fora do padrão usando z-score baseado em média móvel.
    Remoção de outliers: Substitui os outliers identificados por interpolação linear.
    """

def media_movel(df, janela):
    df_copia = df.copy() 
    df_copia = df_copia.rolling(window=int(janela), min_periods=1).mean() 

    return df_copia.round(4)

def adjust_offset(df, n_linhas):
    df_copia = df.copy()
    adjust = df_copia.iloc[:int(n_linhas)].mean()
    df_copia = df_copia - adjust

    return df_copia


def filter_low_pass(df, cut_freq, sample_rate, order):
    df_copia = df.copy()
    nyquisfreq = 0.5 * sample_rate
    low_pass_ratio = cut_freq/nyquisfreq
    b, a = signal.butter(order, low_pass_ratio, btype="lowpass")
    for col in df_copia.columns:
        df_copia[col] = signal.filtfilt(b, a, df_copia[col])

    return df_copia.round(4)


def filter_high_pass(df, freq_corte, freq_rate, order):
    df_copia = df.copy()
    nyquisfreq = 0.5 * freq_rate
    filter_high_pass = freq_corte/nyquisfreq
    b, a = signal.butter(order, filter_high_pass, btype="highpass")
    for col in df_copia.columns:
        df_copia[col] = signal.filtfilt(b, a, df_copia[col])

    return df_copia.round(4)


def indentify_outliers(df, window, thresh=3, verbose=False):
    df_copia = df.copy()
    outlier_mask = pd.DataFrame(False, index=df_copia.index, columns=df_copia.columns)
    for col in df_copia.columns:
        series = df_copia[col]
        rolling_mean = series.rolling(window=window, min_periods=1).mean()
        rolling_std = series.rolling(window=window, min_periods=1).std()
        z_scores = (series - rolling_mean) / rolling_std
        outliers = np.abs(z_scores) > thresh
        outlier_mask[col] = outliers
        if verbose:
                print(f"[INFO] Coluna: {col}")
                print(f"Média: {series.mean():.2f}, Desvio padrão: {series.std():.2f}")
                print(f"Outliers detectados: {outliers.sum()} de {len(series)}\n")

    return outlier_mask
    
def remove_outliers(df, window, thresh=3, verbose=False):
    df_copia = df.copy()
    outlier_mask = indentify_outliers(df_copia, window, thresh, verbose)
    df_copia = df_copia.mask(outlier_mask)
    df_copia = df_copia.interpolate(method='linear', limit_direction='both').fillna(0)

    return df_copia.round(4)

#------- Calculo da tendência global ---------
    """Calcula a TENDÊNCIA GLOBAL (Regressão Linear Simples).
    Gera uma reta única que mostra a direção geral (drift) dos dados.
    """

def tendency(df, window_size=None): 
    df_copia = df.copy()
    tendencia_df = pd.DataFrame()
    print("Calculando Regressão Linear")
    
    x_axis = np.arange(len(df_copia))
    
    for col in df_copia.columns:
        y_axis = df_copia[col].values
        
        try:
            coeficientes = np.polyfit(x_axis, y_axis, 1) #calcula a regressão linear
            funcao_reta = np.poly1d(coeficientes) # Cria a função da reta: f(x) = ax + b
            tendencia_df[col] = funcao_reta(x_axis) # Plota na reta
            
        except Exception as e:
            print(f"Erro na regressão global de {col}: {e}")
            tendencia_df[col] = y_axis 

    return tendencia_df.round(4)


def actual_tendency(janela_pontos=None):
    if DataStorage.df_visualizacao_atual.empty:
        print("[Erro] Nenhum dado disponível.")
        return None
    return tendency(DataStorage.df_visualizacao_atual)