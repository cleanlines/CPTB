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

    def update_features_for_area(self,layer):
        print 'big dirty cock bags'
        a_job = None
        if self._overlay_task.executionType == "esriExecutionTypeAsynchronous":
            #submit the job - stupid esri object
            gp1 = GPString()
            gp2 = GPString()
            gp1.paramName = "inputLayer"
            gp2.paramName = "overlayLayer"
            gp1.value = '{"url": "' + layer.url + '"}'
            gp2.value = '{"url": "' + self._area_fl.url + '"}'
             #of BaseGPObject (name,value)
            a_job = self._overlay_task.submitJob([gp1,gp2])
            status = a_job.jobStatus
            print a_job# we have the job url on the job so need to keep checking it I suppose??
            while (status not in self._config.esrifinishcodes):
                sleep(2)
                print a_job.jobStatus
                print a_job.messages
                status = a_job.jobStatus
            print a_job.results


        else:
            #execute the job
            pass
        if a_job and a_job.results and "outputLayer" in a_job.results:
            self._process_overlay_results(layer, a_job.results['outputLayer'].value)

    def _process_overlay_results(self,layer,result_dic):
        print result_dic
        updates = {}
        object_ids = []
        if "featureSet" in result_dic:
            # # get FID field
            fd = [k for k in result_dic["featureSet"]["features"][0]["attributes"].keys() if "FID" in k and "AREA" not in k][0]
            #
            print "------------------>>>",fd
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
        print updates
        print "12345"
        layer.updateFeature(features=update_features)


    def _perform_area_update(self,current_value,new_values):
        if not current_value: return True
        current_values = [x.strip() for x in current_value.split(',')]
        print current_values,",",new_values

        sorted_current = sorted(current_values)
        sorted_new = sorted(set(new_values))
        print sorted_current, ",", sorted_new
        return not sorted_current == sorted_new
            # dealing with the overlay task
        #get all the objectIDS of the affected features, then uypodate and post back to the layer


    # def check_job_status(self, job):
    #     try:
    #         params = {"f": "json"}
    #         finish_codes = ["esriJobSucceeded", "esriJobFailed", "esriJobTimedOut", "esriJobCancelled",
    #                         "esriJobDeleted"]
    #
    #         response = self._do_server_request(job, params)
    #         if "jobStatus" in response:
    #             # self.config.log.do_message("\n".join([x["description"] for x in response["messages"]]),"debug")
    #             status = response["jobStatus"]
    #             while (status not in finish_codes):
    #                 sleep(10)
    #                 response = self._do_server_request(job, params)
    #                 status = response["jobStatus"]
    #             self.config.log.do_message("\n".join([x["description"] for x in response["messages"]]), "debug")
    #             return 1 if response["jobStatus"] == "esriJobSucceeded" else 0
    #         else:
    #             self.config.log.do_message(str(response), "info")
    #             return 0
    #     except Exception, err:
    #         self.config.log.do_message(err.message, "error")
    #         return 0





    # def update_features_for_area(self,layer):
    #     print
    #     # we have a FS with all the areas and a layer
    #     for k,v in self._geom_filters.items():
    #         in_area_feats = layer.query(where='1=1',out_fields=self._config.areaupdate["updatefield"],returnGeometry=False,geometry=v.JSON,geometryType="esriGeometry"+v.type.capitalize())
    #         print k, len(in_area_feats.features)
    #         if len(in_area_feats.features) > 0:
    #             for in_feat in in_area_feats.features:
    #                 current_area = in_feat.get_value(self._config.areaupdate["updatefield"])
    #                 print current_area," also ",k
    #                 if current_area is None:
    #                     in_feat.set_value(self._config.areaupdate["updatefield"],k)
    #                 applied_areas = current_area.split(",")
    #                 if k not in applied_areas: applied_areas += k
    #                 in_feat.set_value(self._config.areaupdate["updatefield"], ",".join(applied_areas))
    #
    #         #FIXME: this is only updating - not removing what could be incorrect values - ie if a bbq has shifted


# FIXME - we are going to shift how we do this - ind queries are too slow
''' use the AGOL analysis tools

https://analysis6.arcgis.com/arcgis/rest/services/tasks/GPServer?f=json&token=5atP-dgQzSygEAS_vjjQQuU2X8f1WZFdxHiva-zWtYu3U2WTdJomqRKucnIo9PMnnQpYr56GGwhvld7Oay0EUev7YWhRDRaox-1TGwB7I5SKrlVBAH3vhdqRE56199WPSQXZ-uw2-1bKHSjzV_qMtac1mfATS__HulhpSbISeZl9T7RuGcNgZmiQYzY9fBa9oqLsT3ClGUwfUpk2hDNEJauaDb0CGm_ZkM4ZBVqeLNEWeeR7fU5oje58M-ziKLmIw3maBfZP8RNJI-mBCvSjjQ..



https://developers.arcgis.com/rest/analysis/api-reference/tasks-overview.htm
http://doc.arcgis.com/en/arcgis-online/reference/roles.htm

'''