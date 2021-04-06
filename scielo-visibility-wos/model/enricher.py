class WosEnricher:
    def __init__(self, index):
        self.source_titles = []
        self.core_titles = {}
        self.base_titles = {}
        self.results = {}
        self.index = index

    def enrich_source_titles(self, wos_title_to_issn=None):
        for s in self.source_titles:
            title = s[0]
            records = s[1]
            year = s[2]
            issn, eissn = self.core_titles.get(title, ('', ''))
            countries = ''

            ed_key = '|'.join([title, year])

            if not issn and not eissn:
                bissns = self.base_titles['title2issns'].get(title, set())
                if bissns:
                    if len(bissns) == 1:
                        issn = list(bissns)[0]
                    else:
                        issn = '#'.join(bissns)

            if issn:
                if '#' not in issn:
                    countries = '#'.join(self.base_titles['issn2countries'].get(issn, []))
                else:
                    countries = set()
                    for i in issn.split('#'):
                        for iv in self.base_titles['issn2countries'].get(i, []):
                            countries.add(iv)
                    countries = '#'.join(countries)

            self.results[ed_key] = [title, records, year, issn, eissn, countries]

    def save_source_title_years(self):
        no_issn, multiple_issn = self.get_problematic_source_titles()
        data = {'no_issn': no_issn, 'multiple_issn': multiple_issn}

        for i in data:
            with open(i + '_' + self.index + '.csv', 'w') as f:
                for source_title in sorted(data[i]):
                    years = data[i][source_title]
                    f.write('\t'.join([source_title, '#'.join(years)]) + '\n')

    def get_problematic_source_titles(self):
        st_no_issn = {}
        st_multiple_issn = {}

        for v in self.results.values():
            source_title = v[0]
            year = v[2]
            issn = v[3]
            eissn = v[4]
            country = v[5]

            if country == '':
                if (not issn and not eissn) or '#' in issn:
                    self._update_dict(source_title, st_no_issn, year)

            if '#' in country:
                if '#' in issn:
                    self._update_dict(source_title, st_multiple_issn, year)

        return st_no_issn, st_multiple_issn

    def _update_dict(self, source_title, result_dict, st_year):
        if source_title not in result_dict:
            result_dict[source_title] = []
        result_dict[source_title].append(st_year)

    # def merge(self, issn_data, base_titles):
    #     for k, v in self.results.items():
    #         source_title, year = k.split('|')
    #
    #         if source_title in issn_data:
    #             issn = issn_data[source_title][0]
    #             self.results[k].append(issn)
    #
    #             if '#' not in issn and len(issn) == 9:
    #                 countries = '#'.join(base_titles['issn2countries'].get(issn, []))
    #                 if countries:
    #                     self.results[k].append(countries)
    #                 else:
    #                     self.results[k].append('-')
    #         else:
    #             self.results[k].append('-')
    #             self.results[k].append('-')

    # def save(self, path):
    #     with open(path, 'w') as f:
    #         for v in self.results.values():
    #             f.write('|'.join(v) + '\n')
