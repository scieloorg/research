import logging
import os
import shutil
import re

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from util import PATTERN_YEAR


CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH', os.path.join(os.getcwd(), 'chromedriver'))
CHROME_DOWNLOAD_DIR = os.environ.get('CHROME_DOWNLOAD_DIR', os.getcwd())
GENERAL_RESULTS_DIR = os.environ.get('GENERAL_RESULTS_DIR', os.getcwd())
WOS_CIT_ANALYSIS_NAMES = ['SO_SourceTitle_SourceTitle_en', 'SE_BookSeries_BookSeries_en']
WOS_INTERACTION_ERROR = -1
WOS_INTERACTION_SUCCESS = 1

logging.basicConfig(level=os.environ.get('LOGGING_LEVEL', 'INFO'),
                    format='[%(asctime)s] %(levelname)s %(message)s',
                    datefmt='%d/%b/%Y %H:%M:%S')


class WosRobot:
    def __init__(self):
        self.download_directory = CHROME_DOWNLOAD_DIR
        self.driver = None
        self.driver_path = CHROME_DRIVER_PATH
        self.output = ''
        self.results_directory = ''
        self.wos_indexes = ['SCI', 'SSCI', 'AHCI', 'ISTP', 'ISSHP', 'ESCI']
        self.wos_result_types = ['Article', 'Review']
        self.wos_search_years = range(1997, 2020)
        self.wos_selected_index = 'AHCI'
        self.wos_min_wait_time = 0.30
        self.wos_med_wait_time = 0.70
        self.wos_max_wait_time = 1.50

    def initialize(self, mode):
        if mode == 'citation_report':
            self.results_directory = os.path.join(self.download_directory, self.wos_selected_index.lower())
            if not os.path.exists(self.results_directory):
                os.makedirs(self.results_directory)

        self.wos_indexes = ['editionitem' + s.upper() for s in self.wos_indexes]
        self.wos_selected_index = 'editionitem' + self.wos_selected_index.upper()

    def create_driver(self):
        if not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)

        chrome_options = webdriver.ChromeOptions()
        prefs = {'download.default_directory': self.download_directory}
        chrome_options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(executable_path=self.driver_path, chrome_options=chrome_options)

    def collect_issn(self, source_title_years, output_filename):
        fullpath_output = os.path.join(GENERAL_RESULTS_DIR, output_filename)

        last_line = self._detect_last_saved_line(fullpath_output)
        if last_line > 0:
            last_line += 1
            logging.info('Continuing from line %d' % last_line)

        self.output = open(fullpath_output, 'a')
        self.create_driver()

        for c, source_title in enumerate(sorted(source_title_years.keys())[last_line:]):
            year = source_title_years[source_title][0]
            try:
                logging.info('(%d, %s) collecting' % (c + last_line, source_title))

                self._open_advanced_search()

                search_text = 'PY=' + year + ' AND SO=({0})'.format(source_title)
                self._set_search_text(search_text)

                self._set_result_types()
                self._set_indexes()
                self._search()
                self._clean_history()

                if self._open_result() == WOS_INTERACTION_SUCCESS:
                    issns = self._extract_issns()

                    for i in issns:
                        logging.info('Saving (%d, %s, %s)' % (c + last_line, source_title, i))
                        self._save_issn_data(c + last_line, source_title, i)
                else:
                    logging.info('Not found (%d, %s)' % (c + last_line, source_title))

            except NoSuchElementException:
                logging.error('Not collected (%d, %s)' % (c + last_line, source_title))

        self.output.close()

    def collect_citation_reports(self):
        self.create_driver()

        for sf in self.wos_search_years:
            self._open_advanced_search()
            self._set_search_text(sf)
            self._set_result_types()
            self._set_indexes()
            self._search()

            if self._open_result() == WOS_INTERACTION_SUCCESS:
                self.driver.find_element_by_class_name('create-cite-report').find_element_by_tag_name('a').click()
                sleep(self.wos_max_wait_time)

                for ca in WOS_CIT_ANALYSIS_NAMES:
                    self._save_cit_report(ca, sf)

    def _clean_history(self):
        try:
            self.driver.find_element_by_id('deleteSets2')
            self.driver.find_element_by_id('deleteSets1').click()
            self.driver.find_element_by_id('deleteBtm').click()
        except NoSuchElementException:
            pass

    def _detect_last_saved_line(self, fullpath_output):
        if os.path.exists(fullpath_output):
            with open(fullpath_output) as f:
                try:
                    return int(f.readlines()[-1].split('\t')[0])
                except ValueError:
                    pass
                except IndexError:
                    pass
        return 0

    def _extract_issns(self):
        st_results = []

        self.driver.find_element_by_id('RECORD_1').find_element_by_tag_name('a').click()
        sleep(self.wos_min_wait_time)

        try:
            self.driver.find_element_by_link_text('See more data fields').click()
        except NoSuchElementException:
            pass

        for i in self.driver.find_elements_by_xpath("//p[@class='FR_field']"):
            if 'ISSN' in i.text:
                issn = i.text.split(': ')[-1]
                if issn:
                    st_results.append(issn)

        return st_results

    def _open_advanced_search(self):
        self.driver.get('https://apps.webofknowledge.com/')
        sleep(self.wos_min_wait_time)
        self.driver.find_element_by_link_text('Advanced Search').click()

    def _open_result(self):
        history_results = self.driver.find_element_by_class_name('historyResults')
        if history_results.text != '0':
            history_results.find_element_by_tag_name('a').click()
            sleep(self.wos_min_wait_time)
            return WOS_INTERACTION_SUCCESS
        return WOS_INTERACTION_ERROR

    def _save_cit_report(self, ca, sf):
        self.driver.find_element_by_xpath("//button[@value='%s']" % ca).click()
        self.driver.find_element_by_id('save_what_all_bottom').click()
        self.driver.find_element_by_id('save').click()
        sleep(self.wos_min_wait_time)

        year = re.search(PATTERN_YEAR, sf).group()
        cat = 'book' if 'book' in ca.lower() else 'source'

        filename = max([os.path.join(self.download_directory, f) for f in os.listdir(self.download_directory) if 'analyze' in f], key=os.path.getctime)
        shutil.move(filename, os.path.join(self.results_directory, '%s-%s.txt' % (cat, year)))

    def _save_issn_data(self, line_number, source_title, issn):
        self.output.write('\t'.join([str(line_number), source_title, issn]) + '\n')
        self.output.flush()

    def _search(self):
        self.driver.find_element_by_id('search-button').click()
        sleep(self.wos_med_wait_time)

    def _set_search_text(self, text):
        self.driver.find_element_by_class_name('Adv_formBoxesSearch').clear()
        self.driver.find_element_by_class_name('Adv_formBoxesSearch').send_keys(text)

    def _set_result_types(self):
        for rt in self.wos_result_types:
            rti = self.driver.find_element_by_xpath("//select[@name='value(input3)']/option[text()='%s']" % rt)
            if not rti.is_selected():
                rti.click()

    def _set_indexes(self):
        self.driver.find_element_by_id('settings-arrow').click()

        for wi in self.wos_indexes:
            checkbox = self.driver.find_element_by_id(wi)
            if wi != self.wos_selected_index:
                if checkbox.is_selected():
                    checkbox.click()
            else:
                if not checkbox.is_selected():
                    checkbox.click()
