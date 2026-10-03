import customtkinter as ctk
import fpdf as fpdf
import pandas as pd
import pdfplumber as pdftool
from tkinter import filedialog, messagebox, ttk
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Motor de reorganização do PDF
from reorganizador import gerar_pdf, ler_relatorio, reorganizar


def buscar_texto():
    filepath = filedialog.askopenfilename(
        title="Selecione o seu PDF",
        filetypes=[("Apenas PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
    )

    if not filepath:
        messagebox.showwarning(title="Aviso", message="Nenhum arquivo foi selecionado.")
        return

    print(f"\n📂 - Arquivo selecionado: {filepath}\n")

    odf_sem_apontamento = []
    odf_maiores_100 = []
    odf_pai = ""
    maquina = ""
    prox_odf = False
    prox_desc = False
    titulo = f"{odf_pai} | {maquina}"

    setores = {
        "1": "SERRA",
        "2": "PLASMA",
        "3": "DOBRA",
        "4": "FURAÇÃO",
        "5": "USINAGEM",
        "6": "SOLDA",
        "7": "ACABAMENTO",
        "8": "PINTURA",
        "9": "MONTAGEM",
    }

    setor_atual = None

    with pdftool.open(filepath) as pdf:
        for p_no, paginas in enumerate(pdf.pages, start=1):
            data = paginas.extract_text()

            if not data:
                continue

            for line in data.split("\n"):
                line = line.strip()
                partes = line.split()

                if len(partes) >= 3 and partes[0] in setores and partes[1] == "-":
                    setor_atual = setores[partes[0]]
                    continue

                linha_porcentagem = partes[-1] if partes else ""

                if linha_porcentagem.upper() in ("NECESSIDADE", "PRODUZIDO"):
                    continue

                porcentagem = []

                if not linha_porcentagem.endswith("%"):
                    continue
                else:
                    porcentagem = partes[-1]

                str_para_valor = partes[-1].replace("%", "").replace(",", ".")

                if not str_para_valor.replace(".", "", 1).isdigit():
                    continue

                transformar_float = float(str_para_valor)

                if 0 <= transformar_float < 100:
                    if len(partes) >= 1:
                        odf = partes[0]
                else:
                    continue

                if not odf.isdigit():
                    continue

                odf_sem_apontamento.append((odf, setor_atual, porcentagem))

    # Limpar tabela
    for item in tabela.get_children():
        tabela.delete(item)

    # Preencher tabela
    if odf_sem_apontamento:
        for odf, setor, porcentagem in odf_sem_apontamento:
            setor_exibido = setor if setor is not None else "ODF terceirizada"
            tabela.insert("", "end", values=(odf, setor_exibido, porcentagem))
    else:
        tabela.insert("", "end", values=("", "Nenhuma ODF encontrada", ""))


def exportar_excel():
    dados = []

    for item in tabela.get_children():
        valores = tabela.item(item, "values")
        if valores[0]:
            dados.append(valores)

    if not dados:
        messagebox.showwarning(title="Aviso", message="Não há nada para exportar")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension="xlsx",
        filetypes=[("Excel", "*.xlsx")],
        title="Salvar como Excel",
    )

    if filepath:
        df = pd.DataFrame(dados, columns=["ODF", "SETOR", "%"])
        df.to_excel(filepath, index=False)
        messagebox.showinfo(
            "Operação bem sucedida", f"Excel salvo!\n{filepath}"
        )


def exportar_pdf():
    dados = []

    for item in tabela.get_children():
        valores = tabela.item(item, "values")
        if valores[0]:
            dados.append(valores)

    if not dados:
        messagebox.showwarning(title="Aviso", message="Não há nada para exportar")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
        title="Salvar como PDF",
    )

    if filepath:
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Relatório de ODFs", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        colunas = ["ODF", "SETOR", "%"]
        larguras = [30, 120, 30]

        for i, coluna in enumerate(colunas):
            pdf.cell(larguras[i], 10, coluna, border=1, align="C")

        pdf.ln()
        pdf.set_font("Arial", size=10)

        for linha in dados:
            for i, valor in enumerate(linha):
                pdf.cell(larguras[i], 7, str(valor), border=1, align="C")
            pdf.ln()

        pdf.output(filepath)
        messagebox.showinfo("Sucesso", f"PDF salvo!\n{filepath}")


# ============================================================
# Reorganizar ODFs por código
# ============================================================


