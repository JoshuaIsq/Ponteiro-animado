import importação_calibração
import pandas as pd
import numpy as np
import scipy as sp
from scipy import signal
import dearpygui.dearpygui as dpg


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
                print(f"       Média: {series.mean():.2f}, Desvio padrão: {series.std():.2f}")
                print(f"       Outliers detectados: {outliers.sum()} de {len(series)}\n")

    return outlier_mask
    
def remove_outliers(df, window, thresh=3, verbose=False):
    df_copia = df.copy()
    outlier_mask = indentify_outliers(df_copia, window, thresh, verbose)
    df_copia = df_copia.mask(outlier_mask)
    df_copia = df_copia.interpolate(method='linear', limit_direction='both').fillna(0)

    return df_copia.round(4)

def tendency(df, window_size=None): 
    """
    Calcula a TENDÊNCIA GLOBAL (Regressão Linear Simples).
    Gera uma reta única que mostra a direção geral (drift) dos dados.
    """
    df_copia = df.copy()
    tendencia_df = pd.DataFrame()
    
    print("Calculando Regressão Linear")
    
    x_axis = np.arange(len(df_copia))
    
    for col in df_copia.columns:
        y_axis = df_copia[col].values
        
        try:
            #calcula a regressão linear
            coeficientes = np.polyfit(x_axis, y_axis, 1)
            
            # Cria a função da reta: f(x) = ax + b
            funcao_reta = np.poly1d(coeficientes)
            
            # Gera os pontos da reta para plotar
            tendencia_df[col] = funcao_reta(x_axis)
            
        except Exception as e:
            print(f"Erro na regressão global de {col}: {e}")
            tendencia_df[col] = y_axis 

    return tendencia_df.round(4)


def actual_tendency(janela_pontos=None):
    if importação_calibração.DataStorage.df_visualizacao_atual.empty:
        print("[Erro] Nenhum dado disponível.")
        return None
    
    # Não precisamos mais passar janela para essa lógica global
    return tendency(importação_calibração.DataStorage.df_visualizacao_atual)

tempo, sensores = importação_calibração.Load_data("instruções.txt")
media = media_movel(sensores, 50)
print(media)