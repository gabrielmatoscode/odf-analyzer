# ODF Analyzer

Aplicação desenvolvida em Python para automatizar a leitura e análise de relatórios de ODFs (Ordens de Fabricação) em formato PDF.

O projeto foi desenvolvido e aplicado na **indústria Watanabe**, com o objetivo de reduzir tarefas manuais, otimizar o tempo de trabalho e facilitar a identificação de ODFs que possuem apontamento inferior a 100%.

## Funcionalidades

*  Leitura de relatórios de ODF em PDF
*  Identificação de ODFs com apontamento inferior a 100%
*  Identificação do setor relacionado à ODF
*  Identificação de ODFs terceirizadas
*  Visualização dos resultados em tabela
*  Exportação dos resultados para Excel
*  Exportação dos resultados para PDF
*  Cópia do número da ODF para a área de transferência
*  Interface gráfica em modo escuro

## Setores analisados

O programa identifica os seguintes setores:

* Serra
* Plasma
* Dobra
* Furação
* Usinagem
* Solda
* Acabamento
* Pintura
* Montagem

## Tecnologias utilizadas

* **Python**
* **CustomTkinter** — interface gráfica
* **pdfplumber** — leitura dos arquivos PDF
* **Pandas** — organização e exportação dos dados
* **FPDF** — geração de relatórios em PDF
* **Tkinter / ttk** — componentes da interface

## Objetivo

O projeto surgiu a partir de uma necessidade real de automatização de processos.

Anteriormente, a análise dos relatórios de ODF exigia etapas manuais para identificar as ordens que apresentavam apontamentos inferiores a 100%. O ODF Analyzer automatiza essa etapa, permitindo que os dados sejam analisados de forma mais rápida e organizada.

## Estrutura atual

O projeto foi inicialmente desenvolvido em um único arquivo Python, como parte do processo de aprendizado e desenvolvimento da solução.

Conforme o projeto evoluir, novas funcionalidades e melhorias de organização do código serão implementadas.

## Status

- **Em desenvolvimento**

O projeto continua sendo aprimorado a partir das necessidades identificadas durante sua utilização.

Este repositório contém apenas o código da aplicação.

Arquivos PDF, dados internos, credenciais, tokens e outras informações confidenciais relacionadas à empresa não fazem parte deste projeto.
