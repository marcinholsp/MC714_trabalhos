import simpy
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# ----------------------
# Servidor com fila explícita
# ----------------------
class Servidor:
    def __init__(self, env, id, queue_size= 100, speed=1.0, alpha=0.2):
        self.env = env
        self.id = id
        self.fila = simpy.Store(env, capacity=queue_size)
        self.ocupado = False
        self.times = []
        self.processados = 0
        self.tempo_ocupado = 0
        self.speed = speed  # velocidade de processamento
        self.action = env.process(self.run())
        self.action = env.process(self.run())
        self.alpha = alpha
        self.ema_response = 1.0 

    def run(self):
        while True:
            req = yield self.fila.get()
            self.ocupado = True
            chegada, tipo, tamanho = req

            # tempo de processamento depende do tipo + tamanho
            if tipo == "cpu":
                tempo_proc = (tamanho * random.expovariate(1/2.0)) /  self.speed
            else:  # I/O
                tempo_proc = (tamanho * random.expovariate(1/4.0)) /  self.speed

            inicio = self.env.now
            yield self.env.timeout(tempo_proc)
            fim = self.env.now

            self.times.append(fim - chegada)
            self.processados += 1
            self.tempo_ocupado += (fim - inicio)
            self.ocupado = False
            # Cálculo do tempo de resposta
            tempo_resposta= fim-chegada
            # Atualização do tempo médio de resposta (EMA)
            if self.ema_response is None:
                self.ema_response = tempo_resposta
            else:
                self.ema_response = (
                    self.alpha * tempo_resposta +
                    (1 - self.alpha) * self.ema_response
                )

    def enviar(self, requisicao):
        self.fila.put(requisicao)

# ----------------------
# Balanceador
# ----------------------
class Balanceador:
    def __init__(self, env, servidores, politica="random"):
        self.env = env
        self.servidores = servidores
        self.politica = politica
        self.rr_index = 0

    def encaminhar(self, requisicao):
        if self.politica == "random":
            servidor = random.choice(self.servidores)

        elif self.politica == "roundrobin":
            servidor = self.servidores[self.rr_index % len(self.servidores)]
            self.rr_index += 1

        elif self.politica == "shortest":
            servidor = min(self.servidores, key=lambda s: len(s.fila.items))

        elif self.politica == "Least_Response_Time":
             servidor = min( self.servidores, key=lambda s: s.ema_response )
        elif self.politica== "least_connections":
            servidor = min(self.servidores, key=lambda s: len(s.fila.items) + (1 if s.ocupado else 0))

        elif self.politica == "p2c":  # Power of Two Choices
            candidatos = random.sample(self.servidores, 2)
            servidor = min(candidatos, key=lambda s: len(s.fila.items))

        elif self.politica == "leastload":  # Least-loaded
            servidor = min(self.servidores,
                           key=lambda s: s.tempo_ocupado / (self.env.now + 1e-6))

        elif self.politica == "led":  # Least Expected Delay
            servidor = min(
                self.servidores,
                key=lambda s: (len(s.fila.items) + (1 if s.ocupado else 0)) * (1.0 / s.speed)
            )

        elif self.politica == "adaptive":
            carga_total = sum(len(s.fila.items) for s in self.servidores)
            if carga_total < len(self.servidores):  # carga baixa
                servidor = random.choice(self.servidores)
            else:  # carga alta
                servidor = min(self.servidores, key=lambda s: len(s.fila.items))

        else:
            raise ValueError(f"Política inválida: {self.politica}")

        servidor.enviar(requisicao)


# ----------------------
# Geração de Requisições
# ----------------------
def gerador_requisicoes(env, balanceador, taxa=1.0):
    tipos = ["cpu", "io"]
    while True:
        yield env.timeout(random.expovariate(taxa))  # chegadas exponenciais
        tipo = random.choice(tipos)
        tamanho = random.uniform(1, 5)  # tamanho da requisição (1 a 5 "unidades")
        balanceador.encaminhar((env.now, tipo, tamanho))

