import json
import inspect
import os
from Borg import Borg
from Log import Log

class Config(Borg):
    """
    Class to handle application configuration.
    Follows a singleton pattern - all instances of Config will share
    the same variable dictionary
    """
    def __init__(self,a_file=None):
        Borg.__init__(self)
        if not hasattr(self,'_file'):
            try:

                if a_file is None:
                    a_file = inspect.getframeinfo(inspect.currentframe())[0]
                    self._file = os.path.join(os.path.split(a_file)[0],os.path.splitext(os.path.split(a_file)[1])[0]+'.json')
                    self.__mixin_config(self._file)
                elif a_file is not None:
                    #mixin config
                    self.__mixin_config(a_file)
            except Exception as err:
                raise RuntimeError("Cannot load application configuration")
        elif a_file is not None:
            # mixin config
            self.__mixin_config(a_file)

    def __mixin_config(self,a_file):
        try:
            json_data = open(a_file)
            config = json.load(json_data)
            json_data.close()
            self._shared_state.update(config)
            if not hasattr(self,"log"):
                self.__initialise_loging__()
            self.log.do_message("Config loaded from:" + json_data.name, "debug")
        except Exception as err:
            self.log.do_message("Cannot load application configuration","err")
            raise RuntimeError("Cannot load application configuration")

    def __setattr__(self,name,value):
        """Override fuction to ensure read only of config objects """
        if  name in self._shared_state:
            raise AttributeError(name+ ' attribute is read only')
        else:
            Borg.__setattr__(self, name, value)

    def __str__(self):
        return self._file

    def __initialise_loging__(self):
        """
        Check to see if logging has been set
        """
        if hasattr(self,'logging'):
            # redirect = self.logging['redirectallouput'] == "true"
            loc = self.logging['loglocation'] if 'loglocation' in self.logging else None
            if self.logging['logtofile'] == "true":
                self.log = Log(self.logging['loglevel'],True,loc)
            else:
                self.log = Log(self.logging['loglevel'],False)
        else:
            self.log = Log("error")

        self.log.do_message('Log created app ready')

    # def __del__(self):
    #     if hasattr(self,"log"):
    #         self.log.close_log()

    def config_has_attribute(self,atts=[],obj=None):
        if atts == []:
            return True
        obj = self if not obj else obj
        for an_att in atts:
            if an_att in obj:
                return True + self.config_has_attribute()
            else:
                return False