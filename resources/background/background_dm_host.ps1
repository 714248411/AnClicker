[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
if ($env:ANCLICKER_DM_BACKEND -ne 'native-7.2424') {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class DmLoader {
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct ACTCTX { public int size; public uint flags; public string source; public ushort arch; public ushort lang; public string directory; public string resource; public string application; public IntPtr module; }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateActCtx(ref ACTCTX context);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool ActivateActCtx(IntPtr context,out IntPtr cookie);
 public static void Activate(string source) { var c=new ACTCTX(); c.size=Marshal.SizeOf(c); c.source=source; var handle=CreateActCtx(ref c); if(handle==new IntPtr(-1)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error()); IntPtr cookie; if(!ActivateActCtx(handle,out cookie)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error()); }

 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr LoadLibrary(string path);
 [DllImport("kernel32.dll", CharSet=CharSet.Ansi)] static extern IntPtr GetProcAddress(IntPtr lib, string name);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetClassObject(ref Guid clsid, ref Guid iid, out IntPtr factory);
 [ComImport, Guid("00000001-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
 interface IClassFactory {
  [PreserveSig] int CreateInstance(IntPtr outer, ref Guid iid, [MarshalAs(UnmanagedType.Interface)] out object instance);
  [PreserveSig] int LockServer([MarshalAs(UnmanagedType.Bool)] bool locked);
 }
 public static object Create(string path) {
  IntPtr lib=LoadLibrary(path); if(lib==IntPtr.Zero) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
  IntPtr proc=GetProcAddress(lib,"DllGetClassObject"); if(proc==IntPtr.Zero) throw new Exception("DllGetClassObject missing");
  var get=(GetClassObject)Marshal.GetDelegateForFunctionPointer(proc, typeof(GetClassObject));
  var clsid=new Guid("26037A0E-7CBD-4FFF-9C63-56F2D0770214"); var iid=new Guid("00000001-0000-0000-C000-000000000046"); IntPtr ptr;
  Marshal.ThrowExceptionForHR(get(ref clsid,ref iid,out ptr));
  var factory=(IClassFactory)Marshal.GetTypedObjectForIUnknown(ptr,typeof(IClassFactory)); Marshal.Release(ptr);
  try { object result; var dispatch=new Guid("00020400-0000-0000-C000-000000000046"); Marshal.ThrowExceptionForHR(factory.CreateInstance(IntPtr.Zero,ref dispatch,out result)); return result; }
  finally { Marshal.ReleaseComObject(factory); }
 }
}
'@
}

$dm = $null
$native = $env:ANCLICKER_DM_BACKEND -eq 'native-7.2424'
if ($native) {
 $hashes = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'background_native_72424.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 if ((Get-FileHash -LiteralPath $env:ANCLICKER_DM_DLL -Algorithm SHA256).Hash -ne $hashes.dll_sha256 -or (Get-FileHash -LiteralPath $env:ANCLICKER_DM_HELPER -Algorithm SHA256).Hash -ne $hashes.helper_sha256) { throw '组件校验失败，已停止加载' }
 Add-Type -TypeDefinition (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'background_native_72424.cs') -Raw -Encoding UTF8)
}
$catalog = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'background_dm_methods.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$allowed = @('BindWindow','UnBindWindow','MoveTo','LeftClick','RightClick','MiddleClick','LeftDown','LeftUp','RightDown','RightUp','MiddleDown','MiddleUp','KeyDown','KeyUp','SendString','WheelUp','WheelDown','Capture','GetColor')
try {
 while ($null -ne ($line = [Console]::ReadLine())) {
  try {
   $request = ConvertFrom-Json $line
   $method = [string]$request.method
   if ($native) {
    if ($method -eq 'init') { $value=[NativeDm]::Init($env:ANCLICKER_DM_DLL,$env:ANCLICKER_DM_HELPER); $dm=$true }
    elseif ($dm -and (($allowed -contains $method) -or ($catalog.PSObject.Properties.Name -contains $method))) {
     $value=[NativeDm]::Call($method,[object[]]@($request.args))
     if ((-not $request.raw) -and ($method -ne 'GetColor') -and ([int]$value -ne 1)) { throw ('后台操作 ' + $method + ' 失败，返回码 ' + $value) }
    } else { throw '无效的后台调用' }
   } elseif ($method -eq 'init') {
    [DmLoader]::Activate($env:ANCLICKER_DM_MANIFEST)
    $dm = [DmLoader]::Create($env:ANCLICKER_DM_DLL)
    $value = [string]$dm.Ver()
    if ($env:ANCLICKER_DM_REG_CODE) {
     $registered = $dm.Reg($env:ANCLICKER_DM_REG_CODE, [string]$env:ANCLICKER_DM_REG_EXTRA)
     if ($registered -ne 1) { throw ('大漠授权失败，返回码 ' + $registered) }
    } elseif ($value -ne '3.1233') { throw '此大漠版本尚未配置授权，已阻止后台绑定；请配置大漠注册码' }
   } elseif ((($allowed -contains $method) -or ($catalog.PSObject.Properties.Name -contains $method)) -and ($null -ne $dm)) {
    [object[]]$arguments = @($request.args)
    $definition = $catalog.$method
    if ($request.raw -and $definition) {
     if ($arguments.Count -ne $definition.args.Count) { throw '无效的后台调用参数数量' }
     $modifier = if ($arguments.Count -gt 0) { New-Object System.Reflection.ParameterModifier($arguments.Count) } else { $null }
     $hasOutput = $false
     for ($i=0; $i -lt $arguments.Count; $i++) {
      if ($definition.args[$i].out) { $modifier[$i]=$true; if (-not $definition.args[$i].inout) { $arguments[$i]=0 }; $hasOutput=$true }
      elseif ($definition.args[$i].type -eq 3) { $arguments[$i]=[int]$arguments[$i] }
      elseif ($definition.args[$i].type -eq 20) { $arguments[$i]=[long]$arguments[$i] }
      elseif ($definition.args[$i].type -eq 4) { $arguments[$i]=[single]$arguments[$i] }
      elseif ($definition.args[$i].type -eq 5) { $arguments[$i]=[double]$arguments[$i] }
      else { $arguments[$i]=[string]$arguments[$i] }
     }
     $modifiers = if($hasOutput) { [System.Reflection.ParameterModifier[]]@($modifier) } else { $null }
     $value = $dm.GetType().InvokeMember($method,[System.Reflection.BindingFlags]::InvokeMethod,$null,$dm,$arguments,$modifiers,$null,$null)
     if ($hasOutput) {
      $output = @{}
      for($i=0; $i -lt $arguments.Count; $i++) { if ($definition.args[$i].out) { $output[$definition.args[$i].name]=$arguments[$i] } }
      $value = @{value=$value; output=$output}
     }
    } else {
     $value = $dm.GetType().InvokeMember($method, [System.Reflection.BindingFlags]::InvokeMethod, $null, $dm, $arguments)
    }
    if ((-not $request.raw) -and ($method -ne 'GetColor') -and ([int]$value -ne 1)) { throw ('后台操作 ' + $method + ' 失败，返回码 ' + $value) }
   } else { throw '无效的后台调用' }
   $response = @{ok=$true; result=$value}
  } catch {
   $message = if ($_.Exception -is [System.Management.Automation.RuntimeException] -and $_.Exception.Message -match '^(大漠授权失败|此大漠版本|后台操作|无效的后台)') { $_.Exception.Message } else { '大漠组件调用失败，请检查插件安装、位数、授权和窗口状态' }
   $response = @{ok=$false; error=$message}
  }
  [Console]::WriteLine(($response | ConvertTo-Json -Compress -Depth 5))
 }
} finally {
 if ($native) { if ($dm) { try { [void][NativeDm]::Call('UnBindWindow',[object[]]@()) } catch {}; [NativeDm]::Close() } }
 elseif ($null -ne $dm) { try { [void]$dm.UnBindWindow() } catch {}; [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($dm) }
}
