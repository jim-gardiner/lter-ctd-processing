import pandas as pd 

def _col_values(line, col_widths):
    """read fixed with column values that are assumed
    to be right-justified"""
    vals = []
    i = 0

    for w in col_widths:
        start = i
        end = i + w
        vals.append(line[start:end].lstrip())
        i += w

    return vals

def parse_btl_file(path):
    """parse a Seabird .btl file and return a Pandas dataframe"""

    # read lines of file, skipping headers
    lines = []

    with open(path) as fin:
        for l in fin.readlines():
            # skip header lines
            if l.startswith('#') or l.startswith('*'):
                continue
            lines.append(l.rstrip())

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

    # average values are every four lines
    avg_lines = lines[::4]
    # the lines with the time (and stddev values) are the ones immediately
    # following the average value lines
    time_lines = lines[1::4]

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
        
    # all done
    return df

class BtlFile(object):
    def __init__(self, path):
        self.path = path
    def to_dataframe(self):
        df = parse_btl_file(self.path)
        return df

if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    outpath = sys.argv[2]
    btl = BtlFile(path)
    df = btl.to_dataframe()
    df.to_csv(outpath, index=False)