# Project: CPTB 
# File: arcrestpatches.py
# Created: 30/11/2016 4:15 PM
# Author: FS Hand

from __future__ import absolute_import
from __future__ import print_function
from arcrest.manageorg._content import User, UserItem,Item
import json
import os

class PatchedUser(User):
    def __init__(self, url,
                 securityHandler,
                 proxy_url=None,
                 proxy_port=None,
                 initalize=False):
        super(PatchedUser, self).__init__(url,securityHandler,proxy_url,proxy_port,initalize)

    def patchedAddItem(self,
                       itemParameters,
                filePath=None,
                overwrite=False,
                folder=None,
                dataURL=None,
                url=None,
                text=None,
                relationshipType=None,
                originItemId=None,
                destinationItemId=None,
                serviceProxyParams=None,
                metadata=None,
                multipart=False):
        params = {
            "f": "json"
        }
        res = ""
        if itemParameters is not None:
            for k, v in itemParameters.value.items():
                if isinstance(v, bool):
                    params[k] = json.dumps(v)
                else:
                    params[k] = v
        if itemParameters.overwrite is not None:
            params['overwrite'] = json.dumps(overwrite)
        if itemParameters.overwrite != overwrite:
            params['overwrite'] = json.dumps(overwrite)
        if dataURL is not None:
            params['dataURL'] = dataURL
        if url is not None:
            params['url'] = url
        if text is not None:
            params['text'] = text
        if relationshipType is not None:
            params['relationshipType'] = relationshipType
        if originItemId is not None:
            params['originItemId'] = originItemId
        if destinationItemId is not None:
            params['destinationItemId'] = destinationItemId
        if serviceProxyParams is not None:
            params['serviceProxyParams'] = serviceProxyParams
        url = "{0}/addItem".format(self.location) if not folder else "{0}/{1}/addItem".format(self.location,folder)
        files = {}
        if multipart:
            res = self._addItemMultiPart(
                itemParameters=itemParameters,
                filePath=filePath)
        else:
            if filePath is not None and os.path.isfile(filePath):
                files['file'] = filePath
                params["filename"] = os.path.basename(filePath)
            elif filePath is not None and multipart:
                params["filename"] = os.path.basename(filePath)
            elif filePath is not None and not os.path.isfile(filePath):
                print ("{0} not found".format(filePath))
            if 'thumbnail' in params:
                v = params['thumbnail']
                del params['thumbnail']
                files['thumbnail'] = v
            if metadata is not None and os.path.isfile(metadata):
                files['metadata'] = metadata
            if len(files) < 1:
                res = self._post(url,
                                 param_dict=params,
                                 securityHandler=self._securityHandler,
                                 proxy_url=self._proxy_url,
                                 proxy_port=self._proxy_port)
            else:
                params['itemType'] = 'file'
                params['async'] = False
                res = self._post(url=url,
                                 param_dict=params,
                                 files=files,
                                 securityHandler=self._securityHandler,
                                 proxy_url=self._proxy_url,
                                 proxy_port=self._proxy_port)
        if (isinstance(res, dict) and \
                        "id" not in res):
            raise Exception("Cannot add the item: %s" % res)
        elif (isinstance(res, (UserItem, Item)) and \
                          res.id is None):
            raise Exception("Cannot add the item: %s" % str(res))
        elif isinstance(res, (UserItem, Item)):
            return res
        else:
            itemId = res['id']
            return UserItem(url="%s/items/%s" % (self.location, itemId),
                            securityHandler=self._securityHandler,
                            proxy_url=self._proxy_url,
                            proxy_port=self._proxy_port)
