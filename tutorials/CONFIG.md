# CONFIGURATION FILE GENERATOR
In this tutorial, we will generate the configuration file used in the KIE tutorial.
1. Select the desired temperature. Note that the temperature indicated during the EIE or KIE calculation _will_ replace this temperature.
2. Select an imaginary threshold. If left unchanged, the program will automatically choose 50 as its default value.  
3. Select a scaling factor for the frequencies. If left unchanged, the program will automatically choose 1 as its default value.
4. Choose the isotopic desired isotopic exchanges, seperate each section with a sinlge space:
    1. Select a label; the label can be any name. If two isotopic exchanges are desired, ensure that both isotopomer share the same label (third picture).
    2. Select the ground state/reactant atom number; the molecular viewer provieds both a 3D picture and the atom numbers.
    3. Select the transition state/product atom number.
    4. Select the Isotope to be replaced; choose from the list provided.
5. Press "Calculate!"
![CONFIG PAGE](../pics/config.png)
If done correctly, your output will look similar to ![SAMPLE CONFIG](../pics/config_example.png)

For the case of mutiple isotopic substituion, indicate all isotopomer with the same label:
![MULTI SUBSTITUTION](../pics/multiconfig.png)

## Possible replacements
### Hydrogen
* Protium: 1H
* Deuterium: 2D
* Tritium: 3T
### Carbon
* Carbon 12: 12C
* Carbon 13: 13C
* Carbon 14: 14C
### Nitrogen
* Nitrogen 14: 14N
* Nitrogen 15: 15N
### Oxygen
* Oxygen 16: 16O
* Oxygen 17: 17O
* Oxygen 18: 18O
### Fluorine
* Fluorine 18: 18F
* Fluorine 19: 19F