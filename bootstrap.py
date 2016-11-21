# Project: CPTB 
# File: bootstrap.py
# Created: 9/11/2016 4:16 PM
# Author: FS Hand

# we have 2 requirements
# update data based on algorithms
# create simple excel reports (needs xlsxwriter)


# admin url /rest/admin/services/
# pre req ArcREST 3.5.6
# http://esri.github.io/ArcREST/arcrest.html
# set the result type to standard so we can get 32000 results back

from AssetUpdateHelper import AssetUpdateHelper

def main():
    AssetUpdateHelper().execute_update_process()

if __name__ == "__main__":
    # shelve the current runtime / date and check all records in the editor tracking
    main()




