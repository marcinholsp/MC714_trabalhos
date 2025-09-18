import simpy
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# ----------------------
# Servidor com fila explícita
# ----------------------
class Servidor:
    def __init__(self, env, id):
        self.env = env
        self.id = id
        self.fila = simpy.Store(env)
        self.ocupado = False
        self.times = []
        self.processados = 0
        self.tempo_ocupado = 0
        self.action = env.process(self.run())

    def run(self):
        while True:
            req = yield self.fila.get()
            self.ocupado = True
            chegada, tipo = req

            # tempo de processamento variável
            if tipo == "cpu":
                tempo_proc = random.uniform(2, 5)
            else:
                tempo_proc = random.uniform(4, 8)

            inicio = self.env.now
            yield self.env.timeout(tempo_proc)
            fim = self.env.now

            self.times.append(fim - chegada)
            self.processados += 1
            self.tempo_ocupado += (fim - inicio)
            self.ocupado = False

    def enviar(self, requisicao):
        self.fila.put(requisicao)

# ----------------------
# Balanceador
# ----------------------
class Balanceador:
    def __init__(self, servidores, politica="random"):
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
        else:
            raise ValueError("Política inválida!")

        servidor.enviar(requisicao)

# ----------------------
# Geração de Requisições
# ----------------------
def gerador_requisicoes(env, balanceador, taxa=1.0):
    tipos = ["cpu", "io"]
    while True:
        yield env.timeout(random.expovariate(taxa))
        tipo = random.choice(tipos)
        balanceador.encaminhar((env.now, tipo))

# ----------------------
# Simulação
# ----------------------
def simular(politica, taxa_chegada=0.5, tempo_simulacao=2000, seed=42):
    random.seed(seed)
    env = simpy.Environment()
    servidores = [Servidor(env, i) for i in range(3)]
    balanceador = Balanceador(servidores, politica=politica)

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
politicas = ["random", "roundrobin", "shortest"]
taxas_chegada = np.linspace(0.2, 4.0, 40)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Subplots para throughput, resposta, utilização
lines = {pol: [] for pol in politicas}
metrics = {pol: {"thr": [], "resp": [], "util": []} for pol in politicas}
colors = {"random": "tab:blue", "roundrobin": "tab:green", "shortest": "tab:red"}

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
        thr, resp, util = simular(pol, taxa_chegada=taxa, tempo_simulacao=200)
        metrics[pol]["thr"].append(thr)
        metrics[pol]["resp"].append(resp)
        metrics[pol]["util"].append(util)

        lines[pol][0].set_data(taxas_chegada[:frame+1], metrics[pol]["thr"])
        lines[pol][1].set_data(taxas_chegada[:frame+1], metrics[pol]["resp"])
        lines[pol][2].set_data(taxas_chegada[:frame+1], metrics[pol]["util"])

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