# ----------------------
# Simulação
# ----------------------
def simular(politica, taxa_chegada=0.5, tempo_simulacao=5000, seed=42):
    random.seed(seed)
    env = simpy.Environment()
    servidores = [Servidor(env, i, speed= 2**i) for i in range(3)]
    balanceador = Balanceador(env, servidores, politica=politica)

    env.process(gerador_requisicoes(env, balanceador, taxa=taxa_chegada))
    env.run(until=tempo_simulacao)

    tempos = [t for s in servidores for t in s.times]
    total_processados = sum(s.processados for s in servidores)
    throughput = total_processados / tempo_simulacao
    avg_response = np.mean(tempos) if tempos else 0
    utilizacoes = [s.tempo_ocupado / tempo_simulacao for s in servidores]
    utilizacao_media = np.mean(utilizacoes)

    return throughput, avg_response, utilizacao_media

# ----------------------
# Configuração da animação
# ----------------------
#"""random", "roundrobin", "shortest",""" 
politicas = [ "random", "roundrobin", "shortest","p2c", "leastload", "led", "adaptive", "Least_Response_Time","least_connections"]
taxas_chegada = np.linspace(0.2, 10.0, 100)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Subplots para throughput, resposta, utilização
lines = {pol: [] for pol in politicas}
metrics = {pol: {"thr": [], "resp": [], "util": []} for pol in politicas}
#colors = {"random": "tab:blue", "roundrobin": "tab:green", "shortest": "tab:red", "p2c": "tab:orange", "leastload": "tab:purple", "led": "tab:brown", "adaptive": "tab:pink"}
colors = {"random": "tab:blue", "roundrobin": "tab:green", "shortest": "tab:red","p2c": "tab:orange", "leastload": "tab:purple", "led": "tab:brown", "adaptive": "tab:pink", "Least_Response_Time": "tab:grey", "least_connections":"tab:cyan"}

for ax, title in zip(axes, ["Throughput", "Tempo médio de resposta", "Utilização"]):
    ax.set_title(title)
    ax.set_xlabel("Taxa de chegada")

axes[0].set_ylabel("Throughput")
axes[1].set_ylabel("Tempo médio")
axes[2].set_ylabel("Utilização média")

for pol in politicas:
    lines[pol].append(axes[0].plot([], [], marker="o", color=colors[pol], label=pol)[0])
    lines[pol].append(axes[1].plot([], [], marker="o", color=colors[pol], label=pol)[0])
    lines[pol].append(axes[2].plot([], [], marker="o", color=colors[pol], label=pol)[0])

for ax in axes:
    ax.legend()

# Configuração inicial dos eixos
for ax in axes:
    ax.set_xlim(taxas_chegada.min(), taxas_chegada.max())

# Função de inicialização da animação
def init():
    for pol in politicas:
        for l in lines[pol]:
            l.set_data([], [])
    return [l for pol in politicas for l in lines[pol]]

# Função de atualização da animação
def update(frame):
    taxa = taxas_chegada[frame]
    for pol in politicas:
        thr, resp, util = simular(pol, taxa_chegada=taxa)
        metrics[pol]["thr"].append(thr)
        metrics[pol]["resp"].append(resp)
        metrics[pol]["util"].append(util)

        lines[pol][0].set_data(taxas_chegada[:frame+1], metrics[pol]["thr"])
        lines[pol][1].set_data(taxas_chegada[:frame+1], metrics[pol]["resp"])
        lines[pol][2].set_data(taxas_chegada[:frame+1], metrics[pol]["util"])
 # Adicione esta linha para imprimir no terminal:
      #  print(f"Política: {pol} | Taxa: {taxa:.2f} | Throughput: {thr:.4f} | Tempo Médio: {resp:.4f} | Utilização: {util:.4f}")

    # Ajusta limites dinâmicos de Y
    axes[0].relim()
    axes[0].autoscale_view()
    axes[1].relim()
    axes[1].autoscale_view()
    axes[2].relim()
    axes[2].autoscale_view()

    return [l for pol in politicas for l in lines[pol]]

ani = animation.FuncAnimation(
    fig, update, frames=len(taxas_chegada),
    init_func=init, interval=1000, blit=False, repeat=False
)

plt.tight_layout()
plt.show()