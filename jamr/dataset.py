#!/usr/bin/env python3

import os
import re
import glob

from abc import ABC, abstractmethod

from jamr.utils import grass_remove_mask, grass_set_named_region


class DS:
    def __init__(self, 
                 config: dict, 
                 overwrite: bool) -> None:
        self.config = config 
        self.overwrite = overwrite 
        self.filenames = None 
        self.preprocessed_filenames = None
        self.mapnames = None
        self.get_input_filenames()
        self.set_mapnames()

    @abstractmethod    
    def initial(self):
        pass

    @abstractmethod
    def get_input_filenames(self):
        pass 

    @abstractmethod
    def set_mapnames(self):
        pass

    def get_input_filenames_as_list(self):
        pass 

    def set_mapnames_as_list(self):
        pass 

    def preprocess(self):
        self.preprocessed_filenames = self.filenames

    @abstractmethod
    def read(self):
        pass 


class MFDS(DS):
    def __init__(self, config, overwrite):
        super().__init__(config, overwrite)


class SFDS(DS):
    @property 
    def filename(self):
        return self.filenames[0] if isinstance(self.filenames, list) else self.filenames

    @property 
    def mapname(self):
        return self.mapnames[0] if isinstance(self.mapnames, list) else self.mapnames 

    @property 
    def preprocessed_filename(self):
        return self.preprocessed_filenames[0] if isinstance(self.preprocessed_filenames, list) else self.preprocessed_filenames
    

class AncillaryDataset:
    def __init__(self, 
                 config: dict,
                 region: str, 
                 overwrite: bool) -> None:
        self.config = config 
        self.region = region 
        self.overwrite = overwrite 
        grass_remove_mask()
        grass_set_named_region(self.region)

    @abstractmethod 
    def compute(self):
        pass