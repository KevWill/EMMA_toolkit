import pandas as pd

def get_place(place_in_bio, geonames):
    def try_geoname(place):
        try:
            place_geoname = geonames[geonames['name'] == place]
            if len(place_geoname) > 1:
                highest_pop = place_geoname['pop'].idxmax()
                place_geoname = place_geoname.loc[highest_pop]
            else:
                place_geoname = place_geoname.iloc[0]
            return place_geoname
        except IndexError:
            return pd.Series()
    place_geoname = try_geoname(place_in_bio)
    if place_geoname.empty:
        return None
    name = place_geoname['name']
    adm1 = place_geoname['ADM1']
    adm2 = geonames.loc[int(place_geoname['ADM2'])]['name'] if pd.notnull(place_geoname['ADM2']) else ''
    adm3 = geonames.loc[int(place_geoname['ADM3'])]['name'] if pd.notnull(place_geoname['ADM3']) else ''
    adm4 = geonames.loc[int(place_geoname['ADM4'])]['name'] if pd.notnull(place_geoname['ADM4']) else ''
    return {
        'name': name,
        'adm1': adm1,
        'adm2': adm2,
        'adm3': adm3,
        'adm4': adm4
    }