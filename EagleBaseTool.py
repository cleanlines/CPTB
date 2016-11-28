# Project: CPTB 
# File: EagleBaseTool.py
# Created: 25/11/2016 2:55 PM
# Author: FS Hand

from Config import Config
import arcpy
class EagleBaseTool(object):
    def __init__(self):
        #common code here
        self._config = Config()

    # @property
    # def config(self):
    #     return self._config

    def message(self, message, type):
        if hasattr(self, '_config') and self._config is not None:
            self._config.log.do_message(message, type)
        arcpy.AddError(message) if type == "err" else arcpy.AddMessage(message)

    @property
    def log_location(self):
        return self._config.log.log_file