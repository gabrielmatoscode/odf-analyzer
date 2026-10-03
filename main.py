"""
main.py - ARQUIVO PRINCIPAL - menu do programa 

Mostra um menu inicial com as funcionalidades:
    1) ODFs sem apontamento        ----> odf_not_reported.py
    2) Reorganizar ODFs por código ----> odf_reorganizer.py

Instalações necessárias no Terminal:  pip install customtkinter pdfplumber pandas openpyxl fpdf2 pymupdf
"""
import customtkinter as ctk
import fpdf
import pandas as pd
from tkinter import filedialog, messagebox, ttk

import odf_reorganizer
import odfs_not_reported

COR = "#DA9D1C"          # amarelo do programa
VERDE = "#50816A"
VERMELHO = "#CC8282"
CINZA = "#3A3A3A"


# ============================================================================
# Tabela reutilizável (Treeview + rolagem + Ctrl+C copiando a ODF)
# ============================================================================
class Tabela(ctk.CTkFrame):
    def __init__(self, master, colunas, larguras):
        super().__init__(master)
        self.colunas = colunas
        self.tv = ttk.Treeview(self, columns=colunas, show="headings", height=25)
        for c, w in zip(colunas, larguras):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w, anchor="center")
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv.pack(fill="both", expand=True)
        self.tv.tag_configure("repetido", background="#FFE8A3")
        self.tv.bind("<Control-c>", self._copiar)

    def limpar(self):
        for i in self.tv.get_children():
            self.tv.delete(i)

    def inserir(self, valores, tag=""):
        self.tv.insert("", "end", values=valores, tags=(tag,) if tag else ())

    def linhas(self):
        return [self.tv.item(i, "values") for i in self.tv.get_children()
                if self.tv.item(i, "values")[0]]

    def _copiar(self, event=None):
        sel = self.tv.focus()
        if not sel:
            return
        self.clipboard_clear()
        self.clipboard_append(self.tv.item(sel, "values")[0])
        self.update()


def pedir_pdf():
    return filedialog.askopenfilename(
        title="Selecione o seu PDF",
        filetypes=[("Apenas PDF", "*.pdf"), ("Todos os arquivos", "*.*")])


def exportar_excel(dados, colunas):
    if not dados:
        messagebox.showwarning("Aviso", "Não há nada para exportar")
        return
    caminho = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                           filetypes=[("Excel", "*.xlsx")],
                                           title="Salvar como Excel")
    if caminho:
        pd.DataFrame(dados, columns=colunas).to_excel(caminho, index=False)
        messagebox.showinfo("Operação bem sucedida", f"Excel salvo!\n{caminho}")


# ============================================================================
# Tela 1 - ODFs sem apontamento
# ============================================================================
class TelaSemApontamento(ctk.CTkFrame):
    def __init__(self, master, voltar):
        super().__init__(master)
        topo(self, "ODFs sem apontamento", voltar)

        ctk.CTkButton(self, text="Buscar PDF e executar análise", command=self.executar,
                      text_color="#000000", fg_color=COR,
                      font=("Segoe UI", 26, "bold")).pack(pady=15)

        barra = ctk.CTkFrame(self)
        barra.pack(pady=8)
        ctk.CTkButton(barra, text="📊 Exportar Excel", command=self.excel, width=180,
                      fg_color=VERDE, font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(barra, text="📄 Exportar PDF", command=self.pdf, width=180,
                      fg_color=VERMELHO, font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)

        self.tabela = Tabela(self, ("ODF", "SETOR", "%"), (100, 250, 100))
        self.tabela.pack(padx=10, pady=20, fill="both", expand=True)

    def executar(self):
        caminho = pedir_pdf()
        if not caminho:
            messagebox.showwarning("Aviso", "Nenhum arquivo foi selecionado.")
            return
        try:
            itens = odfs_not_reported.analisar(caminho)
        except Exception as e:
            messagebox.showerror("Erro", f"Não consegui ler o PDF:\n{e}")
            return
        self.tabela.limpar()
        if itens:
            for odf, setor, pct in itens:
                self.tabela.inserir((odf, setor if setor is not None else "ODF terceirizada", pct))
        else:
            self.tabela.inserir(("", "Nenhuma ODF encontrada", ""))

    def excel(self):
        exportar_excel(self.tabela.linhas(), ["ODF", "SETOR", "%"])

    def pdf(self):
        dados = self.tabela.linhas()
        if not dados:
            messagebox.showwarning("Aviso", "Não há nada para exportar")
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".pdf",
                                               filetypes=[("PDF", "*.pdf")],
                                               title="Salvar como PDF")
        if not caminho:
            return
        doc = fpdf.FPDF()
        doc.add_page()
        doc.set_font("Arial", "B", 16)
        doc.cell(0, 10, "Relatório de ODFs", ln=True, align="C")
        doc.ln(10)
        doc.set_font("Arial", "B", 12)
        larguras = [30, 120, 30]
        for i, c in enumerate(["ODF", "SETOR", "%"]):
            doc.cell(larguras[i], 10, c, border=1, align="C")
        doc.ln()
        doc.set_font("Arial", size=10)
        for linha in dados:
            for i, v in enumerate(linha):
                doc.cell(larguras[i], 7, str(v), border=1, align="C")
            doc.ln()
        doc.output(caminho)
        messagebox.showinfo("Sucesso", f"PDF salvo!\n{caminho}")