def reorganizar_odfs():
    filepath = filedialog.askopenfilename(
        title="Selecione o relatório de ODFs",
        filetypes=[("Apenas PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
    )

    if not filepath:
        return

    # Pergunta onde salvar ANTES de processar ou LOGO APÓS selecionar o arquivo
    saida = filedialog.asksaveasfilename(
        title="Salvar PDF reorganizado",
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")]
    )

    if not saida:
        return

    try:
        print(f"\nReorganizando arquivo: {filepath}\n")

        # 1. Lê a estrutura do PDF original
        relatorio = ler_relatorio(filepath)

        # 2. Agrupa os códigos iguais dentro de cada setor
        estrutura = reorganizar(relatorio)

        # 3. Gera o novo PDF
        paginas = gerar_pdf(relatorio, estrutura, saida)

        messagebox.showinfo(
            "Sucesso",
            f"PDF reorganizado com sucesso!\n\n"
            f"Arquivo salvo em:\n{saida}\n\n"
            f"Páginas geradas: {paginas}"
        )

        print(f"Sucesso! PDF salvo em: {saida}")

    except Exception as erro:
        print(f"Erro ao processar PDF: {erro}")
        messagebox.showerror(
            "Erro ao reorganizar",
            f"Ocorreu um erro ao processar o arquivo.\n\n"
            f"Detalhe do erro:\n{erro}"
        )


# ============================================================
# GUI
# ============================================================

ctk.set_appearance_mode("dark")

window = ctk.CTk()
window.title("Automatizador de ODFs")
window.geometry("600x750")

title1 = ctk.CTkLabel(
    window,
    text="Automatizador de ODFs",
    text_color="#DA9D1C",
    font=("Arial Black", 35, "bold"),
)
title1.pack(pady=15)

# ============================================================
# BOTÃO PRINCIPAL
# ============================================================

button1 = ctk.CTkButton(
    window,
    text="Buscar arquivo e executar análise",
    command=buscar_texto,
    text_color="#000000",
    fg_color="#DA9D1C",
    font=("Segoe UI", 30, "bold"),
)
button1.pack(pady=20)

# ============================================================
# BOTÕES
# ============================================================

frame_botoes = ctk.CTkFrame(window)
frame_botoes.pack(pady=8.5)

button2_excel = ctk.CTkButton(
    frame_botoes,
    text="📊 Exportar Excel",
    command=exportar_excel,
    text_color="#FFFFFF",
    fg_color="#50816A",
    font=("Segoe UI", 16, "bold"),
    width=180,
)
button2_excel.pack(side="left", padx=10)

button3_pdf = ctk.CTkButton(
    frame_botoes,
    text="📄 Exportar PDF",
    command=exportar_pdf,
    text_color="#FFFFFF",
    fg_color="#CC8282",
    font=("Segoe UI", 16, "bold"),
    width=180,
)
button3_pdf.pack(side="left", padx=10)

# ============================================================
# NOVO BOTÃO - REORGANIZAR
# ============================================================

button4_reorganizar = ctk.CTkButton(
    window,
    text="🔄 Reorganizar ODFs por Código",
    command=reorganizar_odfs,
    text_color="#FFFFFF",
    fg_color="#5B6FA6",
    font=("Segoe UI", 17, "bold"),
    width=380,
    height=45,
)
button4_reorganizar.pack(pady=8)

# ============================================================
# TABELA
# ============================================================

frame_tabela = ctk.CTkFrame(window)
frame_tabela.pack(padx=10, pady=25, fill="both", expand=True)

tabela = ttk.Treeview(
    frame_tabela,
    columns=("ODF", "SETOR", "%"),
    show="headings",
    height=25,
)

tabela.heading("ODF", text="ODF")
tabela.heading("SETOR", text="SETOR")
tabela.heading("%", text="%")

tabela.column("ODF", width=100, anchor="center")
tabela.column("SETOR", width=250, anchor="center")
tabela.column("%", width=100, anchor="center")

texto_scroll = ttk.Scrollbar(
    frame_tabela, orient="vertical", command=tabela.yview
)
tabela.configure(yscrollcommand=texto_scroll.set)

texto_scroll.pack(side="right", fill="y")
tabela.pack(fill="both", expand=True)

# ============================================================
# ESTILO DA TABELA
# ============================================================

estilo = ttk.Style()
estilo.theme_use("default")

estilo.configure(
    "Treeview.Heading",
    font=("Segoe UI", 14, "bold"),
    background="#A18E65",
    foreground="white",
)

estilo.configure(
    "Treeview",
    font=("CreatoDisplay-Bold", 13),
    rowheight=30,
    background="#F5F5F5",
    fieldbackground="#F5F5F5",
)

estilo.map(
    "Treeview",
    background=[("selected", "#6BA77A")],
    foreground=[("selected", "white")],
)

# ============================================================
# COPIAR ODF
# ============================================================


def copiar(event=None):
    selected = tabela.focus()
    if not selected:
        return

    valores = tabela.item(selected, "values")
    odf = valores[0]

    window.clipboard_clear()
    window.clipboard_append(odf)
    window.update()


tabela.bind("<Control-c>", copiar)

# ============================================================
# EXECUTAR
# ============================================================

window.mainloop()