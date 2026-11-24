import sys,subprocess
for command in [['tools/check_online_operations.py','spreadsheet-web-regression','--candidate'],['tools/check_general_operations.py','spreadsheet-web-regression','--unseen']]:
 r=subprocess.run([sys.executable,'-X','utf8','-u',*command]);assert r.returncode==0,command
print('REGRESSION_COMPLETE',flush=True)
