import argparse
import csv
import logging
import os
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import shutil
from time import sleep


CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH', '/home/rafaeljpd/Downloads/visibility/bin/chromedriver')
CHROME_DOWNLOAD_DIR = os.environ.get('CHROME_DOWNLOAD_DIR', '/home/rafaeljpd/Downloads/visibility/data/selenium')
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO')
HEADER_RESULT_FILE = '|'.join(['Source Title', 'Records', 'Year', 'ISSN', 'eISSN', 'Country', 'WoS-ISSN', 'WoS-Base-Country'])
PATTERN_YEAR = r'\d{4}'
WOS_CIT_ANALYSIS_NAMES = ['SO_SourceTitle_SourceTitle_en', 'SE_BookSeries_BookSeries_en']
WOS_MIN_WAIT_TIME = 1
WOS_MID_WAIT_TIME = 5
WOS_MAX_WAIT_TIME = 10
WOS_SEARCH_YEARS = ['PY=' + str(year) for year in range(1997, 2020)]


def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', default='collect')
    parser.add_argument('-i', '--indexes', default='SCI,SSCI,AHCI,ISTP,ISSHP,ESCI')
    parser.add_argument('-s', '--selected_index', default='AHCI')
    parser.add_argument('-r', '--result_types', default='Article,Review')
    parser.add_argument('-c', '--core_titles', default='')
    parser.add_argument('-t', '--source_titles', default='')
    parser.add_argument('-b', '--base_titles', default='')
    parser.add_argument('--start_line', type=int, default=0)

    params = parser.parse_args()

    return {'mode': params.mode,
            'indexes': params.indexes,
            'selected_index': params.selected_index,
            'result_types': params.result_types,
            'core_titles': params.core_titles,
            'source_titles': params.source_titles,
            'base_titles': params.base_titles,
            'start_line': params.start_line}


def fix_issn(issn):
    if len(issn) == 8:
        return issn[0:4] + '-' + issn[4:]
    return issn


def read_source_titles(path_source_titles):
    st = []

    files = [os.path.join(path_source_titles, f) for f in os.listdir(path_source_titles) if 'source' in f]

    for f in files:
        f_year = re.search(PATTERN_YEAR, f).group()

        with open(f, encoding='utf-8-sig') as fi:
            csv_reader = csv.DictReader(fi, delimiter='\t')

            for row in csv_reader:
                source_title = row['Source Titles']
                records = row['records']
                if records:
                    st.append((source_title, records, f_year))

    return st


def read_core_titles(path_core_titles):
    ct = {}

    with open(path_core_titles) as f:
        csv_reader = csv.DictReader(f, delimiter=',')

        for row in csv_reader:
            journal_title = row['Journal title']
            issn = row['ISSN']
            eissn = row['eISSN']

            if journal_title not in ct:
                ct[journal_title] = (issn, eissn)
            else:
                print('%s está repetido no arquivo core_titles' % journal_title)

    return ct


def read_base_titles(path_base_titles):
    title2issn = {}
    issn2country = {}

    with open(path_base_titles) as f:
        csv_reader = csv.DictReader(f, delimiter='|')

        for row in csv_reader:
            issns = [fix_issn(i) for i in row['ISSNS'].split('#')]
            titles = [t for t in row['TITLES'].split('#')]

            # Povoa dicionário título -> issn
            for t in titles:
                if t not in title2issn:
                    title2issn[t] = set()
                for i in issns:
                    title2issn[t].add(i)

            # Povoa dicionário issn -> país
            for ic in row['COUNTRIES'].split('#'):
                els = ic.split('-')
                if len(els) == 2:
                    i = els[0]
                    c = els[1]

                    fixed_issn = fix_issn(i)

                    if fixed_issn not in issn2country:
                        issn2country[fixed_issn] = set()

                    issn2country[fixed_issn].add(c)

    return title2issn, issn2country


def start_driver():
    if not os.path.exists(CHROME_DOWNLOAD_DIR):
        os.makedirs(CHROME_DOWNLOAD_DIR)

    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': CHROME_DOWNLOAD_DIR}
    chrome_options.add_experimental_option('prefs', prefs)

    return webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options)


