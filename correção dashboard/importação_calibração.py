import pandas as pd
import numpy as np
import scipy as sp
from scipy import signal
import dearpygui.dearpygui as dpg

class DataStorage:
    x_data = []   #Armazena os dados de tempo (eixo x)
    df_sensores = pd.DataFrame() #Armazena os dados dos sensores em um dataframe (eixo Y)
    checkbox_tags = {} #Tag das checkbox dos sensores (lado esquerdo do gráfico)
    colunas_disponiveis = [] #Colunas que estão marcadas para plotagem
    arquivos_acumulados = [] #Arquivos de plotagem acumulados
    df_visualizacao_atual = pd.DataFrame() #Dataframe que está sendo vizualizado com suas respectivas correções

def Load_data(filename):

    if isinstance(filename, str): 
        filenames = [filename] #se filename for string (é um txt), transforma em lista

    if filename:
        for f in filenames:
            if f not in DataStorage.arquivos_acumulados:
                DataStorage.arquivos_acumulados.append(f)


    arquivos_para_processar = DataStorage.arquivos_acumulados #Pega os arquivos acumulados
    lista_dfs_processados = [] #Junta os dataframe de tempo e sensores
    qtd_colunas_padrao = None #check para confirmar a quantidade de colunas

    for arquivo in arquivos_para_processar: #esse loop se repete para cada arquivo que decidi adicionar no software
        if arquivo.endswith('.txt'):
            txt_file = pd.read_csv(arquivo, sep='\t', header=None, engine='python', on_bad_lines='skip' )

            print(f"Lendo arquivo {arquivo}, colunas encontradas: {(txt_file.shape[1])}")

            num_colunas = txt_file.shape[1]
            if qtd_colunas_padrao == None:
                qtd_colunas_padrao = num_colunas
            elif qtd_colunas_padrao != num_colunas:
                print("A quantidade de colunas do arquivo não é compativel")

            colum_time = [0, 1, 2, 3, 4, 5]
            for col in colum_time:
                txt_file[col] = pd.to_numeric(txt_file[col], errors='coerce') #Transforma as 6 primeiras colunas do CSV em numeros
            txt_file[colum_time] = txt_file[colum_time].astype(int)
            time_cols = txt_file.iloc[:, 0:6] 
            time_cols.columns = ["day", "month", "year", "hour", "minute", "second"]
            timestamp = pd.to_datetime(time_cols) #Converto a time_cols em um timestamp
            df_temp = pd.DataFrame({'timestamp': timestamp}) #transformo em UM dataframe só (uma coluna) chamada timestamp

            df_temp = pd.concat([df_temp, txt_file.iloc[:, 6:]], axis=1) #estou concatenando o timestamp criado com os sensores da 6 pra frente
            lista_dfs_processados.append(df_temp) #juntei o dataframe com os sensores na lista 

    df_full = pd.concat(lista_dfs_processados, ignore_index=True) #concatenando todos os arquivos para virarem 1 só

    df_sorted = df_full.sort_values(by='timestamp').reset_index(drop=True) #ordena pos timestamps por ordem, deixando o arquivo organizado
    eixo_x_segundos = (df_sorted['timestamp'].astype('int64') / 10**9).tolist() #os coloca em segundos
    dados_brutos = df_sorted.iloc[:, 1:].copy() #pego as colunas da 1 pra frente (a 0 virou um timestamp) e ficam so os sensores

    for col in dados_brutos.columns:
        dados_brutos[col] = pd.to_numeric(dados_brutos[col], errors='coerce')
            
    sensores = dados_brutos.fillna(0.0)

    return eixo_x_segundos, sensores


def calibration(sensor, factor):

    factor_val = float(factor)
    calibration = sensor * factor
    return calibration


