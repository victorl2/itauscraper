# Itaú Scraper

Scraper para obter dados do banco [Itaú](itau.com.br):  **extrato, cartões de crédito e investimentos**.

## Motivação
Como a maioria dos bancos, o Itaú não disponibiliza APIs para consultas de dados bancários a seus clientes. Antigas implementações disponíveis online, como [bankscraper](https://github.com/kamushadenes/bankscraper), estão em sua maioria defasadas. Desta forma foi necessário a criação deste repositório para interagir com o banco Itaú, a fim de obter os dados desejados.

## Funcionamento
Com o objetivo de obter as credenciais necessárias, um navegador é utilizado através com [playwright](https://playwright.dev/python/) para realizar o **login** no [banco Itaú](itau.com.br). Após o login, de posse das informações/credenciais necessárias, é possível realizar as consultas desejadas diretamente via **requisições HTTP**.


## Instalação
É necessário possuir [Python 3.9.6](https://www.python.org/downloads/) (ou superior) instalado.

Adicione as dependências do projeto 
```bash
pip install -r requirements.txt
```

## Utilização
Entre na pasta **itauscraper** e execute o arquivo **itau.py** com o comando desejado.
```bash
Usage: itau.py [OPTIONS] COMMAND [ARGS]...

  Scraper para obter informações de contas (pessoa física) no banco Itaú

Options:
  --help  Show this message and exit.

Commands:
  cartoes        Lista os cartões de crédito com suas faturas abertas
  extrato        Extrato com transações dos últimos 90 dias
  investimentos  Saldo investido consolidado por categoria
  login          Inicia a conexão com o banco Itaú
  saldo          Saldo disponível em conta
```

