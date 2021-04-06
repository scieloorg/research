import argparse
import logging
import os

from model.enricher import WosEnricher
from util import read_source_titles, read_core_titles, read_base_titles


logging.basicConfig(level=os.environ.get('LOGGING_LEVEL', 'INFO'),
                    format='[%(asctime)s] %(levelname)s %(message)s',
                    datefmt='%d/%b/%Y %H:%M:%S')


def get_params():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--core_titles', required=True)
    parser.add_argument('-t', '--source_titles', required=True)
    parser.add_argument('-b', '--base_titles', required=True)
    parser.add_argument('-i', '--index', required=True)

    params = parser.parse_args()

    return {'core_titles': params.core_titles,
            'source_titles': params.source_titles,
            'base_titles': params.base_titles,
            'index': params.index}


if __name__ == '__main__':
    params = get_params()

    enricher = WosEnricher(params['index'])

    logging.info('Carregando dados...')
    enricher.source_titles = read_source_titles(params['source_titles'])
    enricher.core_titles = read_core_titles(params['core_titles'])
    t2i, i2c = read_base_titles(params['base_titles'])
    enricher.base_titles = {'title2issns': t2i, 'issn2countries': i2c}

    logging.info('Enriquecendo dados...')
    enricher.enrich_source_titles()

    logging.info('Salvando dados...')
    enricher.save_problematic_sources_titles_years()
