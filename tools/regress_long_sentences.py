import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ["evaluate_long_sentence.py","evaluate_long_sentence_conversational.py","evaluate_long_sentence_independent.py"]:
 subprocess.run([sys.executable,"-X","utf8","-u","models/training/"+name],cwd=ROOT,check=True)
print("REGRESSION_COMPLETE",flush=True)
