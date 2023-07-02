# Itaú Scraper

Scraper para obter dados do banco [Itaú](itau.com.br):  **extrato, cartões de crédito e investimentos**.

## Motivação
Como a maioria dos bancos, o Itaú não disponibiliza APIs para consultas de dados bancários a seus clientes. Antigas implementações disponíveis online, como [bankscraper](https://github.com/kamushadenes/bankscraper), estão em sua maioria defasadas. Desta forma foi necessário a criação deste repositório para interagir com o banco Itaú, a fim de obter os dados de contas corrente.

## Funcionamento
É necessário obter as credenciais para interagir diretamente com as APIs internas do [banco Itaú](itau.com.br), para isso um navegador é utilizado através do [playwright](https://playwright.dev/python/) para realizar o **login**. Após o login, de posse das informações/credenciais, as consultas desejadas são feitas diretamente via **requisições HTTP**.

_Nota: As credenciais tem validade de algumas horas, após este período é necessário atualizar os tokens utilizados._


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
  atualizar-credenciais  Atualiza credenciais armazenadas
  cartoes                Lista os cartões de crédito com suas faturas
  extrato                Extrato com transações dos últimos 90 dias
  fiis                   Saldo de cada FII investido
  investimentos          Saldo investido consolidado por categoria
  login                  Inicia a conexão com o banco Itaú
  saldo                  Saldo disponível em conta
```

