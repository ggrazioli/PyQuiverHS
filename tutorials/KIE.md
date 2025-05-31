# KIE TUTORIAL
In this tutorial, we will reproduce Amide bond rotation in formamide shown below:

| ![Ground State](../pics/KIE_ground_state.png) | ![Transition State](../pics/KIE_transition_state.png) |
|-----------------------------------------------|-------------------------------------------------------|
| Ground State                                  | Transition State                                      |



First, generate the configuration file through the Configuration File Generator. For a guide, please look at [config file tutorial](CONFIG.md).

After generating the configuration file, along with obtaining the Gaussian files for both the ground state and transition state*: 
1. Head to the KIE page
2. Upload the files in the designated sections.
3. Enter the  desired Temperature in kelvin. If a range of temperature is desired, simply enter the beginning and the end:
    * Single temperature: 298.15
    * Range of temperatures: 250, 350
4. (optional) set the increment value for temperature range.
5. Press calculate!
 ![KIE PAGE](../pics/kie.png)

Once done, you will recieve a zip file that includes a text file for each temperature in the temperature range, a csv file that includes all of the calculations, and a plot for the temperature range. Below is a an example of the calculation done using the provided gaussian files, and already generated configuration file for temperature range of 273.15K to 298.15K, with increments of 1K.
![KIE EXAMPLE FOLDER](../pics/kie_output_folder.png)
![KIE EXAMPLE CSV](../pics/kie_output.png)
![KIE PLOT](../pics/plot.png)

