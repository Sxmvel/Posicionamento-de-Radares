# 📡 Simulador GRASP - Posicionamento de Radares

Este repositório contém a implementação da metaheurística **GRASP** (Greedy Randomized Adaptive Search Procedure) com Busca Local Tabu para solucionar o 
Problema de Localização com Máxima Cobertura (MCLP), aplicado ao cenário estratégico de posicionamento de radares de vigilância.

O projeto foi desenvolvido com uma interface gráfica interativa que permite a visualização em tempo real do espaço de busca, geração de dados dinâmicos e acompanhamento das iterações da metaheurística.

---

## 🚀 Funcionalidades

* **Geração Dinâmica de Instâncias:** Criação de pontos de demanda e locais candidatos aleatórios dentro de um grid visual.
* **Heurística Construtiva:** Geração de solução inicial viável de forma gulosa-aleatória.
* **Busca Local (Swap 1-opt):** Refinamento da solução trocando um radar ativo por um inativo, buscando o melhor ganho de cobertura (Steepest Ascent/Best Improvement).
* **Lista Tabu:** Memória de curto prazo estruturada para impedir a reavaliação de movimentos recentes e quebrar ciclos ótimos locais.
* **Métricas em Tempo Real:** Acompanhamento do tempo de execução, número de iterações, tamanho da lista tabu e porcentagem de área coberta.
* **Exportação:** Geração de relatórios de execução em `.txt` e exportação do mapa de cobertura em `.png`.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.x**
* **Tkinter / ttkbootstrap:** Para a construção da interface gráfica moderna.
* **Matplotlib:** Para a renderização do gráfico de evolução da cobertura.
* **Pillow (PIL):** Para a captura e exportação visual do canvas.

---

## ⚙️ Instruções de Instalação e Execução

Certifique-se de ter o Python instalado na sua máquina. O projeto requer bibliotecas externas que podem ser instaladas via `pip`.
Clone o projeto com este comando: git clone https://github.com/Sxmvel/Posicionamento-de-Radares.git
Abra o terminal e instale as dependências:
- pip install ttkbootstrap matplotlib pillow
Executando o Simulador


Link do video de apresentação do projeto:


Desenvolvido por Samuel Resende Silva - RA:0083170.
Bacharelado em Sistemas de Informação – 5º Período
Instituto Federal de Minas Gerais (IFMG) - Campus Ouro Branco
