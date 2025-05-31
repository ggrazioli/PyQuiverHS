class FileWriter:
    def __init__(self, filepath):
        self.filepath = filepath

    def write_script(self, script_content):
        with open(self.filepath, 'a') as file:
            file.write(script_content + '\n')