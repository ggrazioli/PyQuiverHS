from ase import io
from flask import Flask, render_template, request, send_file

import datetime
import os
import time
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import sys
import zipfile

matplotlib.use('Agg')

app = Flask(__name__)

VALID_EXTENSIONS = {
    'config_file': ['.config'],
    'file1': ['.out', '.log'],
    'file2': ['.out', '.log'],
}

# This function generates a session folder with the appropriate time
def generate_session() -> str:
    folder_name = os.path.join('sessions', 'session_' + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

# Load the main page
@app.route('/')
def home():
    return render_template('mainMenu.html')

# Load the KIE Calculation page
@app.route('/kie', methods=['GET'])
def kie():
    return render_template('kie_AL.html')           # for AL use only

@app.route('/calculate_kie', methods=['POST'])
def calculate_kie():

    original_cwd = os.getcwd()
    temperature = request.form.get('temperature').split(',')
    temp_increment = request.form.get('temp_increment')
    symmetry_number = request.form.get('symmetry_number')
    scaling_factor = request.form.get('scaling_factor')

    if len(temperature) == 1:
        temperature.append(temperature[0])
        temp_increment = 1
    start_temp = float(temperature[0])
    final_temp = float(temperature[1])

    SESSION_FOLDER = generate_session()
    app.config['SESSION_FOLDER'] = SESSION_FOLDER
    
    # Handling file uploads
    config_file = request.files.get('config_file')
    ground_state_file = request.files.get('ground_state_file')
    transition_state_file = request.files.get('transition_state_file')

    # Save uploaded files if they exist
    if config_file:
        config_path = os.path.join(app.config['SESSION_FOLDER'], 'my.config')
        config_file.save(config_path)

    if ground_state_file:
        ground_state_path = os.path.join(app.config['SESSION_FOLDER'], 'gs.out')
        ground_state_file.save(ground_state_path)

    if transition_state_file:
        transition_state_path = os.path.join(app.config['SESSION_FOLDER'], 'ts.out')
        transition_state_file.save(transition_state_path)

    while start_temp <= final_temp:
        output_file_path = os.path.join(app.config['SESSION_FOLDER'], f'output_{start_temp}.txt')

        command = f"{sys.executable} {os.path.join('PyQuiver', 'src', 'quiver_AL.py')} -v {config_path} {ground_state_path} {transition_state_path} {start_temp} {output_file_path}"
        os.system(command)
        start_temp += float(temp_increment)
        # os.system('clear')
        
        timeout = 5  # seconds
        start_time = time.time()
        while not os.path.exists(output_file_path):
            if time.time() - start_time > timeout:
                return "File not found", 404  # Timeout exceeded
            time.sleep(0.1)  # Small delay to check again
    


    #-- create zip folder for outputs (.txt, .csv, and plots)
    zip_path = os.path.join(app.config['SESSION_FOLDER'], 'outputs.zip')

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        start_temp = float(temperature[0])      # reset starting temperature
        while start_temp <= final_temp:
            output_file_path = os.path.join(app.config['SESSION_FOLDER'], f'output_{start_temp}.txt')
            if os.path.exists(output_file_path):
                zipf.write(output_file_path, os.path.basename(output_file_path)) 
            start_temp += float(temp_increment)


    #-- process .txt files and prepare dataframe
    kie_data = {}

    column_names = ['Isotopologue', 'Temperature', 'Uncorrected', 'Wigner', 'Bell', 'Enthalpy', 'Entropy']
    df = pd.DataFrame(columns=column_names)

    start_temp = float(temperature[0])  # reset temperature to start
    while start_temp <= final_temp: 
        output_file_path = os.path.join(app.config['SESSION_FOLDER'], f'output_{start_temp}.txt')
        
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as f:
                lines = f.readlines()

            for line in lines[5:]:      # skip 5-line header
                line_components = line.strip().split()

                if "referenced" in line_components or len(line_components) < 5:
                    continue                # skip any lines discussing reference isotopologue or any irrelevant lines 

                isotopologue_name = line_components[1]
                all_values = list(map(float, line_components[2:7]))     # temporary?
                kie_values = list(map(float, line_components[2:5]))

                if isotopologue_name not in kie_data:
                    kie_data[isotopologue_name] = {"temperature": [], "kies": []}

                if start_temp not in kie_data[isotopologue_name]['temperature']:
                    kie_data[isotopologue_name]['temperature'].append(start_temp)

                kie_data[isotopologue_name]['kies'].append(kie_values)


                df.loc[len(df)] = [isotopologue_name, start_temp] + all_values

        start_temp += float(temp_increment)

    df.to_csv(app.config['SESSION_FOLDER'] + "/full_output.csv", index=False)
    csv_path = os.path.join(app.config['SESSION_FOLDER'], 'full_output.csv')

    #-- generate plots (uncorrected, Wigner, Bell)
    plot_paths = []

    for isotopologue_name, data in kie_data.items():
        plt.figure()
        plt.xlabel("Temperature (K)")
        plt.ylabel("KIE Value")
        plt.title(f"KIE Plot for {isotopologue_name}")

        kie_labels = ['Uncorrected KIE', 'Wigner KIE', 'Bell KIE']

        for i, kie_label in enumerate(kie_labels):
            plt.plot(data['temperature'], [kie_list[i] for kie_list in data['kies']], marker = '.', label = kie_label)

        plt.legend()

        plot_path = os.path.join(app.config['SESSION_FOLDER'], f'plot_{isotopologue_name}.png')
        plt.savefig(plot_path)
        plot_paths.append(plot_path)
        plt.close()

    with zipfile.ZipFile(zip_path, 'a') as zipf:
        for plot_path in plot_paths:
            plot_filename = os.path.basename(plot_path)
            zipf.write(plot_path, os.path.join('plots', plot_filename))

        zipf.write(csv_path, os.path.basename(csv_path))

    return send_file(os.path.join(original_cwd, SESSION_FOLDER, 'outputs.zip'), mimetype="application/zip", as_attachment=True, download_name="outputs.zip")

# Load the EIE page
@app.route('/eie')
def eie():
    return render_template('eie.html')


# Load the config generator page
@app.route('/config', methods=['GET'])
def config():
    return render_template('config.html')

# Generate the config file
@app.route('/generate_config', methods=['POST'])
def generate_config():

    original_cwd = os.getcwd()

    temperature = request.form.get("temperature")
    imag_threshold = request.form.get("imag_threshold")
    scaling = request.form.get("scaling")
    
    isotopomers = request.form.getlist("isotopomers[]")
    # Ensure at least one isotopomer is recieved
    if not isotopomers or all(obj.strip() == "" for obj in isotopomers):
        return "You must enter at least one isotopomer.", 400
    
    # Generate a session folder
    SESSION_FOLDER = generate_session()

    # Open a new file
    f = open(os.path.join(SESSION_FOLDER, "autogenerated.config"), "w")


    f.write("### THIS FILE HAS BEEN AUTOMATICALLY GENERATED ###\n\n\n")

    # scaling
    f.write("# scaling factor for frequencies\n")
    f.write(f"scaling {scaling}\n\n")

    # imaginary threshold
    f.write("# imaginaries less than this value in i*cm-1 will be ignored for the transition mode\n")
    f.write(f"imag_threshold {imag_threshold}\n\n")

    # temperature
    f.write("# temperature in K\n")
    f.write(f"temperature {temperature}\n\n")

    # TODO Implement this
    # light isotopomer mass replacement
    f.write("# specifies the masses used for the light isotopomer\n")
    f.write(f"mass_override_isotopologue {'default'}\n\n")

    # TODO Implement this
    # reference isotopomer
    f.write("#all KIEs will be divided by the KIE at this position\n")
    f.write(f"reference_isotopomer {'none'}\n\n")

    f.write("# define the isotopomers\n")
    for isotopomer in isotopomers:
        f.write(f"isotopomer {isotopomer}\n")
    f.write("\n\n\n")

    f.write("### END OF THE FILE ###")
    f.close()

    return send_file(os.path.join(original_cwd, SESSION_FOLDER, 'autogenerated.config'), mimetype="text/plain", as_attachment=True, download_name="autogenerated.config")

# Molecule Viewer
def extract_structure(file_path):
    try:
        atoms = io.read(file_path, format='gaussian-out')
        num_atoms = len(atoms)

        # Convert to standard XYZ format (atom count + title + coordinates)
        xyz_data = f"{num_atoms}\nMolecule from Gaussian Log\n" + "\n".join(
            f"{atom.symbol} {atom.position[0]:.6f} {atom.position[1]:.6f} {atom.position[2]:.6f}"
            for atom in atoms
        )
        return xyz_data

    except Exception as e:
        print(f"Error reading file: {e}")
        return "Error reading molecular structure."

@app.route('/view_molecule', methods=['GET', 'POST'])
def view_molecule():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_path = os.path.join(generate_session(), 'molecule.out')
            uploaded_file.save(file_path)
            xyz_data = extract_structure(file_path)
        return render_template('view_molecule_active.html', xyz_data=xyz_data)
    elif request.method == 'GET':
        return render_template('view_molecule_form.html')

        
app.run()