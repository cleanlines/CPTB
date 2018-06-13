# Project: CPTB 
# File: UpdateFactory.py
# Created: 14/11/2016 3:34 PM
# Author: FS Hand
from FeatureServiceUpdateHelper import FeatureServiceUpdateHelper
from NewTreeUpdateHelper import NewTreeUpdateHelper
from CPTBExcelChart import CPTBExcelChart
from Config import Config

class UpdateFactory(object):
    @staticmethod
    def factory(json_object):
        config = Config()
        tag = None
        if config.config_has_attribute("newschema"):
            # get the new schema tag
            tag = config.newschema["tag"]
            config.log.do_message("found a tag:"+tag,"debug")
        if "type" in json_object:
            obj_type = json_object["type"]
            if obj_type == "Feature Service":
                if tag in json_object["tags"]:
                    return NewTreeUpdateHelper(json_object)
                else:
                    return FeatureServiceUpdateHelper(json_object)
            assert 0, "Bad generator creation: " + obj_type
        else:
            raise Exception("Object has no type")

    @staticmethod
    def reportfactory(json_object):
        return CPTBExcelChart(json_object)

#TODO: we should have 2 tags - one for newschema one for the particular helper we want - at the moment it's only using one tag
