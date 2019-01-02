# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""Parse a BLS series_id"""

class LauSeriesId(object):
    """Series Id for Local Area Unemployment series"""

    measure_codes = {
        '03': 'unemployment rate',
        '04': 'unemployment',
        '05': 'employment',
        '06': 'labor_force'
    }

    # These are type codes that are in the la.area_type file
    area_types = {
        'A': 'Statewide',
        'B': 'Metropolitan areas',
        'C': 'Metropolitan divisions',
        'D': 'Micropolitan areas',
        'E': 'Combined areas',
        'F': 'Counties and equivalents',
        'G': 'Cities and towns above 25,000 population',
        'H': 'Cities and towns below 25,000 population in New England',
        'I': 'Parts of cities that cross county boundaries',
        'J': 'Multi-entity small labor market areas',
        'K': 'Intrastate parts of interstate areas',
        'L': 'Balance of state areas',
        'M': 'Census regions',
        'N': 'Census divisions'}

    # These are the prefixes on the series_id's area_code.
    ac_prefixes  = [
     ('A', 'ST'), # state
     ('B', 'MT'), # Metro
     ('C', 'DV'), # Metro division
     ('D', 'MC'), # Micropolitan
     ('E', 'CA'), # Combined area
     ('F', 'CN'), # County and County Equiv
     ('G', 'CS'), # Cities and towns above 25,000 population ( Town? )
     ('G', 'CT'), # Cities and towns above 25,000 population ( City? )
     ('H', 'CS'), # Cities and towns below 25,000 population in New England ( Town? )
     ('H', 'CT'), # Cities and towns below 25,000 population in New England ( City? )
     ('I', 'PT'), # Parts of cities that cross county boundaries
     ('J', 'SA'), # Multi-entity small labor market areas
     ('K', 'ID'), # Intrastate parts of interstate areas
     ('K', 'IM'), # Intrastate parts of interstate areas
     ('K', 'IS'), # Intrastate parts of interstate areas
     ('L', 'BS'), # Balance of state area
     ('M', 'RD'), # Census regions
     ('N', 'RD')] # Census divisions


    def __init__(self, v):

        self.prefix = v[0:2]
        self.sa_code = v[2]
        self.area_type_code = v[3]
        self.area_code = v[3:18]
        self.measure_code = v[18:20]

        self.ac_prefix = self.area_code[0:2]

        self.state = v[5:7] # State FIPS code
        self.place = v[7:12] if self.ac_prefix in ('CS','CT') else None # FIPS Place code
        self.county = v[7:10] if self.ac_prefix == 'CN' else None # FIPS county code
        self.cbsa = v[7:12] if self.ac_prefix in ('MT','MC') else None  # FIPS CBSA code
        self.csa = v[7:10] if self.ac_prefix in ('CA',) else None  # FIPS csa code

    @property
    def geoid(self):
        """Return a geoid for state, counties, places, Cbsa ans CSA """

        import geoid.acs as acs

        if self.place:
            return acs.Place(self.state, self.place)
        elif self.cbsa:
            return acs.Cbsa(self.cbsa)
        elif self.csa:
            return acs.Csa(self.csa)
        elif self.county:
            return acs.County(self.state,  self.county)
        elif self.ac_prefix in ('ST', 'BS'):
            return acs.State(self.state)
        else:
            return None


    def __str__(self):
        return "{self.prefix:2s}{self.sa_code:1s}{self.area_code:15s}{self.measure_code:2s}".format(self=self)



