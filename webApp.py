# Standard python libraries
import datetime
import os
import time
import subprocess
import sys
import zipfile
import shutil

from auth import auth_bp
from extensions import db, login_manager
from models import User

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import db, login_manager, limiter, mail

# 3rd party Libriaries   
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    send_from_directory,
    abort,
    after_this_request,
)
from flask_login import login_user, logout_user, current_user, login_required
from ase import io
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

VALID_EXTENSIONS = {
    "config_file": [".config"],
    "file1": [".out", ".log"],
    "file2": [".out", ".log"],
}

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get(
    "SECURITY_PASSWORD_SALT", "dev-salt"
)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("EMAIL_USER")

mail.init_app(app)


# Define some important file paths:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
quiver_path = os.path.join(BASE_DIR, "src", "quiver.py")
MAX_TIME = 30 # seconds before calculation times out
PYTHON_EXECUTABLE = os.environ.get("PYTHON_EXECUTABLE", sys.executable)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()

# Old function to generate a session folder with the appropriate time, delete later
# def generate_session() -> str:
#     folder_name = os.path.join(
#         "sessions", "session_" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
#     )
#     os.makedirs(folder_name, exist_ok=True)
#     return folder_name

# This function generates a session folder with the appropriate time
def generate_session() -> str:
    folder_name = os.path.join(
        BASE_DIR,
        "sessions",
        "session_" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    )
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

# Load the landing page
@app.route("/")
def landing():
    return render_template("landing.html")

# Load the main app page
@app.route("/app")
@login_required
def home():
    return render_template("mainMenu.html")

# Load the citation page
@app.route("/citation")
def citation():
    return render_template("citation.html")

