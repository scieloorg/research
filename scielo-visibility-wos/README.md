# SciELO Visibility WoS

Este repositório contém scripts que automatizam processos relacionados à coleta e ao tratamento de dados de periódicos citados na WoS.


## Instalação
É preciso criar um ambiente virtual `python`, versão 3, e instalar os requerimentos que constam no arquivo `requirements.txt`. Uma forma de fazer isso é:
```shell
virtualenv -p python3 .venv
source .venv/bin/activate.bin
pip install -r requirements.txt
```

É preciso obter o driver de navegação Chrome específico para a biblioteca `selenium`, utilizada nesta aplicação para automatização de alguns processos. Os passos para fazer isso são:

1. Baixar o navegador-driver deste [link](https://chromedriver.storage.googleapis.com/index.html?path=89.0.4389.23/);
2. Extrair o navegador-driver em uma pasta;
3. Configurara variável de ambiente CHROME_DRIVER_PATH com o caminho do navegador-driver, o que pode ser feito por meio da seguinte instrução, em um `terminal` de ambiente `Linux`:
```shell
export CHROME_DRIVER_PATH=/home/user/data/driver/chromedriver
```

__Variáveis de ambiente__

Sugere-se definir também a variável de ambiente CHROME_DOWNLOAD_DIR. Consulte a tabela a seguir para conhecer todas as variáveis de ambiente utilizadas pela aplicação.

| Variável | Descrição |
|---|---|
| CHROME_DRIVER_PATH | Caminho completo do navegador-driver Chrome |
| CHROME_DOWNLOAD_DIR | Caminho completo do diretório aonde os dados serão salvos |


__Parâmetros de linha de comando__

| Parâmetro | Descrição | Padrão | Como usar |
|-----------|-----------|--------|-----------|
| WOS_INDEXES | Um lista de siglas que representam os core-indexes WoS | SCI,SSCI,AHCI,ISTP,ISSHP,ESCI | `-i SCI,SSCI,AHCI,ISTP,ISSHP,ESCI` 
| WOS_RESULT_TYPES | Uma lista dos tipos de resultados a serem filtrados | Article,Review | `-r Article,Review` |
| WOS_SELECTED_INDEX | O índice a ser tratado (uma das siglas indicadas em WOS_INDEXES) | AHCI | `-s AHCI` |
| GATHER_MODE | Modo de uso da aplicação (e.g. collect ou issn) | collect | `-m collect `  

## Uso

### wos_gather

Coleta de forma automática relatórios de periódicos citados. Formas de usar:

```shell
# Coletar dados de periódicos citados para 
#   core AHCI
#   considerando tipos de resultados Article e Review
python wos_gather.py -m collect -i AHCI -r Article,Review

# Como os parâmetros possuem por padrão os valores indicados acima, 
#    pode-se executar o script sem a indicação desses valores
python wos_gather.py

# Coletar dados de periódicos citados para 
#   core SSCI
#   considerando tipos de resultados Article e Review
python wos_gather.py -m collect -i SSCI -r Article,Review
```


### enrich_data

```shell
# Enriquece os dados de periódicos citados com informações de ISSN e país
python enrich_data.py
```
