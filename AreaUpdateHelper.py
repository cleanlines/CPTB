# Project: CPTB 
# File: AreaUpdateHelper.py
# Created: 14/11/2016 3:30 PM
# Author: FS Hand
from Base import Base
from arcresthelper import securityhandlerhelper
from arcrest.agol.services import FeatureLayer
from arcrest.agol.helperservices.analysis import analysis
from arcrest.ags._gpobjects import GPString
from time import sleep
from Decorator import Decorator

class AreaUpdateHelper(Base):

    def __init__(self):
        super(AreaUpdateHelper, self).__init__()
        if not self._config.areaupdate or "areaservice" not in self._config.areaupdate:
            raise Exception("Cannot update areas for features no area service defined")

        self._geom_filters = {}
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        self._area_fl = FeatureLayer(url=self._config.areaupdate["areaservice"], securityHandler=token.securityhandler, initialize=True)
        self._overlay_task = filter(lambda task: task.name == "OverlayLayers",  analysis(securityHandler=token.securityhandler).tasks)[0]

        # areas = self._area_fl.query(where='1=1', out_fields=self._config.areaupdate["queryfield"], returnGeometry=True)
        # for an_area in areas.features:
        #     self._geom_filters[an_area.get_value(self._config.areaupdate["queryfield"])] = an_area.geometry
    @Decorator.method_call_log
    def update_features_for_area(self,layer):
        try:
            a_job = None
            gp1 = GPString()
            gp2 = GPString()
            gp1.paramName = "inputLayer"
            gp2.paramName = "overlayLayer"
            gp1.value = '{"url": "' + layer.url + '"}'
            gp2.value = '{"url": "' + self._area_fl.url + '"}'
            self._config.log.do_message("{0},{1}".format(gp1.value,gp2.value),"debug")
            if self._overlay_task.executionType == "esriExecutionTypeAsynchronous":
                a_job = self._overlay_task.submitJob([gp1,gp2])
                status = a_job.jobStatus
                while (status not in self._config.esrifinishcodes):
                    sleep(2)
                    # print a_job.jobStatus
                    # print a_job.messages
                    status = a_job.jobStatus
            else:
                a_job = self._overlay_task.executeTask([gp1,gp2]) #TODO: I believe this will be json - check
            if a_job and a_job.results and "outputLayer" in a_job.results:
                self._process_overlay_results(layer, a_job.results['outputLayer'].value)
        except Exception as e:
            self._config.log.do_message(e.message,"error")

    def _process_overlay_results(self,layer,result_dic):
        print result_dic
        updates = {}
        object_ids = []
        if "featureSet" in result_dic:
            # # get FID field
            fd = [k for k in result_dic["featureSet"]["features"][0]["attributes"].keys() if "FID" in k and "AREA" not in k][0]
            self._config.log.do_message("Found FID field:"+fd,"debug")
            object_ids = [str(feat["attributes"][fd]) for feat in result_dic["featureSet"]["features"]]

        # use these to get the layers
        update_features = layer.query(out_fields="OBJECTID,"+self._config.areaupdate["updatefield"],returnGeometry=False, resultType='standard',objectIds=",".join(object_ids))

        # after this cache all the global ids in a dict with the area name (remember multiple features will be split)
        for feat in result_dic["featureSet"]["features"]:
            if feat["attributes"][fd] not in updates.keys():
                updates[feat["attributes"][fd]] = []
            if feat["attributes"][self._config.areaupdate["queryfield"]] is not None: updates[feat["attributes"][fd]] += feat["attributes"][self._config.areaupdate["queryfield"]].split(",")

        not_an_update = []
        for update_feature in update_features.features:
            if self._perform_area_update(update_feature.get_value(self._config.areaupdate["updatefield"]),updates[update_feature.get_value("OBJECTID")]):
                update_feature.set_value(self._config.areaupdate["updatefield"],", ".join(updates[update_feature.get_value("OBJECTID")]))
            else:
                # same same
                not_an_update.append(update_feature)
        #bit naughty here we are firing something down the exhaust plorts
        update_features._features = [f for f in update_features.features if f not in not_an_update]
        layer.updateFeature(features=update_features)

    @Decorator.method_call_log
    def _perform_area_update(self,current_value,new_values):
        if not current_value: return True
        current_values = [x.strip() for x in current_value.split(',')]
        self._config.log.do_message(str(current_values)+","+str(new_values),"debug")
        sorted_current = sorted(current_values)
        sorted_new = sorted(set(new_values))
        self._config.log.do_message(str(sorted_current)+","+str(sorted_new),"debug")
        return not sorted_current == sorted_new



