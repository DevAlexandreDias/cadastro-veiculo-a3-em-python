 Sistema PDV (Ponto de Venda) em Python

Um sistema de Ponto de Venda (PDV) desenvolvido em Python puro, utilizando Programação Orientada a Objetos (POO) e uma interface de linha de comando (CLI) robusta e segura contra erros de digitação.

 Funcionalidades

- Cadastros Completos:** Gerenciamento de Produtos, Clientes e Vendedores.
- Validação de Dados:** Prevenção contra duplicidade (ex: CPFs duplicados) e erros de tipo nas entradas do usuário.
- Carrinho de Compras Interativo: Adição de múltiplos itens por venda com validação em tempo real do estoque disponível.
- Controle Automático de Estoque: A baixa no estoque ocorre estritamente no momento da finalização da venda.
- Regras de Negócio Automatizadas:
  - Cálculo automático de impostos (25% sobre o subtotal).
  - Cálculo de comissão de vendedores (5% sobre o subtotal dos produtos).
  - Congelamento do preço unitário no item da venda, garantindo histórico preciso mesmo se o preço do produto mudar futuramente.
- Emissão de Documentos e Relatórios:
  - Geração automática de recibos formatados salvos na pasta `recibos/`.
  - Relatório detalhado de estoque com alertas visuais (`<< ESTOQUE BAIXO`).
  - Relatório financeiro de vendas e faturamento total.
  - Relatório de comissões acumuladas por vendedor.

 Tecnologias Utilizadas
- Python 3.x
- Módulos nativos utilizados:
  - `os` (para manipulação de diretórios e arquivos de recibos)
  - `datetime` (para carimbo de data e hora nas transações)


 Arquitetura do Sistema

O código está dividido em 5 camadas lógicas principais:
1 constantes: Centralização das regras de negócio (`ALIQUOTA_IMPOSTO`, `PERCENTUAL_COMISSAO`, `ESTOQUE_MINIMO`, etc.).
2. Classes de Dados: Entidades do mundo real (`Produto`, `Cliente`, `Vendedor`, `ItemVenda`, `Venda`).
3. Classe PDV: O "cérebro" do sistema, responsável por gerenciar os dicionários de cadastros, histórico de vendas e operações.
4.Funções de Entrada: Leituras seguras (`ler_texto`, `ler_inteiro`, `ler_decimal`) que evitam quebras no programa por entradas inválidas.
5. Menu / Interface: Loop principal em CLI com opções para interagir com o sistema.

 Como Executar o Projeto

1. Certifique-se de ter o Python 3.x instalado em sua máquina.
2. Baixe ou copie o código para um arquivo chamado `pdv.py`.
3. Abra o terminal (prompt de comando) na pasta onde o arquivo foi salvo.
4. Execute o comando:

bash
python pdv.py
