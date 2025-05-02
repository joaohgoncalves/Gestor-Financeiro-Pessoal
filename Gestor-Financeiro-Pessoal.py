import json
from datetime import datetime
import os
import matplotlib.pyplot as plt
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GerenciadorGastosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Gastos Pessoais")
        self.root.geometry("1000x700")
        
        # Dados
        self.arquivo_dados = 'gastos.json'
        self.gastos = []
        self.limites_categoria = {}
        self.carregar_dados()
        
        # Configuração do tema
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Criar widgets
        self.criar_widgets()
        
        # Atualizar lista de gastos
        self.atualizar_lista_gastos()
    
    def criar_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de entrada de dados
        input_frame = ttk.LabelFrame(main_frame, text="Adicionar Novo Gasto", padding="10")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Campos de entrada
        ttk.Label(input_frame, text="Valor:").grid(row=0, column=0, sticky="w")
        self.valor_entry = ttk.Entry(input_frame)
        self.valor_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(input_frame, text="Categoria:").grid(row=1, column=0, sticky="w")
        self.categoria_entry = ttk.Entry(input_frame)
        self.categoria_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(input_frame, text="Descrição:").grid(row=2, column=0, sticky="w")
        self.descricao_entry = ttk.Entry(input_frame)
        self.descricao_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        # Botão adicionar
        add_btn = ttk.Button(input_frame, text="Adicionar Gasto", command=self.adicionar_gasto)
        add_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Frame de lista de gastos
        list_frame = ttk.LabelFrame(main_frame, text="Lista de Gastos", padding="10")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Treeview para lista de gastos
        columns = ('id', 'data', 'valor', 'categoria', 'descricao')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('data', text='Data')
        self.tree.heading('valor', text='Valor (R$)')
        self.tree.heading('categoria', text='Categoria')
        self.tree.heading('descricao', text='Descrição')
        
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('data', width=150)
        self.tree.column('valor', width=100, anchor='e')
        self.tree.column('categoria', width=150)
        self.tree.column('descricao', width=300)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Frame de botões de ação
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        
        ttk.Button(btn_frame, text="Editar", command=self.editar_gasto).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remover", command=self.remover_gasto).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Filtrar por Categoria", command=self.filtrar_por_categoria).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Filtrar por Mês", command=self.filtrar_por_mes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpar Filtros", command=self.atualizar_lista_gastos).pack(side=tk.LEFT, padx=5)
        
        # Frame de resumo
        resumo_frame = ttk.LabelFrame(main_frame, text="Resumo", padding="10")
        resumo_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Botões de resumo
        ttk.Button(resumo_frame, text="Resumo por Categoria", command=self.mostrar_resumo_categoria).pack(fill=tk.X, pady=2)
        ttk.Button(resumo_frame, text="Resumo por Mês", command=self.mostrar_resumo_mes).pack(fill=tk.X, pady=2)
        ttk.Button(resumo_frame, text="Definir Limite", command=self.definir_limite_categoria).pack(fill=tk.X, pady=2)
        ttk.Button(resumo_frame, text="Ver Limites", command=self.mostrar_limites).pack(fill=tk.X, pady=2)
        ttk.Button(resumo_frame, text="Gerar Gráficos", command=self.gerar_graficos).pack(fill=tk.X, pady=2)
        
        # Configurar pesos das linhas/colunas
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
    def carregar_dados(self):
        if os.path.exists(self.arquivo_dados):
            try:
                with open(self.arquivo_dados, 'r') as f:
                    dados = json.load(f)
                    
                    if isinstance(dados, list):  # Formato antigo
                        self.gastos = [{'id': i+1, **gasto} for i, gasto in enumerate(dados)]
                        self.limites_categoria = {}
                        self.salvar_dados()
                    elif isinstance(dados, dict):  # Formato novo
                        self.gastos = dados.get('gastos', [])
                        for i, gasto in enumerate(self.gastos):
                            if 'id' not in gasto:
                                gasto['id'] = i + 1
                        self.limites_categoria = dados.get('limites', {})
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
                self.gastos = []
                self.limites_categoria = {}
    
    def salvar_dados(self):
        dados = {
            'gastos': self.gastos,
            'limites': self.limites_categoria
        }
        try:
            with open(self.arquivo_dados, 'w') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")
    
    def adicionar_gasto(self):
        valor = self.valor_entry.get()
        categoria = self.categoria_entry.get()
        descricao = self.descricao_entry.get()
        
        try:
            valor = float(valor)
            if valor <= 0:
                messagebox.showwarning("Aviso", "O valor deve ser positivo!")
                return
        except ValueError:
            messagebox.showwarning("Aviso", "Valor inválido! Digite um número.")
            return
            
        if not categoria.strip():
            messagebox.showwarning("Aviso", "A categoria não pode ser vazia!")
            return
            
        data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        novo_id = max([g['id'] for g in self.gastos] + [0]) + 1
        
        gasto = {
            'id': novo_id,
            'data': data,
            'valor': valor,
            'categoria': categoria.strip(),
            'descricao': descricao.strip()
        }
        
        self.gastos.append(gasto)
        self.salvar_dados()
        
        # Limpar campos
        self.valor_entry.delete(0, tk.END)
        self.categoria_entry.delete(0, tk.END)
        self.descricao_entry.delete(0, tk.END)
        
        self.atualizar_lista_gastos()
        self.verificar_limite_categoria(categoria)
        messagebox.showinfo("Sucesso", f"Gasto de R${valor:.2f} em {categoria} registrado com sucesso!")
    
    def atualizar_lista_gastos(self, gastos=None):
        if gastos is None:
            gastos = self.gastos
        
        # Ordenar por data (mais recente primeiro)
        gastos_ordenados = sorted(gastos, key=lambda x: x['data'], reverse=True)
        
        # Limpar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Preencher com novos dados
        for gasto in gastos_ordenados:
            self.tree.insert('', tk.END, values=(
                gasto['id'],
                gasto['data'],
                f"R${gasto['valor']:.2f}",
                gasto['categoria'],
                gasto['descricao']
            ))
    
    def editar_gasto(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um gasto para editar!")
            return
            
        item = self.tree.item(selecionado[0])
        id_gasto = item['values'][0]
        
        for gasto in self.gastos:
            if gasto['id'] == id_gasto:
                # Janela de edição
                edit_window = tk.Toplevel(self.root)
                edit_window.title("Editar Gasto")
                edit_window.geometry("400x300")
                
                ttk.Label(edit_window, text="Valor:").pack(pady=(10,0))
                valor_entry = ttk.Entry(edit_window)
                valor_entry.insert(0, str(gasto['valor']))
                valor_entry.pack(fill=tk.X, padx=10, pady=5)
                
                ttk.Label(edit_window, text="Categoria:").pack()
                categoria_entry = ttk.Entry(edit_window)
                categoria_entry.insert(0, gasto['categoria'])
                categoria_entry.pack(fill=tk.X, padx=10, pady=5)
                
                ttk.Label(edit_window, text="Descrição:").pack()
                descricao_entry = ttk.Entry(edit_window)
                descricao_entry.insert(0, gasto['descricao'])
                descricao_entry.pack(fill=tk.X, padx=10, pady=5)
                
                def salvar_edicao():
                    try:
                        novo_valor = float(valor_entry.get())
                        if novo_valor <= 0:
                            messagebox.showwarning("Aviso", "O valor deve ser positivo!")
                            return
                    except ValueError:
                        messagebox.showwarning("Aviso", "Valor inválido! Digite um número.")
                        return
                        
                    nova_categoria = categoria_entry.get().strip()
                    if not nova_categoria:
                        messagebox.showwarning("Aviso", "A categoria não pode ser vazia!")
                        return
                        
                    gasto['valor'] = novo_valor
                    gasto['categoria'] = nova_categoria
                    gasto['descricao'] = descricao_entry.get().strip()
                    gasto['data'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.salvar_dados()
                    self.atualizar_lista_gastos()
                    edit_window.destroy()
                    messagebox.showinfo("Sucesso", "Gasto atualizado com sucesso!")
                
                ttk.Button(edit_window, text="Salvar", command=salvar_edicao).pack(pady=10)
                return
        
        messagebox.showerror("Erro", f"Gasto com ID {id_gasto} não encontrado!")
    
    def remover_gasto(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um gasto para remover!")
            return
            
        item = self.tree.item(selecionado[0])
        id_gasto = item['values'][0]
        
        for i, gasto in enumerate(self.gastos):
            if gasto['id'] == id_gasto:
                if messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover o gasto de R${gasto['valor']:.2f} em {gasto['categoria']}?"):
                    del self.gastos[i]
                    self.salvar_dados()
                    self.atualizar_lista_gastos()
                    messagebox.showinfo("Sucesso", "Gasto removido com sucesso!")
                return
        
        messagebox.showerror("Erro", f"Gasto com ID {id_gasto} não encontrado!")
    
    def filtrar_por_categoria(self):
        categoria = simpledialog.askstring("Filtrar", "Digite a categoria para filtrar:")
        if categoria:
            gastos_filtrados = [g for g in self.gastos if g['categoria'].lower() == categoria.lower()]
            self.atualizar_lista_gastos(gastos_filtrados)
    
    def filtrar_por_mes(self):
        mes = simpledialog.askstring("Filtrar", "Digite o mês/ano para filtrar (MM/AAAA):")
        if mes:
            try:
                mes_num, ano = map(int, mes.split('/'))
                gastos_filtrados = [
                    g for g in self.gastos 
                    if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').month == mes_num
                    and datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').year == ano
                ]
                self.atualizar_lista_gastos(gastos_filtrados)
            except ValueError:
                messagebox.showerror("Erro", "Formato inválido! Use MM/AAAA (ex: 05/2023)")
    
    def mostrar_resumo_categoria(self):
        mes = simpledialog.askstring("Resumo", "Digite o mês/ano para o resumo (MM/AAAA) ou deixe em branco para todos:")
        
        categorias = defaultdict(float)
        for gasto in self.gastos:
            if mes:
                try:
                    data_gasto = datetime.strptime(gasto['data'], '%Y-%m-%d %H:%M:%S')
                    if data_gasto.strftime('%m/%Y') != mes:
                        continue
                except ValueError:
                    continue
            categorias[gasto['categoria']] += gasto['valor']
        
        if not categorias:
            messagebox.showinfo("Resumo", "Nenhum gasto encontrado para o período selecionado.")
            return
        
        # Criar janela de resumo
        resumo_window = tk.Toplevel(self.root)
        resumo_window.title("Resumo por Categoria")
        resumo_window.geometry("600x400")
        
        # Treeview para o resumo
        columns = ('categoria', 'total', 'limite', 'percentual')
        tree = ttk.Treeview(resumo_window, columns=columns, show='headings', height=15)
        
        tree.heading('categoria', text='Categoria')
        tree.heading('total', text='Total Gastos')
        tree.heading('limite', text='Limite')
        tree.heading('percentual', text='% do Limite')
        
        tree.column('categoria', width=200)
        tree.column('total', width=150, anchor='e')
        tree.column('limite', width=150, anchor='e')
        tree.column('percentual', width=100, anchor='e')
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Adicionar dados
        for categoria, total in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
            limite = self.limites_categoria.get(categoria)
            if limite:
                percentual = (total / limite) * 100
                tree.insert('', tk.END, values=(
                    categoria,
                    f"R${total:.2f}",
                    f"R${limite:.2f}",
                    f"{percentual:.1f}%"
                ))
            else:
                tree.insert('', tk.END, values=(
                    categoria,
                    f"R${total:.2f}",
                    "-",
                    "-"
                ))
        
        # Total
        total_gasto = sum(categorias.values())
        ttk.Label(resumo_window, text=f"Total gasto: R${total_gasto:.2f}", font=('Arial', 10, 'bold')).pack(pady=5)
    
    def mostrar_resumo_mes(self):
        self.mostrar_resumo_categoria()  # Reutiliza a mesma função
    
    def definir_limite_categoria(self):
        categoria = simpledialog.askstring("Limite", "Digite a categoria:")
        if not categoria:
            return
            
        limite = simpledialog.askstring("Limite", f"Digite o limite para {categoria} (R$):")
        if limite:
            try:
                limite = float(limite)
                if limite <= 0:
                    messagebox.showwarning("Aviso", "O limite deve ser positivo!")
                    return
                    
                self.limites_categoria[categoria.strip()] = limite
                self.salvar_dados()
                messagebox.showinfo("Sucesso", f"Limite de R${limite:.2f} definido para {categoria}!")
                self.verificar_limite_categoria(categoria)
            except ValueError:
                messagebox.showerror("Erro", "Valor de limite inválido!")
    
    def mostrar_limites(self):
        if not self.limites_categoria:
            messagebox.showinfo("Limites", "Nenhum limite definido ainda.")
            return
            
        # Criar janela de limites
        limites_window = tk.Toplevel(self.root)
        limites_window.title("Limites Definidos")
        limites_window.geometry("400x300")
        
        # Treeview para os limites
        columns = ('categoria', 'limite')
        tree = ttk.Treeview(limites_window, columns=columns, show='headings', height=10)
        
        tree.heading('categoria', text='Categoria')
        tree.heading('limite', text='Limite (R$)')
        
        tree.column('categoria', width=200)
        tree.column('limite', width=150, anchor='e')
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Adicionar dados
        for categoria, limite in self.limites_categoria.items():
            tree.insert('', tk.END, values=(categoria, f"R${limite:.2f}"))
    
    def verificar_limite_categoria(self, categoria):
        if categoria in self.limites_categoria:
            gasto_categoria = sum(g['valor'] for g in self.gastos if g['categoria'].lower() == categoria.lower())
            limite = self.limites_categoria[categoria]
            if gasto_categoria > limite:
                messagebox.showwarning("Limite Excedido", 
                    f"Você ultrapassou o limite de R${limite:.2f} para {categoria}!\n"
                    f"Total gasto: R${gasto_categoria:.2f}")
    
    def gerar_graficos(self):
        mes = simpledialog.askstring("Gráficos", "Digite o mês/ano para o gráfico (MM/AAAA) ou deixe em branco para todos:")
        
        categorias = defaultdict(float)
        for gasto in self.gastos:
            if mes:
                try:
                    data_gasto = datetime.strptime(gasto['data'], '%Y-%m-%d %H:%M:%S')
                    if data_gasto.strftime('%m/%Y') != mes:
                        continue
                except ValueError:
                    continue
            categorias[gasto['categoria']] += gasto['valor']
        
        if not categorias:
            messagebox.showinfo("Gráficos", "Nenhum dado para exibir no período selecionado.")
            return
        
        # Criar figura
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle('Análise de Gastos' + (f" ({mes})" if mes else ""))
        
        # Gráfico de barras
        categorias_ordenadas = dict(sorted(categorias.items(), key=lambda x: x[1], reverse=True))
        bars = ax1.bar(categorias_ordenadas.keys(), categorias_ordenadas.values(), color='skyblue')
        ax1.set_title('Gastos por Categoria')
        ax1.tick_params(axis='x', rotation=45)
        ax1.set_ylabel('Valor (R$)')
        
        # Valores nas barras
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'R${height:.2f}',
                    ha='center', va='bottom')
        
        # Gráfico de pizza
        ax2.pie(categorias_ordenadas.values(), 
               labels=categorias_ordenadas.keys(), 
               autopct='%1.1f%%',
               startangle=90,
               wedgeprops={'edgecolor': 'white'})
        ax2.set_title('Distribuição dos Gastos')
        
        # Ajustar layout
        plt.tight_layout()
        
        # Mostrar em uma janela Tkinter
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Gráficos de Gastos")
        
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorGastosGUI(root)
    root.mainloop()