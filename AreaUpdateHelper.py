# Project: CPTB 
# File: AreaUpdateHelper.py
# Created: 14/11/2016 3:30 PM
# Author: FS Hand
from Base import Base
from arcresthelper import securityhandlerhelper
from arcrest.agol.services import FeatureLayer

class AreaUpdateHelper(Base):

    def __init__(self):
        super(AreaUpdateHelper, self).__init__()
        if not self._config.areaupdate or "areaservice" not in self._config.areaupdate:
            raise Exception("Cannot update areas for features no area service defined")

        self._geom_filters = {}
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        self._area_fl = FeatureLayer(url=self._config.areaupdate["areaservice"], securityHandler=token.securityhandler, initialize=True)
        areas = self._area_fl.query(where='1=1', out_fields=self._config.areaupdate["queryfield"], returnGeometry=True)
        for an_area in areas.features:
            self._geom_filters[an_area.get_value(self._config.areaupdate["queryfield"])] = an_area.geometry

    def update_features_for_area(self,layer):
        print
        # we have a FS with all the areas and a layer
        for k,v in self._geom_filters.items():
            in_area_feats = layer.query(where='1=1',out_fields=self._config.areaupdate["updatefield"],returnGeometry=False,geometry=v.JSON,geometryType="esriGeometry"+v.type.capitalize())
            print k, len(in_area_feats.features)
            if len(in_area_feats.features) > 0:
                for in_feat in in_area_feats.features:
                    current_area = in_feat.get_value(self._config.areaupdate["updatefield"])
                    print current_area," also ",k
                    if current_area is None:
                        in_feat.set_value(self._config.areaupdate["updatefield"],k)
                    applied_areas = current_area.split(",")
                    if k not in applied_areas: applied_areas += k
                    in_feat.set_value(self._config.areaupdate["updatefield"], ",".join(applied_areas))

            #FIXME: this is only updating - not removing what could be incorrect values - ie if a bbq has shifted
