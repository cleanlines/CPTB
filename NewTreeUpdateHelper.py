# Project: CPTB
# File: NewTreeUpdateHelper.py
# Created: 07/06/2018
# Author: FS Hand

from FeatureServiceUpdateHelper import FeatureServiceUpdateHelper
from Decorator import Decorator

class NewTreeUpdateHelper(FeatureServiceUpdateHelper):

    @Decorator.function_timer
    @Decorator.method_call_log
    def process_features(self, layer):
        # Note - check for the exceededTransferLimit in the response - otherwise reset the maxrecordcount in the layer and tables https://support.esri.com/en/technical-article/000012383
        if layer.type == 'Table': return # the parent function also processes tables - we don't do that here nor do we need to copy the code
        all_fields = 'OBJECTID,' + ",".join(self._config.newschema["fields"]["maintenance"])+ "," + ",".join(self._config.newschema["fields"]["qtra"])
        self._config.log.do_message(all_fields,"debug")
        self._process_features(layer, all_fields)

    @Decorator.function_timer
    @Decorator.method_call_log
    def _process_related_record_group(self, group):
        try:
            all_fields = [f.upper() for f in self._config.newschema["fields"]["maintenance"]+ self._config.newschema["fields"]["qtra"]]
            result = {}
            obj = {}
            # the logic here is different - we don't need to work out the last etc - just get the last_edited_date OR if that is null the last review date
            # sorted(iterable[, key][, reverse])
            # we know that the second field sort is _REVIEW_DATE so look for that
            second_sort = self._config.newschema["fields"]["fd_sort"][1]
            sec_sort_fd = [fd for fd in group["relatedRecords"][0]["attributes"] if second_sort in fd]
            keys = [self._config.newschema["fields"]["fd_sort"][0],sec_sort_fd[0]]
            sorted_items = sorted(group["relatedRecords"],key=lambda relrec: (relrec["attributes"][keys[0]],relrec["attributes"][keys[1]]),reverse=True)
            # at this point we *should* we have the last edited record
            item = None
            if len(sorted_items) >= 1:
                item = sorted_items[0]
            else:
                pass # do the additional sorting logic here - try the next field?
            for a_fld,val in item["attributes"].items():
                if a_fld.upper() in all_fields:
                    obj[a_fld] = val
            if obj:
                result[group["objectId"]] = obj
            else:
                del result[group["objectId"]]

            return result
        except Exception as e:
            self._config.log.do_message(e.message, "error")

    @Decorator.function_timer
    @Decorator.method_call_log
    def update_areas_for_features(self):
        self._config.log.do_message("empty stub", "info")
        #stub method to override the parent and not call - we don't need to update the areas here
        return