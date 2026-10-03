# odf-analyzer

Projeto desenvolvido em Python e aplicado na indústria Watanabe para automatizar processos, reduzir tarefas manuais e otimizar o tempo de trabalho.

O arquivo principal para executar o projeto é o `main.py`, que disponibiliza um menu para selecionar as opções de automação disponíveis, eliminando atividades manuais e reduzindo o tempo gasto em tarefas operacionais.

## Funcionalidades

### **ODFs sem apontamento**

Saiba exatamente onde agir. Com poucos cliques, é possível identificar automaticamente quais Ordens de Fabricação (ODFs) ainda não foram finalizadas pela produção.

Essa funcionalidade não está disponível no ERP utilizado na empresa, sendo necessário realizar esse acompanhamento manualmente sem a automação.

### **Reorganizador**

Imagine a seguinte situação: o operador do setor de Corte recebe um relatório gerado pelo ERP contendo várias peças com os mesmos códigos, porém distribuídas entre diferentes ODFs (Ordens de Fabricação).

Além disso, essas ODFs podem estar espalhadas ao longo do documento, aumentando o risco de alguma Ordem passar despercebida e a peça correspondente não ser produzida.

Com essa função, o relatório em PDF é reorganizado automaticamente, agrupando as peças que possuem o mesmo código e deixando-as uma abaixo da outra.

Dessa forma, o operador consegue visualizar todas as peças semelhantes de maneira organizada, reduzindo a possibilidade de uma ODF passar despercebida e facilitando o planejamento da produção de uma peça.



