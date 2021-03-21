import argparse

from util import read_source_title_years
from model.robot import WosRobot


def get_params():
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--mode', default='citation_report')
    parser.add_argument('-i', '--wos_indexes', default='SCI,SSCI,AHCI,ISTP,ISSHP,ESCI')
    parser.add_argument('-s', '--wos_selected_index', default='AHCI')
    parser.add_argument('-r', '--wos_result_types', default='Article,Review')
    parser.add_argument('-y', '--source_title_years', required=True)

    params = parser.parse_args()

    return {'mode': params.mode,
            'wos_indexes': [i.upper() for i in params.wos_indexes.split(',')],
            'wos_selected_index': params.wos_selected_index.upper(),
            'wos_result_types': [i.title() for i in params.wos_result_types.split(',')],
            'source_title_years': params.source_title_years}


if __name__ == '__main__':
    params = get_params()

    robot = WosRobot()

    robot.wos_indexes = params['wos_indexes']
    robot.wos_selected_index = params['wos_selected_index']
    robot.wos_result_types = params['wos_result_types']

    robot.initialize(mode=params['mode'])

    if params['mode'] == 'citation_report':
        robot.collect_citation_reports()

    if params['mode'] == 'issn':
        source_title_years = read_source_title_years(params['source_title_years'])
        output_file_name = params['source_title_years'].replace('.csv', '.gathered.csv')
        robot.collect_issn(source_title_years, output_file_name)
