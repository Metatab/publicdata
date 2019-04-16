# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Load various metadata into the HDF5 file
"""

## Now add the CSV files into the HDF5 file

import h5py
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm
from math import ceil
from itertools import islice

def convert_nlsy(dat_file, header_file, hdf5_file):
    """Convert an nlsy file data file to HDF5"""

    base = Path(dat_file).stem

    nrows = 8983
    chunk_size = 250
    nchunks = ceil(nrows / chunk_size)

    def header_row():
        # Yield the header
        with open(header_file) as f:
            return [c.strip() for c in f.readlines()]

    def yield_rows():

        with open(dat_file) as f:
            for i, line in enumerate(islice(f.readlines(), nrows)):
                yield line.rstrip().split(' ')

    ncols = len(header_row())

    chunkn = 0
    with h5py.File(hdf5_file, "w") as h5f:

        dset = h5f.create_dataset(f'{base}', (chunk_size * nchunks, ncols), dtype=np.int32, chunks=True,
                                  compression="gzip")

        a = np.zeros((chunk_size, ncols), dtype=np.int32)

        for row_n, row in enumerate(tqdm(yield_rows(), total=nrows, ncols=80, desc='Load HDF5')):

            a[row_n % chunk_size, :] = [int(e) for e in row]

            if (row_n + 1) % chunk_size == 0:
                dset[chunkn * chunk_size:(chunkn + 1) * chunk_size, :] = a[:, :]
                a = np.zeros((chunk_size, ncols), dtype=np.int32)
                chunkn += 1
        else:
            dset[chunkn * chunk_size:(chunkn + 1) * chunk_size, :] = a[:, :]

        dset.resize((nrows, ncols))


def load_metadata(dat_file ):
    """Load metadata into the HDF file"""

    hdf5_file = Path(dat_file).with_suffix('.h5')

    csv_meta_file = Path(dat_file).with_suffix('.meta.csv')
    csv_labels_file = Path(dat_file).with_suffix('.labels.csv') # All labels
    csv_reducedlabels_file = Path(dat_file).with_suffix('.rlabels.csv')  # Reduced labels
    header_file = Path(dat_file).with_suffix('.NLSY97')

    with h5py.File(hdf5_file, 'r+') as f:

        base = Path(dat_file).stem

        try:
            f[str(base)]  # Throw exception if it does not exist
        except KeyError:
            raise Exception("Failed to find dataset {}. File has: {}".format(base, list(f.keys())))

        # Value and Variable labels

        for dsn, fn in (('value_labels', csv_labels_file),
                        ('reduced_value_labels', csv_reducedlabels_file),
                        ('variable_labels', csv_meta_file)):

            dsn = base + '_' + dsn

            values = pd.read_csv(fn, low_memory=False)

            if dsn in f:
                del f[dsn]

            f.create_dataset(dsn, values.shape, dtype=h5py.special_dtype(vlen=str), chunks=True, compression="gzip",
                             data=values)

            if dsn+'_headers' in f:
                del f[dsn+'_headers']

            f.create_dataset(dsn+'_headers',  (len(values.columns),), dtype=h5py.special_dtype(vlen=str), chunks=True,
                             compression="gzip",
                             data=values.columns)


        headers_df = pd.read_csv(header_file, header=None)

        if base + '_headers' in f:
            del f[base + '_headers']

        f.create_dataset(base + '_headers', (len(headers_df),), dtype=h5py.special_dtype(vlen=str), chunks=True,
                         compression="gzip",
                         data=headers_df)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Convert an NLSY dataset to HDF5')

    parser.add_argument('-c', '--convert', action='store_true', help='Create the hdf5 file.')

    parser.add_argument('-m', '--metadata', action='store_true', help='Load metadata')

    parser.add_argument('dat_file', help='.dat file')

    args = parser.parse_args()

    if args.convert:
        convert_nlsy(args.dat_file)

    if args.metadata:
        load_metadata(args.dat_file)

if __name__ == "__main__":
    # execute only if run as a script
    main()

