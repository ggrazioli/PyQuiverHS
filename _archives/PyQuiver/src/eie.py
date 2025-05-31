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

## DS: importing shared functions from kie.py.
##     In the final version, remove _[initial] part of the file name

from kie_AL.py import calculate_rpfr

from constants import PHYSICAL_CONSTANTS, REPLACEMENTS
h  = PHYSICAL_CONSTANTS["h"]  # in J . s
c  = PHYSICAL_CONSTANTS["c"]  # in cm . s
rJ = PHYSICAL_CONSTANTS["rJ"]
rCal = PHYSICAL_CONSTANTS["rCal"]
r = PHYSICAL_CONSTANTS["r"]
kB = PHYSICAL_CONSTANTS["kB"] # in J/K
kcalToJ = PHYSICAL_CONSTANTS["kcalToJ"]

class EIE_Calculation(object):
    ## DS: what is g90 style and is it applicable to EIE calcualtions?
    def __init__(self, config, react, prod, temperature, path, style="g90") -> None:
        if type(config) is str:
            self.config = Config(config)
        elif type(config) is Config:
            self.config = Config
        else:
            raise TypeError("config argument must be either a filepath or Config object.")
        
        self.path = path


        if type(react) is str:
            self.react_system = quiver.System(react, style=style)
        elif type(react) is quiver.System:
            self.react_system = react
        else:
            raise TypeError("reactant argument must be either a filepath or quiver.System object.")

        if type(prod) is str:
            self.prod_system = quiver.System(prod, style=style)
        elif type(prod) is quiver.System:
            self.prod_system = prod
        else:
            raise TypeError("product argument must be either a filepath or quiver.System object.")
        
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
    
        if self.config.reference_isotopologue != "default" and self.config.reference_isotopologue != "none":
            keys.remove(self.config.reference_isotopologue)

        if self.config.mass_override_isotopologue != "default" and self.config.reference_isotopologue != "none":
            keys.remove(self.config.mass_override_isotopologue)

        for name in keys:
            if report_tunnelling:
                title_row += "%s,%s," % (name + "_uncorr", name + "_inf_para")
            else:
                title_row += "{0},".format(name)

            row += "{0:.4f},".format(self.KIES[name].value)
        
        return (title_row, row)

    def build_mass_override_masses(self):
        config = self.config
        react_system = self.react_system
        prod_system = self.prod_system

        react_masses = self.build_default_masses(react_system)
        prod_masses = self.build_default_masses(prod_system)

        if config.mass_override_isotopologue != "default":
            iso = self.config.isotopologues[config.mass_override_isotopologue]
            react_rules, prod_rules = self.compile_mass_rules(iso)

            react_masses = self.apply_mass_rules(react_masses, react_rules)
            prod_masses = self.apply_mass_rules(prod_masses, prod_rules)
        
        return react_masses, prod_masses


    def build_default_masses(self, system):
        masses = []
        #print "---start---"
        #for e in DEFAULT_MASSES:
        #    print e, DEFAULT_MASSES[e]
        #print "---"
        for i in range(system.number_of_atoms):
            #print i, system.atomic_numbers[i], DEFAULT_MASSES[system.atomic_numbers[i]]
            if not system.atomic_numbers[i] in DEFAULT_MASSES:
                raise ValueError("Default mass not available for atomic number %d at atom number %d in %s!" % (system.atomic_numbers[i], i+1, system.filename))
            masses.append(DEFAULT_MASSES[system.atomic_numbers[i]])
        #print "--end--"
        return np.array(masses)

    def apply_mass_rules(self, prev_masses, rules):
        masses = list(prev_masses)
        for e,v in rules.items():
            masses[e] = v
        return masses

    def compile_mass_rules(self, iso_rules):
        react_rules = {}
        prod_rules = {}
        for replacement in iso_rules:
            react_atom_number, prod_atom_number, replacement_label = replacement
            replacement_mass = REPLACEMENTS[replacement_label]
            react_rules[react_atom_number-1] = replacement_mass
            prod_rules[prod_atom_number-1] = replacement_mass
        print(f'And then we have prod_rules which is {prod_rules}')
        return react_rules, prod_rules

    def make_isotopologues(self):
        config = self.config
        react_system = self.react_system
        prod_system = self.prod_system
        config.check(react_system, prod_system)

        mass_override_react_masses, mass_override_prod_masses = self.build_mass_override_masses()

        default_react = quiver.Isotopologue("default", react_system, mass_override_react_masses)
        default_prod = quiver.Isotopologue("default", react_system, mass_override_prod_masses)

        for id_,iso in config.isotopologues.items():
            if id_ != config.mass_override_isotopologue:
                react_rules, prod_rules = self.compile_mass_rules(iso)
                react_masses = self.apply_mass_rules(mass_override_react_masses, react_rules)
                prod_masses = self.apply_mass_rules(mass_override_prod_masses, prod_rules)
                sub_react = quiver.Isotopologue(id_, react_system, react_masses)
                sub_prod = quiver.Isotopologue(id_, prod_system, prod_masses)
                yield ((default_react, sub_react), (default_react, sub_prod), prod_rules)

    def __str__(self):
        # print(self.eie_flag)
        string = "\n=== PyQuiver Analysis ===\n"
        string += "Isotopologue        Name                                   EIE"
        keys = list(self.EIES.keys())
        if self.config.reference_isotopologue != "default" and self.config.reference_isotopologue != "none":
            keys.remove(self.config.reference_isotopologue)
        if self.config.mass_override_isotopologue != "default":
            keys.remove(self.config.mass_override_isotopologue)
        #keys.sort()
        for name in keys:
            string += "\n" + str(self.EIES[name])

        if self.config.reference_isotopologue != "default" and self.config.reference_isotopologue != "none":
            string += "\n\nEIEs referenced to isotopologue {0}, whose absolute EIESs are:".format(self.config.reference_isotopologue)
            string += "\n" + str(self.EIES[self.config.reference_isotopologue])
        else:
            string += "\n\nAbsolute EIEs for all isotopologues are given."

        return string


