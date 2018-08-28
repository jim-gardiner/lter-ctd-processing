import os

from matplotlib import pyplot as plt 
import pandas as pd

CRUISE = 'ar29'

CHL_SPREADSHEET_FILE = r'\\sosiknas1\Backup\SPIROPA\SFDchl.xlsx'
AB_OUTPUT_FILE = 'chl_ab_{}.csv'.format(CRUISE)
PLOT_OUTPUT_FILE = 'chl_ab_{}_plot.png'.format(CRUISE)

def subset_rename_columns(df, current_cols, new_cols):
    df = df[current_cols]
    df.columns = new_cols
    return df

def distill_chl_spreadsheet(raw):
    # can't use rows where Ra or Rb are na
    chl = raw.dropna(subset=['Ra','Rb']).copy()
    # no such thing as na ints, so use 0 for cast to fill in nans
    chl['Cast #'] = chl['Cast #'].fillna(0).astype(int)

    # rename columns
    current_cols = ['Cruise #:', 'Cast #', 'Niskin #', 'Filter\nSize', 'Replicate', 'Chl (ug/l)', 'Phaeo (ug/l)']
    new_cols = ['cruise', 'cast', 'niskin', 'filter_size', 'replicate', 'chl', 'phaeo']
    chl = subset_rename_columns(chl, current_cols, new_cols)

    return chl

def merge_replicates(chl):
    chla = chl[chl['replicate'] == 'a']
    chlb = chl[chl['replicate'] == 'b']

    df = chla.merge(chlb,on=['cruise','cast','niskin','filter_size'])

    # rename annoying "x/y" vars to more descriptive "a/b"
    df = df[['cruise','cast','niskin','filter_size','chl_x','chl_y','phaeo_x','phaeo_y']]
    df.columns=['cruise','cast','niskin','filter_size','chl_a','chl_b','phaeo_a','phaeo_b']

    # get rid of nans
    df.dropna(inplace=True)

    return df

def plot_curve(merged, output_file):
    x = merged['chl_a']
    y = merged['chl_b']

    plt.figure(figsize=(10,10))
    plt.grid(True)
    plt.scatter(x,y,s=2)
    plt.title('Chlorophyll replicates, cruise {} (all stations)'.format(CRUISE))
    plt.xlabel('Chlorophyll concentration, replicate A (µg/l)')
    plt.ylabel('Chlorophyll concentration, replicate B (µg/l)')
    plt.savefig(output_file)

if __name__ == '__main__':
    # read file
    assert os.path.exists(CHL_SPREADSHEET_FILE), 'cannot find chlorophyll spreadsheet'
    raw = pd.read_excel(CHL_SPREADSHEET_FILE)

    # clean up and put replicates on same rows
    chl = distill_chl_spreadsheet(raw)
    merged = merge_replicates(chl)

    # output results
    plot_curve(merged, PLOT_OUTPUT_FILE) # plot
    merged.to_csv(AB_OUTPUT_FILE, index=False) # csv data
