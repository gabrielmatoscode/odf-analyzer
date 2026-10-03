"""
odf_reorganizer.py  -  Funcionalidade 2: Reorganizar ODFs por Código.

Este arquivo NÃO tem interface gráfica. Ele só:
  1. lê o PDF original do relatório de ODFs (posição exata de cada linha, traço e caixinha);
  2. reordena as linhas de cada setor para que códigos iguais fiquem juntos;
  3. gera um PDF novo com o layout IDÊNTICO ao original (mesma fonte, mesmos espaçamentos,
     mesmo cabeçalho, mesmas caixinhas, mesma numeração de páginas);
  4. entrega os dados em formato de tabela (para exportar para Excel).

Como o layout é preservado? -- IA Claude
  - O TEXTO de cada linha é copiado do PDF original (mesma fonte Arial embutida),
    só que colocado numa nova posição vertical.
  - Os TRAÇOS (divisórias, caixinhas, faixa cinza do setor, retângulo do cabeçalho)
    são redesenhados com exatamente a mesma espessura/cor/coordenadas, só deslocados.

Dependência:  pip install pymupdf
"""

import re
from dataclasses import dataclass, field

import pymupdf as fitz

# ----------------------------------------------------------------------------
# Constantes de layout (medidas no relatório original)
# ----------------------------------------------------------------------------
LARGURA_PAGINA = 595
ALTURA_PAGINA = 842
TOPO_PAGINAS_SEGUINTES = 14.16   # y do topo da 1ª linha nas páginas 2, 3, 4...
GAP_ENTRE_SETORES = 10.92        # distância entre o fim da última linha e a faixa cinza do setor
X_CAIXINHA = 566.88              # x da borda esquerda da caixinha de cada linha
TOL = 0.05

# limites das colunas (ODF, Código, Descrição, Máquina, Qtde, Saldo, % Prod.)
COLUNAS = [(0, 47), (47, 96.4), (96.4, 336.8), (336.8, 455.8),
           (455.8, 496), (496, 531.5), (531.5, 567)]
NOMES_COLUNAS = ["odf", "codigo", "descricao", "maquina", "qtde", "saldo", "prod"]


# ----------------------------------------------------------------------------
# Estruturas de dados
# ----------------------------------------------------------------------------
@dataclass
class Linha:
    pagina: int            # página de origem (0-based)
    top: float             # y do topo na página de origem
    bottom: float          # y da base na página de origem
    graficos: list         # traços que pertencem a esta linha
    campos: dict           # odf, codigo, descricao, maquina, qtde, saldo, prod
    setor: str = ""

    @property
    def altura(self):
        return self.bottom - self.top


@dataclass
class Secao:
    titulo: str            # ex.: "1 - SERRA"  (ou "-" para ODFs sem setor)
    pagina: int
    y0: float              # y da faixa cinza na página de origem
    altura_titulo: float   # da faixa cinza até o topo da 1ª linha (faixa + cabeçalho das colunas)
    graficos: list
    gap: float = GAP_ENTRE_SETORES
    linhas: list = field(default_factory=list)


@dataclass
class Relatorio:
    caminho: str
    cabecalho_altura: float          # de 0 até a faixa do 1º setor (página 1)
    cabecalho_graficos: list
    secoes: list
    n_paginas_origem: int



# ----------------------------------------------------------------------------
# Leitura dos traços diretamente dos operadores do PDF original
# (assim conseguimos reemiti-los IDÊNTICOS, só com outra posição vertical)
# ----------------------------------------------------------------------------
_NUM = r"(-?\d*\.?\d+)"
_SEG = r"1 0 0 1 %s %s cm 0 0 m\n%s %s l\nS" % (_NUM, _NUM, _NUM, _NUM)
_RE_BLOCO = re.compile(r"q (?:0 0 0 RG \d J \d j \.72 w 10 M \[\] 0 d /GS1 gs 1 i )?" + _SEG + r"((?: " + _SEG + r")*)\nQ")
_RE_SEG = re.compile(_SEG)
_RE_RETANGULO = re.compile(r"(?<![\w.])%s %s %s %s re\nS\n" % (_NUM, _NUM, _NUM, _NUM))
_RE_PREENCHIDO = re.compile(r"((?:%s ){3})rg[\n ]%s %s %s %s re\nf\n" % (_NUM, _NUM, _NUM, _NUM, _NUM))
_RE_ESTADO = re.compile(r"(\d) J (\d) j")


def _fmt(v):
    t = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if t in ("-0", "") else t


