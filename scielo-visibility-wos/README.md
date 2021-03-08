```
Uso: enrich_data.py [-h] -d ISSN_MAPS -w WOS_MJL -s WOS_SEARCHED_DATA_DIR

Parâmetros
-h, --help
    Mostra esse texto de ajuda
    
-d ISSN_MAPS, --issn_maps ISSN_MAPS
    Um dicionário, legível por pickle, de ISSNs, títulos de periódicos e países
    
-w WOS_MJL, --wos_mjl WOS_MJL
    Arquivo em formato CSV que contém dados de Web of Science Master Journal List
    
-s WOS_SEARCHED_DATA_DIR, --wos_searched_data_dir WOS_SEARCHED_DATA_DIR
    Diretório contendo resultados de busca na Web of Science 
    Usar um arquivo por ano, no formato CSV
    Cada linha deve representar Source Title, Records, Percent
```