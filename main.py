import tkinter as tk
from tkinter import messagebox, ttk

from db import conectar


class App:
    TABELAS = [
        "Diretor",
        "Departamento",
        "Funcionario",
        "Artista",
        "Programador",
        "Musico",
    ]
    SUBTABELAS_FUNCIONARIO = {"Artista", "Programador", "Musico"}

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Ejogos")
        self.root.geometry("1100x700")

        self.tabela = "Diretor"
        self.campos = {}

        # Topo
        topo = tk.Frame(root)
        topo.pack(fill="x", padx=10, pady=10)

        tk.Label(topo, text="Escolha a tabela:").pack(side="left", padx=(0, 8))

        self.combo = ttk.Combobox(topo, values=self.TABELAS, state="readonly")
        self.combo.current(0)
        self.combo.bind("<<ComboboxSelected>>", self.mudar_tabela)
        self.combo.pack(side="left")

        # Formulário
        self.form_frame = tk.LabelFrame(root, text="Inserir novo registro")
        self.form_frame.pack(fill="x", padx=10, pady=10)

        # Botões
        botoes = tk.Frame(root)
        botoes.pack(fill="x", padx=10, pady=5)

        tk.Button(botoes, text="Carregar", command=self.carregar).pack(
            side="left", padx=5
        )
        tk.Button(botoes, text="Inserir", command=self.inserir).pack(
            side="left", padx=5
        )
        tk.Button(botoes, text="Deletar", command=self.deletar).pack(
            side="left", padx=5
        )

        # Tabela visual
        self.tree = ttk.Treeview(root)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.montar_formulario()
        self.carregar()

    def obter_schema(self):
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SHOW COLUMNS FROM `{self.tabela}`")
            return cursor.fetchall()
        finally:
            conn.close()

    def obter_colunas(self):
        schema = self.obter_schema()
        return [c["Field"] for c in schema]

    def obter_coluna_auto_increment(self):
        schema = self.obter_schema()
        for col in schema:
            extra = (col["Extra"] or "").lower()
            if "auto_increment" in extra:
                return col["Field"]
        return None

    def obter_colunas_insercao(self):
        schema = self.obter_schema()
        resultado = []

        for col in schema:
            extra = (col["Extra"] or "").lower()
            if "auto_increment" not in extra:
                resultado.append(col["Field"])

        return resultado

    def proximo_id_livre(self, coluna_id):
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"SELECT `{coluna_id}` AS id_valor FROM `{self.tabela}` ORDER BY `{coluna_id}` ASC"
            )
            rows = cursor.fetchall()

            proximo = 1
            for row in rows:
                valor = row["id_valor"]
                if valor == proximo:
                    proximo += 1
                elif valor > proximo:
                    break

            return proximo
        finally:
            conn.close()

    def mudar_tabela(self, event=None):
        self.tabela = self.combo.get()
        self.montar_formulario()
        self.carregar()

    def montar_formulario(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.campos.clear()
        colunas = self.obter_colunas_insercao()

        if not colunas:
            tk.Label(
                self.form_frame, text="Nenhuma coluna disponível para inserção."
            ).pack(padx=10, pady=10)
            return

        for i, col in enumerate(colunas):
            linha = i // 2
            coluna = (i % 2) * 2

            tk.Label(self.form_frame, text=f"{col}:").grid(
                row=linha, column=coluna, sticky="e", padx=5, pady=5
            )

            entry = tk.Entry(self.form_frame, width=30)
            entry.grid(row=linha, column=coluna + 1, sticky="w", padx=5, pady=5)

            self.campos[col] = entry

    def carregar(self):
        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute(f"SELECT * FROM `{self.tabela}`")
            dados = cursor.fetchall()

            colunas = self.obter_colunas()

            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = colunas
            self.tree["show"] = "headings"

            for col in colunas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=140, anchor="center")

            for linha in dados:
                self.tree.insert("", "end", values=[linha.get(col) for col in colunas])

        except Exception as e:
            messagebox.showerror("Erro ao carregar", str(e))
        finally:
            conn.close()

    def inserir(self):
        colunas_form = list(self.campos.keys())
        valores_form = []

        if not colunas_form:
            messagebox.showwarning(
                "Atenção", "Não há campos para inserir nesta tabela."
            )
            return

        # Validação de remuneração
        if self.tabela == "Funcionario" and "remuneracao" in self.campos:
            try:
                remuneracao = float(self.campos["remuneracao"].get().strip())
                if remuneracao < 0:
                    messagebox.showerror("Erro", "A remuneração não pode ser negativa.")
                    return
            except ValueError:
                messagebox.showerror("Erro", "A remuneração deve ser um número válido.")
                return

        for col in colunas_form:
            valor = self.campos[col].get().strip()
            valores_form.append(valor if valor != "" else None)

        colunas_sql = list(colunas_form)
        valores_sql = list(valores_form)

        coluna_ai = self.obter_coluna_auto_increment()
        if coluna_ai:
            novo_id = self.proximo_id_livre(coluna_ai)
            colunas_sql = [coluna_ai] + colunas_sql
            valores_sql = [novo_id] + valores_sql

        colunas_sql_txt = ", ".join(f"`{c}`" for c in colunas_sql)
        placeholders = ", ".join(["%s"] * len(colunas_sql))
        sql = f"INSERT INTO `{self.tabela}` ({colunas_sql_txt}) VALUES ({placeholders})"

        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute(sql, valores_sql)
            conn.commit()

            messagebox.showinfo("Sucesso", "Registro inserido com sucesso.")

            for entry in self.campos.values():
                entry.delete(0, tk.END)

            self.carregar()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro ao inserir", str(e))
        finally:
            conn.close()

    def deletar(self):
        item = self.tree.selection()

        if not item:
            messagebox.showwarning("Atenção", "Selecione uma linha para deletar.")
            return

        item_id = item[0]
        valores = self.tree.item(item_id)["values"]

        if not valores:
            return

        id_coluna = self.tree["columns"][0]
        id_valor = valores[0]

        conn = conectar()
        cursor = conn.cursor()

        try:
            if self.tabela in self.SUBTABELAS_FUNCIONARIO:
                cursor.execute(
                    "DELETE FROM `Funcionario` WHERE `id_funcionario` = %s", (id_valor,)
                )
            else:
                cursor.execute(
                    f"DELETE FROM `{self.tabela}` WHERE `{id_coluna}` = %s", (id_valor,)
                )

            conn.commit()
            self.carregar()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro ao deletar", str(e))
        finally:
            conn.close()


root = tk.Tk()
app = App(root)
root.mainloop()
