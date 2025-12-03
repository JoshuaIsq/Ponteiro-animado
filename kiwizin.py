from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.lang import Builder
import math

# --- O DESIGN VISUAL (Linguagem KV) ---
# Aqui definimos a aparência. É como o CSS/HTML do Kivy.
KV_DESIGN = '''
<Dashboard>:
    # Fundo Preto
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # --- 1. O VELOCÍMETRO (GAUGE) ---
    Label:
        text: "TESTE KIVY"
        pos_hint: {"center_x": 0.5, "top": 0.95}
        size_hint: None, None
        font_size: '20sp'
        color: 0.5, 0.5, 0.5, 1

    # Desenhando o Mostrador Circular
    Widget:
        id: gauge
        size_hint: None, None
        size: 200, 200
        pos_hint: {"center_x": 0.5, "center_y": 0.6}
        
        canvas:
            # Círculo de fundo
            Color:
                rgba: 0.2, 0.2, 0.3, 1
            Ellipse:
                pos: self.pos
                size: self.size
                angle_start: 0
                angle_end: 360
            
            # O Ponteiro (Usamos PushMatrix para isolar a rotação)
            PushMatrix
            
            # Movemos a origem para o centro do Widget
            Translate:
                xy: self.center_x, self.center_y
            
            # Rotaciona baseado na propriedade 'angulo_ponteiro' do Python
            Rotate:
                angle: root.angulo_ponteiro
                axis: 0, 0, 1 # Eixo Z
            
            # Desenha o ponteiro (agora estamos no centro 0,0)
            Color:
                rgba: 1, 0, 0, 1 # Vermelho
            Rectangle:
                size: 10, 80
                pos: -5, 0 # Centraliza a largura (10/2 = 5) e aponta pra cima
            
            PopMatrix

    Label:
        text: root.texto_velocidade
        pos_hint: {"center_x": 0.5, "center_y": 0.45}
        font_size: '30sp'
        bold: True

    # --- 2. O GRÁFICO (Canvas Line) ---
    Widget:
        id: graph_area
        size_hint: 0.8, 0.3
        pos_hint: {"center_x": 0.5, "y": 0.05}
        
        canvas:
            # Borda do gráfico
            Color:
                rgba: 0.3, 0.3, 0.3, 1
            Line:
                rectangle: self.x, self.y, self.width, self.height
            
            # A Linha da Senoide
            Color:
                rgba: 0, 1, 1, 1 # Ciano
            Line:
                points: root.pontos_grafico
                width: 2
'''

# Carrega o layout acima
Builder.load_string(KV_DESIGN)

# --- A LÓGICA DO DASHBOARD ---
class Dashboard(FloatLayout):
    # Variáveis Reativas (Se mudar aqui, muda na tela sozinho)
    velocidade = NumericProperty(0.0)
    angulo_ponteiro = NumericProperty(0) # 0 graus
    texto_velocidade = StringProperty("0.00 Hz")
    pontos_grafico = ListProperty([]) # Lista de pontos [x1, y1, x2, y2...]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Variáveis de física interna
        self.fase = 0.0
        self.last_speed = 0.1
        
        # Configurar Teclado
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        
        # Iniciar o Loop de Atualização (60 FPS)
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # keycode[1] dá o nome da tecla (up, down, spacebar)
        key = keycode[1]
        
        if key == 'up':
            self.velocidade += 0.05
            if self.velocidade > 1.0: self.velocidade = 1.0
            
        elif key == 'down':
            self.velocidade -= 0.05
            if self.velocidade < 0: self.velocidade = 0
            
        elif key == 'spacebar':
            if self.velocidade != 0:
                self.last_speed = self.velocidade
                self.velocidade = 0
            else:
                self.velocidade = self.last_speed
        
        return True

    def update(self, dt):
        # 1. Física
        if self.velocidade > 0:
            self.fase += self.velocidade
        
        # 2. Atualizar Ponteiro (Matemática de Rotação)
        # Vamos definir que 0 Hz = -90 graus (Esquerda) e 1 Hz = 90 graus (Direita)
        # Total range 180 graus.
        # No Kivy, 0 graus é topo (Norte). 
        # Então -90 é esquerda, +90 é direita? Depende da orientação.
        # Vamos testar: Velocidade * range + offset
        self.angulo_ponteiro = -90 + (self.velocidade * 180)

        # 3. Atualizar Texto
        self.texto_velocidade = f"{self.velocidade:.2f} Hz"

        # 4. Atualizar Gráfico
        # O Kivy desenha linha com lista [x1, y1, x2, y2, x3, y3...]
        # Precisamos mapear o seno (-1 a 1) para pixels da tela dentro do Widget graph_area
        graph = self.ids.graph_area
        points = []
        
        pontos_na_tela = 100
        passo_x = graph.width / pontos_na_tela
        centro_y = graph.center_y
        altura_onda = graph.height / 2 * 0.8 # 80% da altura
        
        for i in range(pontos_na_tela):
            # Coordenada X (Pixel)
            px = graph.x + (i * passo_x)
            
            # Valor Matemático
            valor_seno = math.sin((i * 0.1) + self.fase)
            
            # Coordenada Y (Pixel)
            py = centro_y + (valor_seno * altura_onda)
            
            points.extend([px, py])
            
        self.pontos_grafico = points

# --- A CLASSE DO APP ---
class VelocimetroApp(App):
    def build(self):
        return Dashboard()

if __name__ == '__main__':
    VelocimetroApp().run()