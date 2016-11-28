from EagleBaseTool import EagleBaseTool
from AssetUpdateHelper import AssetUpdateHelper

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "CPTB Toolbox"
        self.alias = "CPTB Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [UpdateFeatures,UpdateAreas]


class UpdateFeatures(EagleBaseTool):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        super(UpdateFeatures, self).__init__()
        self.label = "Update Features"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        self.message("bag of dicks","info")
        try:
            self.message("Log file: "+self.log_location,"info")
            AssetUpdateHelper().execute_update_features_process()
        except Exception as e:
            self.message(e.message, "err")
        return

class UpdateAreas(EagleBaseTool):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        super(UpdateAreas, self).__init__()
        self.label = "Update Areas"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            self.message("Log file: "+self.log_location,"info")
            AssetUpdateHelper().execute_update_areas_process()
        except Exception as e:
            self.message(e.message,"err")
        return

#   DEBUG
# def main():
#     tbx = Toolbox()
#     tool = UpdateAreas()
#     param = tool.execute(tool.getParameterInfo(),None)
#     print param
#
# if __name__ == '__main__':
#     main()