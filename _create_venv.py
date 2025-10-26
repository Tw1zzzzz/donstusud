import os
import sys
import venv
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent.absolute()
venv_path = script_dir / '.venv'

print(f"Creating virtual environment at: {venv_path}")
print(f"Python: {sys.executable}")

try:
    venv.create(str(venv_path), with_pip=True)
    print("✓ Virtual environment created successfully!")
    print(f"\nActivate with:")
    print(f"  {venv_path}\\Scripts\\activate")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

