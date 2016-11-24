import time
from Config import Config

class Decorator(object):
    config = Config()

    @classmethod
    def function_timer(cls,func):
        def _function_timer(*args,**kwargs):
            start = time.time()
            cls.config.log.do_message("Executing Function {0}".format(str(func.__name__)),"debug")
            res = func(*args,**kwargs)
            stop = time.time()
            cls.config.log.do_message("Function {0} took {1}".format(str(func.__name__),str(stop-start)),"debug")
            print "Function {0} took {1}".format(str(func.__name__),str(stop-start))
            return res
        return _function_timer

    @classmethod
    def method_call_log(cls,func):
        def _function_call_log(*args, **kwargs):
            cls.config.log.do_message("=============> Executing Function {0}".format(str(func.__name__)), "debug")
            res = func(*args, **kwargs)
            cls.config.log.do_message("=============> End Function {0}".format(str(func.__name__)), "debug")
            return res
        return _function_call_log
