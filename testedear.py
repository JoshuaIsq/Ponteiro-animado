import dearpygui.dearpygui as dpg
import math

dpg.create_context()

# --- ESTADO ---
speed = 0.0
last_speed = 0.1
fase = 0.0

# Dados
eixo_x = [i/10 for i in range(100)]
eixo_y = [0.0] * 100

# Configurações Visuais
gauge_radius = 110
center_x = 150
center_y = 150

def update_system():
    global speed, fase
    
    # 1. Física
    if speed > 0:
        fase += speed
        new_y = [math.sin(x + fase) for x in eixo_x]
        dpg.set_value("linha_seno", [eixo_x, new_y])

    # 2. Ponteiro (Matemática)
    # 0.0 -> 2.35 rad (135°)
    # 1.0 -> 5.50 rad (315°)
    angle = 2.35 + (speed * (5.5 - 2.35))
    
    tip_x = center_x + (gauge_radius - 15) * math.cos(angle)
    tip_y = center_y + (gauge_radius - 15) * math.sin(angle)
    
    dpg.configure_item("needle", p2=[tip_x, tip_y])
    
    # --- CORREÇÃO DO BUG AQUI ---
    # Para draw_text, usamos configure_item(tag, text=...), e não set_value
    display_speed = int(speed * 100)
    dpg.configure_item("text_speed", text=f"{display_speed}")

def check_input():
    global speed, last_speed
    
    # DICA: Clique na janela do Dashboard para o teclado funcionar!
    if dpg.is_key_down(dpg.mvKey_Up):
        speed = min(speed + 0.01, 1.0)
    if dpg.is_key_down(dpg.mvKey_Down):
        speed = max(speed - 0.01, 0.0)
    if dpg.is_key_pressed(dpg.mvKey_Spacebar):
        if speed != 0:
            last_speed = speed
            speed = 0
        else:
            speed = last_speed

# --- INTERFACE ---
with dpg.window(tag="Primary Window"):
    
    # Estilização Global
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 10), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220), category=dpg.mvThemeCat_Core)
    dpg.bind_theme(global_theme)

    dpg.add_text("TESTE DEARPYGUI", color=(255, 50, 50))
    dpg.add_separator()

    with dpg.group(horizontal=True):
        
        # --- ESQUERDA: O VELOCÍMETRO ---
        with dpg.drawlist(width=300, height=300):
            
            # 1. Aro Externo (Metálico)
            dpg.draw_circle((center_x, center_y), gauge_radius+5, color=(100, 100, 100), thickness=2)
            
            # 2. Aro Interno (Vermelho Escuro / Preto)
            # Simulando o fundo do mostrador
            dpg.draw_circle((center_x, center_y), gauge_radius, color=(30, 30, 30), fill=(0, 0, 0), thickness=0)

            # 3. Marcas de Velocidade (Tracinhos)
            for i in range(11): # 0 a 10
                # Interpolação do ângulo (mesma lógica do ponteiro)
                val = i / 10.0
                a = 2.35 + (val * (5.5 - 2.35))
                
                # Tracinho longo ou curto?
                len_mark = 15 if i % 5 == 0 else 8
                col_mark = (255, 255, 255) if i % 5 == 0 else (150, 150, 150)
                
                x1 = center_x + (gauge_radius - len_mark) * math.cos(a)
                y1 = center_y + (gauge_radius - len_mark) * math.sin(a)
                x2 = center_x + gauge_radius * math.cos(a)
                y2 = center_y + gauge_radius * math.sin(a)
                
                dpg.draw_line((x1, y1), (x2, y2), color=col_mark, thickness=2)

            # 4. Texto Digital Central (Grande)
            # Dica: Centralizar texto desenhado é chato, tem que ajustar o X/Y no olho ou calcular
            dpg.draw_text((center_x - 25, center_y + 10), "0", size=50, tag="text_speed", color=(255, 255, 255))
            dpg.draw_text((center_x - 15, center_y + 40), "hz", size=15, color=(150, 150, 150))

            # 5. O Ponteiro (Vermelho Brilhante)
            dpg.draw_line((center_x, center_y), (center_x, center_y), color=(255, 20, 20), thickness=6, tag="needle")
            
            # Acabamento central (Capa do ponteiro)
            dpg.draw_circle((center_x, center_y), 8, fill=(50, 50, 50), color=(100, 100, 100))

        # --- DIREITA: GRÁFICO ---
        # Padding para afastar um pouco
        dpg.add_spacer(width=20)
        
        with dpg.plot(label="Telemetria da Onda", height=300, width=-1):
            # Tirando o fundo cinza claro padrão do plot para combinar com o painel escuro
            dpg.add_plot_legend()
            xaxis = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo")
            yaxis = dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude")
            #dpg.set_axis_limits(yaxis, -1.5, 1.5)
            
            dpg.add_line_series(eixo_x, eixo_y, parent=yaxis, tag="linha_seno")

# Setup
dpg.create_viewport(title='Velocimetro', width=800, height=450)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

while dpg.is_dearpygui_running():
    check_input()
    update_system()
    dpg.render_dearpygui_frame()

dpg.destroy_context()