
# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Main function for converting an NLSY download into HDF5
"""

from .cdb import convert_cdb, extract_from_codebook
from .h5 import convert_nlsy, load_metadata
from pathlib import Path
import sys

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Convert an NLSY dataset to HDF5')

    parser.add_argument('-n', '--hdf', action='store_true', help='Create a new hdf5 file.')

    parser.add_argument('-c', '--csv', action='store_true', help='Parse the codebook to CSV files')

    parser.add_argument('-e', '--extract', action='store_true', help='Only extract the cdb file, ignoring the cached version')

    parser.add_argument('-m', '--meta', action='store_true', help='Load CSV metadata into the HDF5 file')

    parser.add_argument('-L','--limit', type=int, help='Set limit for number of rows processed with -e')


    parser.add_argument('archive_dir', help='Path to the unpacked NLS archive')

    args = parser.parse_args()

    try:
        run(args)
    except FileNotFoundError as e:
        print(f"ERROR: Not found: {e}")
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"ERROR: Found, but not a directory: {e}")
        sys.exit(1)


def filemap(z):
    files = {}

    for e in z.namelist():
        p = Path(e)
        files[p.suffix] = str(p)

    return files

# convert_nlsy(base, dat_f, header_f, h5_file)

def run(args):
    import sys

    base = Path(args.archive_dir)

    if not base.exists():
        raise FileNotFoundError(args.archive_dir)

    if not base.is_dir():
        raise NotADirectoryError(args.archive_dir)

    if not any([args.hdf, args.csv, args.extract, args.meta]):
        args.hdf = args.csv = args.extract = args.meta = 1

    if args.hdf:
        make_hdf(args)

    if args.csv:
        make_csv(args)

    if args.extract:
        make_extract(args)

    if args.meta:
        make_meta(args)

def _get_dat_file(base):
    dat_file = next(base.glob('**/*.dat'))

    if not dat_file:
        raise FileNotFoundError(f'{base}.dat')

    return dat_file

def _get_cdb_file(base):
    cdb_file = next(base.glob('**/*.cdb'))

    if not cdb_file:
        raise FileNotFoundError(f'{base}.cdb')

    return cdb_file

def make_hdf(args):

    base = Path(args.archive_dir)

    header_file = next(base.glob('**/*.NLSY97'))

    if not header_file:
        raise FileNotFoundError(f'{base}.NLSY97')

    h5_file = base.joinpath(base).with_suffix('.h5')

    print("Convert .dat file to .hdf5")
    convert_nlsy(_get_dat_file(base), header_file, h5_file)

    print("Wrote HDF5 file: ", h5_file)


def make_csv(args):
    base = Path(args.archive_dir)

    print("Create .csv files from codebook")
    wrote_files = convert_cdb(_get_cdb_file(base))

    for f in wrote_files:
        print("Wrote  ",f)

def make_extract(args):

    base = Path(args.archive_dir)

    print("Extract codebook to a datastructure")

    extract_from_codebook(_get_cdb_file(base), force=True, limit=args.limit)


def make_meta(args):

    base = Path(args.archive_dir)

    load_metadata(_get_dat_file(base))


if __name__ == "__main__":
    # execute only if run as a script
    main()

