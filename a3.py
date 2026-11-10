"""
PROJETO 1 - SISTEMA PDV (Ponto de Venda)

Requisitos do projeto:
  - Cadastros: Produtos, Clientes e Vendedores
  - Controle automático de estoque (baixa a cada venda)
  - Cálculo de comissão (5%) e impostos (25%)
  - Emissão de recibos e relatórios

Como o sistema está organizado (visão geral da lógica):
  1. CONSTANTES      -> valores das regras de negócio (5%, 25%, estoque mínimo)
  2. CLASSES         -> Produto, Cliente, Vendedor, ItemVenda, Venda
                        (cada classe representa uma "coisa" do mundo real)
  3. CLASSE PDV      -> o "cérebro": guarda os cadastros e executa as operações
  4. FUNÇÕES DE ENTRADA -> leitura segura do que o usuário digita
  5. MENU            -> interface de texto que chama as funções do PDV
"""

import os
from datetime import datetime

# ============================================================
# 1. CONSTANTES (regras de negócio)
# ============================================================
# Ficam no topo para que, se a regra mudar, alteremos em UM só lugar.
ALIQUOTA_IMPOSTO = 0.25      # 25% de imposto sobre o valor da venda
PERCENTUAL_COMISSAO = 0.05   # 5% de comissão para o vendedor
ESTOQUE_MINIMO = 5           # abaixo (ou igual) a isso, o relatório avisa
PASTA_RECIBOS = "recibos"    # pasta onde os recibos .txt serão salvos


# ============================================================
# 2. CLASSES DE DADOS
# ============================================================
class Produto:
    """Representa um produto à venda."""

    def __init__(self, codigo, nome, preco, estoque):
        self.codigo = codigo      # identificador único (ex.: 1, 2, 3...)
        self.nome = nome
        self.preco = preco        # preço de venda unitário
        self.estoque = estoque    # quantidade disponível agora


class Cliente:
    """Representa um cliente que compra no PDV."""

    def __init__(self, codigo, nome, cpf):
        self.codigo = codigo
        self.nome = nome
        self.cpf = cpf


class Vendedor:
    """Representa um vendedor. Acumula a comissão que ele já ganhou."""

    def __init__(self, codigo, nome):
        self.codigo = codigo
        self.nome = nome
        self.comissao_acumulada = 0.0   # soma das comissões de todas as vendas


class ItemVenda:
    """
    Uma linha dentro de uma venda (ex.: 3 unidades do produto X).

    IMPORTANTE: guardamos o preço no MOMENTO da venda (preco_unitario).
    Assim, se o preço do produto mudar depois, o recibo antigo continua correto.
    """

    def __init__(self, produto, quantidade):
        self.produto = produto
        self.quantidade = quantidade
        self.preco_unitario = produto.preco   # "congela" o preço atual

    @property
    def subtotal(self):
        # Valor desta linha = preço unitário x quantidade
        return self.preco_unitario * self.quantidade
# O decorador @property em Python serve para transformar um método de uma classe em um atributo gerenciado. 
# Na prática, ele permite que você execute códigos (como validações ou cálculos) ao ler, modificar ou deletar o valor de um atributo, 
# mas mantendo uma sintaxe limpa de acesso direto — sem precisar chamar métodos com parênteses (como .get_x() ou .set_x())


class Venda:
    """
    Uma venda completa: quem comprou, quem vendeu e a lista de itens.
    Os valores (subtotal, imposto, total, comissão) são calculados
    automaticamente a partir dos itens, usando @property.
    """

    def __init__(self, numero, cliente, vendedor):
        self.numero = numero
        self.data = datetime.now()   # data/hora da venda
        self.cliente = cliente
        self.vendedor = vendedor
        self.itens = []              # lista de ItemVenda

    @property
    def subtotal(self):
        # Soma de todos os itens (valor dos produtos, ainda sem imposto)
        return sum(item.subtotal for item in self.itens)

    @property
    def imposto(self):
        # 25% do subtotal
        return self.subtotal * ALIQUOTA_IMPOSTO

    @property
    def total(self):
        # O que o cliente efetivamente paga: produtos + imposto
        return self.subtotal + self.imposto

    @property
    def comissao(self):
        # 5% do subtotal (comissão calculada sobre o valor dos produtos,
        # não sobre o imposto, pois imposto não é receita da loja)
        return self.subtotal * PERCENTUAL_COMISSAO


