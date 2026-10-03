"""
odfs_not_reported.py - Funcionalidade 1: ODFs sem apontamento (lógica .

- Extrai as ODFs do PDF da Watanabe onde ainda não foi realizada a produção da peça
- Não tem interface gráfica
"""
import pdfplumber as pdftool

SETORES = {
    "1": "SERRA", "2": "PLASMA", "3": "DOBRA", "4": "FURAÇÃO", "5": "USINAGEM",
    "6": "SOLDA", "7": "ACABAMENTO", "8": "PINTURA", "9": "MONTAGEM",
}


def analisar(filepath):
    """Retorna lista de tuplas (odf, setor, porcentagem) das ODFs com % < 100."""
    odf_sem_apontamento = []
    setor_atual = None

    with pdftool.open(filepath) as pdf:
        for paginas in pdf.pages:
            data = paginas.extract_text()
            if not data:
                continue

            for line in data.split("\n"):
                partes = line.strip().split()
                if not partes:                     # (novo) linha vazia não derruba o programa
                    continue

                if len(partes) >= 3 and partes[0] in SETORES and partes[1] == "-":
                    setor_atual = SETORES[partes[0]]
                    continue

                ultima = partes[-1]
                if ultima.upper() in ("NECESSIDADE", "PRODUZIDO"):
                    continue
                if not ultima.endswith("%"):
                    continue

                str_para_valor = ultima.replace("%", "").replace(",", ".")
                if not str_para_valor.replace(".", "", 1).isdigit():
                    continue

                if not (0 <= float(str_para_valor) < 100):
                    continue

                odf = partes[0]
                if not odf.isdigit():
                    continue

                odf_sem_apontamento.append((odf, setor_atual, ultima))

    return odf_sem_apontamento