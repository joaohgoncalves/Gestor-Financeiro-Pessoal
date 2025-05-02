import json
from datetime import datetime
import os
import matplotlib.pyplot as plt
from collections import defaultdict

class GerenciadorGastos:
    def __init__(self, arquivo_dados='gastos.json'):
        self.arquivo_dados = arquivo_dados
        self.gastos = []
        self.limites_categoria = {}
        self.carregar_dados()
        
    def carregar_dados(self):
        if os.path.exists(self.arquivo_dados):
            with open(self.arquivo_dados, 'r') as f:
                dados = json.load(f)
                self.gastos = dados.get('gastos', [])
                self.limites_categoria = dados.get('limites', {})
    
    def salvar_dados(self):
        dados = {
            'gastos': self.gastos,
            'limites': self.limites_categoria
        }
        with open(self.arquivo_dados, 'w') as f:
            json.dump(dados, f, indent=2)
    
    def adicionar_gasto(self, valor, categoria, descricao=''):
        try:
            valor = float(valor)
            if valor <= 0:
                print("O valor deve ser positivo!")
                return
        except ValueError:
            print("Valor inválido! Digite um número.")
            return
            
        data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        gasto = {
            'id': len(self.gastos) + 1,
            'data': data,
            'valor': valor,
            'categoria': categoria,
            'descricao': descricao
        }
        self.gastos.append(gasto)
        self.salvar_dados()
        self.verificar_limite_categoria(categoria)
        print(f"\n✅ Gasto de R${valor:.2f} em {categoria} registrado com sucesso!")
    
    def editar_gasto(self, id_gasto):
        for gasto in self.gastos:
            if gasto['id'] == id_gasto:
                print(f"\nEditando gasto ID {id_gasto}:")
                print(f"1. Valor atual: R${gasto['valor']:.2f}")
                print(f"2. Categoria atual: {gasto['categoria']}")
                print(f"3. Descrição atual: {gasto['descricao']}")
                
                opcao = input("O que deseja editar? (1-3, ou 0 para cancelar): ")
                
                if opcao == '1':
                    novo_valor = input("Novo valor: R$")
                    try:
                        gasto['valor'] = float(novo_valor)
                    except ValueError:
                        print("Valor inválido!")
                elif opcao == '2':
                    antiga_categoria = gasto['categoria']
                    gasto['categoria'] = input("Nova categoria: ")
                    self.verificar_limite_categoria(gasto['categoria'])
                elif opcao == '3':
                    gasto['descricao'] = input("Nova descrição: ")
                elif opcao == '0':
                    return
                else:
                    print("Opção inválida!")
                    return
                
                gasto['data'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.salvar_dados()
                print("Gasto atualizado com sucesso!")
                return
        
        print(f"Gasto com ID {id_gasto} não encontrado!")
    
    def remover_gasto(self, id_gasto):
        for i, gasto in enumerate(self.gastos):
            if gasto['id'] == id_gasto:
                confirmacao = input(f"Tem certeza que deseja remover o gasto de R${gasto['valor']:.2f} em {gasto['categoria']}? (s/n): ")
                if confirmacao.lower() == 's':
                    del self.gastos[i]
                    self.salvar_dados()
                    print("Gasto removido com sucesso!")
                return
        
        print(f"Gasto com ID {id_gasto} não encontrado!")
    
    def verificar_limite_categoria(self, categoria):
        if categoria in self.limites_categoria:
            gasto_categoria = sum(g['valor'] for g in self.gastos if g['categoria'] == categoria)
            limite = self.limites_categoria[categoria]
            if gasto_categoria > limite:
                print(f"\n⚠️ ATENÇÃO: Você ultrapassou o limite de R${limite:.2f} para {categoria}!")
                print(f"Total gasto em {categoria}: R${gasto_categoria:.2f}")
    
    def definir_limite_categoria(self, categoria, limite):
        try:
            limite = float(limite)
            self.limites_categoria[categoria] = limite
            self.salvar_dados()
            print(f"Limite de R${limite:.2f} definido para a categoria {categoria}!")
            self.verificar_limite_categoria(categoria)
        except ValueError:
            print("Valor de limite inválido!")
    
    def listar_gastos(self, filtro_categoria=None, filtro_mes=None):
        gastos_filtrados = self.gastos
        
        if filtro_categoria:
            gastos_filtrados = [g for g in gastos_filtrados if g['categoria'].lower() == filtro_categoria.lower()]
        
        if filtro_mes:
            try:
                mes, ano = map(int, filtro_mes.split('/'))
                gastos_filtrados = [
                    g for g in gastos_filtrados 
                    if datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').month == mes
                    and datetime.strptime(g['data'], '%Y-%m-%d %H:%M:%S').year == ano
                ]
            except:
                print("Formato de mês inválido! Use MM/AAAA")
                return
        
        if not gastos_filtrados:
            print("Nenhum gasto encontrado com os filtros aplicados.")
            return
        
        print("\n--- LISTA DE GASTOS ---")
        for gasto in gastos_filtrados:
            print(f"ID: {gasto['id']} | Data: {gasto['data']} | Valor: R${gasto['valor']:.2f} | "
                  f"Categoria: {gasto['categoria']} | Descrição: {gasto['descricao']}")
    
    def resumo_por_categoria(self, mes=None):
        if not self.gastos:
            print("Nenhum gasto registrado.")
            return
        
        categorias = defaultdict(float)
        for gasto in self.gastos:
            if mes:
                data_gasto = datetime.strptime(gasto['data'], '%Y-%m-%d %H:%M:%S')
                if data_gasto.strftime('%m/%Y') != mes:
                    continue
            categorias[gasto['categoria']] += gasto['valor']
        
        if not categorias:
            print(f"Nenhum gasto encontrado para o mês {mes}.")
            return
        
        print("\n--- RESUMO POR CATEGORIA ---")
        for categoria, total in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
            limite = self.limites_categoria.get(categoria, None)
            if limite:
                percentual = (total / limite) * 100
                print(f"{categoria}: R${total:.2f} ({(percentual):.1f}% do limite de R${limite:.2f})")
            else:
                print(f"{categoria}: R${total:.2f}")
        
        total_gasto = sum(categorias.values())
        print(f"\nTotal gasto: R${total_gasto:.2f}")
    
    def gerar_grafico(self):
        if not self.gastos:
            print("Nenhum gasto registrado para gerar gráfico.")
            return
        
        categorias = defaultdict(float)
        for gasto in self.gastos:
            categorias[gasto['categoria']] += gasto['valor']
        
        if not categorias:
            print("Nenhum dado para exibir.")
            return
        
        plt.figure(figsize=(10, 6))
        categorias_ordenadas = dict(sorted(categorias.items(), key=lambda x: x[1], reverse=True))
        
        # Gráfico de barras
        plt.subplot(1, 2, 1)
        plt.bar(categorias_ordenadas.keys(), categorias_ordenadas.values())
        plt.title('Gastos por Categoria')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Valor (R$)')
        
        # Gráfico de pizza
        plt.subplot(1, 2, 2)
        plt.pie(categorias_ordenadas.values(), labels=categorias_ordenadas.keys(), autopct='%1.1f%%')
        plt.title('Distribuição dos Gastos')
        
        plt.tight_layout()
        plt.show()
    
    def menu(self):
        while True:
            print("\n=== GESTOR DE GASTOS AVANÇADO ===")
            print("1. Adicionar novo gasto")
            print("2. Editar gasto existente")
            print("3. Remover gasto")
            print("4. Listar todos os gastos")
            print("5. Listar gastos por categoria")
            print("6. Listar gastos por mês")
            print("7. Resumo por categoria")
            print("8. Resumo por mês")
            print("9. Definir limite para categoria")
            print("10. Gerar gráficos")
            print("11. Sair")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == '1':
                valor = input("Valor do gasto: R$")
                categoria = input("Categoria: ")
                descricao = input("Descrição (opcional): ")
                self.adicionar_gasto(valor, categoria, descricao)
            elif opcao == '2':
                id_gasto = input("ID do gasto a editar: ")
                try:
                    self.editar_gasto(int(id_gasto))
                except ValueError:
                    print("ID inválido!")
            elif opcao == '3':
                id_gasto = input("ID do gasto a remover: ")
                try:
                    self.remover_gasto(int(id_gasto))
                except ValueError:
                    print("ID inválido!")
            elif opcao == '4':
                self.listar_gastos()
            elif opcao == '5':
                categoria = input("Digite a categoria para filtrar: ")
                self.listar_gastos(filtro_categoria=categoria)
            elif opcao == '6':
                mes = input("Digite o mês/ano para filtrar (MM/AAAA): ")
                self.listar_gastos(filtro_mes=mes)
            elif opcao == '7':
                self.resumo_por_categoria()
            elif opcao == '8':
                mes = input("Digite o mês/ano para o resumo (MM/AAAA): ")
                self.resumo_por_categoria(mes)
            elif opcao == '9':
                categoria = input("Categoria: ")
                limite = input(f"Limite para {categoria}: R$")
                self.definir_limite_categoria(categoria, limite)
            elif opcao == '10':
                self.gerar_grafico()
            elif opcao == '11':
                print("Saindo do sistema...")
                break
            else:
                print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    gestor = GerenciadorGastos()
    gestor.menu()