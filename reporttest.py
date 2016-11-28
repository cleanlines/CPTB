# Project: CPTB 
# File: reporttest.py
# Created: 25/11/2016 5:06 PM
# Author: FS Hand


from arcresthelper.orgtools import orgtools
from UpdateFactory import UpdateFactory
from Config import Config

#  DEBUG
def main():
    # think about this - pits it into separate xls files
    some_config = Config()
    ot = orgtools(securityinfo=some_config.agolconfig)
    for item in ot.getGroupContent(some_config.assetgroupname):

        UpdateFactory.reportfactory(item).do_reporting()

if __name__ == '__main__':
    main()