def _graficos(page):
    """Lista os traços da página como dicts {type, rect, emit(dy)}."""
    altura = page.rect.height
    txt = page.read_contents().decode("latin1")
    achados = []
    for m in _RE_BLOCO.finditer(txt):
        achados.append((m.start(), "bloco", m))
    for m in _RE_RETANGULO.finditer(txt):
        achados.append((m.start(), "retangulo", m))
    for m in _RE_PREENCHIDO.finditer(txt):
        achados.append((m.start(), "preenchido", m))
    achados.sort(key=lambda a: a[0])

    def estado_em(pos):
        ult = None
        for e in _RE_ESTADO.finditer(txt, 0, pos):
            ult = e
        return (ult.group(1), ult.group(2)) if ult else ("0", "0")

    graficos = []
    for pos, tipo, m in achados:
        J, j = estado_em(pos)
        g = m.groups()
        if tipo == "bloco":
            # um bloco q..Q pode encadear vários traços (cm relativos): separa em segmentos absolutos
            X, Y, DX, DY = (float(v) for v in g[:4])
            segs = [(X, Y, DX, DY)]
            cx, cy = X, Y
            for sm in _RE_SEG.finditer(g[4] or ""):
                ddx, ddy, sdx, sdy = (float(v) for v in sm.groups())
                cx, cy = cx + ddx, cy + ddy
                segs.append((cx, cy, sdx, sdy))
            for (X, Y, DX, DY) in segs:
                rect = fitz.Rect(min(X, X + DX), altura - max(Y, Y + DY),
                                 max(X, X + DX), altura - min(Y, Y + DY))

                def emit(dy, X=X, Y=Y, DX=DX, DY=DY, J=J, j=j):
                    return ("q 0 0 0 RG %s J %s j .72 w 10 M [] 0 d /GS1 gs 1 i 1 0 0 1 %s %s cm 0 0 m\n%s %s l\nS\nQ\n"
                            % (J, j, _fmt(X), _fmt(Y - dy), _fmt(DX), _fmt(DY)))
                graficos.append({"type": "s", "rect": rect, "emit": emit})
        elif tipo == "retangulo":
            X, Y, W, H = (float(v) for v in g)
            rect = fitz.Rect(min(X, X + W), altura - max(Y, Y + H),
                             max(X, X + W), altura - min(Y, Y + H))

            def emit(dy, X=X, Y=Y, W=W, H=H, J=J, j=j):
                return ("q 0 0 0 RG %s J %s j .72 w 10 M [] 0 d /GS1 gs 1 i %s %s %s %s re\nS\nQ\n"
                        % (J, j, _fmt(X), _fmt(Y - dy), _fmt(W), _fmt(H)))
            graficos.append({"type": "s", "rect": rect, "emit": emit})
        else:
            cor = g[0].strip()
            X, Y, W, H = (float(v) for v in g[-4:])
            rect = fitz.Rect(min(X, X + W), altura - max(Y, Y + H),
                             max(X, X + W), altura - min(Y, Y + H))

            def emit(dy, cor=cor, X=X, Y=Y, W=W, H=H):
                return "q %s rg %s %s %s %s re\nf\nQ\n" % (cor, _fmt(X), _fmt(Y - dy), _fmt(W), _fmt(H))
            graficos.append({"type": "f", "rect": rect, "emit": emit})
    return graficos


# ----------------------------------------------------------------------------
# Leitura do PDF
# ----------------------------------------------------------------------------
def _e_horizontal(d):
    return d["rect"].height < 0.01


def _texto_apenas(caminho):
    """Cópia do PDF só com o texto (sem nenhum traço/preenchimento)."""
    doc = fitz.open(caminho)
    for p in doc:
        p.add_redact_annot(p.rect, fill=False)
        p.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                           graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
                           text=fitz.PDF_REDACT_TEXT_NONE)
    return doc


def _campos_da_linha(palavras, top, bottom):
    campos = {n: [] for n in NOMES_COLUNAS}
    for w in palavras:
        cy = (w[1] + w[3]) / 2
        if not (top - 0.5 <= cy <= bottom + 0.5):
            continue
        cx = (w[0] + w[2]) / 2
        for (a, b), nome in zip(COLUNAS, NOMES_COLUNAS):
            if a <= cx < b:
                campos[nome].append(w)
                break
    saida = {}
    for nome, ws in campos.items():
        ws.sort(key=lambda w: (round(w[1] / 3), w[0]))
        textos = [w[4] for w in ws]
        # o código pode quebrar de linha no meio (ex.: "W1.20.CAN" + ".002")
        saida[nome] = ("".join(textos) if nome == "codigo" else " ".join(textos)).strip()
    return saida


