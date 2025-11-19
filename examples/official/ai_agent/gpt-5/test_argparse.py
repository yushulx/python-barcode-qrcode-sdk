import subprocess, sys

# Basic smoke test for help output
result = subprocess.run([sys.executable, "scan.py", "--help"], capture_output=True, text=True)
assert result.returncode == 0, "Help command failed"
assert "Command-line Dynamsoft Barcode Scanner" in result.stdout

print("Argparse help OK")
