# Alunos
Márcio Levi Sales Prado - 183680
Carlos Vasco Chironda - 298800
# Descricão 
Este è um trabalho em da disciplina de Sistema Destribuidos 

A ideia fundamental do projecto è a implementação de um servidores e balanceadores de carga que envia os pedidos de cliente ao servidor de otimizada.

# serviodr 
O servidor foi implementato com a biblioteca simpy-PTBR de python.  O que faz:
É um framework de eventos discretos, que permite criar modelos para simular sistemas complexos, como filas de espera, fluxos de pessoas, Servidores etc.
# Balanceadore 

Para gerenciar o fluxo dos pedidos aos servidores e avaliar diferentes métricas como Throughput, Tempo Médio de Resposta e Utilização, implementamos os seguintes algoritmos de balanceamento de carga:
- **Random:** Escolhe aleatoriamente um dos servidores disponíveis para cada nova requisição.
- **Shortest Queue:** Direciona a requisição para o servidor com a menor fila de espera no momento.
- **Round Robin:** Distribui as requisições de forma sequencial entre os servidores, um de cada vez.
- **Least Load:** Seleciona o servidor com menor tempo acumulado de processamento, ou seja, o menos carregado.
- **P2C (Power of Two Choices):** Seleciona dois servidores aleatórios e encaminha a requisição para aquele com a menor fila.
- **Adaptive:** Alterna entre balanceamento aleatório e por menor fila, dependendo da carga total do sistema.
- **Least Response Time:** Escolhe o servidor com o menor tempo médio de resposta estimado.
- **Least Connections:** Direciona a requisição para o servidor com o menor número de conexões ativas no momento.

Esses algoritmos permitem comparar o desempenho do sistema sob diferentes estratégias de distribuição de carga.



# informação adcional
Além do codigo que è possivel visualizar e analisar o codigo implementado è possivel ler o relatório do projecto pedido acesso a atráves do email a:

c298800@unicamp.br

Link github:
https://github.com/marcinholsp/MC714_trabalhos