def ler_relatorio(caminho):
    doc = fitz.open(caminho)
    secoes, cab_graficos, cab_altura = [], [], 0
    secao_atual = None

    for pno, page in enumerate(doc):
        desenhos = _graficos(page)
        palavras = page.get_text("words")

        faixas = sorted([d for d in desenhos if d["type"] == "f" and d["rect"].width > 500],
                        key=lambda d: d["rect"].y0)

        # --- linhas: cada uma tem uma caixinha (vertical em x=566.88)
        caixas = sorted({(round(d["rect"].y0, 2), round(d["rect"].y1, 2))
                         for d in desenhos if d["type"] == "s"
                         and abs(d["rect"].x0 - X_CAIXINHA) < TOL
                         and d["rect"].width < 0.01 and d["rect"].height > 10})
        divisorias = sorted({round(d["rect"].y0, 2) for d in desenhos if d["type"] == "s"
                             and _e_horizontal(d) and d["rect"].x0 < 100
                             and d["rect"].x1 < 100 and d["rect"].x0 > 14})
        linhas_pag = []
        for (t, b) in caixas:
            base = next((s for s in divisorias if s >= b - TOL), None)
            if base is None:
                raise ValueError("Estrutura de linha não reconhecida (página %d)." % (pno + 1))
            linhas_pag.append([t, base])

        # --- distribui os traços entre cabeçalho / faixas / linhas
        usados = set()
        eventos = [("faixa", f["rect"].y0, f) for f in faixas] + \
                  [("linha", t, (t, b)) for t, b in linhas_pag]
        eventos.sort(key=lambda e: e[1])

        # 1) cabeçalho (só existe antes da 1ª faixa da página 1)
        if pno == 0 and faixas:
            y_primeira = faixas[0]["rect"].y0
            for i, d in enumerate(desenhos):
                if d["rect"].y1 < y_primeira - 1:
                    cab_graficos.append(d)
                    usados.add(i)
            cab_altura = y_primeira

        # 2) faixas cinza
        info_faixa = {}
        for f in faixas:
            y0, y1 = f["rect"].y0, f["rect"].y1
            gs = []
            for i, d in enumerate(desenhos):
                if i in usados:
                    continue
                if d is f or (d["rect"].y0 >= y0 - 0.01 and d["rect"].y1 <= y1 + 0.01):
                    gs.append(d)
                    usados.add(i)
            info_faixa[id(f)] = gs

        # 3) traços de cada linha
        info_linha = {}
        for t, base in linhas_pag:
            gs = []
            for i, d in enumerate(desenhos):
                if i in usados:
                    continue
                r = d["rect"]
                caixa = r.x0 >= X_CAIXINHA - TOL
                if caixa:
                    # bordas da caixinha: topo em t, base em t+altura da caixa
                    tb = [c for c in caixas if abs(c[0] - t) < TOL]
                    if tb and (abs(r.y0 - tb[0][0]) < TOL or abs(r.y0 - tb[0][1]) < TOL
                               or abs(r.y1 - tb[0][1]) < TOL) and r.y0 >= t - TOL and r.y1 <= tb[0][1] + TOL:
                        gs.append(d); usados.add(i)
                elif _e_horizontal(d) and abs(r.y0 - base) < TOL:
                    gs.append(d); usados.add(i)
            info_linha[t] = gs

        sobra = [d for i, d in enumerate(desenhos) if i not in usados]
        if sobra:
            raise ValueError("Traços não reconhecidos na página %d (%d)." % (pno + 1, len(sobra)))

        # --- percorre em ordem vertical montando seções e linhas
        for tipo, y, obj in eventos:
            if tipo == "faixa":
                titulo_ws = [w for w in palavras
                             if obj["rect"].y0 - 1 <= (w[1] + w[3]) / 2 <= obj["rect"].y1 + 1
                             and w[0] < 300]
                titulo_ws.sort(key=lambda w: w[0])
                titulo = " ".join(w[4] for w in titulo_ws)
                # topo da 1ª linha logo abaixo da faixa (na mesma página)
                seguintes = [t for t, _ in linhas_pag if t > obj["rect"].y1]
                if not seguintes:
                    raise ValueError("Setor sem linhas no fim da página %d." % (pno + 1))
                altura_titulo = seguintes[0] - obj["rect"].y0
                # gap até a linha anterior (se estiver na mesma página)
                ant = [b for _, b in linhas_pag if b <= obj["rect"].y0 + 0.01]
                gap = round(obj["rect"].y0 - ant[-1], 2) if ant else GAP_ENTRE_SETORES
                secao_atual = Secao(titulo=titulo, pagina=pno, y0=obj["rect"].y0,
                                    altura_titulo=altura_titulo,
                                    graficos=info_faixa[id(obj)], gap=gap)
                secoes.append(secao_atual)
            else:
                t, base = obj
                if secao_atual is None:
                    raise ValueError("Linha encontrada antes de qualquer setor.")
                campos = _campos_da_linha(palavras, t, base)
                secao_atual.linhas.append(Linha(pagina=pno, top=t, bottom=base,
                                                graficos=info_linha[t], campos=campos,
                                                setor=secao_atual.titulo))

    if not secoes or not any(s.linhas for s in secoes):
        raise ValueError("Não encontrei ODFs neste PDF. Ele é o relatório correto?")
    return Relatorio(caminho, cab_altura, cab_graficos, secoes, len(doc))


