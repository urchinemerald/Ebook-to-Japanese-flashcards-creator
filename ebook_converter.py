import os
import subprocess
import tempfile
import shutil
import sys

class EbookConverter:
    def __init__(self):
        # Create a temporary directory to store converted .txt files
        self.temp_dir = tempfile.mkdtemp(prefix="ebook_to_txt_")

        # Figure out the correct path to the ebook-convert executable
        self.ebook_convert_path = os.path.join("bin", "ebook-convert")
        if sys.platform == "win32":
            self.ebook_convert_path += ".exe"

    def convert_to_text(self, ebook_path):
        # Get a .txt output path in the temp dir
        base_name = os.path.splitext(os.path.basename(ebook_path))[0]
        output_txt_path = os.path.join(self.temp_dir, base_name + ".txt")

        try:
            # Run the ebook-convert tool on the file
            subprocess.run([
                self.ebook_convert_path,
                ebook_path,
                output_txt_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Conversion failed: {e}")
            return None

        if os.path.exists(output_txt_path):
            with open(output_txt_path, encoding="utf-8") as f:
                return f.read()
        else:
            print("[ERROR] Output file not found.")
            return None

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
