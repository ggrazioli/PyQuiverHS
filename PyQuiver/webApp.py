from flask import Flask, render_template, request

app = Flask(__name__)

VALID_EXTENSIONS = {
    'config_file': ['.config'],
    'file1': ['.out', '.log'],
    'file2': ['.out', '.log'],
}

@app.route('/')
def home():
    return render_template('mainMenu.html')

@app.route('/kie')
def kie():
    return render_template('kie.html')

@app.route('/eie')
def eie():
    return render_template('eie.html')

@app.route('/validate_data', methods=['POST'])
def validate_data():
    # case 1: any one of the files is not selected and uploaded
    if 'config_file' not in request.files or 'file1' not in request.files or 'file2' not in request.files:
        return "Missing file", 400
    
    files = {
        'config_file': request.files['config_file'],
        'file1': request.files['file1'], 
        'file2': request.files['file2']
    }

    for key, file in files.items():
        # case 2: dialog to select file comes up, but nothing is uploaded
        if file.filename == '':
            return f"No selected file for {key}", 400
        
        # case 3: invalid file format uploaded
        if not any(file.filename.endswith(ext) for ext in VALID_EXTENSIONS[key]):
            return f"Invalid file format for {key}. Expected one of {VALID_EXTENSIONS[key]}"

    return "Files uploaded successfully!", 200



app.run()