from flask import Flask, render_template, request, send_file
import datetime
import os
import time
import subprocess
import sys

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
    return render_template('kie.html')

@app.route('/calculate_kie', methods=['POST'])
def calculate_kie():

    original_cwd = os.getcwd()
    temperature = request.form.get('temperature')
    temp_increment = request.form.get('temp_increment')
    symmetry_number = request.form.get('symmetry_number')
    scaling_factor = request.form.get('scaling_factor')

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

    output_file_path = os.path.join(app.config['SESSION_FOLDER'], 'output.txt')

    command = f"{sys.executable} PyQuiver/src/quiver_AL.py -v {config_path} {ground_state_path} {transition_state_path} {temperature} {output_file_path}"
    os.system(command)
    # os.system('clear')
    
    timeout = 5  # seconds
    start_time = time.time()
    while not os.path.exists(output_file_path):
        if time.time() - start_time > timeout:
            return "File not found", 404  # Timeout exceeded
        time.sleep(0.1)  # Small delay to check again
    
    return send_file(os.path.join(original_cwd, SESSION_FOLDER, 'output.txt'), mimetype="text/plain", as_attachment=True, download_name="output.txt")

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
    ...


app.run()