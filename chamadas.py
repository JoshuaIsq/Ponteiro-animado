from Import_And_Math import load_data, calibration_factor
from Import_And_Math import media_movel, adjust_offset, filter_low_pass
from Import_And_Math import filter_high_pass, indentify_outliers, remove_outliers, actual_tendency
from Import_And_Math import DataStorage
import pandas as pd
import numpy as np
import dearpygui.dearpygui as dpg
import scipy as sp
from scipy import signal

"""Funções para processar os dados importados e plotar no gráfico.
    Contém as funções:
    processar_e_plotar: Processa os dados e plota no gráfico.
    callback_zomm: Função de callback para zoom no gráfico.
    select_archive: Função para selecionar o arquivo de dados."""

def callback_calibration(sender, app_data, user_data): #Essa função recalcula o fator de calibração (inicialmente 1) quando o usuario clicar no botão
    if DataStorage.df_dados_brutos.empty:
        print("Nenhum dado bruto disponível para calibração.")
        return
    val_calibração = dpg.get_value("input_calibration_factor")
    calibration_factor(val_calibração)
    processar_e_plotar(None, None, None)

def processar_e_plotar(sender, app_data, user_data):

    if DataStorage.df_sensores.empty: 
        if not DataStorage.df_dados_brutos.empty:
            try:
                val_calibração = dpg.get_value("input_calibration_factor")
            except:
                val_calibração = 1.0
            calibration_factor(val_calibração)
        else:
            return

    df_trabalho = DataStorage.df_sensores.copy()

    if len(DataStorage.x_data) > 1:
        tempo_total = DataStorage.x_data[-1] - DataStorage.x_data[0]

        if tempo_total > 0:
            taxa_real = len(DataStorage.x_data) / tempo_total
        else:
            taxa_real = 1.0 
    else:
        taxa_real = 1.0

    print(f"Processando... Taxa: {taxa_real:.2f} Hz")

# ------ Processamento dos dados de filtragem---------  

    n_offset = dpg.get_value("input_offset")
    if n_offset > 0:
        df_trabalho = adjust_offset(df_trabalho, n_offset)

    janela = dpg.get_value("input_janela_mm")
    if janela > 1:
        df_trabalho = media_movel(df_trabalho, janela)

    corte_low = dpg.get_value("input_passabaixa")
    ordem_low = dpg.get_value("input_order_low")
    if corte_low > 0 and ordem_low > 0 and corte_low < (taxa_real / 2):
        df_trabalho = filter_low_pass(df_trabalho, cut_freq=corte_low, sample_rate=taxa_real, order=ordem_low)   

    corte_high = dpg.get_value("input_highpass")
    ordem_high = dpg.get_value("input_order_high")
    if ordem_high > 0 and corte_high > 0 and corte_high < (taxa_real / 2):
        df_trabalho = filter_high_pass(df_trabalho, freq_corte=corte_high, freq_rate=taxa_real, order=ordem_high)

    remove_out = dpg.get_value("input_outliers")
    if remove_out > 0:
        df_trabalho = remove_outliers(df_trabalho, window=remove_out, thresh=3, verbose=False)

     # ------ PLOTAGEM ---------
    dpg.delete_item("eixo_y", children_only=True)

    for col_name in DataStorage.colunas_disponiveis:
        tag_check = DataStorage.checkbox_tags.get(col_name)

        if tag_check and dpg.get_value(tag_check):
            if col_name in df_trabalho.columns:
                value_y = df_trabalho[col_name].tolist()
                dpg.add_line_series(DataStorage.x_data, value_y, parent="eixo_y", label=f"Ext {col_name}")

    DataStorage.df_visualizacao_atual = df_trabalho.copy()



    #  ------- Criando o zoom ------ #
def callback_zomm(sender, app_data):
    x_min, x_max = app_data[0], app_data[1]
    y_min, y_max = app_data[2], app_data[3]
    dpg.set_axis_limits("eixo_x", x_min, x_max)
    dpg.set_axis_limits("eixo_y", y_min, y_max)

# --------- Seleção de arquivo ----------- #

def select_archive(sender, app_data):

    file_to_import = []
    if 'app_data' in app_data and app_data['app_data']:
        file_to_import = list(app_data['app_data'].values())
    elif 'file_path_name' in app_data:
         file_to_import = [app_data['file_path_name']]
    if not file_to_import:
        return 
    
    raw_files = load_data(file_to_import) #Carregando dadosa brutos

    if raw_files:
        try:
            val_calibração = dpg.get_value("input_calibration_factor")
        except:
            val_calibração = 1.0
        calibration_factor(val_calibração)
    
        DataStorage.colunas_disponiveis = DataStorage.df_sensores.columns.tolist()
        dpg.delete_item("grupo_lista_canais", children_only=True) # 2. Reconstrói a lista de Checkboxes
        DataStorage.checkbox_tags.clear()
        
        for col in DataStorage.colunas_disponiveis:
            tag_chk = f"chk_{col}"
            DataStorage.checkbox_tags[col] = tag_chk
            estado = True if col in DataStorage.colunas_disponiveis[:3] else False # Marca os 3 primeiros por padrão
            dpg.add_checkbox(label=f"Ext {col}", tag=tag_chk, default_value=estado, callback=processar_e_plotar, parent="grupo_lista_canais")

        processar_e_plotar(None, None, None)
        dpg.fit_axis_data("eixo_x")
        dpg.fit_axis_data("eixo_y")
        dpg.set_axis_limits("eixo_y",-40, 40)
        

def open_tendency(sender, app_data, user_data): #Existe uma possibilidade de eu mover isso para a parte da interface gráfica
    """Abre uma segunda janela com o gráfico da tendência dos dados atuais.
    Plota a regressão linear dos dados selecionados.
    Mostrando a tendÇencia de estabilidade ou drift dos extensômetros."""

    tag_win = "win_tendencia"
    
    with dpg.theme() as tema_branco: 
        with dpg.theme_component(dpg.mvAll):
            # Fundo Branco 
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (255, 255, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255), category=dpg.mvThemeCat_Core)
            # Texto e Bordas Pretos
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 0, 0), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 255), category=dpg.mvThemeCat_Core)

    if dpg.does_item_exist(tag_win):
        dpg.delete_item(tag_win)
    
    df_tendencia = actual_tendency()
    if df_tendencia is None or df_tendencia.empty:
        return

    with dpg.window(tag=tag_win, label="Extensômetros superiores", width=1000, height=700):
        dpg.bind_item_theme(tag_win, tema_branco)
        
        dpg.add_text("Regressão Linear")
        
        with dpg.plot(label="Extensômetros superiores", height=-1, width=-1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Data / Hora", time=True)
            
            with dpg.plot_axis(dpg.mvYAxis, label="Deslocamento (mm)", tag="eixo_y_tendencia"):
                
                for col_name in DataStorage.colunas_disponiveis:
                    if col_name not in df_tendencia.columns:
                        continue

                    tag_chk = DataStorage.checkbox_tags.get(col_name)
                    if tag_chk and dpg.get_value(tag_chk):
                        y_vals = df_tendencia[col_name].tolist()
                        
                        s = dpg.add_line_series(DataStorage.x_data, y_vals, label=f"Ext {col_name}", parent="eixo_y_tendencia")
                        
    dpg.set_axis_limits("eixo_y_tendencia", -40, 40)                    