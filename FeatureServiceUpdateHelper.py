# Project: CPTB 
# File: FeatureServiceUpdateHelper.py
# Created: 14/11/2016 3:33 PM
# Author: FS Hand

from AbstractUpdateHelper import AbstractUpdateHelper
from arcresthelper import securityhandlerhelper
from arcrest.agol.services import FeatureService
from Decorator import Decorator
from AreaUpdateHelper import AreaUpdateHelper
from Utility import Utility


class FeatureServiceUpdateHelper(AbstractUpdateHelper, AreaUpdateHelper):
    def __init__(self, json_object):
        super(FeatureServiceUpdateHelper, self).__init__()
        self._json_object = json_object
        print self._config.log

    @Decorator.function_timer
    @Decorator.method_call_log
    def update_areas_for_features(self):
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        fs = FeatureService(url=self._json_object["url"], securityHandler=token.securityhandler, initialize=True)
        for layer in fs.layers:
            self._config.log.do_message('LAYER:' + layer.name, "debug")
            self.update_features_for_area(layer)

    @Decorator.function_timer
    @Decorator.method_call_log
    def update_features_asset_info(self):
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        fs = FeatureService(url=self._json_object["url"], securityHandler=token.securityhandler, initialize=True)
        for layer in fs.layers:
            self._config.log.do_message('LAYER:' + layer.name, "debug")
            self.process_features(layer)
        for table in fs.tables:
            self._config.log.do_message('TABLE:' + table.name, "debug")
            self.process_features(table)

    @Decorator.function_timer
    @Decorator.method_call_log
    def update_features(self):
        # print self._json_object
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        fs = FeatureService(url=self._json_object["url"], securityHandler=token.securityhandler, initialize=True)
        for layer in fs.layers:
            self._config.log.do_message('LAYER:' + layer.name, "debug")
            self.process_features(layer)
            self.update_features_for_area(layer)
        for table in fs.tables:
            self._config.log.do_message('TABLE:' + table.name, "debug")
            self.process_features(table)

    @Decorator.function_timer
    @Decorator.method_call_log
    def process_features(self, layer):
        fields = 'OBJECTID,' + ",".join(
            self._config.related_fields["condition"]["fieldlookups"].values()) + "," + ",".join(
            self._config.related_fields["maintenance"]["fieldlookups"].values()) + "," + ",".join(
            self._config.valuation_field_lookups.values())
        self._process_features(layer,fields)

    def _process_features(self, layer, fields):
        try:
            features = layer.query(out_fields=fields, resultType='standard')  # we are here sorting out the field
            # print [feat.get_value("OBJECTID") for feat in features.features]
            feat_ids = ",".join([str(feat.get_value("OBJECTID")) for feat in features.features])
            # print feat_ids
            some_updates = {}
            # note we only want to process origin relationships (otherwise we end up doing backwards ones - wont find anything but still
            [some_updates[k].update(v) if k in some_updates else some_updates.update({k: v}) for w in
             [self.get_related_records(layer.query_related_records(feat_ids, r["id"]), r["id"]) for r in layer.relationships
              if r["role"] == 'esriRelRoleOrigin'] for k, v in w.items()]
            # print some_updates
            some_feats = filter(lambda some_feat: some_feat.get_value('OBJECTID') in some_updates.keys(), features.features)
            for a_feat in some_feats:
                try:
                    for k, v in some_updates[a_feat.get_value('OBJECTID')].items():
                        a_feat.set_value(k, v)
                except Exception as e:
                    self._config.log.do_message(e.message, "error")

            try:
                if some_feats:
                    if len(some_feats) <= 100:
                        chunks = [some_feats]
                    else:
                        chunks = [list(some_feats[i:i + 100]) for i in range(0, len(some_feats), 100)]
                        self._config.log.do_message("Chunking data into 100 record chuncks - {} chunks".format(len(chunks)),"debug")
                for a_chunk in chunks:
                    self._config.log.do_message("Processing chunk","debug")
                    result = layer.updateFeature(features=a_chunk)
                    self._config.log.do_message(str(result),"debug")
                # don't update the current value.
                # if self._update_current_value(features):
                #     layer.updateFeature(features=features)
            except Exception as e:
                self._config.log.do_message(e.message, "error")
        except Exception as e:
            self._config.log.do_message(e.message, "error")

    @Decorator.method_call_log
    @Decorator.function_timer
    def _update_current_value(self, features):
        if len(features.features) == 0:
            return False
        for v in self._config.valuation_field_lookups.values():
            if v not in features.features[0].fields:
                return False

        return_val = False
        updated_features = []
        for f in features.features:
            # this is well known stuff - we need the following bits of info
            d1 = f.get_value(self._config.valuation_field_lookups["installdate"])
            c1 = f.get_value(self._config.valuation_field_lookups["installcost"])
            d2 = f.get_value(self._config.valuation_field_lookups["renewaldate"])
            # set this
            if not d1 or not d2 or not c1:
                continue
            # the dates should be milliseconds
            print d1, d2, c1
            now = Utility.current_milli_time()
            full_period = d2 - d1
            time_left = d2 - now
            current_cost = round(float(c1) * float(float(time_left) / float(full_period)), 0)
            if current_cost < 0:
                current_cost = 0
            f.set_value(self._config.valuation_field_lookups["currentvalue"], current_cost)
            updated_features.append(f)
            return_val = True
        if return_val:
            del features.features[:]
            [features.features.append(af) for af in updated_features]
        return return_val

    @Decorator.function_timer
    def get_related_records(self, rec_list, relationship_id):
        # print relationship_id

        updates = {}
        if "relatedRecordGroups" in rec_list:
            if len(rec_list["relatedRecordGroups"]) > 0:
                for group in rec_list["relatedRecordGroups"]:
                    try:
                        updates[group["objectId"]] = {}
                        [updates[k].update(v) for k, v in self._process_related_record_group(group).items()]
                    except Exception as e:
                        self._config.log.do_message(e.message, "error")
        return updates

    @Decorator.function_timer
    @Decorator.method_call_log
    def _process_related_record_group(self, group):
        skips = ["OBJECTID", "SHAPE", "GLOBALID"]
        result = {}
        obj = {}
        for updatekey in self._config.related_fields.keys():
            if "sortby" in self._config.related_fields[updatekey]:
                try:
                    # print len(group["relatedRecords"])
                    sorted_items = sorted(group["relatedRecords"], key=lambda relrec: relrec["attributes"][
                        self._config.related_fields[updatekey]["sortby"]])
                    if self._config.related_fields[updatekey]["select"] == "newest":
                        sorted_items = list(reversed(sorted_items))
                    item = sorted_items[0]
                    # we could have got sorted_items[-1] but if there is a where then we need a consistent loop
                    # not done yet - even though we have an item we need to check if there is any other processing to do
                    # if nothing satisfies the where then set these fields to null
                    if "where" in self._config.related_fields[updatekey]:
                        for i in sorted_items:
                            if i['attributes'][self._config.related_fields[updatekey]["where"][0]] == \
                                    self._config.related_fields[updatekey]["where"][1]:
                                break
                            else:
                                item = i
                        # we are at the end of the sorted items - do final check and set to null if required
                        if item['attributes'][self._config.related_fields[updatekey]["where"][0]] != \
                                self._config.related_fields[updatekey]["where"][1] and \
                                        self._config.related_fields[updatekey]["sortby"] is not None:
                            # nothing to do for this record - clear out fields
                            for fl in self._config.related_fields[updatekey]["fieldlookups"]:
                                item["attributes"][fl] = None

                    for k, v in item["attributes"].items():
                        # print k,v
                        if k in self._config.related_fields[updatekey]["fieldlookups"].keys():
                            if k.upper() in skips:
                                continue
                            obj[self._config.related_fields[updatekey]["fieldlookups"][k]] = v
                    if obj:
                        result[group["objectId"]] = obj
                    else:
                        del result[group["objectId"]]
                except KeyError as ke:
                    self._config.log.do_message(ke.message + "key not on this related table - skip", "info")
                except Exception as e:
                    self._config.log.do_message(e.message, "error")
        return result
