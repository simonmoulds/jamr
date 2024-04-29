#!/usr/bin/env python3


import tomllib


class Configuration:
    def __init__(self, configfile):

        self.configfile = configfile

        with open(configfile, "rb") as f:
            config_dict = tomllib.load(f)

    def landfraction(self):
        pass

    def topography(self):
        pass

    def landcover(self):
        pass

    def soil(self):
        pass
