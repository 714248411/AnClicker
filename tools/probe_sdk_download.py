import requests,time
u='https://dotnetcli.blob.core.windows.net/dotnet/Sdk/8.0.427/dotnet-sdk-8.0.427-win-x64.zip'
t=time.monotonic()
with requests.get(u,headers={'Range':'bytes=0-1048575'},timeout=(10,20)) as r:
 r.raise_for_status();print(r.status_code,len(r.content),round(time.monotonic()-t,2))