# ============================================================
# 3. CLASSE PDV (o "cérebro" do sistema)
# ============================================================
class PDV:
    """Guarda todos os cadastros e executa as operações do sistema."""

    def __init__(self):
        # Dicionários: a chave é o código, o valor é o objeto.
        # Isso torna a busca por código muito rápida e simples.
        self.produtos = {}
        self.clientes = {}
        self.vendedores = {}
        self.vendas = []             # histórico de vendas finalizadas

        # Contadores para gerar códigos automáticos e únicos
        self._prox_produto = 1
        self._prox_cliente = 1
        self._prox_vendedor = 1
        self._prox_venda = 1

    # ---------------- CADASTROS ----------------
    def cadastrar_produto(self, nome, preco, estoque):
        produto = Produto(self._prox_produto, nome, preco, estoque)
        self.produtos[produto.codigo] = produto
        self._prox_produto += 1      # prepara o próximo código
        return produto

    def cadastrar_cliente(self, nome, cpf):
        # Regra: não permitir dois clientes com o mesmo CPF
        for c in self.clientes.values():
            if c.cpf == cpf:
                raise ValueError("Já existe um cliente com esse CPF.")
        cliente = Cliente(self._prox_cliente, nome, cpf)
        self.clientes[cliente.codigo] = cliente
        self._prox_cliente += 1
        return cliente

    def cadastrar_vendedor(self, nome):
        vendedor = Vendedor(self._prox_vendedor, nome)
        self.vendedores[vendedor.codigo] = vendedor
        self._prox_vendedor += 1
        return vendedor

    # ---------------- VENDA ----------------
    def iniciar_venda(self, cod_cliente, cod_vendedor):
        """Cria uma venda vazia (um 'carrinho'), validando cliente e vendedor."""
        if cod_cliente not in self.clientes:
            raise ValueError("Cliente não encontrado.")
        if cod_vendedor not in self.vendedores:
            raise ValueError("Vendedor não encontrado.")
        return Venda(self._prox_venda,
                     self.clientes[cod_cliente],
                     self.vendedores[cod_vendedor])

    def adicionar_item(self, venda, cod_produto, quantidade):
        """
        Adiciona um produto ao carrinho SEM baixar o estoque ainda.
        A baixa só acontece quando a venda é finalizada.
        """
        if cod_produto not in self.produtos:
            raise ValueError("Produto não encontrado.")
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")

        produto = self.produtos[cod_produto]

        # Se o produto já está no carrinho, somamos as quantidades.
        # Assim a checagem de estoque considera o TOTAL pedido.
        for item in venda.itens:
            if item.produto.codigo == cod_produto:
                if item.quantidade + quantidade > produto.estoque:
                    raise ValueError(
                        f"Estoque insuficiente. Disponível: {produto.estoque}")
                item.quantidade += quantidade
                return

        # Produto novo no carrinho: confere se há estoque suficiente
        if quantidade > produto.estoque:
            raise ValueError(f"Estoque insuficiente. Disponível: {produto.estoque}")
        venda.itens.append(ItemVenda(produto, quantidade))

    def finalizar_venda(self, venda):
        """
        Confirma a venda. Aqui acontece o CONTROLE AUTOMÁTICO DE ESTOQUE:
        para cada item, subtraímos a quantidade vendida do estoque do produto.
        Também creditamos a comissão ao vendedor e guardamos a venda no histórico.
        """
        if not venda.itens:
            raise ValueError("A venda não possui itens.")

        for item in venda.itens:
            item.produto.estoque -= item.quantidade     # baixa automática

        venda.vendedor.comissao_acumulada += venda.comissao
        self.vendas.append(venda)
        self._prox_venda += 1

    # ---------------- RECIBO ----------------
    def gerar_recibo(self, venda):
        """Monta o texto do recibo, mostra na tela e salva em arquivo .txt."""
        linhas = []
        linhas.append("=" * 52)
        linhas.append("                 RECIBO DE VENDA")
        linhas.append("=" * 52)
        linhas.append(f"Venda nº: {venda.numero:05d}")
        linhas.append(f"Data....: {venda.data.strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append(f"Cliente.: {venda.cliente.nome} (CPF {venda.cliente.cpf})")
        linhas.append(f"Vendedor: {venda.vendedor.nome}")
        linhas.append("-" * 52)
        linhas.append(f"{'Produto':<20}{'Qtd':>5}{'Unit.':>11}{'Subtotal':>13}")
        linhas.append("-" * 52)
        for item in venda.itens:
            linhas.append(
                f"{item.produto.nome[:19]:<20}{item.quantidade:>5}"
                f"{item.preco_unitario:>11.2f}{item.subtotal:>13.2f}")
        linhas.append("-" * 52)
        linhas.append(f"{'Subtotal:':<39}R$ {venda.subtotal:>8.2f}")
        linhas.append(f"{'Imposto (25%):':<39}R$ {venda.imposto:>8.2f}")
        linhas.append(f"{'TOTAL A PAGAR:':<39}R$ {venda.total:>8.2f}")
        linhas.append("=" * 52)

        texto = "\n".join(linhas)

        # Salva em arquivo: recibos/recibo_00001.txt
        os.makedirs(PASTA_RECIBOS, exist_ok=True)
        caminho = os.path.join(PASTA_RECIBOS, f"recibo_{venda.numero:05d}.txt")
        with open(caminho, "w", encoding="utf-8") as arq:
            arq.write(texto)

        return texto, caminho

    # ---------------- RELATÓRIOS ----------------
    def relatorio_estoque(self):
        print("\n--- RELATÓRIO DE ESTOQUE ---")
        if not self.produtos:
            print("Nenhum produto cadastrado.")
            return
        print(f"{'Cód':<5}{'Produto':<25}{'Preço':>10}{'Estoque':>10}  Aviso")
        for p in self.produtos.values():
            # Alerta se o estoque estiver baixo
            aviso = "<< ESTOQUE BAIXO" if p.estoque <= ESTOQUE_MINIMO else ""
            print(f"{p.codigo:<5}{p.nome:<25}{p.preco:>10.2f}{p.estoque:>10}  {aviso}")

    def relatorio_vendas(self):
        print("\n--- RELATÓRIO DE VENDAS ---")
        if not self.vendas:
            print("Nenhuma venda realizada.")
            return
        print(f"{'Nº':<7}{'Data':<18}{'Cliente':<18}{'Vendedor':<14}"
              f"{'Subtotal':>10}{'Imposto':>10}{'Total':>10}")
        for v in self.vendas:
            print(f"{v.numero:<7}{v.data.strftime('%d/%m/%Y %H:%M'):<18}"
                  f"{v.cliente.nome[:17]:<18}{v.vendedor.nome[:13]:<14}"
                  f"{v.subtotal:>10.2f}{v.imposto:>10.2f}{v.total:>10.2f}")

        # Totais gerais do período
        print("-" * 87)
        print(f"Faturamento (total pago): R$ {sum(v.total for v in self.vendas):.2f}")
        print(f"Impostos arrecadados....: R$ {sum(v.imposto for v in self.vendas):.2f}")

    def relatorio_comissoes(self):
        print("\n--- RELATÓRIO DE COMISSÕES (5%) ---")
        if not self.vendedores:
            print("Nenhum vendedor cadastrado.")
            return
        for vend in self.vendedores.values():
            qtd = sum(1 for v in self.vendas if v.vendedor.codigo == vend.codigo)
            print(f"{vend.nome:<20} Vendas: {qtd:<4} "
                  f"Comissão: R$ {vend.comissao_acumulada:.2f}")

    # ---------------- LISTAGENS ----------------
    def listar_clientes(self):
        print("\n--- CLIENTES ---")
        for c in self.clientes.values():
            print(f"{c.codigo} - {c.nome} (CPF {c.cpf})")
        if not self.clientes:
            print("Nenhum cliente cadastrado.")

    def listar_vendedores(self):
        print("\n--- VENDEDORES ---")
        for v in self.vendedores.values():
            print(f"{v.codigo} - {v.nome}")
        if not self.vendedores:
            print("Nenhum vendedor cadastrado.")

    # ---------------- DADOS DE EXEMPLO ----------------
    def carregar_exemplos(self):
        """Cadastra alguns dados para testar o sistema rapidamente."""
        self.cadastrar_produto("Caderno", 15.00, 20)
        self.cadastrar_produto("Caneta", 3.50, 50)
        self.cadastrar_produto("Mochila", 89.90, 8)
        self.cadastrar_cliente("Maria Silva", "111.111.111-11")
        self.cadastrar_cliente("João Souza", "222.222.222-22")
        self.cadastrar_vendedor("Carlos")
        self.cadastrar_vendedor("Ana")


# ============================================================
# 4. FUNÇÕES DE ENTRADA (evitam que o programa quebre)
# ============================================================
def ler_texto(mensagem):
    """Lê um texto e não aceita vazio."""
    while True:
        valor = input(mensagem).strip()
        if valor:
            return valor
        print("Valor obrigatório.")


def ler_inteiro(mensagem):
    """Lê um número inteiro; repete a pergunta se o usuário digitar errado."""
    while True:
        try:
            return int(input(mensagem))
        except ValueError:
            print("Digite um número inteiro válido.")


def ler_decimal(mensagem):
    """Lê um número decimal; aceita vírgula (ex.: 12,50)."""
    while True:
        try:
            return float(input(mensagem).replace(",", "."))
        except ValueError:
            print("Digite um valor numérico válido.")


# ============================================================
# 5. MENU (interface com o usuário)
# ============================================================
def tela_nova_venda(pdv):
    """Fluxo completo de uma venda: escolher cliente/vendedor, itens e finalizar."""
    if not pdv.produtos or not pdv.clientes or not pdv.vendedores:
        print("Cadastre ao menos 1 produto, 1 cliente e 1 vendedor antes de vender.")
        return

    pdv.listar_clientes()
    cod_cliente = ler_inteiro("Código do cliente: ")
    pdv.listar_vendedores()
    cod_vendedor = ler_inteiro("Código do vendedor: ")

    try:
        venda = pdv.iniciar_venda(cod_cliente, cod_vendedor)
    except ValueError as erro:
        print(f"Erro: {erro}")
        return

    # Loop do "carrinho": continua até o usuário digitar 0
    while True:
        pdv.relatorio_estoque()
        cod_produto = ler_inteiro("\nCódigo do produto (0 para encerrar): ")
        if cod_produto == 0:
            break
        quantidade = ler_inteiro("Quantidade: ")
        try:
            pdv.adicionar_item(venda, cod_produto, quantidade)
            print(f"Item adicionado. Subtotal parcial: R$ {venda.subtotal:.2f}")
        except ValueError as erro:
            print(f"Erro: {erro}")

    try:
        pdv.finalizar_venda(venda)
    except ValueError as erro:
        print(f"Venda cancelada: {erro}")
        return

    texto, caminho = pdv.gerar_recibo(venda)
    print("\n" + texto)
    print(f"Recibo salvo em: {caminho}")
    print(f"Comissão do vendedor nesta venda: R$ {venda.comissao:.2f}")


def menu():
    pdv = PDV()

    # Loop principal: roda até o usuário escolher sair
    while True:
        print("\n========== PDV ==========")
        print("1 - Cadastrar produto")
        print("2 - Cadastrar cliente")
        print("3 - Cadastrar vendedor")
        print("4 - Nova venda")
        print("5 - Relatório de estoque")
        print("6 - Relatório de vendas")
        print("7 - Relatório de comissões")
        print("8 - Carregar dados de exemplo")
        print("0 - Sair")
        opcao = ler_inteiro("Escolha: ")

        try:
            if opcao == 1:
                nome = ler_texto("Nome do produto: ")
                preco = ler_decimal("Preço: ")
                estoque = ler_inteiro("Quantidade em estoque: ")
                if preco <= 0 or estoque < 0:
                    print("Preço deve ser positivo e estoque não pode ser negativo.")
                else:
                    p = pdv.cadastrar_produto(nome, preco, estoque)
                    print(f"Produto cadastrado com código {p.codigo}.")
            elif opcao == 2:
                nome = ler_texto("Nome do cliente: ")
                cpf = ler_texto("CPF: ")
                c = pdv.cadastrar_cliente(nome, cpf)
                print(f"Cliente cadastrado com código {c.codigo}.")
            elif opcao == 3:
                nome = ler_texto("Nome do vendedor: ")
                v = pdv.cadastrar_vendedor(nome)
                print(f"Vendedor cadastrado com código {v.codigo}.")
            elif opcao == 4:
                tela_nova_venda(pdv)
            elif opcao == 5:
                pdv.relatorio_estoque()
            elif opcao == 6:
                pdv.relatorio_vendas()
            elif opcao == 7:
                pdv.relatorio_comissoes()
            elif opcao == 8:
                pdv.carregar_exemplos()
                print("Dados de exemplo carregados.")
            elif opcao == 0:
                print("Encerrando o sistema. Até logo!")
                break
            else:
                print("Opção inválida.")
        except ValueError as erro:
            # Captura erros de regra de negócio lançados pelo PDV
            print(f"Erro: {erro}")


# Só executa o menu se o arquivo for rodado diretamente
# (e não quando importado por outro arquivo).
if __name__ == "__main__":
    menu()
