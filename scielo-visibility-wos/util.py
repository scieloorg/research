import csv
import re
import os


HEADER_SOURCE_TITLE_ISSN = ['Id', 'Source Title', 'ISSN']
PATTERN_YEAR = r'\d{4}'


def fix_issn(issn):
    if len(issn) == 8:
        return issn[0:4] + '-' + issn[4:]
    return issn


def read_wos_issns(path_wos_issns):
    title_to_issns = {}

    with open(path_wos_issns) as f:
        csv_reader = csv.DictReader(f, fieldnames=['id', 'source_title', 'issn'], delimiter='\t')
        for row in csv_reader:
            source_title = row['source_title']
            issn = row['issn']

            if source_title not in title_to_issns:
                title_to_issns[source_title] = []
            title_to_issns[source_title].append(issn)

    return title_to_issns


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


def read_source_title_years(path_source_title_years):
    results = {}

    with open(path_source_title_years) as f:
        csv_reader = csv.DictReader(f, fieldnames=['Source Title', 'Years'], delimiter='\t')
        for row in csv_reader:
            source_title = row.get('Source Title')
            years = row.get('Years').split('#')

            results[source_title] = years

    return results


def save_wos_issns(source_title_issns, wos_selected_index, results_directory):
    output = os.path.join(results_directory, wos_selected_index + '_source_title_issn.csv')

    with open(output, 'a') as f:
        for st, issns in source_title_issns.items():
            for i in issns:
                f.write('\t'.join([st, i]) + '\n')


def read_wos_gathered_issns(path_gathered_file):
    title_to_issn = {}

    with open(path_gathered_file) as f:
        csv_reader = csv.DictReader(f, fieldnames=['id', 'title', 'issn'], delimiter='\t')
        for row in csv_reader:
            title = row['title']
            issn = row['issn']

            if title not in title_to_issn:
                title_to_issn[title] = []

            if issn not in title_to_issn[title]:
                title_to_issn[title].append(issn)

    return title_to_issn
