import math
from glob import glob
import os
import pandas as pd 

from .parsing import CtdTextParser, pathname2cruise_cast

def _col_values(line, col_widths):
    """read fixed-width column values that are assumed
    to be right-justified"""
    vals = []
    i = 0

    for w in col_widths:
        start = i
        end = i + w
        vals.append(line[start:end].lstrip())
        i += w

    return vals

def p_to_z(p, latitude):
    """convert pressure to depth in seawater.
    p = pressure in dbars
    latitude"""

    # for now, use the Seabird calculation
    # from http://www.seabird.com/document/an69-conversion-pressure-depth

    # FIXME use GSW-Python

    x = math.pow(math.sin(latitude / 57.29578),2)
    g = 9.780318 * ( 1.0  + (5.2788e-3 + 2.36e-5 * x) * x ) + 1.092e-6 * p
    
    depth_m_sw = ((((-1.82e-15 * p + 2.279e-10) * p - 2.2512e-5) * p + 9.72659) * p) / g
    
    return depth_m_sw

class BtlFile(CtdTextParser):
    def __init__(self, path, parse=True):
        super(BtlFile, self).__init__(path, parse)
        self._df = None
    def to_dataframe(self):
        if self._df is not None:
            return self._df

        # read lines of file, skipping headers
        lines = []

        for l in self._lines:
            if l.startswith('#') or l.startswith('*'):
                continue
            lines.append(l)

        # column headers are fixed with at 11 characters per column,
        # except the first two
        h1_width = 10
        h2_width = 12

        n_cols = ((len(lines[0]) - (h1_width + h2_width)) // 11) + 2

        header_col_widths = [h1_width,h2_width] + [11] * (n_cols - 2)

        # the first line is the first line of column headers; skip the second
        col_headers = _col_values(lines[0], header_col_widths)

        # discard the header lines, the rest are data lines
        lines = lines[2:]

        # data lines are in groups of 4 (if min/max is written to the file)
        # or in groups of 2

        n_lines_per_sample = 2

        for line in lines:
            if line.endswith('(min)'): # min/max are present
                n_lines_per_sample = 4
                break

        # average values are every four lines
        avg_lines = lines[::n_lines_per_sample]
        # the lines with the time (and stddev values) are the ones immediately
        # following the average value lines
        time_lines = lines[1::n_lines_per_sample]

        # value columns are fixed width 11 characters per col except the first two
        v1_width = 7
        v2_width = 15

        col_widths = [7,15] + [11] * (n_cols - 2)

        # now assemble the rows of the dataframe
        rows = []

        for al, tl in zip(avg_lines, time_lines):
            cvs = _col_values(al, col_widths)
            time = _col_values(tl, col_widths)[1] # just use the first value
            cvs[1] = '{} {}'.format(cvs[1], time)
            rows.append(cvs)

        df = pd.DataFrame(rows, columns=col_headers)

        # convert df columns to reasonable types
        df.Bottle = df.Bottle.astype(int)
        df.Date = pd.to_datetime(df.Date)

        for c in df.columns[2:]:
            df[c] = df[c].astype(float)
        
        self._df = df

        # add cruise / cast

        df['Cruise'] = self.cruise
        df['Cast'] = self.cast

        # move those columns to the front
        cols = df.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        df = df[cols]

        # all done
        return df

    def _niskin_sdf(self, niskin_number):
        df = self.to_dataframe()
        return df[df.Bottle == int(niskin_number)]

    def niskin_time(self, niskin_number):
        return self._niskin_sdf(niskin_number).Date.iloc[0]

    def niskin_depth(self, niskin_number):
        prDM = self._niskin_sdf(niskin_number).PrDM.iloc[0]

        return p_to_z(prDM, self.lat)

def find_btl_file(dir, cruise, cast):
    for path in glob(os.path.join(dir, '*.btl')):
        cr, ca = pathname2cruise_cast(path)
        if cr.lower() == cruise.lower() and int(ca) == int(cast):
            return BtlFile(path)

def convert_file(in_path, out_path):
    btl = BtlFile(in_path)
    df = btl.to_dataframe()
    df.to_csv(out_path, index=False)
    return btl

if __name__ == '__main__':
    import sys
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    btl = convert_file(in_path, out_path)
    print('Cruise: {}'.format(btl.cruise))
    print('Cast: {}'.format(btl.cast))
    print('Lat/lon: {}/{}'.format(btl.lat, btl.lon))
    print('Time: {}'.format(btl.time))