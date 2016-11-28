# Project: CPTB 
# File: UpdateFactory.py
# Created: 14/11/2016 3:34 PM
# Author: FS Hand
from FeatureServiceUpdateHelper import FeatureServiceUpdateHelper
from CPTBExcelChart import CPTBExcelChart


class UpdateFactory(object):
    @staticmethod
    def factory(json_object):
        if "type" in json_object:
            obj_type = json_object["type"]
            if obj_type == "Feature Service":
                return FeatureServiceUpdateHelper(json_object)
            assert 0, "Bad generator creation: " + obj_type
        else:
            raise Exception("Object has no type")

    @staticmethod
    def reportfactory(json_object):
        return CPTBExcelChart(json_object)
