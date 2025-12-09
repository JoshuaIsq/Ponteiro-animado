"""Inserir aqui posteriormente aa descrição desse trecho de código"""


#2. ---------------- Filtros e ajustes -------------

#2.1 ------ Média movel ------- 

def media_movel(df, janela):###
    df_copia = df.copy() #criando uma copia do meu dataframe pra não quebrar ele
    df_copia = df_copia.rolling(window=int(janela), min_periods=1).mean() #aplicação do filtro de fato atráves do pandas
    return df_copia.round(4)

#2.2 ------ Ajuste de offset ------- 

def adjust_offset(df, n_linhas):
    df_copia = df.copy()
    adjust = df_copia.iloc[:int(n_linhas)].mean()
    df_copia = df_copia - adjust

    return df_copia

#2.3 ------ Filtro Passa Baixa ------- 

def filter_low_pass(df, cut_freq, sample_rate, order):
    df_copia = df.copy()
    nyquisfreq = 0.5 * sample_rate
    low_pass_ratio = cut_freq/nyquisfreq
    b, a = signal.butter(order, low_pass_ratio, btype="low")
    for col in df_copia.columns:
        df_copia[col] = signal.filtfilt(b, a, df_copia[col])
    return df_copia.round(4)

#2.4 ------- Filtro Passa Alta ------- #

def filter_high_pass(df, freq_corte, freq_rate, order):
    df_copia = df.copy()
    nyquisfreq = 0.5 * freq_rate
    filter_high_pass = freq_corte/nyquisfreq
    b, a = signal.butter(order, filter_high_pass, btype="high")
    for col in df_copia.columns:
        df_copia[col] = signal.filtfilt(b, a, df_copia[col])
    return df_copia.round(4)