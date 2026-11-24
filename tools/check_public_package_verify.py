import sys,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from tools.packaging.public_package_verify import verify_public_package
body=b'0123456789abcdef';sha=hashlib.sha256(body).hexdigest();calls=[]
class Response:
 def __init__(self,data,start,end,fail=False,status=206):self.data=data;self.status_code=status;self.headers={'Content-Range':f'bytes {start}-{end}/{len(body)}'};self.fail=fail
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def raise_for_status(self):pass
 def iter_content(self,size):
  yield self.data[:2]
  if self.fail:raise requests.exceptions.ChunkedEncodingError('simulated reset')
  yield self.data[2:]
def get(url,**kwargs):
 start,end=map(int,kwargs['headers']['Range'][6:].split('-'));calls.append(start)
 return Response(body[start:end+1],start,end,fail=start==4 and calls.count(4)==1)
with patch('tools.packaging.public_package_verify.requests.get',get),patch('tools.packaging.public_package_verify.time.sleep'):
 verify_public_package('https://example.invalid/file',len(body),sha,chunk_size=4)
assert calls==[0,4,4,8,12],calls
with patch('tools.packaging.public_package_verify.requests.get',return_value=Response(body,0,15,status=200)):
 verify_public_package('https://example.invalid/file',len(body),sha,chunk_size=4)
with patch('tools.packaging.public_package_verify.requests.get',return_value=Response(b'xxxx',0,3)):
 try:verify_public_package('https://example.invalid/file',4,hashlib.sha256(b'abcd').hexdigest(),chunk_size=4)
 except RuntimeError:pass
 else:raise AssertionError('Invalid range accepted')
def corrupt(url,**kwargs):
 start,end=map(int,kwargs['headers']['Range'][6:].split('-'));return Response(b'x'*(end-start+1),start,end)
with patch('tools.packaging.public_package_verify.requests.get',corrupt):
 try:verify_public_package('https://example.invalid/file',len(body),sha,chunk_size=4)
 except RuntimeError:pass
 else:raise AssertionError('Corrupt hash accepted')
print('PASS range retries without double hashing, whole-response fallback, wrong ranges and corruption rejected')
