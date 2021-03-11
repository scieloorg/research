import argparse
import os
import re
import shutil
from time import sleep

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH', '/home/rafaeljpd/Downloads/visibility/bin/chromedriver')
CHROME_DOWNLOAD_DIR = os.environ.get('CHROME_DOWNLOAD_DIR', '/home/rafaeljpd/Downloads/visibility/data/selenium')
PATTERN_YEAR = r'\d{4}'
WOS_CIT_ANALYSIS_NAMES = ['SO_SourceTitle_SourceTitle_en', 'SE_BookSeries_BookSeries_en']
WOS_SEARCH_YEARS = ['PY=' + str(year) for year in range(1997, 2020)]


# def detail(text):
#     detailed_query = 'AND SO=(%s))' % text
#     return detailed_query


def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', default='collect')
    parser.add_argument('-i', '--indexes', default='SCI,SSCI,AHCI,ISTP,ISSHP,ESCI')
    parser.add_argument('-s', '--selected_index', default='AHCI')
    parser.add_argument('-r', '--result_types', default='Article,Review')

    params = parser.parse_args()

    return {'mode': params.mode,
            'indexes': params.indexes,
            'selected_index': params.selected_index,
            'result_types': params.result_types}


def collect_citation_reports(wos_indexes, wos_result_types, wos_selected_index, results_dir):
    # Inicializa navegador
    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': CHROME_DOWNLOAD_DIR}
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options)

    if not os.path.exists(CHROME_DOWNLOAD_DIR):
        os.makedirs(CHROME_DOWNLOAD_DIR)

    for sf in WOS_SEARCH_YEARS:
        # Abre página inicial
        driver.get('https://apps.webofknowledge.com/')
        sleep(3)

        # Abre aba de busca avançada
        driver.find_element_by_link_text('Advanced Search').click()
        sleep(3)

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
        sleep(3)

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
        sleep(3)

        # Acessa página de resultados
        driver.find_element_by_class_name('historyResults').find_element_by_tag_name('a').click()
        sleep(3)

        # Acessa página de análise de resultados
        driver.find_element_by_class_name('create-cite-report').find_element_by_tag_name('a').click()
        sleep(3)

        # Acessa página de Source Titles e Book Series Titles
        for ca in WOS_CIT_ANALYSIS_NAMES:
            driver.find_element_by_xpath("//button[@value='%s']" % ca).click()

            # Ativa campo para salvar todos os dados disponíveis
            driver.find_element_by_id('save_what_all_bottom').click()

            # Salva arquivo em disco
            driver.find_element_by_id('save').click()
            sleep(5)

            # Renomeia arquivo
            year = re.search(PATTERN_YEAR, sf).group()
            cat = 'book' if 'book' in ca.lower() else 'source'

            filename = max([os.path.join(CHROME_DOWNLOAD_DIR, f) for f in os.listdir(CHROME_DOWNLOAD_DIR) if 'analyze' in f], key=os.path.getctime)
            shutil.move(filename, os.path.join(results_dir, '%s-%s.txt' % (cat, year)))


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
