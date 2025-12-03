import pandas as pd
import numpy as np
import dearpygui.dearpygui as dpg

#Carregar dados do arquivo
def load_data_converte(filename, calibration):

    if filename.endswith(".txt"):
        #1. Importando código

        txt_file = pd.read_csv(filename, sep=r'[;\s]+', header=None, engine="python") 

# --- BLINDAGEM (NOVO) ---
            # Vamos garantir que as primeiras 6 colunas (tempo) sejam NÚMEROS
            # errors='coerce' transforma tudo que for texto ruim/vazio em NaN (Not a Number)
        cols_tempo_indices = [0, 1, 2, 3, 4, 5]
        for col in cols_tempo_indices:
            txt_file[col] = pd.to_numeric(txt_file[col], errors='coerce')
            
            # Agora jogamos fora (drop) qualquer linha que tenha ficado com NaN no tempo
            # Isso elimina a linha 330581 problemática
        txt_file = txt_file.dropna(subset=cols_tempo_indices)
            
            # Converte para inteiro (porque dia 10.0 fica feio, queremos dia 10)
        txt_file[cols_tempo_indices] = txt_file[cols_tempo_indices].astype(int)
            # ------------------------

        #2. Criando timestamp das horas
        time_cols = txt_file.iloc[:, 0:6] #Colocando o timestamp e as colunas de tempo
        time_cols.columns = ["day", "month", "year", "hour", "minute", "second"]
        timestamp = pd.to_datetime(time_cols)

        #3. Ajustando o tempo e concatenando todas as colunas
        df_temp = pd.DataFrame({'timestamp': timestamp})
        df_data = pd.concat([df_temp, txt_file.iloc[:, 7:]], axis=1)

        df_sorted = df_data.sort_values(by='timestamp').reset_index(drop=True)
        start_time = df_sorted['timestamp'].iloc[0]
        eixo_x_segundos = (df_sorted['timestamp'] - start_time).dt.total_seconds().tolist()

        sensores_df = df_sorted.iloc[:, 1:].fillna(0) * calibration

        return eixo_x_segundos, sensores_df
    
    return [], pd.DataFrame()


x_data, df_sensores = load_data_converte("LOG_1.txt", 0.00003375)

#Inrerface
dpg.create_context()

with dpg.window(tag="Primary Window"):
    dpg.add_text("VISUALIZADOR DE EXTENSOMETRIA", color=(0, 255, 255))
    
    with dpg.plot(label="Sensores - Tensão (MPa)", height=-1, width=-1):
        dpg.add_plot_legend()
        xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo (s)")
        yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="Tensão (MPa)")
        
        if len(x_data) > 0:
            
            colunas_disponiveis = df_sensores.columns
            
            # Vamos plotar os primeiros 5 canais encontrados
            for i in range(min(18, len(colunas_disponiveis))):
                col_name = colunas_disponiveis[i]
                y_sensor = df_sensores[col_name].tolist()
                
                # Adiciona a linha ao gráfico
                # O label será "Canal 7", "Canal 8" baseado na lógica original (+7)
                dpg.add_line_series(x_data, y_sensor, parent=yaxis, label=f"Canal {7+i:02d}")
                
            # Ajuste de Zoom automático
            dpg.fit_axis_data(yaxis)
            dpg.fit_axis_data(xaxis)
            
        else:
            dpg.add_text("Erro ao carregar dados.")

dpg.create_viewport(title='Analise Grafica', width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()