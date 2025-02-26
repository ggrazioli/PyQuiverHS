# ADDED JUST IN CASE
# This calculates EIEs based on the Bigeleisen-Mayer equation.
import numpy as np
#from quiver import System, Isotopologue, DEBUG
import pandas as pd
import quiver
import settings
from file_writer import FileWriter
from config import Config
from constants import DEFAULT_MASSES
from collections import OrderedDict

from constants import PHYSICAL_CONSTANTS, REPLACEMENTS
h  = PHYSICAL_CONSTANTS["h"]  # in J . s
c  = PHYSICAL_CONSTANTS["c"]  # in cm . s
rJ = PHYSICAL_CONSTANTS["rJ"]
rCal = PHYSICAL_CONSTANTS["rCal"]
r = PHYSICAL_CONSTANTS["r"]
kB = PHYSICAL_CONSTANTS["kB"] # in J/K
kcalToJ = PHYSICAL_CONSTANTS["kcalToJ"]

class EIE_Calculation(object):
    def __init__(self, config, react, prod, temperature, path, style="g90"):
        if type(config) is str:
            self.config = Config(config)
        elif type(config) is Config:
            self.config = Config
        else:
            raise TypeError("config argument must be either a filepath or Config object.")
        
        self.path = path


        if type(react) is str:
            self.react_system = quiver.System(react, style=style)
        elif type(gs) is quiver.System:
            self.react_system = react
        else:
            raise TypeError("gs argument must be either a filepath or quiver.System object.")

        if type(prod) is str:
            self.prod_system = quiver.System(prod, style=style)
        elif type(prod) is quiver.System:
            self.prod_system = prod
        else:
            raise TypeError("ts argument must be either a filepath or quiver.System object.")
        
        print(vars(self.react_system))
        print('and')
        print(vars(self.prod_system))

        # ;;;;JUST IN CASE;;;;;
        # self.eie_flag = 1

        if settings.DEBUG != 0:
            print(self.config)
        
        EIES = OrderedDict()

        if self.config.frequency_threshold:
            print("WARNING: config file uses the frequency_threshold parameter. This has been deprecated and low frequencies are dropped by linearity detection.")
        
        for p in self.make_isotopologues():
            react_tuple, prod_tuple, prod_mass = p
            name = react_tuple[1].name
            eie = EIE(name, react_tuple, prod_tuple, temperature, path, self.config.scaling, self.config.imag_threshold, prod_mass)
            EIES[name] = eie
        
        for name,e in EIES.items():
            if name != self.config.reference_isotopologue:
                if self.config.reference_isotopologue != "default" and self.config.reference_isotopologue != "none":
                    e.apply_reference(EIES[self.config.reference_isotopologue])

        self.EIES = EIES

    def get_row(self, report_tunnelling=False):
        title_row = ""
        row = ""
        keys = list()
        for key in self.EIES:
            keys.append(key)
    