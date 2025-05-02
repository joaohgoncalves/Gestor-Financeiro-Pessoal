import json
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import Calendar, DateEntry
from PIL import Image, ImageTk
import webbrowser

class GerenciadorGastosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("💰 Gestor Financeiro Pessoal")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configurações
        self.arquivo_dados = 'gastos.json'
        self.backup_dir = 'backups'
        self.theme = 'light'  # 'light' or 'dark'
        self.gastos = []
        self.limites_categoria = {}
        self.categorias_predefinidas = [
            'Alimentação', 'Transporte', 'Moradia', 'Lazer', 
            'Saúde', 'Educação', 'Vestuário', 'Outros'
        ]
        
        # Carregar dados e configurar interface
        self.criar_diretorio_backup()
        self.carregar_dados()
        self.configurar_estilos()
        self.criar_widgets()
        self.atualizar_lista_gastos()
        self.criar_menu()
    
    def configurar_estilos(self):
        """Configura os estilos visuais da aplicação"""
        self.style = ttk.Style()
        
        if self.theme == 'light':
            self.bg_color = '#f5f5f5'
            self.fg_color = '#333333'
            self.primary_color = '#4a6baf'
            self.secondary_color = '#6c757d'
            self.style.theme_use('clam')
        else:
            self.bg_color = '#2d2d2d'
            self.fg_color = '#ffffff'
            self.primary_color = '#6a8fd8'
            self.secondary_color = '#adb5bd'
            self.style.theme_use('alt')
        
        self.root.configure(bg=self.bg_color)
        
        # Configurar estilos dos widgets
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TButton', padding=6, font=('Arial', 10))
        self.style.configure('Primary.TButton', foreground='white', background=self.primary_color)
        self.style.configure('Secondary.TButton', foreground='white', background=self.secondary_color)
        self.style.configure('Treeview', rowheight=25)
        self.style.map('Primary.TButton', background=[('active', self.primary_color)])
    
    def criar_diretorio_backup(self):
        """Cria diretório para backups se não existir"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def carregar_dados(self):
        """Carrega os dados do arquivo JSON com tratamento de erros"""
        if os.path.exists(self.arquivo_dados):
            try:
                with open(self.arquivo_dados, 'r', encoding='utf-8') as f:
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
                        self.categorias_predefinidas = dados.get('categorias', self.categorias_predefinidas)
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
                if messagebox.askyesno("Recuperação", "Deseja restaurar do último backup?"):
                    self.restaurar_backup()
    
    def salvar_dados(self):
        """Salva os dados no arquivo JSON e cria backup"""
        dados = {
            'gastos': self.gastos,
            'limites': self.limites_categoria,
            'categorias': self.categorias_predefinidas
        }
        
        try:
            # Criar backup antes de salvar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f'gastos_backup_{timestamp}.json')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            # Salvar arquivo principal
            with open(self.arquivo_dados, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
                
            # Manter apenas os 5 backups mais recentes
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('gastos_backup_')])
            for old_backup in backups[:-5]:
                os.remove(os.path.join(self.backup_dir, old_backup))
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar dados: {str(e)}")
    
    def restaurar_backup(self):
        """Restaura dados a partir do backup mais recente"""
        try:
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('gastos_backup_')], reverse=True)
            if backups:
                with open(os.path.join(self.backup_dir, backups[0]), 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.gastos = dados.get('gastos', [])
                    self.limites_categoria = dados.get('limites', {})
                    self.categorias_predefinidas = dados.get('categorias', self.categorias_predefinidas)
                messagebox.showinfo("Sucesso", "Backup restaurado com sucesso!")
                self.atualizar_lista_gastos()
            else:
                messagebox.showwarning("Aviso", "Nenhum backup disponível para restaurar.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao restaurar backup: {str(e)}")
    
    def criar_menu(self):
        """Cria a barra de menu superior"""
        menubar = tk.Menu(self.root)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exportar Dados", command=self.exportar_dados)
        file_menu.add_command(label="Importar Dados", command=self.importar_dados)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Agora", command=self.criar_backup_manual)
        file_menu.add_command(label="Restaurar Backup", command=self.restaurar_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Alternar Tema", command=self.alternar_tema)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Sobre", command=self.mostrar_sobre)
        help_menu.add_command(label="Documentação", command=lambda: webbrowser.open("https://exemplo.com/docs"))
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def criar_widgets(self):
        """Cria todos os widgets da interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de entrada de dados (lado esquerdo)
        input_frame = ttk.LabelFrame(main_frame, text="➕ Novo Gasto", padding=10)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Campos de entrada
        ttk.Label(input_frame, text="Valor (R$):").grid(row=0, column=0, sticky="w", pady=2)
        self.valor_entry = ttk.Entry(input_frame, font=('Arial', 11))
        self.valor_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(input_frame, text="Categoria:").grid(row=1, column=0, sticky="w", pady=2)
        self.categoria_combobox = ttk.Combobox(input_frame, values=self.categorias_predefinidas, font=('Arial', 11))
        self.categoria_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.categoria_combobox.bind('<KeyRelease>', self.autocompletar_categoria)
        
        ttk.Label(input_frame, text="Data:").grid(row=2, column=0, sticky="w", pady=2)
        self.data_entry = DateEntry(input_frame, date_pattern='dd/mm/yyyy', font=('Arial', 11))
        self.data_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(input_frame, text="Descrição:").grid(row=3, column=0, sticky="w", pady=2)
        self.descricao_entry = ttk.Entry(input_frame, font=('Arial', 11))
        self.descricao_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        
        # Botão adicionar
        add_btn = ttk.Button(input_frame, text="Adicionar Gasto", style='Primary.TButton', command=self.adicionar_gasto)
        add_btn.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Frame de estatísticas rápidas
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Estatísticas", padding=10)
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Widgets de estatísticas
        self.total_mes_var = tk.StringVar(value="R$ 0,00")
        self.maior_gasto_var = tk.StringVar(value="R$ 0,00 - Nenhum")
        self.categoria_mais_gasto_var = tk.StringVar(value="Nenhuma")
        
        ttk.Label(stats_frame, text="Gasto Mensal:").grid(row=0, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.total_mes_var, font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky="e")
        
        ttk.Label(stats_frame, text="Maior Gasto:").grid(row=1, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.maior_gasto_var, font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky="e")
        
        ttk.Label(stats_frame, text="Categoria com Mais Gastos:").grid(row=2, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.categoria_mais_gasto_var, font=('Arial', 10, 'bold')).grid(row=2, column=1, sticky="e")
        
        # Atualizar estatísticas
        self.atualizar_estatisticas()
        
        # Frame de lista de gastos (centro)
        list_frame = ttk.LabelFrame(main_frame, text="📋 Lista de Gastos", padding=10)
        list_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Treeview para lista de gastos
        columns = ('id', 'data', 'valor', 'categoria', 'descricao')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15, selectmode='extended')
        
        # Configurar colunas
        self.tree.heading('id', text='ID', anchor='center')
        self.tree.heading('data', text='Data', anchor='center')
        self.tree.heading('valor', text='Valor (R$)', anchor='e')
        self.tree.heading('categoria', text='Categoria', anchor='center')
        self.tree.heading('descricao', text='Descrição', anchor='w')
        
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('data', width=100, anchor='center')
        self.tree.column('valor', width=100, anchor='e')
        self.tree.column('categoria', width=120, anchor='center')
        self.tree.column('descricao', width=200, anchor='w')
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Frame de botões de ação
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        
        ttk.Button(btn_frame, text="Editar", style='Secondary.TButton', command=self.editar_gasto).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remover", style='Secondary.TButton', command=self.remover_gasto).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Filtrar", style='Secondary.TButton', command=self.mostrar_dialogo_filtro).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Limpar Filtros", style='Secondary.TButton', command=self.limpar_filtros).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Exportar Seleção", style='Secondary.TButton', command=self.exportar_selecao).pack(side=tk.LEFT, padx=2)
        
        # Frame de resumo e gráficos (lado direito)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Notebook (abas) para resumo e gráficos
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba de resumo
        resumo_tab = ttk.Frame(self.notebook)
        self.notebook.add(resumo_tab, text="📈 Resumo")
        
        ttk.Button(resumo_tab, text="Atualizar Resumo", style='Primary.TButton', 
                  command=self.mostrar_resumo).pack(fill=tk.X, pady=5)
        
        self.resumo_text = tk.Text(resumo_tab, wrap=tk.WORD, height=10, font=('Arial', 10))
        self.resumo_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Aba de gráficos
        graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(graph_tab, text="📊 Gráficos")
        
        ttk.Button(graph_tab, text="Gerar Gráficos", style='Primary.TButton',
                  command=self.gerar_graficos).pack(fill=tk.X, pady=5)
        
        self.graph_frame = ttk.Frame(graph_tab)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar pesos das linhas/colunas
        main_frame.columnconfigure(0, weight=1, uniform='col')
        main_frame.columnconfigure(1, weight=3, uniform='col')
        main_frame.columnconfigure(2, weight=2, uniform='col')
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
    def autocompletar_categoria(self, event):
        """Autocompleta a categoria baseado nas categorias predefinidas"""
        typed = self.categoria_combobox.get().lower()
        if typed:
            matches = [c for c in self.categorias_predefinidas if c.lower().startswith(typed)]
            if matches:
                self.categoria_combobox['values'] = matches
                self.categoria_combobox.event_generate('<Down>')
        else:
            self.categoria_combobox['values'] = self.categorias_predefinidas
    
    def adicionar_gasto(self):
        """Adiciona um novo gasto à lista"""
        valor = self.valor_entry.get().replace(',', '.')
        categoria = self.categoria_combobox.get()
        descricao = self.descricao_entry.get()
        data = self.data_entry.get_date()
        
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
            
        # Adicionar nova categoria se não existir
        if categoria not in self.categorias_predefinidas:
            self.categorias_predefinidas.append(categoria)
            self.categorias_predefinidas.sort()
            self.categoria_combobox['values'] = self.categorias_predefinidas
        
        # Criar novo gasto
        novo_id = max([g['id'] for g in self.gastos] + [0]) + 1
        gasto = {
            'id': novo_id,
            'data': data.strftime('%Y-%m-%d %H:%M:%S'),
            'valor': valor,
            'categoria': categoria.strip(),
            'descricao': descricao.strip()
        }
        
        self.gastos.append(gasto)
        self.salvar_dados()
        
        # Limpar campos e atualizar interface
        self.valor_entry.delete(0, tk.END)
        self.categoria_combobox.set('')
        self.descricao_entry.delete(0, tk.END)
        self.data_entry.set_date(datetime.now())
        
        self.atualizar_lista_gastos()
        self.atualizar_estatisticas()
        self.verificar_limite_categoria(categoria)
        
        messagebox.showinfo("Sucesso", f"Gasto de R${valor:.2f} em {categoria} registrado com sucesso!")
    
    def atualizar_lista_gastos(self, gastos=None):
        """Atualiza a lista de gastos na Treeview"""
        if gastos is None:
            gastos = self.gastos
        
        # Ordenar por data (mais recente primeiro)
        gastos_ordenados = sorted(gastos, key=lambda x: x['data'], reverse=True)
        
        # Limpar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Preencher com novos dados
        for gasto in gastos_ordenados:
            data_formatada = datetime.strptime(gasto['data'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            self.tree.insert('', tk.END, values=(
                gasto['id'],
                data_formatada,
                f"{gasto['valor']:,.2f}".replace('.', '|').replace(',', '.').replace('|', ','),
                gasto['categoria'],
                gasto['descricao']
            ))
    
    def atualizar_estatisticas(self):
        """Atualiza as estatísticas exibidas"""
        hoje = datetime.now()
        mes_atual = hoje.strftime('%m/%Y')
        
        # Gastos do mês atual
        gastos_mes = [
            g for g in self.gastos 
            if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').strftime('%m/%Y') == mes_atual
        ]
        total_mes = sum(g['valor'] for g in gastos_mes)
        self.total_mes_var.set(f"R$ {total_mes:,.2f}".replace('.', '|').replace(',', '.').replace('|', ','))
        
        # Maior gasto
        if self.gastos:
            maior_gasto = max(self.gastos, key=lambda x: x['valor'])
            self.maior_gasto_var.set(
                f"R$ {maior_gasto['valor']:,.2f} - {maior_gasto['categoria']}".replace('.', '|').replace(',', '.').replace('|', ',')
            )
        else:
            self.maior_gasto_var.set("R$ 0,00 - Nenhum")
        
        # Categoria com mais gastos
        if self.gastos:
            categorias = defaultdict(float)
            for g in self.gastos:
                categorias[g['categoria']] += g['valor']
            categoria_mais_gasto = max(categorias.items(), key=lambda x: x[1])[0]
            self.categoria_mais_gasto_var.set(categoria_mais_gasto)
        else:
            self.categoria_mais_gasto_var.set("Nenhuma")
    
    def editar_gasto(self):
        """Abre diálogo para editar gasto selecionado"""
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
                edit_window.geometry("400x350")
                edit_window.transient(self.root)
                edit_window.grab_set()
                
                # Frame principal
                edit_frame = ttk.Frame(edit_window, padding=10)
                edit_frame.pack(fill=tk.BOTH, expand=True)
                
                # Campos de edição
                ttk.Label(edit_frame, text="Valor (R$):").grid(row=0, column=0, sticky="w", pady=5)
                valor_entry = ttk.Entry(edit_frame, font=('Arial', 11))
                valor_entry.insert(0, str(gasto['valor']))
                valor_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
                
                ttk.Label(edit_frame, text="Categoria:").grid(row=1, column=0, sticky="w", pady=5)
                categoria_combobox = ttk.Combobox(edit_frame, values=self.categorias_predefinidas, font=('Arial', 11))
                categoria_combobox.set(gasto['categoria'])
                categoria_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
                
                ttk.Label(edit_frame, text="Data:").grid(row=2, column=0, sticky="w", pady=5)
                data_entry = DateEntry(edit_frame, date_pattern='dd/mm/yyyy', font=('Arial', 11))
                data_entry.set_date(datetime.strptime(gasto['data'], '%Y-%m-%d %H:%M:%S'))
                data_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
                
                ttk.Label(edit_frame, text="Descrição:").grid(row=3, column=0, sticky="w", pady=5)
                descricao_entry = ttk.Entry(edit_frame, font=('Arial', 11))
                descricao_entry.insert(0, gasto['descricao'])
                descricao_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
                
                # Botões
                btn_frame = ttk.Frame(edit_frame)
                btn_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
                
                ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', 
                          command=lambda: self.salvar_edicao(
                              gasto, valor_entry.get(), categoria_combobox.get(),
                              data_entry.get_date(), descricao_entry.get(), edit_window)
                          ).pack(side=tk.LEFT, padx=5, expand=True)
                
                ttk.Button(btn_frame, text="Cancelar", 
                          command=edit_window.destroy).pack(side=tk.LEFT, padx=5, expand=True)
                
                return
        
        messagebox.showerror("Erro", f"Gasto com ID {id_gasto} não encontrado!")
    
    def salvar_edicao(self, gasto, novo_valor, nova_categoria, nova_data, nova_descricao, janela):
        """Salva as alterações do gasto editado"""
        try:
            novo_valor = float(novo_valor.replace(',', '.'))
            if novo_valor <= 0:
                messagebox.showwarning("Aviso", "O valor deve ser positivo!")
                return
        except ValueError:
            messagebox.showwarning("Aviso", "Valor inválido! Digite um número.")
            return
            
        if not nova_categoria.strip():
            messagebox.showwarning("Aviso", "A categoria não pode ser vazia!")
            return
            
        # Atualizar gasto
        gasto['valor'] = novo_valor
        gasto['categoria'] = nova_categoria.strip()
        gasto['descricao'] = nova_descricao.strip()
        gasto['data'] = nova_data.strftime('%Y-%m-%d %H:%M:%S')
        
        # Adicionar nova categoria se não existir
        if nova_categoria not in self.categorias_predefinidas:
            self.categorias_predefinidas.append(nova_categoria)
            self.categorias_predefinidas.sort()
            self.categoria_combobox['values'] = self.categorias_predefinidas
        
        self.salvar_dados()
        self.atualizar_lista_gastos()
        self.atualizar_estatisticas()
        janela.destroy()
        messagebox.showinfo("Sucesso", "Gasto atualizado com sucesso!")
    
    def remover_gasto(self):
        """Remove o gasto selecionado"""
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione um ou mais gastos para remover!")
            return
            
        ids_gastos = [self.tree.item(item)['values'][0] for item in selecionados]
        total = sum(float(self.tree.item(item)['values'][2].replace('.', '').replace(',', '.')) 
                   for item in selecionados)
        
        confirmacao = messagebox.askyesno(
            "Confirmar", 
            f"Tem certeza que deseja remover {len(ids_gastos)} gasto(s) selecionado(s) no total de R$ {total:,.2f}?"
        )
        
        if confirmacao:
            self.gastos = [g for g in self.gastos if g['id'] not in ids_gastos]
            self.salvar_dados()
            self.atualizar_lista_gastos()
            self.atualizar_estatisticas()
            messagebox.showinfo("Sucesso", f"{len(ids_gastos)} gasto(s) removido(s) com sucesso!")
    
    def mostrar_dialogo_filtro(self):
        """Mostra diálogo com opções de filtro"""
        filter_window = tk.Toplevel(self.root)
        filter_window.title("Filtrar Gastos")
        filter_window.geometry("400x300")
        filter_window.transient(self.root)
        filter_window.grab_set()
        
        # Frame principal
        filter_frame = ttk.Frame(filter_window, padding=10)
        filter_frame.pack(fill=tk.BOTH, expand=True)
        
        # Variáveis de controle
        self.filtro_categoria_var = tk.StringVar()
        self.filtro_mes_var = tk.StringVar()
        self.filtro_valor_min_var = tk.StringVar()
        self.filtro_valor_max_var = tk.StringVar()
        self.filtro_data_inicio_var = tk.StringVar()
        self.filtro_data_fim_var = tk.StringVar()
        
        # Widgets de filtro
        ttk.Label(filter_frame, text="Categoria:").grid(row=0, column=0, sticky="w", pady=5)
        categoria_combobox = ttk.Combobox(filter_frame, textvariable=self.filtro_categoria_var, 
                                        values=self.categorias_predefinidas)
        categoria_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Mês/Ano (MM/AAAA):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(filter_frame, textvariable=self.filtro_mes_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Valor Mínimo:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(filter_frame, textvariable=self.filtro_valor_min_var).grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Valor Máximo:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(filter_frame, textvariable=self.filtro_valor_max_var).grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Período Inicial:").grid(row=4, column=0, sticky="w", pady=5)
        data_inicio_entry = DateEntry(filter_frame, textvariable=self.filtro_data_inicio_var, 
                                    date_pattern='dd/mm/yyyy')
        data_inicio_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Período Final:").grid(row=5, column=0, sticky="w", pady=5)
        data_fim_entry = DateEntry(filter_frame, textvariable=self.filtro_data_fim_var, 
                                 date_pattern='dd/mm/yyyy')
        data_fim_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        
        # Botões
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")
        
        ttk.Button(btn_frame, text="Aplicar Filtros", style='Primary.TButton',
                  command=lambda: self.aplicar_filtros(filter_window)).pack(side=tk.LEFT, padx=5, expand=True)
        
        ttk.Button(btn_frame, text="Cancelar", command=filter_window.destroy).pack(side=tk.LEFT, padx=5, expand=True)
    
    def aplicar_filtros(self, janela):
        """Aplica os filtros selecionados"""
        gastos_filtrados = self.gastos
        
        # Filtro por categoria
        categoria = self.filtro_categoria_var.get()
        if categoria:
            gastos_filtrados = [g for g in gastos_filtrados if g['categoria'].lower() == categoria.lower()]
        
        # Filtro por mês/ano
        mes = self.filtro_mes_var.get()
        if mes:
            try:
                mes_num, ano = map(int, mes.split('/'))
                gastos_filtrados = [
                    g for g in gastos_filtrados 
                    if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').month == mes_num
                    and datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').year == ano
                ]
            except ValueError:
                messagebox.showerror("Erro", "Formato de mês inválido! Use MM/AAAA.")
                return
        
        # Filtro por valor mínimo
        valor_min = self.filtro_valor_min_var.get()
        if valor_min:
            try:
                valor_min = float(valor_min.replace(',', '.'))
                gastos_filtrados = [g for g in gastos_filtrados if g['valor'] >= valor_min]
            except ValueError:
                messagebox.showerror("Erro", "Valor mínimo inválido! Digite um número.")
                return
        
        # Filtro por valor máximo
        valor_max = self.filtro_valor_max_var.get()
        if valor_max:
            try:
                valor_max = float(valor_max.replace(',', '.'))
                gastos_filtrados = [g for g in gastos_filtrados if g['valor'] <= valor_max]
            except ValueError:
                messagebox.showerror("Erro", "Valor máximo inválido! Digite um número.")
                return
        
        # Filtro por período
        data_inicio = self.filtro_data_inicio_var.get()
        data_fim = self.filtro_data_fim_var.get()
        if data_inicio or data_fim:
            try:
                if data_inicio:
                    inicio = datetime.strptime(data_inicio, '%d/%m/%Y')
                    gastos_filtrados = [
                        g for g in gastos_filtrados 
                        if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S') >= inicio
                    ]
                
                if data_fim:
                    fim = datetime.strptime(data_fim, '%d/%m/%Y') + timedelta(days=1)
                    gastos_filtrados = [
                        g for g in gastos_filtrados 
                        if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S') <= fim
                    ]
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido! Use DD/MM/AAAA.")
                return
        
        self.atualizar_lista_gastos(gastos_filtrados)
        janela.destroy()
        messagebox.showinfo("Filtros", f"{len(gastos_filtrados)} gastos encontrados com os filtros aplicados.")
    
    def limpar_filtros(self):
        """Remove todos os filtros aplicados"""
        self.atualizar_lista_gastos()
        messagebox.showinfo("Filtros", "Todos os filtros foram removidos.")
    
    def mostrar_resumo(self):
        """Mostra resumo completo dos gastos"""
        hoje = datetime.now()
        mes_atual = hoje.strftime('%m/%Y')
        mes_passado = (hoje.replace(day=1) - timedelta(days=1)).strftime('%m/%Y')
        
        # Calcular totais
        total_geral = sum(g['valor'] for g in self.gastos)
        total_mes = sum(
            g['valor'] for g in self.gastos 
            if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').strftime('%m/%Y') == mes_atual
        )
        total_mes_passado = sum(
            g['valor'] for g in self.gastos 
            if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').strftime('%m/%Y') == mes_passado
        )
        
        # Calcular variação mensal
        if total_mes_passado > 0:
            variacao = ((total_mes - total_mes_passado) / total_mes_passado) * 100
            texto_variacao = f"{variacao:+.1f}% em relação ao mês passado"
        else:
            texto_variacao = "Dados insuficientes para comparação"
        
        # Calcular por categoria
        categorias = defaultdict(float)
        for g in self.gastos:
            categorias[g['categoria']] += g['valor']
        
        # Gerar texto do resumo
        resumo_texto = f"=== RESUMO FINANCEIRO ===\n\n"
        resumo_texto += f"Total Geral: R$ {total_geral:,.2f}\n"
        resumo_texto += f"Total Mês Atual ({mes_atual}): R$ {total_mes:,.2f}\n"
        resumo_texto += f"  → {texto_variacao}\n\n"
        resumo_texto += "=== GASTOS POR CATEGORIA ===\n\n"
        
        for categoria, total in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
            percentual = (total / total_geral) * 100 if total_geral > 0 else 0
            limite = self.limites_categoria.get(categoria)
            
            if limite:
                percentual_limite = (total / limite) * 100
                resumo_texto += (
                    f"{categoria}: R$ {total:,.2f} ({percentual:.1f}% do total) | "
                    f"Limite: R$ {limite:,.2f} ({percentual_limite:.1f}%)\n"
                )
            else:
                resumo_texto += f"{categoria}: R$ {total:,.2f} ({percentual:.1f}% do total)\n"
        
        # Exibir no widget de texto
        self.resumo_text.config(state=tk.NORMAL)
        self.resumo_text.delete(1.0, tk.END)
        self.resumo_text.insert(tk.END, resumo_texto)
        self.resumo_text.config(state=tk.DISABLED)
    
    def gerar_graficos(self):
        """Gera e exibe gráficos de análise"""
        # Limpar frame de gráficos
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Obter período para filtro
        periodo = simpledialog.askstring("Período", "Digite o mês/ano (MM/AAAA) ou deixe em branco para todos:")
        
        # Filtrar gastos por período
        gastos_filtrados = self.gastos
        if periodo:
            try:
                mes, ano = map(int, periodo.split('/'))
                gastos_filtrados = [
                    g for g in self.gastos 
                    if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').month == mes
                    and datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').year == ano
                ]
            except ValueError:
                messagebox.showerror("Erro", "Formato inválido! Use MM/AAAA.")
                return
        
        if not gastos_filtrados:
            messagebox.showinfo("Info", "Nenhum dado para exibir no período selecionado.")
            return
        
        # Calcular dados para gráficos
        categorias = defaultdict(float)
        meses = defaultdict(float)
        for g in gastos_filtrados:
            data = datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S')
            categorias[g['categoria']] += g['valor']
            meses[data.strftime('%m/%Y')] += g['valor']
        
        # Criar figura com subplots
        fig = plt.figure(figsize=(10, 8), tight_layout=True)
        
        # Gráfico 1: Pizza de categorias
        ax1 = fig.add_subplot(2, 2, 1)
        categorias_ordenadas = dict(sorted(categorias.items(), key=lambda x: x[1], reverse=True))
        ax1.pie(
            categorias_ordenadas.values(), 
            labels=categorias_ordenadas.keys(), 
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'white'}
        )
        ax1.set_title('Distribuição por Categoria')
        
        # Gráfico 2: Barras de categorias
        ax2 = fig.add_subplot(2, 2, 2)
        bars = ax2.bar(categorias_ordenadas.keys(), categorias_ordenadas.values(), color='skyblue')
        ax2.set_title('Gastos por Categoria')
        ax2.tick_params(axis='x', rotation=45)
        ax2.set_ylabel('Valor (R$)')
        
        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width()/2., height,
                f'R${height:,.2f}',
                ha='center', va='bottom', fontsize=8
            )
        
        # Gráfico 3: Evolução mensal
        if len(meses) > 1:  # Só mostra se tiver mais de um mês
            ax3 = fig.add_subplot(2, 1, 2)
            meses_ordenados = sorted(meses.items(), key=lambda x: datetime.strptime(x[0], '%m/%Y'))
            meses_labels = [m[0] for m in meses_ordenados]
            meses_valores = [m[1] for m in meses_ordenados]
            
            ax3.plot(meses_labels, meses_valores, marker='o', linestyle='-', color='green')
            ax3.set_title('Evolução Mensal')
            ax3.set_ylabel('Valor (R$)')
            ax3.grid(True)
            
            # Adicionar valores nos pontos
            for i, v in enumerate(meses_valores):
                ax3.text(i, v, f"R${v:,.2f}", ha='center', va='bottom', fontsize=8)
        
        # Exibir gráficos na interface
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Adicionar botão para salvar gráficos
        ttk.Button(
            self.graph_frame, text="Salvar Gráficos", style='Primary.TButton',
            command=lambda: self.salvar_graficos(fig)
        ).pack(pady=5)
    
    def salvar_graficos(self, fig):
        """Salva os gráficos em um arquivo de imagem"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")],
            title="Salvar Gráficos Como"
        )
        
        if filepath:
            try:
                fig.savefig(filepath, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Sucesso", f"Gráficos salvos com sucesso em:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar gráficos:\n{str(e)}")
    
    def verificar_limite_categoria(self, categoria):
        """Verifica se o limite da categoria foi excedido"""
        if categoria in self.limites_categoria:
            gasto_categoria = sum(g['valor'] for g in self.gastos if g['categoria'].lower() == categoria.lower())
            limite = self.limites_categoria[categoria]
            
            if gasto_categoria > limite:
                # Mostrar alerta visual
                self.mostrar_alerta_limite(categoria, gasto_categoria, limite)
    
    def mostrar_alerta_limite(self, categoria, gasto, limite):
        """Mostra alerta visual de limite excedido"""
        alert_window = tk.Toplevel(self.root)
        alert_window.title("⚠️ Limite Excedido")
        alert_window.geometry("400x200")
        alert_window.resizable(False, False)
        
        # Ícone de alerta
        try:
            icon = Image.open("alert_icon.png") if os.path.exists("alert_icon.png") else None
            if icon:
                icon = icon.resize((64, 64), Image.LANCZOS)
                icon = ImageTk.PhotoImage(icon)
                icon_label = tk.Label(alert_window, image=icon)
                icon_label.image = icon
                icon_label.pack(pady=10)
        except:
            pass
        
        # Mensagem
        msg = (
            f"Você ultrapassou o limite para {categoria}!\n\n"
            f"Limite definido: R$ {limite:,.2f}\n"
            f"Total gasto: R$ {gasto:,.2f}\n\n"
            f"Diferença: R$ {gasto - limite:,.2f}"
        )
        
        ttk.Label(alert_window, text=msg, justify=tk.CENTER, font=('Arial', 10)).pack(pady=5)
        ttk.Button(alert_window, text="OK", command=alert_window.destroy).pack(pady=10)
        
        # Manter a janela no topo
        alert_window.transient(self.root)
        alert_window.grab_set()
        self.root.wait_window(alert_window)
    
    def exportar_selecao(self):
        """Exporta os gastos selecionados para CSV"""
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione um ou mais gastos para exportar!")
            return
            
        gastos_selecionados = []
        for item in selecionados:
            values = self.tree.item(item)['values']
            gasto = {
                'id': values[0],
                'data': datetime.strptime(values[1], '%d/%m/%Y').strftime('%Y-%m-%d'),
                'valor': float(values[2].replace('.', '').replace(',', '.')),
                'categoria': values[3],
                'descricao': values[4]
            }
            gastos_selecionados.append(gasto)
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv"), ("All Files", "*.*")],
            title="Salvar Gastos Selecionados Como"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("ID,Data,Valor,Categoria,Descrição\n")
                    for g in gastos_selecionados:
                        f.write(f"{g['id']},{g['data']},{g['valor']:.2f},{g['categoria']},{g['descricao']}\n")
                messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar dados:\n{str(e)}")
    
    def exportar_dados(self):
        """Exporta todos os dados para arquivo JSON ou CSV"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON File", "*.json"), ("CSV File", "*.csv"), ("All Files", "*.*")],
            title="Exportar Dados Como"
        )
        
        if filepath:
            try:
                if filepath.endswith('.json'):
                    dados = {
                        'gastos': self.gastos,
                        'limites': self.limites_categoria,
                        'categorias': self.categorias_predefinidas
                    }
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(dados, f, indent=2, ensure_ascii=False)
                elif filepath.endswith('.csv'):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write("ID,Data,Valor,Categoria,Descrição\n")
                        for g in self.gastos:
                            data_formatada = datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                            f.write(f"{g['id']},{data_formatada},{g['valor']:.2f},{g['categoria']},{g['descricao']}\n")
                
                messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar dados:\n{str(e)}")
    
    def importar_dados(self):
        """Importa dados de arquivo JSON ou CSV"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON File", "*.json"), ("CSV File", "*.csv"), ("All Files", "*.*")],
            title="Selecionar Arquivo para Importar"
        )
        
        if filepath:
            try:
                if filepath.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        
                    if isinstance(dados, dict):  # Formato novo
                        novos_gastos = dados.get('gastos', [])
                        novos_limites = dados.get('limites', {})
                        novas_categorias = dados.get('categorias', [])
                    else:  # Formato antigo
                        novos_gastos = dados
                        novos_limites = {}
                        novas_categorias = []
                    
                    # Atualizar dados
                    self.gastos.extend(novos_gastos)
                    self.limites_categoria.update(novos_limites)
                    self.categorias_predefinidas = list(set(self.categorias_predefinidas + novas_categorias))
                    self.categorias_predefinidas.sort()
                    self.categoria_combobox['values'] = self.categorias_predefinidas
                    
                    # Atribuir IDs aos novos gastos
                    max_id = max([g['id'] for g in self.gastos] + [0])
                    for i, gasto in enumerate(novos_gastos):
                        if 'id' not in gasto:
                            max_id += 1
                            gasto['id'] = max_id
                
                elif filepath.endswith('.csv'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        linhas = f.readlines()
                    
                    novos_gastos = []
                    max_id = max([g['id'] for g in self.gastos] + [0])
                    
                    for linha in linhas[1:]:  # Pular cabeçalho
                        campos = linha.strip().split(',')
                        if len(campos) >= 5:
                            max_id += 1
                            novo_gasto = {
                                'id': max_id,
                                'data': datetime.strptime(campos[1], '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S'),
                                'valor': float(campos[2]),
                                'categoria': campos[3],
                                'descricao': campos[4]
                            }
                            novos_gastos.append(novo_gasto)
                    
                    self.gastos.extend(novos_gastos)
                
                self.salvar_dados()
                self.atualizar_lista_gastos()
                self.atualizar_estatisticas()
                messagebox.showinfo("Sucesso", f"Dados importados com sucesso!\n{len(novos_gastos)} novos gastos adicionados.")
            
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao importar dados:\n{str(e)}")
    
    def criar_backup_manual(self):
        """Cria um backup manual dos dados"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f'gastos_backup_manual_{timestamp}.json')
            
            dados = {
                'gastos': self.gastos,
                'limites': self.limites_categoria,
                'categorias': self.categorias_predefinidas
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Sucesso", f"Backup criado com sucesso em:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar backup:\n{str(e)}")
    
    def alternar_tema(self):
        """Alterna entre tema claro e escuro"""
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self.configurar_estilos()
    
    def mostrar_sobre(self):
        """Mostra diálogo 'Sobre'"""
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre o Gestor Financeiro")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        # Conteúdo
        ttk.Label(about_window, text="Gestor Financeiro Pessoal", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(about_window, text="Versão 2.0", font=('Arial', 12)).pack(pady=5)
        
        info_text = (
            "Desenvolvido por João Gonçalves\n\n"
            "Um sistema completo para gerenciamento de gastos pessoais\n"
            "com interface amigável e recursos avançados.\n\n"
            "Recursos:\n"
            "✔ Registro de gastos detalhado\n"
            "✔ Limites por categoria\n"
            "✔ Gráficos e relatórios\n"
            "✔ Backup automático\n"
            "✔ Exportação/importação de dados"
        )
        
        ttk.Label(about_window, text=info_text, justify=tk.LEFT).pack(pady=10)
        ttk.Button(about_window, text="Fechar", command=about_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorGastosGUI(root)
    root.mainloop()