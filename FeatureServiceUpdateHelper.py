# Project: CPTB 
# File: FeatureServiceUpdateHelper.py
# Created: 14/11/2016 3:33 PM
# Author: FS Hand
from AbstractUpdateHelper import AbstractUpdateHelper
from arcresthelper import securityhandlerhelper
from arcrest.agol.services import FeatureService
from Base import Base
from Decorator import Decorator
from AreaUpdateHelper import AreaUpdateHelper

class FeatureServiceUpdateHelper(AbstractUpdateHelper, AreaUpdateHelper):

    def __init__(self,json_object):
        super(FeatureServiceUpdateHelper, self).__init__()
        self._json_object = json_object
        print self._config.log


    @Decorator.function_timer
    def update_features(self):
        print self._json_object
        # go through each layer and do the workflow
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        fs = FeatureService(url=self._json_object["url"], securityHandler=token.securityhandler, initialize=True)

        for layer in fs.layers:
            self.process_features(layer)
            self.update_features_for_area(layer)

    @Decorator.function_timer
    def process_features(self,layer): #TODO: fix me!!
        fields = 'OBJECTID,'+",".join(self._config.related_fields["condition"]["fieldlookups"].values())+","+",".join(self._config.related_fields["maintenance"]["fieldlookups"].values())
        features = layer.query(out_fields=fields,resultType='standard') # we are here sorting out the field
        # print [feat.get_value("OBJECTID") for feat in features.features]
        feat_ids = ",".join([str(feat.get_value("OBJECTID")) for feat in features.features])
        print feat_ids
        some_updates = {}
        [some_updates[k].update(v) if k in some_updates else some_updates.update({k:v}) for w in [self.get_related_records(layer.query_related_records(feat_ids,r["id"])) for r in layer.relationships] for k,v in w.items()]
        print some_updates
        some_feats = filter(lambda feat:feat.get_value('OBJECTID') in some_updates.keys(), features.features)
        print some_feats

        for feat in some_feats:
            try:
                for k,v in some_updates[feat.get_value('OBJECTID')].items():
                    feat.set_value(k,v)
            except Exception as e:
                self._config.log.do_message(e.message, "error")
        try:
            layer.updateFeature(features=some_feats) #can we do a map??
        except Exception as e:
            self._config.log.do_message(e.message, "error")

    @Decorator.function_timer
    def get_related_records(self,list):
        updates = {}
        if "relatedRecordGroups" in list:
            if len(list["relatedRecordGroups"]) > 0:
                for group in list["relatedRecordGroups"]:
                    try:
                        updates[group["objectId"]] = {}
                        [updates[k].update(v) for k,v in self._process_related_record_group(group).items()]
                    except Exception as e:
                        self._config.log.do_message(e.message, "error")
        return updates

    @Decorator.function_timer
    def _process_related_record_group(self,group):
        skips = ["OBJECTID","SHAPE","GLOBALID"]
        result = {}
        #obj = {"OBJECTID": group["objectId"]}
        obj = {}
        for rec in group:
            for updatekey in self._config.related_fields.keys():
                if "sortby" in self._config.related_fields[updatekey]:
                    try:
                        print len(group["relatedRecords"])
                        sorted_items = sorted(group["relatedRecords"],key=lambda relrec: relrec["attributes"][self._config.related_fields[updatekey]["sortby"]])
                        # if self._config.related_fields[updatekey]["sortby"] == "newest":
                        #     item = sorted_items[0]
                        if self._config.related_fields[updatekey]["select"] == "newest":
                            sorted_items = list(reversed(sorted_items))
                        item = sorted_items[0] # we could have got sorted_items[-1] but if there is a where then we need a consistent loop
                        # not done yet - even though we have an item we need to check if there is any other processing to do
                        # if nothing satifies the where then set these fields to null
                        if "where" in self._config.related_fields[updatekey]:
                            for i in sorted_items:
                                if i['attributes'][self._config.related_fields[updatekey]["where"][0]] == \
                                self._config.related_fields[updatekey]["where"][1]:
                                    break
                                else:
                                    item = i
                            # we are at the end of the sorted items - do final check and set to null if required
                            if item['attributes'][self._config.related_fields[updatekey]["where"][0]] != \
                                    self._config.related_fields[updatekey]["where"][1] and self._config.related_fields[updatekey]["sortby"] != None:
                                # nothing to do for this record - clear out fields
                                for fl in self._config.related_fields[updatekey]["fieldlookups"]:
                                    item["attributes"][fl] = None

                        for k,v in item["attributes"].items():
                            print k,v
                            if k in self._config.related_fields[updatekey]["fieldlookups"].keys():
                                if k.upper() in skips: continue
                                obj[self._config.related_fields[updatekey]["fieldlookups"][k]] = v
                        if obj:
                            result[group["objectId"]] = obj
                        else:
                            del result[group["objectId"]]
                    except KeyError as ke:
                        self._config.log.do_message(e.message + "key not on this related table - skip", "info")
                    except Exception as e:
                        self._config.log.do_message(e.message,"error")
            return result