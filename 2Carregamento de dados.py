'''O primeiro comando do software consiste na importação e conversão dos dados de extensometria

a função load_data_converter, realiza o carregamento dos arquivos formato .txt (passível de modificaçã para aceitar mais formatos)
usando a biblioteca pandas ela importar os arquivos, utiliza o sep para considerar espaços em branco como intervalos, não adiciona 
cabeçalho e usa python

Como as 6 primeiras colunas da nossa base de dados correspondem as datas temporais que as medições foram realizadas, nos as separamos das demais
e as classificamos como numeros para facilitar os acessos a essas datas futuramente, além de as classificar como datas, e não
como dados de medição. Após isso, concatena as datas e dados 

Coloca os timestemps na ordem correta, garante que irá começar a medição de dados do primeiro, e logo após a sensores_df os multiplica 
pelo valor de calibração (é possível de ser alterado para o digitar diretamente no código)

possíveis melhorias

- adicionar outros formatos de arquivo
- alterar de quantos em quantos dados plota (talvez deixar como fixo, talvez alterar no front, depende do desempenho geral do software)
- talvez criar a calibração em outra função representando mais limpeza de código (mas aqui ficou simples, talvez dê para alterar, a depender
de ser um valor padrão, de ser um valor alteravel devido a condições fisicas, deixar como uma incognita por hora)

'''

import pandas as pd
import numpy as np
import dearpygui.dearpygui as dpg
import scipy as sp
from scipy import signal

#1 ---------------- Carregar dados do arquivo ------------------ #
def load_data_converte(filename, calibration):

    passo = 1
    if filename.endswith(".txt"):
        #1.1 ------ Importando o meu arquivo txt com leitura extensometrica --------

        txt_file = pd.read_csv(filename, sep=r'[;\s]+', header=None, engine="python") 

        #1.2 ---- Transformando possiveis linhas problematicas em linhas funcionais -----

        # Vamos garantir que as primeiras 6 colunas (tempo) sejam NÚMEROS
        # errors='coerce' transforma tudo que for texto ruim/vazio em NaN (Not a Number)
        cols_tempo_indices = [0, 1, 2, 3, 4, 5]
        for col in cols_tempo_indices:
            txt_file[col] = pd.to_numeric(txt_file[col], errors='coerce')
        
        #1.3 --- Descartando linhas que ficaram em NaN
    
        txt_file = txt_file.dropna(subset=cols_tempo_indices)
        # Converte para inteiro (porque dia 10.0 fica feio, queremos dia 10)
        txt_file[cols_tempo_indices] = txt_file[cols_tempo_indices].astype(int)
            
       
        #1.4 ------ Criando timestamp das horas --------
            #separando como colunas de datas       
        time_cols = txt_file.iloc[:, 0:6] 
        time_cols.columns = ["day", "month", "year", "hour", "minute", "second"]
        timestamp = pd.to_datetime(time_cols) #o pandas transforma em uma linha de colunas e a chama de timestamp
        df_temp = pd.DataFrame({'timestamp': timestamp})
            #concatenando datas feitas no df_temp, os dados da coluna 7 pra frente
        df_data = pd.concat([df_temp, txt_file.iloc[:, 7:]], axis=1)

        df_sorted = df_data.sort_values(by='timestamp').reset_index(drop=True) #coloca os timestemps em ordem
        start_time = df_sorted['timestamp'].iloc[0] #começa do primeiro timestemp

        eixo_x_segundos = (df_sorted['timestamp'] - start_time).dt.total_seconds().tolist() #cria um vetor de quanto tempo foi passado em segundos

            #separa de 0.05 em 0.05 segundos (corrigivél)
        eixo_x_segundos = eixo_x_segundos[::50]
        #pega as linhas da 7 pra frente (dados medidos) e os calibra
        sensores_df = df_sorted.iloc[:, 1:].fillna(0) * calibration
        sensores_df = sensores_df.iloc[::50, :]

        return eixo_x_segundos, sensores_df
        #Ao final a função me retorna o eixo X que mostra quanto tempo passou
        #E sensores_df me respresenta meus sensores ja recebendo o valor de calibração dados
        #Quando eu chamar a função, eu passo pra ela os dados de 
    
    return [], pd.DataFrame()