# Load the KIE Calculation page
@app.route("/kie", methods=["GET", "POST"])
@login_required
def kie():
    if request.method == "GET":
        return render_template("kie.html")
    elif request.method == "POST":
        original_cwd = os.getcwd()
        temperature = request.form.get("temperature").split(",")  # added .split(',')
        temp_increment = request.form.get("temp_increment")

        # for case where only one temp is given
        if len(temperature) == 1:
            temperature.append(temperature[0])
            temp_increment = 1

        start_temp = float(temperature[0])
        final_temp = float(temperature[1])

        SESSION_FOLDER = generate_session()
        app.config["SESSION_FOLDER"] = SESSION_FOLDER

        @after_this_request
        def cleanup(response):
            shutil.rmtree(SESSION_FOLDER, ignore_errors=True)
            return response

        # Handling file uploads
        config_file = request.files.get("config_file")
        ground_state_file = request.files.get("ground_state_file")
        transition_state_file = request.files.get("transition_state_file")

        # Save uploaded files if they exist
        if config_file:
            config_path = os.path.join(app.config["SESSION_FOLDER"], "my.config")
            config_file.save(config_path)

        if ground_state_file:
            ground_state_path = os.path.join(app.config["SESSION_FOLDER"], "gs.out")
            ground_state_file.save(ground_state_path)

        if transition_state_file:
            transition_state_path = os.path.join(app.config["SESSION_FOLDER"], "ts.out")
            transition_state_file.save(transition_state_path)

        # added while loop, looping over temperature range to produce .txt files for each temp
        while start_temp <= final_temp:
            output_file_path = os.path.join(
                app.config["SESSION_FOLDER"], f"output_{start_temp}.txt"
            )
            # Old way to create command, delete later
            # command = f"{sys.executable} {os.path.join('src', 'quiver.py')} {config_path} {ground_state_path} {transition_state_path} {start_temp} {output_file_path}"
            command = (
                f'"{sys.executable}" '
                f'"{quiver_path}" '
                f'"{config_path}" '
                f'"{ground_state_path}" '
                f'"{transition_state_path}" '
                f'{start_temp} '
                f'"{output_file_path}"'
            )
            # old way to call the command:
            # os.system(command)
            # more server-friendly way to call command: 
            # result = subprocess.run(
            #     command,
            #     shell=True,
            #     cwd=BASE_DIR,
            #     capture_output=True,
            #     text=True,
            # )

            result = subprocess.run(
                [
                    PYTHON_EXECUTABLE,
                    quiver_path,
                    config_path,
                    ground_state_path,
                    transition_state_path,
                    str(start_temp),
                    output_file_path,
                ],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
            )

            print("COMMAND:", command, flush=True)
            print("STDOUT:", result.stdout, flush=True)
            print("STDERR:", result.stderr, flush=True)
            print("RETURN CODE:", result.returncode, flush=True)

            # if result.returncode != 0:
            #     return f"Calculation failed:<br><pre>{result.stderr}</pre>", 500
            # More informative error message:
            if result.returncode != 0:
                return f"""
                <h2>Calculation failed</h2>
                <h3>Args</h3>
                <pre>{result.args}</pre>
                <h3>STDOUT</h3>
                <pre>{result.stdout}</pre>
                <h3>STDERR</h3>
                <pre>{result.stderr}</pre>
                <h3>Return code</h3>
                <pre>{result.returncode}</pre>
                """, 500

            start_temp += float(temp_increment)
            # os.system('clear')

            timeout = MAX_TIME  # seconds
            start_time = time.time()
            while not os.path.exists(output_file_path):
                if time.time() - start_time > timeout:
                    return "File not found", 404  # Timeout exceeded
                time.sleep(0.1)  # Small delay to check again

        # -- create zip folder for outputs (.txt, .csv, and plots)
        zip_path = os.path.join(app.config["SESSION_FOLDER"], "outputs.zip")

        with zipfile.ZipFile(zip_path, "w") as zipf:
            start_temp = float(temperature[0])  # reset starting temperature
            while start_temp <= final_temp:
                output_file_path = os.path.join(
                    app.config["SESSION_FOLDER"], f"output_{start_temp}.txt"
                )
                if os.path.exists(output_file_path):
                    zipf.write(output_file_path, os.path.basename(output_file_path))
                start_temp += float(temp_increment)

        # -- process .txt files and prepare dataframe
        kie_data = {}

        # column_names = [
        #     "Isotopologue",
        #     "Temperature",
        #     "Uncorrected (TH) KIE",
        #     "Uncorrected (BM) KIE",
        #     "Wigner (TH) KIE",
        #     "Wigner (BM) KIE",
        #     "Bell (TH) KIE",
        #     "Bell (BM) KIE",
        #     "Enthalpy",
        #     "Entropy",
        #     "H_ZPE",
        #     "H_VIB",
        #     "S_VIB",
        #     "S_ROT",
        #     "MMI",
        #     "EXC",
        #     "ZPE"
        # ]
        column_names = [
            "Isotopologue",
            "Temperature",
            "BM MMI",
            "BM ZPE",
            "BM EXC",
            "BM (total)",
            "HS H_ZPE",
            "HS H_VIB",
            "HS H_TOT",
            "HS S_VIB",
            "HS S_ROT",
            "HS S_TOT",
            "HS (total)",
            "BM (total-Wigner)",
            "HS (total-Wigner)",
            "BM (total-Bell)",
            "HS (total-Bell)"
        ]
        
        df = pd.DataFrame(columns=column_names)

        start_temp = float(
            temperature[0]
        )  # reset temperature to start to begin iterating again
        while start_temp <= final_temp:
            output_file_path = os.path.join(
                app.config["SESSION_FOLDER"], f"output_{start_temp}.txt"
            )

            if os.path.exists(output_file_path):
                with open(output_file_path, "r") as f:
                    lines = f.readlines()

                # for line in lines[5:]:  # skip 5-line header (this was when we had KIE in a second row for the column header)
                for line in lines[4:]:  # skip 4-line header
                    line_components = line.strip().split()

                    # if "KIEs" in line_components or len(line_components) < 5:
                    #     continue  
                    # skip any lines discussing reference/absolute isotopologue or any irrelevant lines
                    if (
                        "KIEs" in line_components
                        or len(line_components) < 5
                        or line_components[0].startswith("WARNING")
                        or line_components[0].startswith("===")
                    ):
                        continue

                    isotopologue_name = line_components[1]
                    all_values = list(
                        map(float, line_components[2:])
                    ) 

                    expected_num_values = 15

                    if len(all_values) < expected_num_values:
                        return f"""
                        <h2>Calculation failed</h2>
                        <p>
                            The calculation output did not contain all expected KIE values.
                            This often happens when the imaginary frequency threshold is larger 
                            than the magnitude of the true transition state imaginary frequency.
                        </p>
                        <p>
                            Please inspect your transition state Gaussian output file and choose an
                            imaginary frequency threshold that keeps the true transition state mode
                            while ignoring only small near-zero numerical artifacts. For example if 
                            your imaginary frequency is -40 cm<sup>-1</sup>, then a threshold of 
                            50 cm<sup>-1</sup> is too large, perhaps try 30 cm<sup>-1</sup>.
                        </p>
                        """, 400

                    kie_values = [
                        all_values[3],
                        all_values[10],
                        all_values[11],
                        all_values[12],
                        all_values[13],
                        all_values[14]
                    ]

                    if isotopologue_name not in kie_data:
                        kie_data[isotopologue_name] = {"temperature": [], "kies": []}

                    if start_temp not in kie_data[isotopologue_name]["temperature"]:
                        kie_data[isotopologue_name]["temperature"].append(start_temp)

                    kie_data[isotopologue_name]["kies"].append(kie_values)

                    df.loc[len(df)] = [isotopologue_name, start_temp] + all_values

            start_temp += float(temp_increment)

        df.to_csv(app.config["SESSION_FOLDER"] + "/full_output.csv", index=False)
        csv_path = os.path.join(app.config["SESSION_FOLDER"], "full_output.csv")

        # -- generate plots (uncorrected, Wigner, Bell)
        plot_paths = []

        for isotopologue_name, data in kie_data.items():
            plt.figure()
            plt.xlabel("Temperature (K)")
            plt.ylabel("KIE Value")
            plt.title(f"KIE Plot for {isotopologue_name}")

            kie_labels = ["Uncorrected (BM) KIE", "Uncorrected (HS) KIE", "Wigner (BM) KIE", "Wigner (HS) KIE", "Bell (BM) KIE", "Bell (HS) KIE"]

            for i, kie_label in enumerate(kie_labels):
                plt.plot(
                    data["temperature"],
                    [kie_list[i] for kie_list in data["kies"]],
                    marker=".",
                    label=kie_label,
                )

            plt.legend()

            plot_path = os.path.join(
                app.config["SESSION_FOLDER"], f"plot_{isotopologue_name}.png"
            )
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()

        with zipfile.ZipFile(zip_path, "a") as zipf:
            for plot_path in plot_paths:
                plot_filename = os.path.basename(plot_path)
                zipf.write(plot_path, os.path.join("plots", plot_filename))

            zipf.write(csv_path, os.path.basename(csv_path))

        return send_file(
            os.path.join(original_cwd, SESSION_FOLDER, "outputs.zip"),
            mimetype="application/zip",
            as_attachment=True,
            download_name="results.zip",
            # download_name=f"{SESSION_FOLDER}.zip",
        )