# ============================================================================
# Tela 2 - Reorganizar ODFs por código
# ============================================================================
class TelaReorganizar(ctk.CTkFrame):
    COLS = ("Setor", "ODF", "Código", "Descrição", "Máquina", "Qtde", "Saldo", "%")

    def __init__(self, master, voltar):
        super().__init__(master)
        self.rel = None
        self.estrutura = None
        topo(self, "Reorganizar ODFs por código", voltar)

        ctk.CTkButton(self, text="Buscar PDF", command=self.executar,
                      text_color="#000000", fg_color=COR,
                      font=("Segoe UI", 26, "bold")).pack(pady=15)

        self.info = ctk.CTkLabel(self, text="Nenhum arquivo carregado.", font=("Segoe UI", 14))
        self.info.pack()

        barra = ctk.CTkFrame(self)
        barra.pack(pady=8)
        ctk.CTkButton(barra, text="📊 Exportar Excel", command=self.excel, width=180,
                      fg_color=VERDE, font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(barra, text="📄 Exportar PDF", command=self.pdf, width=180,
                      fg_color=VERMELHO, font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)

        self.tabela = Tabela(self, self.COLS, (110, 70, 85, 330, 100, 55, 55, 70))
        self.tabela.pack(padx=10, pady=15, fill="both", expand=True)
        ctk.CTkLabel(self, text="Linhas em amarelo = código repetido (agrupado).",
                     font=("Segoe UI", 12)).pack(pady=(0, 8))

    def executar(self):
        caminho = pedir_pdf()
        if not caminho:
            messagebox.showwarning("Aviso", "Nenhum arquivo foi selecionado.")
            return
        try:
            self.rel = odf_reorganizer.ler_relatorio(caminho)
            self.estrutura = odf_reorganizer.reorganizar(self.rel)
            dados = odf_reorganizer.tabela(self.rel, self.estrutura)
            res = odf_reorganizer.resumo(self.rel, self.estrutura)
        except Exception as e:
            self.rel = self.estrutura = None
            messagebox.showerror("Erro", f"Não consegui processar o PDF:\n{e}")
            return
        self.tabela.limpar()
        for d in dados:
            self.tabela.inserir((d["Setor"], d["ODF"], d["Código"], d["Descrição"], d["Máquina"],
                                 d["Qtde Ped."], d["Saldo"], d["% Prod."]),
                                "repetido" if d["Repetido"] else "")
        self.info.configure(text=f"{res['setores']} setor(es) • {res['linhas']} linhas • "
                                 f"{res['codigos_repetidos']} código(s) repetido(s) agrupado(s)")

    def excel(self):
        exportar_excel(self.tabela.linhas(), list(self.COLS))

    def pdf(self):
        if not self.rel:
            messagebox.showwarning("Aviso", "Não há nada para exportar")
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".pdf",
                                               filetypes=[("PDF", "*.pdf")],
                                               title="Salvar PDF reorganizado")
        if not caminho:
            return
        try:
            n = odf_reorganizer.gerar_pdf(self.rel, self.estrutura, caminho)
        except Exception as e:
            messagebox.showerror("Erro", f"Não consegui gerar o PDF:\n{e}")
            return
        messagebox.showinfo("Sucesso", f"PDF salvo ({n} páginas)!\n{caminho}")


# ============================================================================
# Menu inicial + navegação entre telas
# ============================================================================
def topo(frame, titulo, voltar):
    barra = ctk.CTkFrame(frame, fg_color="transparent")
    barra.pack(fill="x", padx=10, pady=(10, 0))
    ctk.CTkButton(barra, text="← Menu", width=90, fg_color=CINZA, command=voltar).pack(side="left")
    ctk.CTkLabel(frame, text=titulo, text_color=COR,
                 font=("Arial Black", 28, "bold")).pack(pady=10)


class Menu(ctk.CTkFrame): # Classe da função do menu principal do programa #
    def __init__(self, master, abrir):
        super().__init__(master)
        ctk.CTkLabel(self, text="ODF Analyzer", text_color=COR,
                     font=("Arial Black", 60, "bold")).pack(pady=(60, 5))
        ctk.CTkLabel(self, text="Selecione uma das opções a seguir",
                     font=("Segoe UI", 20)).pack(pady=(0, 40))
        for texto, chave in (("🔎  ODFs sem apontamento", "sem"),
                             ("🗂️  Reorganizar ODFs por código", "reorg")):
            ctk.CTkButton(self, text=texto, height=70, width=420, fg_color=COR,
                          text_color="#000000", font=("Segoe UI", 22),
                          command=lambda c=chave: abrir(c)).pack(pady=12)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("ODF Analyzer")
        self.geometry("1000x760")
        self.telas = {"menu": Menu(self, self.abrir),
                      "sem": TelaSemApontamento(self, lambda: self.abrir("menu")),
                      "reorg": TelaReorganizar(self, lambda: self.abrir("menu"))}
        self._estilo()
        self.abrir("menu")

    def abrir(self, nome):
        for t in self.telas.values():
            t.pack_forget()
        self.telas[nome].pack(fill="both", expand=True, padx=10, pady=10)

    def _estilo(self):
        e = ttk.Style()
        e.theme_use("default")
        e.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"),
                    background="#91762E", foreground="white")
        e.configure("Treeview", font=("Segoe UI", 12), rowheight=28,
                    background="#F5F5F5", fieldbackground="#F5F5F5")
        e.map("Treeview", background=[("selected", "#6BA77A")],
              foreground=[("selected", "white")])


if __name__ == "__main__":
    App().mainloop()