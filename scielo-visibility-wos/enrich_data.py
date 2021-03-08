import argparse
import csv
import logging
import os
import re

from string_processor import preprocess_journal_title


PATTERN_YEAR = r'\d{4}'
WOS_MASTER_JOURNAL_FIELDS = ['Journal title', 'ISSN', 'eISSN']
MIN_CHARS_LENGTH = 6
MIN_WORDS_COUNT = 2
WOS_SEARCHED_RESULTS_FIELDS = ['Source title', 'N', 'Percent', 'Year']


def _fix_issn(issn):
    if len(issn) == 8:
        return issn[:4] + '-' + issn[4:]
    return issn


def _find_data_by_title(title, issn_maps):
    preprocessed_title = preprocess_journal_title(title)
    r_issnls = issn_maps['title_to_issnl'].get(preprocessed_title, [])

    r_countries = []

    if r_issnls:
        for ri in r_issnls:
            tmp_countries = issn_maps['issn_to_country'].get(ri, ['-1'])
            r_countries.extend(tmp_countries)

    return '#'.join(sorted(set(r_countries))), '#'.join(sorted(set(r_issnls)))


def load_issn_maps(path):
    title_to_issnl = {}
    issn_to_issnl = {}
    issn_to_country = {}

    csv_reader = csv.DictReader(open(path), delimiter='|')
    for i in csv_reader:
        issnl = _fix_issn(i['ISSNL'])
        issns = [_fix_issn(k) for k in i['ISSNS'].split('#')]
        titles = i['TITLES'].split('#')

        # Extrai informação de ISSN e COUNTRY
        issn_country = []
        for ic in i['COUNTRIES'].split('#'):
            els = ic.split('-')
            if len(els) == 2:
                issn = els[0][:4] + '-' + els[0][4:]
                country = els[1]
                issn_country.append((issn, country))

        # Cria dicionário TITLE -> ISSNL
        for t in titles:
            if t not in title_to_issnl:
                title_to_issnl[t] = []
            title_to_issnl[t].append(issnl)

        # Cria dicionário ISSN -> ISSNL
        for i in issns:
            if i not in issn_to_issnl:
                issn_to_issnl[i] = []
            issn_to_issnl[i].append(issnl)

        # Cria dicionário ISSN -> COUNTRY
        for i, c in issn_country:
            if i not in issn_to_country:
                issn_to_country[i] = []
            issn_to_country[i].append(c)

    return {'issn_to_issnl': issn_to_issnl, 'issn_to_country': issn_to_country, 'title_to_issnl': title_to_issnl}


def load_wos_searched_data(dir_searched_results_files):
    files = sorted([os.path.join(dir_searched_results_files, f) for f in os.listdir(dir_searched_results_files)])

    data = []

    for f in files:
        year = re.search(PATTERN_YEAR, f).group()

        for row in open(f).readlines()[1:]:
            row_els = row.strip().upper().split('\t') + [year]
            if len(row_els) == len(WOS_SEARCHED_RESULTS_FIELDS):
                data.append(row_els)

    return data


def load_wos_master_journal_list(path):
    title_to_issns = {}

    with open(path) as f:
        csv_reader = csv.DictReader(f, delimiter=',')

        for row in csv_reader:
            row_parsed_data = []

            issn = row.get('ISSN')
            eissn = row.get('eISSN')
            title = row.get('Journal title')

            if title not in title_to_issns:
                title_to_issns[title] = (issn, eissn)
            else:
                logging.warning('%s já está na lista e vale %s' % (title, title_to_issns[title]))

            for field in WOS_MASTER_JOURNAL_FIELDS:
                row_parsed_data.append(row.get(field, ''))

    return title_to_issns


def enrich(searched_data, issn_maps, master_journal_list):
    enriched_data = [WOS_SEARCHED_RESULTS_FIELDS + ['ISSN', 'eISSN', 'Country', 'N-Country']]

    for row in searched_data:
        # Usa dados da Master Journal List para tentar encontrar país e issns
        r_title = row[0]
        r_issn, r_eissn = master_journal_list.get(r_title, ('', ''))

        r_issn_country = issn_maps['issn_to_country'].get(r_issn, [])
        r_eissn_country = issn_maps['issn_to_country'].get(r_eissn, [])
        r_country = '#'.join(sorted(set(r_issn_country + r_eissn_country)))

        if not r_country:
            r_country, r_issnl = _find_data_by_title(r_title, issn_maps)

            # Usa issnls de issn_maps quando issn e eissn não forem identificados na Master Journal List
            if not r_issn and not r_eissn:
                r_issn = r_issnl

        if '#' not in r_country:
            if r_country == '':
                r_country_n = '0'
            else:
                r_country_n = '1'
        else:
            r_country_n = len(r_country.split('#'))

        enriched_data.append(row + [r_issn, r_eissn, r_country, r_country_n])

    return enriched_data


def save_data(data, path):
    with open(path, 'w') as f:
        for i in data:
            f.write('|'.join([str(vi) for vi in i]) + '\n')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d',
        '--issn_maps',
        required=True,
        help='Um dicionário, legível por pickle, de ISSNs, títulos de periódicos e países'
    )

    parser.add_argument(
        '-w',
        '--wos_mjl',
        required=True,
        help='Arquivo em formato CSV que contém dados de Web of Science Master Journal List'
    )

    parser.add_argument(
        '-s',
        '--wos_searched_data_dir',
        required=True,
        help='Diretório contendo resultados de busca na Web of Science. Usar um arquivo por ano, no formato CSV, '
             'em que cada linha representa Source Title, Records, Percent'
    )

    params = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s %(message)s',
                        datefmt='%d/%b/%Y %H:%M:%S')

    logging.info('Carregando dados de dicionário ISSN, títulos e países...')
    issn_mapper = load_issn_maps(params.issn_maps)

    logging.info('Lendo WoS Master Journal List...')
    mlj = load_wos_master_journal_list(params.wos_mjl)

    logging.info('Lendo resultados de busca WoS...')
    search_results = load_wos_searched_data(params.wos_searched_data_dir)

    logging.info('Enriquecendo dados de busca WoS...')
    enriched_results = enrich(search_results, issn_mapper, mlj)

    logging.info('Salvando dados enriquecidos...')
    save_data(enriched_results, 'enriched_results.tsv')


if __name__ == '__main__':
    main()