# Load the EIE page
@app.route("/eie", methods=["GET", "POST"])
@login_required
def eie():
    if request.method == "GET":
        return render_template("eie.html")
    elif request.method == "POST":
        original_cwd = os.getcwd()
        temperature = request.form.get("temperature").split(",")
        temp_increment = request.form.get("temp_increment")

        # for case where only one temp is given 
        if len(temperature) == 1:
            temperature.append(temperature[0])
            temp_increment = 1

        start_temp = float(temperature[0])
        final_temp = float(temperature[1])

        # Generate a folder for all of the files during the calculations
        SESSION_FOLDER = generate_session()
        app.config["SESSION_FOLDER"] = SESSION_FOLDER

        @after_this_request
        def cleanup(response):
            shutil.rmtree(SESSION_FOLDER, ignore_errors=True)
            return response

        # Assigning variables to required files that were uploaded.
        config_file = request.files.get("config_file")

        # Refers the file for EIE Calculations.
        gaussian_file = request.files.get("gaussian")

        if config_file:
            config_path = os.path.join(app.config["SESSION_FOLDER"], "my.config")
            config_file.save(config_path)

        if gaussian_file:
            gaussian_path = os.path.join(app.config["SESSION_FOLDER"], "gaussian.log")
            gaussian_file.save(gaussian_path)

        else:
            # TODO write a method in here and the HTML file to handle the case of use not uploading the or uploading the incorrect gaussian file. Note that the gaussian file should be generated using the verbose flag for the program to run properly.
            ...

        while start_temp <= final_temp:
            output_file_path = os.path.join(
                app.config["SESSION_FOLDER"], f"output_{start_temp}.txt"
            )

            # Old way to create command, delete later
            # command = f"{sys.executable} {os.path.join('src', 'quiver.py')} {config_path} {gaussian_path} {gaussian_path} {start_temp} {output_file_path}"
            command = (
                f'"{sys.executable}" '
                f'"{quiver_path}" '
                f'"{config_path}" '
                f'"{gaussian_path}" '
                f'"{gaussian_path}" '
                f'{start_temp} '
                f'"{output_file_path}"'
            )
            

            result = subprocess.run(
                [
                    PYTHON_EXECUTABLE,
                    quiver_path,
                    config_path,
                    gaussian_path,
                    gaussian_path,
                    str(start_temp),
                    output_file_path,
                ],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
            )


            print("COMMAND:", command, flush=True)
            print("STDOUT:", result.stdout, flush=True)
            print("STDERR:", result.stderr, flush=True)
            print("RETURN CODE:", result.returncode, flush=True)

            # if result.returncode != 0:
            #     return f"Calculation failed:<br><pre>{result.stderr}</pre>", 500
            
            # More informative error message:
            if result.returncode != 0:
                return f"""
                <h2>Calculation failed</h2>
                <h3>Args</h3>
                <pre>{result.args}</pre>
                <h3>STDOUT</h3>
                <pre>{result.stdout}</pre>
                <h3>STDERR</h3>
                <pre>{result.stderr}</pre>
                <h3>Return code</h3>
                <pre>{result.returncode}</pre>
                """, 500

            start_temp += float(temp_increment)
        # os.system('clear')

        # If the calculations is long, the file may not be immidiately ready.
        # This timeout ensures that the reason for error was not the length of calculations
        timeout = MAX_TIME  # seconds.
        start_time = time.time()
        while not os.path.exists(output_file_path):
            if time.time() - start_time > timeout:
                # TODO make this a modal error.
                return "Output file did not generate.", 404
            # Small delay to check again.
            time.sleep(0.1)

        zip_path = os.path.join(app.config["SESSION_FOLDER"], "outputs.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            start_temp = float(temperature[0])  # reset starting temperature
            while start_temp <= final_temp:
                output_file_path = os.path.join(
                    app.config["SESSION_FOLDER"], f"output_{start_temp}.txt"
                )
                if os.path.exists(output_file_path):
                    zipf.write(output_file_path, os.path.basename(output_file_path))
                start_temp += float(temp_increment)

        eie_data = {}

        # column_names = [
        #     "Isotopologue",
        #     "Temperature",
        #     "EIE (TH)",
        #     "EIE (BM)",
        #     "Enthalpy",
        #     "Entropy",
        #     "H_ZPE",
        #     "H_VIB",
        #     "S_VIB",
        #     "S_ROT",
        #     "MMI",
        #     "EXC",
        #     "ZPE"
        # ]
        column_names = [
            "Isotopologue",
            "Temperature",
            "BM MMI",
            "BM ZPE",
            "BM EXC",
            "BM (total)",
            "HS H_ZPE",
            "HS H_VIB",
            "HS H_TOT",
            "HS S_VIB",
            "HS S_ROT",
            "HS S_TOT",
            "HS (total)",
        ]
        df = pd.DataFrame(columns=column_names)

        start_temp = float(
            temperature[0]
        )  # reset temperature to start to begin iterating again
        while start_temp <= final_temp:
            output_file_path = os.path.join(
                app.config["SESSION_FOLDER"], f"output_{start_temp}.txt"
            )

            if os.path.exists(output_file_path):
                with open(output_file_path, "r") as f:
                    lines = f.readlines()

                for line in lines[4:]:  # skip 4-line header
                    line_components = line.strip().split()

                    if "KIEs" in line_components or len(line_components) < 5:
                        continue  # skip any lines discussing reference/absolute isotopologue or any irrelevant lines

                    isotopologue_name = line_components[1]
                    all_values = list(
                        map(float, line_components[2:])
                    )  

                    expected_num_values = 11

                    if len(all_values) < expected_num_values:
                        return f"""
                        <h2>Calculation failed</h2>
                        <p>
                            The EIE calculation output did not contain all expected values.
                            This may indicate an issue with the calculation output or frequency parsing.
                        </p>
                        <h3>Problematic output line</h3>
                        <pre>{line}</pre>
                        <h3>Parsed numerical values</h3>
                        <pre>{all_values}</pre>
                        """, 400

                    eie_values = [
                        all_values[3],
                        all_values[10]
                    ]

                    if isotopologue_name not in eie_data:
                        eie_data[isotopologue_name] = {"temperature": [], "eies": []}

                    if start_temp not in eie_data[isotopologue_name]["temperature"]:
                        eie_data[isotopologue_name]["temperature"].append(start_temp)

                    eie_data[isotopologue_name]["eies"].append(eie_values)

                    df.loc[len(df)] = [isotopologue_name, start_temp] + all_values

            start_temp += float(temp_increment)

        df.to_csv(app.config["SESSION_FOLDER"] + "/full_output.csv", index=False)
        csv_path = os.path.join(app.config["SESSION_FOLDER"], "full_output.csv")

        plot_paths = []

        for isotopologue_name, data in eie_data.items():
            plt.figure()
            plt.xlabel("Temperature (K)")
            plt.ylabel("EIE Value")
            plt.title(f"EIE Plot for {isotopologue_name}")

            eie_labels = ["EIE (HS)", "EIE (BM)"]

            for i, eie_label in enumerate(eie_labels):
                plt.plot(
                    data["temperature"],
                    [eie_list[i] for eie_list in data["eies"]],
                    marker=".",
                    label=eie_label,
                )

            plt.legend()

            plot_path = os.path.join(
                app.config["SESSION_FOLDER"], f"plot_{isotopologue_name}.png"
            )
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()

        with zipfile.ZipFile(zip_path, "a") as zipf:
            for plot_path in plot_paths:
                plot_filename = os.path.basename(plot_path)
                zipf.write(plot_path, os.path.join("plots", plot_filename))

            zipf.write(csv_path, os.path.basename(csv_path))

        return send_file(
            os.path.join(original_cwd, SESSION_FOLDER, "outputs.zip"),
            mimetype="application/zip",
            as_attachment=True,
            download_name="results.zip",
            # download_name=f"{SESSION_FOLDER}.zip",
        )


# Load the config generator page
@app.route("/config", methods=["GET", "POST"])
@login_required
def config():
    if request.method == "GET":
        return render_template("config.html")
    elif request.method == "POST":
        original_cwd = os.getcwd()

        # temperature = request.form.get("temperature")
        imag_threshold = request.form.get("imag_threshold")
        scaling = request.form.get("scaling")
        reference_iso = request.form.get("reference_iso")

        isotopomers = request.form.getlist("isotopomers[]")
        # Ensure at least one isotopomer is recieved
        if not isotopomers or all(obj.strip() == "" for obj in isotopomers):
            return "You must enter at least one isotopomer.", 400

        # Generate a session folder
        SESSION_FOLDER = generate_session()

        @after_this_request
        def cleanup(response):
            shutil.rmtree(SESSION_FOLDER, ignore_errors=True)
            return response

        # Open a new file
        f = open(os.path.join(SESSION_FOLDER, "autogenerated.config"), "w")

        f.write("### THIS FILE HAS BEEN AUTOMATICALLY GENERATED ###\n\n\n")

        # scaling
        f.write("# scaling factor for frequencies\n")
        f.write(f"scaling {scaling}\n\n")

        # imaginary threshold
        f.write(
            "# imaginaries less than this value in i*cm-1 will be ignored for the transition mode\n"
        )
        f.write(f"imag_threshold {imag_threshold}\n\n")

        # temperature
        f.write("# temperature in K\n")
        # f.write(f"temperature {temperature}\n\n")
        f.write(f"temperature 298\n\n")

        # light isotopomer mass replacement
        # consider allowing users to customize the light isotopes later, 
        # default is fine for now
        f.write("# specifies the masses used for the light isotopomer\n")
        f.write(f"mass_override_isotopologue {'default'}\n\n")

        # TODO Implement this
        # reference isotopomer
        f.write("#all KIEs will be divided by the KIE at this position\n")
        f.write(f"reference_isotopomer {reference_iso}\n\n")

        f.write("# define the isotopomers\n")
        for isotopomer in isotopomers:
            f.write(f"isotopomer {isotopomer}\n")
        f.write("\n\n\n")

        f.write("### END OF THE FILE ###")
        f.close()

        return send_file(
            os.path.join(original_cwd, SESSION_FOLDER, "autogenerated.config"),
            mimetype="text/plain",
            as_attachment=True,
            download_name="autogenerated.config",
        )


# Molecule Viewer
def extract_structure(file_path):
    try:
        atoms = io.read(file_path, format="gaussian-out")
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


@app.route("/view_molecule", methods=["GET", "POST"])
@login_required
def view_molecule():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            SESSION_FOLDER = generate_session()

            @after_this_request
            def cleanup(response):
                shutil.rmtree(SESSION_FOLDER, ignore_errors=True)
                return response

            file_path = os.path.join(generate_session(), "molecule.out")
            uploaded_file.save(file_path)
            xyz_data = extract_structure(file_path)
        return render_template("view_molecule_active.html", xyz_data=xyz_data)
    elif request.method == "GET":
        return render_template("view_molecule_form.html")


@app.route("/paper", methods=["GET"])
def paper():
    if request.method == "GET":
        return send_file(
            "paper.pdf",
            mimetype="application/pdf",
            as_attachment=True,
            download_name="cite_PyQuiverHS.pdf",
        )


@app.route("/tutorials", methods=["GET"])
def tutorials():
    if request.method == "GET":
        return render_template("tutorials.html")


AVAILABLE_TUTORIALS = {"TUTORIAL.md", "CONFIG.md", "EIE.md", "KIE.md", "MOLECULE.md"}


@app.route("/tutorials/<filename>")
def serve_tutorial(filename):
    if filename not in AVAILABLE_TUTORIALS:
        abort(403)
    return send_from_directory("tutorials", filename)

@app.route("/download/weights")
def download_weights():
    return send_from_directory(
        "src",
        "weights.dat",
        as_attachment=True
    )

@app.route("/pics/<filename>")
def serve_pictures(filename):
    return send_from_directory("pics", filename)


@app.route("/tutorials/download")
def serve_tutorial_files():
    return send_file(
        os.path.join("tutorials", "tutorial_files.zip"),
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"tutorial_files.zip",
    )

# REMOVE TEST EMAIL ROUTE BELOW BEFORE PRODUCTION
# @app.route("/test-email")
# def test_email():

#     confirm_url = "https://www.isotope-effects.com/auth/confirm/exampletoken"

#     return render_template(
#         "email/confirm_account.html",
#         confirm_url=confirm_url
#     )
# END OF TEST EMAIL ROUTE, REMOVE BEFORE PRODUCTION

if __name__ == "__main__":
    app.run()
