import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from tools.packaging.windows_compatibility import validate_native_runtime
print(validate_native_runtime(root/'artifacts/dist/v1.9.2/AnClicker'))
