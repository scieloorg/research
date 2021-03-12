import argparse
import csv
import os
import re
import shutil

from selenium import webdriver
from time import sleep


CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH', '/home/rafaeljpd/Downloads/visibility/bin/chromedriver')
CHROME_DOWNLOAD_DIR = os.environ.get('CHROME_DOWNLOAD_DIR', '/home/rafaeljpd/Downloads/visibility/data/selenium')
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
    parser.add_argument('-t', '--source_titles', default='')

    params = parser.parse_args()

    return {'mode': params.mode,
            'indexes': params.indexes,
            'selected_index': params.selected_index,
            'result_types': params.result_types,
            'source_titles': params.source_titles}


def read_source_titles(path_source_titles):
    st = set()

    with open(path_source_titles) as f:
        csv_reader = csv.DictReader(f, delimiter='\t')
        for row in csv_reader:
            st.add(row['Source'])

    return st


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


def collect_issn_for_sources(source_titles):
    driver = start_driver()
    # ToDo: implementar obtenção de ISSN a partir de query baseada em SO=(st)


if __name__ == '__main__':
    params = get_params()

    wm = params['mode']
    wis = ['editionitem' + s.upper() for s in params['indexes'].split(',')]
    wrt = [rt.title() for rt in params['result_types'].split(',')]
    wsi = 'editionitem' + params['selected_index'].upper()

    result_wsi_path = os.path.join(CHROME_DOWNLOAD_DIR, wsi.replace('editionitem', '').lower())
    if not os.path.exists(result_wsi_path):
        os.makedirs(result_wsi_path)

    if wm == 'collect':
        collect_citation_reports(wos_indexes=wis, wos_result_types=wrt, wos_selected_index=wsi, results_dir=result_wsi_path)

    if wm == 'issn':
        if params['source_titles']:
            st = read_source_titles(params['source_titles'])
            collect_issn_for_sources(source_titles=st)
