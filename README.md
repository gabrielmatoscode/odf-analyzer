# ODF Analyzer

Aplicação desenvolvida em Python para automatizar processos relacionados à leitura, análise e organização de relatórios de ODFs (Ordens de Fabricação) em formato PDF do ERP.

O projeto foi desenvolvido e aplicado na **indústria Watanabe**, com o objetivo de reduzir tarefas manuais, otimizar o tempo de trabalho e facilitar atividades relacionadas ao acompanhamento e à organização da produção.

## Funcionalidades

Ao executar o programa, um menu permite escolher entre as funcionalidades disponíveis.

### ODFs sem apontamento

Permite identificar automaticamente quais ODFs possuem apontamento inferior a 100%, facilitando a identificação das ordens que ainda possuem etapas de produção não finalizadas.

A funcionalidade também identifica o setor relacionado à ODF e permite visualizar, organizar e exportar os resultados.

**Recursos:**

* Leitura de relatórios de ODF em PDF
* Identificação de ODFs com apontamento inferior a 100%
* Identificação do setor relacionado à ODF
* Identificação de ODFs terceirizadas
* Visualização dos resultados em tabela
* Exportação dos resultados para Excel
* Exportação dos resultados para PDF
* Interface gráfica em modo escuro

### Reorganizador de ODFs

Permite reorganizar relatórios de produção gerados pelo ERP.

Em determinados relatórios, peças com o mesmo código podem estar distribuídas entre diferentes ODFs e espalhadas ao longo do documento. Essa organização dificulta a visualização das peças e aumenta o risco de alguma ODF passar despercebida durante a produção (situação ocorrida diversas vezes).

O Reorganizador recebe o relatório em PDF e reorganiza automaticamente as informações, agrupando as peças que possuem o mesmo código e colocando-as próximas umas das outras.

Dessa forma, o operador consegue visualizar peças iguais de maneira mais organizada, facilitando o planejamento e a programação da produção.

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
* **Pandas** — organização e manipulação dos dados
* **FPDF** — geração de relatórios em PDF
* **Tkinter / ttk** — componentes da interface

## Objetivo

O projeto surgiu a partir de necessidades reais de automatização de processos.

Atividades que anteriormente exigiam análise, conferência e organização manual de informações presentes nos relatórios do ERP foram transformadas em processos automatizados.

O ODF Analyzer reúne essas soluções em uma única aplicação, permitindo selecionar a ferramenta necessária diretamente pelo menu principal.

## Estrutura atual

O projeto foi inicialmente desenvolvido em um único arquivo Python, como parte do processo de aprendizado e desenvolvimento da solução.
Atualmente suas funcionalidades estão dividas em arquivos separados, mostrando evolução e ciência de organização durante desenvolvimento.
Conforme o projeto evoluir, novas funcionalidades e melhorias na organização do código serão implementadas.

## Status

* **Em desenvolvimento**

O projeto continua sendo aprimorado a partir das necessidades identificadas durante sua utilização.

Este repositório contém apenas o código da aplicação.

Arquivos PDF, dados internos, credenciais, tokens e outras informações confidenciais relacionadas à empresa não fazem parte deste projeto.
