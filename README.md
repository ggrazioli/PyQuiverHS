# Welcome to PyQuiverHS
## INTRODUCTION
![picture of main menu](pics/main_menu.png)
*PyQuiverHS is a user friendly web app based on PyQuiver for calculating isotope effects. The best way to use PyQuiverHS is through our web app, which is free to use here:*

https://www.isotope-effects.com/ 

PyQuiverHS is an open-source web-based application to calculate Kinetic Isotope Effects (KIE) and Equilibrium Isotope Effects (EIE) using harmonic frequencies and both the Bigeleisen-Mayer (B-M) formalism and a thermodynamic approach that partitions isotope effects into their enthalpic and entropic (H-S) components. Additionally, this program directly calculates and displays the component of each approach separately. PyQuiverHS is based on PyQuiver, which requires Cartesian Hessian matrices that can be calculated using any electronic structure program.


## FEATURES
- Automatically read frequencies from [`Gaussian`](http://www.gaussian.com/g_prod/g09.htm) output files.
- Ability to view the molecules from the generated Gaussian files.
- Two separate methods for computing the isotope effects:
    - Thermodynamic enthalpy-entropy approach (H-S)
    - Bigeleisen-Mayer formalism (B-M)
- Ability to view and compare the component contributions for each approach, including:
    - Zero-point energy contributions to enthalpy (H_ZPE) for H-S
    - Vibrational contributions to enthalpy (H_VIB) for H-S
    - Total thermal vibrational contributions to enthalpy (H_ZPE * H_VIB = H_TOT) for H-S
    - Vibrational contributions to entropy (S_VIB) for H-S
    - Rotational contributions to entropy (S_ROT) for H-S
    - Total contributions to entropy (S_VIB * S_ROT = S_TOT) for H-S
    - Total free energy contributions to isotope effect (H_TOT * S_TOT = G_TOT = HS) for H-S
    - Mass and moment of inertia (MMI) factor for B-M
    - Zero-point energy (ZPE) factor for B-M
    - Excitation (EXC) factor for B-M
    - Total contributions to isotope effect (MMI * ZPE * EXC = BM) for B-M
- Ability to rapidly calculate temperature ranges with custom increments. 
- Simple and accessible output file formats, such .csv and .txt
- Automatically generated plots for temperature ranges.

## TUTORIALS
To learn how to use this program, please see the tutorial:
https://www.isotope-effects.com/tutorials

## FURTHER READING
## AUTHORS
## HOW TO CITE
## LICENSE