# ----------------------------------------------------------------------------
# Reorganização
# ----------------------------------------------------------------------------
def agrupar_por_codigo(linhas):
    """Junta as linhas de mesmo Código, mantendo:
       - a ordem em que cada código apareceu pela 1ª vez;
       - a ordem original das linhas dentro do grupo (ODFs crescentes)."""
    ordem, grupos = [], {}
    for l in linhas:
        chave = l.campos["codigo"].strip().upper()
        if not chave:                      # sem código: nunca agrupa
            ordem.append([l])
            continue
        if chave not in grupos:
            grupos[chave] = []
            ordem.append(grupos[chave])
        grupos[chave].append(l)
    return [l for g in ordem for l in g]


def reorganizar(rel, agrupar=True):
    """Devolve uma lista de (secao, linhas_na_nova_ordem)."""
    return [(s, agrupar_por_codigo(s.linhas) if agrupar else list(s.linhas))
            for s in rel.secoes]


def tabela(rel, estrutura=None):
    """Linhas em formato de tabela (para tela e Excel). Marca códigos repetidos."""
    estrutura = estrutura or reorganizar(rel)
    saida = []
    for secao, linhas in estrutura:
        contagem = {}
        for l in linhas:
            k = l.campos["codigo"].strip().upper()
            if k:
                contagem[k] = contagem.get(k, 0) + 1
        for l in linhas:
            c = l.campos
            k = c["codigo"].strip().upper()
            saida.append({
                "Setor": "ODF terceirizada" if secao.titulo.strip() in ("-", "") else secao.titulo,
                "ODF": c["odf"], "Código": c["codigo"], "Descrição": c["descricao"],
                "Máquina": c["maquina"], "Qtde Ped.": c["qtde"], "Saldo": c["saldo"],
                "% Prod.": c["prod"],
                "Repetido": contagem.get(k, 0) if contagem.get(k, 0) > 1 else 0,
            })
    return saida


def resumo(rel, estrutura=None):
    estrutura = estrutura or reorganizar(rel)
    total = sum(len(l) for _, l in estrutura)
    codigos_rep = 0
    for _, linhas in estrutura:
        cont = {}
        for l in linhas:
            k = l.campos["codigo"].strip().upper()
            if k:
                cont[k] = cont.get(k, 0) + 1
        codigos_rep += sum(1 for v in cont.values() if v > 1)
    return {"setores": len(estrutura), "linhas": total, "codigos_repetidos": codigos_rep}


# ----------------------------------------------------------------------------
# Geração do PDF
# ----------------------------------------------------------------------------
def _desenhar(gfx, d, dy):
    """Acumula os operadores do traço, deslocado dy na vertical."""
    gfx.append(d["emit"](dy))


def _calibrar_limite(rel):
    """Descobre até onde uma linha pode ir na página (a partir do próprio PDF original)."""
    ultimas, proximas = {}, {}
    seq = []  # (pagina, top, bottom, necessario_para_caber)
    for s in rel.secoes:
        for i, l in enumerate(s.linhas):
            extra = (s.gap + s.altura_titulo) if i == 0 else 0
            seq.append((l.pagina, l.bottom, l.altura + extra))
    cabe = max(b for _, b, _ in seq)
    estoura = 10 ** 6
    for (p1, b1, _), (p2, _, need) in zip(seq, seq[1:]):
        if p2 != p1:
            estoura = min(estoura, b1 + need)
    return cabe, estoura


