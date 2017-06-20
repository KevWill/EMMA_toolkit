def parse_geonames_file(input):
    def get_feature_codes(code, admin_level):
        if not code:
            return ''
        row = geonames[(geonames[admin_level] == code) & (geonames['feature_code'] == admin_level)]
        if len(row) == 0:
            return ''
        name = row.index.tolist()[0]
        return name

    geonames = {}
    with open(input, encoding='utf-8') as f:
        entries = f.read().split('\n')
        for entry in entries:
            split_entry = entry.split('\t')
            if len(split_entry) == 1:
                continue
            id = split_entry[0]
            name = split_entry[1]
            alternate_names = split_entry[3].split(',')
            lat = split_entry[4]
            long = split_entry[5]
            feature_class = split_entry[6]
            feature_code = split_entry[7]
            adm1 = split_entry[10]
            adm2 = split_entry[11]
            adm3 = split_entry[12]
            adm4 = split_entry[13]
            pop = split_entry[14]
            geonames[id] = {
                'name': name,
                'alternate_names': alternate_names,
                'lat': lat,
                'long': long,
                'feature_class': feature_class,
                'feature_code': feature_code,
                'ADM1': adm1,
                'ADM2': adm2,
                'ADM3': adm3,
                'ADM4': adm4,
                'pop': pop
            }
        geonames = pd.DataFrame.from_dict(data = geonames, orient = 'index')
        geonames['ADM2'] = geonames['ADM2'].apply(lambda x: get_feature_codes(x, 'ADM2'))
        geonames['ADM3'] = geonames['ADM3'].apply(lambda x: get_feature_codes(x, 'ADM3'))
        geonames['ADM4'] = geonames['ADM4'].apply(lambda x: get_feature_codes(x, 'ADM4'))
        return geonames