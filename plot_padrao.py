
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

speed = 0.1
last_speed = 0.1
fase  = 0

#Criando um gráfico de função seno
fig, ax = plt.subplots() #A pyplot exige que crie a figura
plt.title("TESTE MATPLOTLIB")
ax.set_ylim(-3, 3)


#Definição dos eixos
eixo_x = np.arange(0, 10, 0.1)
eixo_y = np.sin(eixo_x) #f(x) = sen(x)

#Plotagem
plot, = plt.plot(eixo_x, eixo_y)
plt.grid(True)

texto_velocimetro = ax.text(0.2, 1.2, f"Velocidade: {speed:.2f}", fontsize=12, color='red')

def on_keyboard(event):
    global speed, last_speedPySide6

    if event.key == " ":
        if speed != 0:
            last_speed = speed
            speed = 0
        elif speed == 0:
            speed == last_speed


    elif event.key == "up":
        speed += 0.2
    
    elif event.key == "down":
        speed -= 0.2

    texto_velocimetro.set_text(f"Velocidade (Freq): {speed:.2f}")


fig.canvas.mpl_connect('key_press_event', on_keyboard)

def animate(i):
    global fase

    fase += speed

    new_y = np.sin(eixo_x + fase) 
    plot.set_ydata(new_y)
    return plot, texto_velocimetro


animation = FuncAnimation(fig, animate, interval=50)


plt.show()


