National Longitudinal Survey of Youth
========================================

BUilding the .h5 file:

$ python -mpublicdata.nlsy.h5 nlsy97_all_1997-2013.dat # Initial creation of HDF5 file
$ python -mpublicdata.nlsy.cdb nlsy97_all_1997-2013.cdb -e -c # Create CSV files from codebook
$ python -mpublicdata.nlsy.h5 nlsy97_all_1997-2013.dat -m # Load metadata into HDF5
