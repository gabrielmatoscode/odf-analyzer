"""
odfs_not_reported.py - Funcionalidade 1: ODFs sem apontamento.

- Extrai do PDF da Watanabe as ODFs onde ainda não foi realizada a produção da peça (% Prod. < 100%)
- Devolve os dados (tela / Excel) e um PDF com o MESMO layout do original (cabeçalho, fontes,
  espaçamentos, caixinhas), contendo apenas essas ODFs
- Não tem interface gráfica. A leitura e a geração do PDF são feitas pelo odf_reorganizer.py
"""
import odf_reorganizer


def carregar(caminho, agrupar=True):
    """Lê o PDF e devolve (relatorio, estrutura) só com as ODFs sem apontamento.
    agrupar=True  -> códigos iguais ficam juntos (como na funcionalidade 2)
    agrupar=False -> mantém a ordem do PDF original."""
    rel = odf_reorganizer.ler_relatorio(caminho)
    return rel, odf_reorganizer.sem_apontamento(rel, agrupar=agrupar)


def analisar(filepath):
    """Mesmo formato da versão antiga: lista de tuplas (odf, setor, porcentagem) das ODFs com % < 100."""
    _, estrutura = carregar(filepath, agrupar=False)
    saida = []
    for secao, linhas in estrutura:
        titulo = secao.titulo.strip()
        setor = None if titulo in ("-", "") else titulo.split("-", 1)[1].strip()
        for l in linhas:
            saida.append((l.campos["odf"], setor, l.campos["prod"]))
    return saida