def _registrar_gs(doc, pg):
    """Cria /GS1 (SA false, SM .02) nos recursos da página, igual ao PDF original."""
    gs = doc.get_new_xref()
    doc.update_object(gs, "<< /Type /ExtGState /SA false /SM .02 /OP false /op false /OPM 1 >>")
    res = doc.xref_get_key(pg.xref, "Resources")
    if res[0] == "xref":
        rxref = int(res[1].split()[0])
        doc.xref_set_key(rxref, "ExtGState", "<< /GS1 %d 0 R >>" % gs)
    else:
        doc.xref_set_key(pg.xref, "Resources/ExtGState", "<< /GS1 %d 0 R >>" % gs)


def gerar_pdf(rel, estrutura, saida):
    """Gera o PDF reorganizado com o mesmo layout do original."""
    cabe, estoura = _calibrar_limite(rel)
    limite = (cabe + min(estoura, cabe + 30)) / 2 if estoura > cabe else cabe
    limite = max(cabe + 0.01, min(limite, estoura - 0.01))

    texto = _texto_apenas(rel.caminho)
    out = fitz.open()
    estado = {"pg": None, "n": 0, "gfx": []}

    def fechar_pagina():
        """Grava os traços acumulados como 1 bloco, POR BAIXO do texto da página."""
        pg = estado["pg"]
        if pg is None or not estado["gfx"]:
            return
        xref = out.get_new_xref()
        out.update_object(xref, "<<>>")
        out.update_stream(xref, "".join(estado["gfx"]).encode("latin1"))
        atuais = pg.get_contents()
        refs = " ".join("%d 0 R" % x for x in [xref] + list(atuais))
        out.xref_set_key(pg.xref, "Contents", "[%s]" % refs)
        # mesmo estado gráfico do PDF original (ajuste de traço desligado)
        _registrar_gs(out, pg)
        estado["gfx"] = []

    def rodape(page, n):
        pno = n - 1
        if pno < len(texto):
            ws = [w for w in texto[pno].get_text("words") if w[1] > 812 and w[0] > 500]
            if ws:
                r = fitz.Rect(min(w[0] for w in ws) - 1, min(w[1] for w in ws) - 1,
                              max(w[2] for w in ws) + 1, max(w[3] for w in ws) + 1)
                page.show_pdf_page(r, texto, pno, clip=r, overlay=True)
                return
        page.insert_text((545.9, 822.3), str(n), fontname="helv", fontsize=10)

    def nova_pagina():
        fechar_pagina()
        estado["n"] += 1
        estado["pg"] = out.new_page(width=LARGURA_PAGINA, height=ALTURA_PAGINA)
        rodape(estado["pg"], estado["n"])
        return estado["pg"]

    def colar_texto(page, pno, y0, y1, dy):
        clip = fitz.Rect(0, y0, LARGURA_PAGINA, y1)
        page.show_pdf_page(fitz.Rect(0, y0 + dy, LARGURA_PAGINA, y1 + dy), texto, pno,
                           clip=clip, overlay=True)

    # ---- página 1 + cabeçalho (idêntico ao original, uma única vez)
    page = nova_pagina()
    for d in rel.cabecalho_graficos:
        _desenhar(estado["gfx"], d, 0)
    if rel.cabecalho_altura:
        colar_texto(page, 0, 0, rel.cabecalho_altura - 2, 0)

    y = None
    primeiro = True
    for secao, linhas in estrutura:
        if not linhas:
            continue
        h1 = linhas[0].altura
        y_faixa = secao.y0 if primeiro else round(y + secao.gap, 2)
        if y_faixa + secao.altura_titulo + h1 > limite:
            page = nova_pagina()
            y_faixa = TOPO_PAGINAS_SEGUINTES
        primeiro = False
        dy = round(y_faixa - secao.y0, 2)
        for d in secao.graficos:
            _desenhar(estado["gfx"], d, dy)
        colar_texto(page, secao.pagina, secao.y0 - 2, secao.y0 + secao.altura_titulo - 0.01, dy)
        y = round(y_faixa + secao.altura_titulo, 2)

        for l in linhas:
            if y + l.altura > limite:
                page = nova_pagina()
                y = TOPO_PAGINAS_SEGUINTES
            dy = round(y - l.top, 2)
            for d in l.graficos:
                _desenhar(estado["gfx"], d, dy)
            colar_texto(page, l.pagina, l.top - 0.01, l.bottom, dy)
            y = round(y + l.altura, 2)

    fechar_pagina()
    out.save(saida, garbage=4, deflate=True)
    n = estado["n"]
    out.close()
    return n