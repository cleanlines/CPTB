# Project: CPTB 
# File: AbstractUpdateHelper.py
# Created: 14/11/2016 3:35 PM
# Author: FS Hand

from abc import ABCMeta, abstractmethod

class AbstractUpdateHelper(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def update_features(self):
        raise NotImplementedError()

