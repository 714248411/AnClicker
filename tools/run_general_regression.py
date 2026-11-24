import sys,subprocess
commands=[['tools/check_general_operations.py','unseen','--unseen'],['tools/check_online_operations.py','general-regression','--candidate'],['tools/check_long_sentences_v2.py','general-regression','--candidate'],['models/training/evaluate_v6_4_roles.py']]
for command in commands:
 r=subprocess.run([sys.executable,'-X','utf8','-u',*command]);print('EXIT',command,r.returncode,flush=True)
print('GENERAL_REGRESSION_COMPLETE',flush=True)