def collect_citation_reports(wos_indexes, wos_result_types, wos_selected_index, results_dir):
    driver = start_driver()

    for sf in WOS_SEARCH_YEARS:
        # Abre página inicial
        driver.get('https://apps.webofknowledge.com/')
        sleep(WOS_MIN_WAIT_TIME)

        # Abre aba de busca avançada
        driver.find_element_by_link_text('Advanced Search').click()
        sleep(WOS_MID_WAIT_TIME)

        # Adiciona dados de pesquisa no campo de busca
        driver.find_element_by_class_name('Adv_formBoxesSearch').clear()
        driver.find_element_by_class_name('Adv_formBoxesSearch').send_keys(sf)

        # Seleciona tipo de resultado Article e Review
        for rt in wos_result_types:
            rti = driver.find_element_by_xpath("//select[@name='value(input3)']/option[text()='%s']" % rt)
            if not rti.is_selected():
                rti.click()

        # Expande menu de mais configurações
        driver.find_element_by_id('settings-arrow').click()
        sleep(WOS_MIN_WAIT_TIME)

        # Ativa índice de busca desejado
        for wi in wos_indexes:
            checkbox = driver.find_element_by_id(wi)
            if wi != wos_selected_index:
                if checkbox.is_selected():
                    checkbox.click()
            else:
                if not checkbox.is_selected():
                    checkbox.click()

        # Faz busca
        driver.find_element_by_id('search-button').click()
        sleep(WOS_MIN_WAIT_TIME)

        # Acessa página de resultados
        history_results = driver.find_element_by_class_name('historyResults')
        if history_results.text != '0':
            history_results.find_element_by_tag_name('a').click()
            sleep(WOS_MAX_WAIT_TIME * 2)

            # Acessa página de análise de resultados
            driver.find_element_by_class_name('create-cite-report').find_element_by_tag_name('a').click()
            sleep(WOS_MAX_WAIT_TIME)

            # Acessa página de Source Titles e Book Series Titles
            for ca in WOS_CIT_ANALYSIS_NAMES:
                driver.find_element_by_xpath("//button[@value='%s']" % ca).click()

                # Ativa campo para salvar todos os dados disponíveis
                driver.find_element_by_id('save_what_all_bottom').click()

                # Salva arquivo em disco
                driver.find_element_by_id('save').click()
                sleep(WOS_MIN_WAIT_TIME)

                # Renomeia arquivo
                year = re.search(PATTERN_YEAR, sf).group()
                cat = 'book' if 'book' in ca.lower() else 'source'

                filename = max([os.path.join(CHROME_DOWNLOAD_DIR, f) for f in os.listdir(CHROME_DOWNLOAD_DIR) if 'analyze' in f], key=os.path.getctime)
                shutil.move(filename, os.path.join(results_dir, '%s-%s.txt' % (cat, year)))


def enrich_issn_for_sources(source_titles, core_titles, base_titles):
    enriched_data = {}

    for s in source_titles:
        title = s[0]
        records = s[1]
        year = s[2]
        issn, eissn = core_titles.get(title, ('', ''))
        countries = ''

        ed_key = '|'.join([title, year])

        if not issn and not eissn:
            bissns = base_titles['title2issns'].get(title, set())
            if bissns:
                if len(bissns) == 1:
                    issn = list(bissns)[0]
                else:
                    issn = '#'.join(bissns)

        if issn:
            if '#' not in issn:
                countries = '#'.join(base_titles['issn2countries'].get(issn, []))
            else:
                countries = set()
                for i in issn.split('#'):
                    for iv in base_titles['issn2countries'].get(i, []):
                        countries.add(iv)
                countries = '#'.join(countries)

        enriched_data[ed_key] = [title, records, year, issn, eissn, countries]

    return enriched_data


def save(gold_data):
    with open('gold_data.csv', 'w') as f:
        f.write(HEADER_RESULT_FILE + '\n')
        for v in gold_data.values():
            f.write('|'.join(v) + '\n')


def get_source_titles_no_issn(enriched_data):
    st_no_issn = {}

    for v in enriched_data.values():
        source_title = v[0]
        year = v[2]
        issn = v[3]
        eissn = v[4]
        country = v[5]

        if country == '':
            if (not issn and not eissn) or '#' in issn:
                if source_title not in st_no_issn:
                    st_no_issn[source_title] = []
                st_no_issn[source_title].append(year)

    return st_no_issn


