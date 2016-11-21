# Project: CPTB 
# File: AssetUpdateHelper.py
# Created: 14/11/2016 4:18 PM
# Author: FS Hand

from arcresthelper.orgtools import orgtools
from UpdateFactory import  UpdateFactory
from Base import Base
from Decorator import Decorator

class AssetUpdateHelper(Base):

    def __init__(self):
        super(AssetUpdateHelper,self).__init__()

    @Decorator.function_timer
    def execute_update_process(self):
        ot = orgtools(securityinfo=self._config.agolconfig)
        for item in ot.getGroupContent(self._config.assetgroupname):
            UpdateFactory.factory(item).update_features()
