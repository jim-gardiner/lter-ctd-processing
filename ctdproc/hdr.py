import re
import pandas as pd

def parse_lat_lon(ll):
    """convert deg/dec minutes into dec"""
    REGEX = r'(\d+)[^\d]+([\d.]+)[^NSEW]*([NSEW])'
    deg, mnts, hemi = re.match(REGEX, ll).groups()
    mult = 1 if hemi in ['N', 'E'] else -1
    deg, mnts = int(deg), float(mnts)
    deg = mult * (deg + (mnts / 60))
    return deg

class HdrFile(object):
    def __init__(self, path, parse=True):
        self.path = path
        if parse:
            self.parse()
    def parse(self):
        self._read_lines()
        self._parse_names()
        self._parse_lat_lon()
        self._parse_time()
    def _read_lines(self):
        self.lines = []
        with open(self.path) as fin:
            for l in fin.readlines():
                if not l.startswith('*END*'):
                    self.lines.append(l.rstrip())
    def _parse_names(self):
        REGEX = r'# name \d+ = ([^:]+): ([^\[]+)(?:\[(.*)\](, .*)?)?'
        names, defns, units, params = set(), {}, {}, {}
        for line in self.lines:
            if not re.search(r'^# name \d+', line):
                continue
            name, defn, unit, param = re.match(REGEX, line).groups()
            defn = defn.rstrip() # FIXME do in regex?
            if param is not None:
                param = param.lstrip(', ') # FIXME do in regex?
            names.add(name)
            defns[name] = defn
            units[name] = unit
            params[name] = params
        self.names = names
        self.definitions = defns
        self.units = units
        self._params = params
    def _line_that_matches(self, regex):
        for line in self.lines:
            if re.match(regex, line):
                return line
    def _parse_lat_lon(self):
        lat_line = self._line_that_matches(r'\* NMEA Latitude')
        lon_line = self._line_that_matches(r'\* NMEA Longitude')
        split_regex = r'.*itude = (.*)'
        self.lat = parse_lat_lon(re.match(split_regex, lat_line).group(1))
        self.lon = parse_lat_lon(re.match(split_regex, lon_line).group(1))
    def _parse_time(self):
        line = self._line_that_matches(r'\* NMEA UTC \(Time\)')
        time = re.match(r'.*= (.*)', line).group(1)
        self.time = pd.to_datetime(time)
    def definition(self, name):
        return self.definitions[name]
    def units(self, name):
        return self.units[name]

if __name__=='__main__':
    import sys
    hdr_path = sys.argv[1]
    hdr = HdrFile(hdr_path)
    print(hdr.lat, hdr.lon, hdr.time)