def collect_issn(enriched_data, wos_result_types, start_line):
    results = {}
    if not os.path.exists('source_issn_data.csv'):
        output = open('source_issn_data.csv', 'w')
    else:
        output = open('source_issn_data.csv', 'a')

    sts = get_source_titles_no_issn(enriched_data)
    logging.info('Há %d periódicos com título válido e sem ISSN definido' % len(sts))

    driver = start_driver()

    for index, k in enumerate(sorted(sts.keys())[start_line:]):
        logging.info('Coletando para %d de %d' % (index + 1 + start_line, len(sts)))

        try:
            # Abre página inicial
            driver.get('https://apps.webofknowledge.com/')
            sleep(WOS_MIN_WAIT_TIME)

            # Abre aba de busca avançada
            driver.find_element_by_link_text('Advanced Search').click()

            # Adiciona dados de pesquisa no campo de busca
            search_text = 'PY=' + sts[k][0] + ' AND SO=({0})'.format(k)
            driver.find_element_by_class_name('Adv_formBoxesSearch').clear()
            driver.find_element_by_class_name('Adv_formBoxesSearch').send_keys(search_text)

            # Seleciona tipo de resultado Article e Review
            for rt in wos_result_types:
                rti = driver.find_element_by_xpath("//select[@name='value(input3)']/option[text()='%s']" % rt)
                if not rti.is_selected():
                    rti.click()

            # Expande menu de mais configurações
            driver.find_element_by_id('settings-arrow').click()

            # Ativa índice de busca desejado
            for wi in wos_indexes:
                checkbox = driver.find_element_by_id(wi)
                if wi != wos_selected_index:
                    if checkbox.is_selected():
                        checkbox.click()
                else:
                    if not checkbox.is_selected():
                        checkbox.click()

            # Faz busca
            driver.find_element_by_id('search-button').click()
            sleep(WOS_MIN_WAIT_TIME)

            # Limpa história para evitar limite de 200 itens
            try:
                driver.find_element_by_id('deleteSets2')
                driver.find_element_by_id('deleteSets1').click()
                driver.find_element_by_id('deleteBtm').click()
            except NoSuchElementException:
                pass

            # Acessa página de resultados
            history_results = driver.find_element_by_class_name('historyResults')
            if history_results.text != '0':
                history_results.find_element_by_tag_name('a').click()
                sleep(WOS_MIN_WAIT_TIME)

                # Acessa página do primeiro resultado
                driver.find_element_by_id('RECORD_1').find_element_by_tag_name('a').click()
                sleep(WOS_MIN_WAIT_TIME)

                # Abre mais informações
                try:
                    driver.find_element_by_link_text('See more data fields').click()
                except NoSuchElementException:
                    pass

                # Procura ISSN
                for i in driver.find_elements_by_xpath("//p[@class='FR_field']"):
                    if 'ISSN' in i.text:
                        issn = i.text.split(': ')[-1]
                        if issn:
                            results[k] = issn
                            output.write('\t'.join([str(index + start_line), k, issn]) + '\n')
                            output.flush()
        except NoSuchElementException:
            logging.error('%s was not collected' % k)

    output.close()

    return results


def merge(enriched_data, issn_data, base_titles):
    for k, v in enriched_data.items():
        source_title, year = k.split('|')
        if source_title in issn_data:
            issn = issn_data[source_title]
            enriched_data[k].append(issn)

            if '#' not in issn and len(issn) == 9:
                countries = '#'.join(base_titles['issn2countries'].get(issn, []))
                if countries:
                    enriched_data[k].append(countries)
                else:
                    enriched_data[k].append('-')
        else:
            enriched_data[k].append('-')
            enriched_data[k].append('-')


if __name__ == '__main__':
    params = get_params()

    logging.basicConfig(level=LOGGING_LEVEL,
                        format='[%(asctime)s] %(levelname)s %(message)s',
                        datefmt='%d/%b/%Y %H:%M:%S')

    wos_result_types = [rt.title() for rt in params['result_types'].split(',')]
    wos_indexes = ['editionitem' + s.upper() for s in params['indexes'].split(',')]
    wos_selected_index = 'editionitem' + params['selected_index'].upper()

    result_wsi_path = os.path.join(CHROME_DOWNLOAD_DIR, wos_selected_index.replace('editionitem', '').lower())
    if not os.path.exists(result_wsi_path):
        os.makedirs(result_wsi_path)

    if params['mode'] == 'collect':
        collect_citation_reports(wos_indexes=wos_indexes, wos_result_types=wos_result_types, wos_selected_index=wos_selected_index, results_dir=result_wsi_path)

    if params['mode'] == 'issn':
        if params['source_titles']:
            logging.info('Carregando source titles...')
            source_titles = read_source_titles(params['source_titles'])

            logging.info('Carregando core titles...')
            core_titles = read_core_titles(params['core_titles'])

            logging.info('Carregando base titles...')
            t2i, i2c = read_base_titles(params['base_titles'])

            logging.info('Enriquecendo source titles...')
            base_titles = {'title2issns': t2i, 'issn2countries': i2c}
            enri_data = enrich_issn_for_sources(source_titles=source_titles, core_titles=core_titles, base_titles=base_titles)

            logging.info('Coletando ISSNs do site WoS...')
            issn_data = collect_issn(enriched_data=enri_data, wos_result_types=wos_result_types, start_line=params['start_line'])

            logging.info('Mesclando ISSNs em Source Titles...')
            merge(enri_data, issn_data, base_titles)

            logging.info('Salvando resultados...')
            save(enri_data)