class EIE(object):
    # the constructor expects a tuple of the form yielded by make_isotopologue
    def __init__(self, name, react_tuple, prod_tuple, temperature, path, scaling, imag_threshold, prod_mass):
        # copy fields
        # the associated calculation object useful for pulling config fields etc.
        # self.eie_flag = 0
        self.name = name
        self.imag_threshold = imag_threshold
        self.react_tuple, self.prod_tuple = react_tuple, prod_tuple
        self.temperature = temperature
        self.path = path
        self.scaling = scaling
        self.prod_mass = prod_mass

        if settings.DEBUG >= 2:
            print("Calculating EIE for isotopologue {0}.".format(name))
        self.value = self.calculate_eie()

        ## AL addition:
        ## DS Comment: calling this function in the intializaiton will cause the program to prematurely run the calculation. Is this the expected behaviour?
        # self.components = self.calculate_eie_components()

    def calculate_eie(self):
        # final_enth = self.components[0]
        # final_entr = self.components[1]

        components = self.calculate_eie_components()
        final_enth = components[0]
        final_entr = components[1]

        eie = final_enth * final_entr

        print(f'Final EIE is {eie}')

        return eie
    

    def calculate_eie_components(self):             ## AL: temporary addition -- streamline later by adding under calculate_eie?
        if settings.DEBUG >= 2:
            print("  Calculating Reduced Partition Function Ratio for Reactants.")
        enth_react_sums, entr_react_sums, rpfr_react, react_imag_ratios, react_heavy_freqs, react_light_freqs = calculate_rpfr(self, self.react_tuple, self.imag_threshold, self.scaling, self.temperature)
        if settings.DEBUG >= 2:
            print("    rpfr_react:", np.prod(rpfr_react))
        if settings.DEBUG >= 2:
            print("  Calculating Reduced Partition Function Ratio for Products.")

        enth_prod_sums, entr_prod_sums, rpfr_prod, prod_imag_ratios, prod_heavy_freqs, prod_light_freqs = calculate_rpfr(self, self.prod_tuple, self.imag_threshold, self.scaling, self.temperature)
        if settings.DEBUG >= 2:
            print("    rpfr_prod:", np.prod(rpfr_prod))

        final_enth_sum = enth_prod_sums - enth_react_sums
        final_enth_zpe = np.exp(final_enth_sum[0]/(r*self.temperature))
        final_enth_vib = np.exp(final_enth_sum[1]/(r*self.temperature))
        final_enth = final_enth_zpe * final_enth_vib

        final_entr_sum = entr_prod_sums - entr_react_sums
        final_entr_vib = np.exp(final_entr_sum[0]/rCal)
        final_entr_rot = np.exp(final_entr_sum[1]/rCal)
        final_entr = final_entr_vib * final_entr_rot

        return (final_enth, final_entr)
    

    def apply_reference(self, reference_eie):
        # print('self.value before:', self.value)
        # print('reference_eie used:', reference_eie.value)
        self.value /= reference_eie.value
        # print('self.value after:', self.value)
        return self.value

    def __str__(self):
        if self.value is not None:
            # if self.eie_flag == 1:
            return "Isotopologue {1: >10s} {0: >33s} {2: ^12.8f} ".format("", self.name, self.value)
        else:
            "EIE Object for isotopomer {0}. No value has been calculated yet.".format(self.name)
