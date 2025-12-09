'''Escrever aqui a lógica de implementação dos botões como funções'''

# 3. ---------- Criação de botões ---------- #

# 3.1 --------- calculando taxa de plotagem ----- #

def processar_e_plotar(sender, app_data, user_data):
    df_trabalho = df_sensores.copy()
    
    if len(x_data) > 1:
        # Pega o tempo total (Fim - Início)
        tempo_total = x_data[-1] - x_data[0]

        # calcula a média
        if tempo_total > 0:
            # Taxa = Quantos pontos existem / Quanto tempo durou
            taxa_real = len(x_data) / tempo_total
        else:
            taxa_real = 1.0 # Evita divisão por zero se o arquivo tiver tempo zerado
    else:
        taxa_real = 1.0

    # --- 3.2 Adicionando filtros um após o outro ---
    
    # Passo A: Offset
    n_offset = dpg.get_value("input_offset")
    if n_offset > 0:
        df_trabalho = adjust_offset(df_trabalho, n_offset)

    # Passo B: Média Móvel
    janela = dpg.get_value("input_janela_mm")
    if janela > 1:
        df_trabalho = media_movel(df_trabalho, janela)

    # Passo C: Passa Baixa
    corte_low = dpg.get_value("input_passabaixa")
    if corte_low > 0 and corte_low < (taxa_real / 2):
        df_trabalho = filter_low_pass(df_trabalho, corte_low, taxa_real, order=2)

    # Passo D: Passa Alta
    corte_high = dpg.get_value("input_highpass")
    if corte_high > 0 and corte_high < (taxa_real / 2):
        df_trabalho = filter_high_pass(df_trabalho, corte_high, freq_rate=taxa_real, order=2)

    # 3.3 ------ PLOTAGEM ---------
    dpg.delete_item("Eixo Y", children_only=True)
    
    colunas = df_trabalho.columns
    for i in range(min(18, len(colunas))):
        col_name = colunas[i]
        y_vals = df_trabalho[col_name].tolist()
        dpg.add_line_series(x_data, y_vals, parent="Eixo Y", label=f"Canal {col_name}")

    # 3.4 ------- Criando o zoom ------ #
def callback_zomm(sender, app_data):
    x_min, x_max = app_data[0], app_data[1]
    y_min, y_max = app_data[2], app_data[3]
    dpg.set_axis_limits("Eixo X", x_min, x_max)
    dpg.set_axis_limits("Eixo Y", y_min, y_max)


x_data, df_sensores = load_data_converte("LOG_1.txt", 0.00003375)
df_visualizacao = df_sensores.copy()
