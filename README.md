# Welcome to QuiverHS
## INTRODUCTION
![picture of main menu](pics/main_menu.png)
*QuiverHS is a user friendly web app based on PyQuiver for calculating isotopic effects.*

QuiverHS is an open-source web-based application to calculate Kinetic Isotopic Effects (KIE) and Equilibrium Isotopic Effects (EIE) using harmonic frequencies, both Bigeleisen-Mayer equation, and thermodynamic approach. Additionally, this program directly calculates and displays the component of each approach seperately. QuiverHS is based on PyQuiver, which requires Cartesian Hessian matrices, which itself can be calculated using any electronic structure program.


## FEATURES
- Automatically read frequencies from [`Gaussian`](http://www.gaussian.com/g_prod/g09.htm) output files.
- Ability to view the molecules from the generated Gaussian files.
- Two seperate methods for computing the Isotopic effects:
    - Thermodynamic approach
    - Bigeleisen-Mayer formalism
- Ability to view and compare the componenet of each approach, including:
    - Rotational contributions to entropy
    - Vibrational contributions to entropy
    - Vibrational contributions to enthalpy
    - Zero-point energy contributions to enthalpy
    - Zero-point energy factor for B-M
    - Approximate MMI factor for B-M
    - Exciation factor for B-M
- Ability to rapidly calculate temperature ranges with custom increments. 
- Simple and accessible output file formats, such .csv and .txt
- Automatically generated plots for temperature ranges.

## TUTORIALS
To learn how to use this program, please look at the [tutorial](tutorials/TUTORIAL.md)

## FURTHER READING
## AUTHORS
## HOW TO CITE
## LICENSE