// Generated from the pinned 7.2424 wrapper signatures; isolated x86 process only.
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class NativeDm {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr LoadLibrary(string path);
 [DllImport("kernel32.dll",CharSet=CharSet.Ansi)] static extern IntPtr GetProcAddress(IntPtr h,string name);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr Factory();
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr Unary(IntPtr p);
 static IntPtr library,instance,helper;
 static T Function<T>(int offset) {return (T)(object)Marshal.GetDelegateForFunctionPointer(IntPtr.Add(library,offset),typeof(T));}
 static IntPtr Text(object value,List<IntPtr> pointers) {var b=Encoding.GetEncoding(936).GetBytes(Convert.ToString(value)+"\0");var p=Marshal.AllocHGlobal(b.Length);Marshal.Copy(b,0,p,b.Length);pointers.Add(p);return p;}
 static string StringResult(IntPtr p) {if(p==IntPtr.Zero)return "";int n=0;while(n<16777216&&Marshal.ReadByte(p,n)!=0)n++;if(n==16777216)throw new Exception("native string too long");var b=new byte[n];Marshal.Copy(p,b,0,n);return Encoding.GetEncoding(936).GetString(b);}
 public static string Init(string dll,string helperPath) {
  library=LoadLibrary(dll);if(library==IntPtr.Zero)throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
  helper=LoadLibrary(helperPath);if(helper==IntPtr.Zero)throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
  var entry=GetProcAddress(helper,"Go");if(entry==IntPtr.Zero)throw new Exception("component entry missing");
  ((Unary)Marshal.GetDelegateForFunctionPointer(entry,typeof(Unary)))(library);
  instance=Function<Factory>(98304)();if(instance==IntPtr.Zero)throw new Exception("component creation failed");
  var version=Convert.ToString(Call("Ver",new object[0]));
  if(version!="7.2424")throw new Exception("component version mismatch");
  if(Convert.ToInt32(Call("Reg",new object[]{"",""}))!=1)throw new Exception("component initialization failed");
  return version;
 }
 public static void Close(){if(instance!=IntPtr.Zero){Function<Unary>(98400)(instance);instance=IntPtr.Zero;}}
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FaqSend(IntPtr obj,IntPtr p0,int p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_Ver(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetPath(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetWordsNoDict(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindData(IntPtr obj,int p0,IntPtr p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetColor(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWordLineHeight(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate long F_AsmCall(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindColorBlock(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6,int p7,int p8,ref int p9,ref int p10);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_DisAssemble(IntPtr obj,IntPtr p0,long p1,int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_EncodeFile(IntPtr obj,IntPtr p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WriteString(IntPtr obj,int p0,IntPtr p1,int p2,IntPtr p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStrFastEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate long F_AsmCallEx(IntPtr obj,int p0,int p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindDoubleEx(IntPtr obj,int p0,IntPtr p1,double p2,double p3,int p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SendString2(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindPicSim(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,int p6,int p7,ref int p8,ref int p9);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WriteInt(IntPtr obj,int p0,IntPtr p1,int p2,long p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetMinColGap(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyPressStr(IntPtr obj,IntPtr p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStrWithFontE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,IntPtr p7,int p8,int p9);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_MatchPicName(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqGetSize(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_MiddleClick(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_RGB2BGR(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetClientSize(IntPtr obj,int p0,ref int p1,ref int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarClose(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CreateFoobarRect(IntPtr obj,int p0,int p1,int p2,int p3,int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindColorBlockEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6,int p7,int p8);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindFloat(IntPtr obj,int p0,IntPtr p1,float p2,float p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindShapeEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWindowText(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindShape(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6,ref int p7,ref int p8);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_MiddleDown(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate float F_ReadFloat(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetWindowTitle(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_Assemble(IntPtr obj,long p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetMousePointWindow(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetExportDict(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_Reg(IntPtr obj,IntPtr p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarStopGif(IntPtr obj,int p0,int p1,int p2,IntPtr p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindPicSimEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,int p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_Capture(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStrWithFontEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,IntPtr p7,int p8,int p9);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_AsmAdd(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CaptureGif(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindPic(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,int p7,ref int p8,ref int p9);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindMultiColor(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,int p7,ref int p8,ref int p9);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindPicE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_MiddleUp(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetWindow(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarSetSave(IntPtr obj,int p0,IntPtr p1,int p2,IntPtr p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WheelDown(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FloatToData(IntPtr obj,float p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SendString(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CreateFoobarCustom(IntPtr obj,int p0,int p1,int p2,IntPtr p3,IntPtr p4,double p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStringEx(IntPtr obj,int p0,IntPtr p1,IntPtr p2,int p3,int p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetClientRect(IntPtr obj,int p0,ref int p1,ref int p2,ref int p3,ref int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarSetTrans(IntPtr obj,int p0,int p1,IntPtr p2,double p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarDrawPic(IntPtr obj,int p0,int p1,int p2,IntPtr p3,IntPtr p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindColorE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_LeftClick(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindShapeE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyUpChar(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetRowGapNoDict(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_MoveTo(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyPressChar(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_RightDown(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_ScreenToClient(IntPtr obj,int p0,ref int p1,ref int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_ImageToBmp(IntPtr obj,IntPtr p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WheelUp(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindWindowEx(IntPtr obj,int p0,IntPtr p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetWordResultPos(IntPtr obj,IntPtr p0,int p1,ref int p2,ref int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_LeftDoubleClick(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_ReadData(IntPtr obj,int p0,IntPtr p1,int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_AddDict(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetWindowProcessId(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindColor(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6,ref int p7,ref int p8);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_MoveR(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_IntToData(IntPtr obj,long p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqPost(IntPtr obj,IntPtr p0,int p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetColorHSV(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_DecodeFile(IntPtr obj,IntPtr p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetWordResultStr(IntPtr obj,IntPtr p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_LoadPic(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindStrFast(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,ref int p7,ref int p8);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindDouble(IntPtr obj,int p0,IntPtr p1,double p2,double p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CreateFoobarEllipse(IntPtr obj,int p0,int p1,int p2,int p3,int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetColorBGR(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_UseDict(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindDataEx(IntPtr obj,int p0,IntPtr p1,IntPtr p2,int p3,int p4,int p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_BGR2RGB(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindColorEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CmpColor(IntPtr obj,int p0,int p1,IntPtr p2,double p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_OcrInFile(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_MoveWindow(IntPtr obj,int p0,int p1,int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindStr(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,ref int p7,ref int p8);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarClearText(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_ClientToScreen(IntPtr obj,int p0,ref int p1,ref int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetWordResultCount(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CapturePng(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyDownChar(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CaptureJpg(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,int p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStrEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqCapture(IntPtr obj,int p0,int p1,int p2,int p3,int p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetKeypadDelay(IntPtr obj,IntPtr p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindWindowByProcessId(IntPtr obj,int p0,IntPtr p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WriteDouble(IntPtr obj,int p0,IntPtr p1,double p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindWindow(IntPtr obj,IntPtr p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindInt(IntPtr obj,int p0,IntPtr p1,long p2,long p3,int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetNowDict(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_EnumWindowSuper(IntPtr obj,IntPtr p0,int p1,int p2,IntPtr p3,int p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate long F_GetModuleBaseAddr(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_UnBindWindow(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarDrawText(IntPtr obj,int p0,int p1,int p2,int p3,int p4,IntPtr p5,IntPtr p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetMinRowGap(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_LeftUp(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWindowSize(IntPtr obj,int p0,int p1,int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqCaptureFromFile(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,int p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetWindowProcessPath(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_ClearDict(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SaveDict(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetAveHSV(IntPtr obj,int p0,int p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqIsPosted(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_LeftDown(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FetchWord(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetDictCount(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetDict(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetDict(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_RightClick(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_EnumWindowByProcess(IntPtr obj,IntPtr p0,IntPtr p1,IntPtr p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_AsmClear(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetWindowState(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStrFastE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetColGapNoDict(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindString(IntPtr obj,int p0,IntPtr p1,IntPtr p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_Ocr(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_ReadString(IntPtr obj,int p0,IntPtr p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarUnlock(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetResultCount(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_EnumWindow(IntPtr obj,int p0,IntPtr p1,IntPtr p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetResultPos(IntPtr obj,IntPtr p0,int p1,ref int p2,ref int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyDown(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWordLineHeightNoDict(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarTextRect(IntPtr obj,int p0,int p1,int p2,int p3,int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetPointWindow(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindMultiColorEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindWindowByProcess(IntPtr obj,IntPtr p0,IntPtr p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetColorNum(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWindowState(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqCancel(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWindowTransparent(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_StringToData(IntPtr obj,IntPtr p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_GetWindowRect(IntPtr obj,int p0,ref int p1,ref int p2,ref int p3,ref int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindPicEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetWords(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetExactOcr(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FaqCaptureString(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarTextLineGap(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarDrawLine(IntPtr obj,int p0,int p1,int p2,int p3,int p4,IntPtr p5,int p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetPicPwd(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FaqFetch(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarUpdate(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate double F_ReadDouble(IntPtr obj,int p0,IntPtr p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_DoubleToData(IntPtr obj,double p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWordGapNoDict(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarLock(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FindStrWithFont(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,IntPtr p7,int p8,int p9,ref int p10,ref int p11);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetWindowClass(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetMouseDelay(IntPtr obj,IntPtr p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate long F_ReadInt(IntPtr obj,int p0,IntPtr p1,int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetAveRGB(IntPtr obj,int p0,int p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindFloatEx(IntPtr obj,int p0,IntPtr p1,float p2,float p3,int p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarPrintText(IntPtr obj,int p0,IntPtr p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_OcrEx(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,double p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FreePic(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WriteData(IntPtr obj,int p0,IntPtr p1,IntPtr p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_CreateFoobarRoundRect(IntPtr obj,int p0,int p1,int p2,int p3,int p4,int p5,int p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_WriteFloat(IntPtr obj,int p0,IntPtr p1,float p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetDictInfo(IntPtr obj,IntPtr p0,IntPtr p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyPress(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetClientSize(IntPtr obj,int p0,int p1,int p2);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_MoveToEx(IntPtr obj,int p0,int p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetDictPwd(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarSetFont(IntPtr obj,int p0,IntPtr p1,int p2,int p3);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarStartGif(IntPtr obj,int p0,int p1,int p2,IntPtr p3,int p4,int p5);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindMultiColorE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_SetWordGap(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindStrE(IntPtr obj,int p0,int p1,int p2,int p3,IntPtr p4,IntPtr p5,double p6);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_KeyUp(IntPtr obj,int p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_FindIntEx(IntPtr obj,int p0,IntPtr p1,long p2,long p3,int p4,int p5,int p6,int p7);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_BindWindow(IntPtr obj,int p0,IntPtr p1,IntPtr p2,IntPtr p3,int p4);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr F_GetPicSize(IntPtr obj,IntPtr p0);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_AsmSetTimeout(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_RightUp(IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarTextPrintDir(IntPtr obj,int p0,int p1);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int F_FoobarFillRect(IntPtr obj,int p0,int p1,int p2,int p3,int p4,IntPtr p5);
 public static object Call(string name,object[] args){if(instance==IntPtr.Zero)throw new Exception("component unavailable");var pointers=new List<IntPtr>();try{switch(name){
 case "FaqSend": {if(args.Length!=4)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_FaqSend>(114016)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "Ver": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_Ver>(100320)(instance);
 return StringResult(result); }
 case "SetPath": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_SetPath>(123808)(instance,p0);
 return result; }
 case "GetWordsNoDict": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 var result=Function<F_GetWordsNoDict>(99024)(instance,p0,p1,p2,p3,p4);
 return StringResult(result); }
 case "FindData": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_FindData>(109760)(instance,p0,p1,p2);
 return StringResult(result); }
 case "GetColor": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetColor>(117424)(instance,p0,p1);
 return StringResult(result); }
 case "SetWordLineHeight": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetWordLineHeight>(101296)(instance,p0);
 return result; }
 case "AsmCall": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_AsmCall>(114656)(instance,p0,p1);
 return result; }
 case "FindColorBlock": {if(args.Length!=11)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 int p7=Convert.ToInt32(args[7]);
 int p8=Convert.ToInt32(args[8]);
 int p9=0;
 int p10=0;
 var result=Function<F_FindColorBlock>(113568)(instance,p0,p1,p2,p3,p4,p5,p6,p7,p8,ref p9,ref p10);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p9},{"y",p10}}}}; }
 case "DisAssemble": {if(args.Length!=3)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 long p1=Convert.ToInt64(args[1]);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_DisAssemble>(112656)(instance,p0,p1,p2);
 return StringResult(result); }
 case "EncodeFile": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_EncodeFile>(106528)(instance,p0,p1);
 return result; }
 case "WriteString": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 var result=Function<F_WriteString>(115936)(instance,p0,p1,p2,p3);
 return result; }
 case "FindStrFastEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 var result=Function<F_FindStrFastEx>(122000)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "AsmCallEx": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_AsmCallEx>(99632)(instance,p0,p1,p2);
 return result; }
 case "FindDoubleEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 double p2=Convert.ToDouble(args[2]);
 double p3=Convert.ToDouble(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindDoubleEx>(110416)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "SendString2": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_SendString2>(99888)(instance,p0,p1);
 return result; }
 case "FindPicSim": {if(args.Length!=10)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 int p6=Convert.ToInt32(args[6]);
 int p7=Convert.ToInt32(args[7]);
 int p8=0;
 int p9=0;
 var result=Function<F_FindPicSim>(98768)(instance,p0,p1,p2,p3,p4,p5,p6,p7,ref p8,ref p9);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p8},{"y",p9}}}}; }
 case "WriteInt": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 long p3=Convert.ToInt64(args[3]);
 var result=Function<F_WriteInt>(112416)(instance,p0,p1,p2,p3);
 return result; }
 case "SetMinColGap": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetMinColGap>(110560)(instance,p0);
 return result; }
 case "KeyPressStr": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_KeyPressStr>(102528)(instance,p0,p1);
 return result; }
 case "FindStrWithFontE": {if(args.Length!=10)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 IntPtr p7=Text(args[7],pointers);
 int p8=Convert.ToInt32(args[8]);
 int p9=Convert.ToInt32(args[9]);
 var result=Function<F_FindStrWithFontE>(112544)(instance,p0,p1,p2,p3,p4,p5,p6,p7,p8,p9);
 return StringResult(result); }
 case "MatchPicName": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_MatchPicName>(117984)(instance,p0);
 return StringResult(result); }
 case "FaqGetSize": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_FaqGetSize>(103456)(instance,p0);
 return result; }
 case "MiddleClick": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_MiddleClick>(108560)(instance);
 return result; }
 case "RGB2BGR": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_RGB2BGR>(115744)(instance,p0);
 return StringResult(result); }
 case "GetClientSize": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=0;
 int p2=0;
 var result=Function<F_GetClientSize>(103344)(instance,p0,ref p1,ref p2);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"width",p1},{"height",p2}}}}; }
 case "FoobarClose": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_FoobarClose>(102480)(instance,p0);
 return result; }
 case "CreateFoobarRect": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 var result=Function<F_CreateFoobarRect>(119072)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "FindColorBlockEx": {if(args.Length!=9)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 int p7=Convert.ToInt32(args[7]);
 int p8=Convert.ToInt32(args[8]);
 var result=Function<F_FindColorBlockEx>(103840)(instance,p0,p1,p2,p3,p4,p5,p6,p7,p8);
 return StringResult(result); }
 case "FindFloat": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 float p2=Convert.ToSingle(args[2]);
 float p3=Convert.ToSingle(args[3]);
 var result=Function<F_FindFloat>(103216)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "FindShapeEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindShapeEx>(99792)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "SetWindowText": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_SetWindowText>(113008)(instance,p0,p1);
 return result; }
 case "FindShape": {if(args.Length!=9)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 int p7=0;
 int p8=0;
 var result=Function<F_FindShape>(123856)(instance,p0,p1,p2,p3,p4,p5,p6,ref p7,ref p8);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p7},{"y",p8}}}}; }
 case "MiddleDown": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_MiddleDown>(109872)(instance);
 return result; }
 case "ReadFloat": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_ReadFloat>(100976)(instance,p0,p1);
 return result; }
 case "GetWindowTitle": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_GetWindowTitle>(110816)(instance,p0);
 return StringResult(result); }
 case "Assemble": {if(args.Length!=2)throw new ArgumentException("argument count");
 long p0=Convert.ToInt64(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_Assemble>(119584)(instance,p0,p1);
 return StringResult(result); }
 case "GetMousePointWindow": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_GetMousePointWindow>(105424)(instance);
 return result; }
 case "SetExportDict": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_SetExportDict>(119392)(instance,p0,p1);
 return result; }
 case "Reg": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_Reg>(121344)(instance,p0,p1);
 return result; }
 case "FoobarStopGif": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 var result=Function<F_FoobarStopGif>(108096)(instance,p0,p1,p2,p3);
 return result; }
 case "FindPicSimEx": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 int p6=Convert.ToInt32(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FindPicSimEx>(113728)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return StringResult(result); }
 case "Capture": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 var result=Function<F_Capture>(119456)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "FindStrWithFontEx": {if(args.Length!=10)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 IntPtr p7=Text(args[7],pointers);
 int p8=Convert.ToInt32(args[8]);
 int p9=Convert.ToInt32(args[9]);
 var result=Function<F_FindStrWithFontEx>(118848)(instance,p0,p1,p2,p3,p4,p5,p6,p7,p8,p9);
 return StringResult(result); }
 case "AsmAdd": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_AsmAdd>(121232)(instance,p0);
 return result; }
 case "CaptureGif": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_CaptureGif>(120912)(instance,p0,p1,p2,p3,p4,p5,p6);
 return result; }
 case "FindPic": {if(args.Length!=10)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=Convert.ToInt32(args[7]);
 int p8=0;
 int p9=0;
 var result=Function<F_FindPic>(104032)(instance,p0,p1,p2,p3,p4,p5,p6,p7,ref p8,ref p9);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p8},{"y",p9}}}}; }
 case "FindMultiColor": {if(args.Length!=10)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=Convert.ToInt32(args[7]);
 int p8=0;
 int p9=0;
 var result=Function<F_FindMultiColor>(109360)(instance,p0,p1,p2,p3,p4,p5,p6,p7,ref p8,ref p9);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p8},{"y",p9}}}}; }
 case "FindPicE": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FindPicE>(114144)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return StringResult(result); }
 case "MiddleUp": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_MiddleUp>(115072)(instance);
 return result; }
 case "GetWindow": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetWindow>(120752)(instance,p0,p1);
 return result; }
 case "FoobarSetSave": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 var result=Function<F_FoobarSetSave>(124736)(instance,p0,p1,p2,p3);
 return result; }
 case "WheelDown": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_WheelDown>(112848)(instance);
 return result; }
 case "FloatToData": {if(args.Length!=1)throw new ArgumentException("argument count");
 float p0=Convert.ToSingle(args[0]);
 var result=Function<F_FloatToData>(100464)(instance,p0);
 return StringResult(result); }
 case "SendString": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_SendString>(114832)(instance,p0,p1);
 return result; }
 case "CreateFoobarCustom": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 var result=Function<F_CreateFoobarCustom>(105872)(instance,p0,p1,p2,p3,p4,p5);
 return result; }
 case "FindStringEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindStringEx>(124384)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "GetClientRect": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=0;
 int p2=0;
 int p3=0;
 int p4=0;
 var result=Function<F_GetClientRect>(105808)(instance,p0,ref p1,ref p2,ref p3,ref p4);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x1",p1},{"y1",p2},{"x2",p3},{"y2",p4}}}}; }
 case "FoobarSetTrans": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 IntPtr p2=Text(args[2],pointers);
 double p3=Convert.ToDouble(args[3]);
 var result=Function<F_FoobarSetTrans>(117248)(instance,p0,p1,p2,p3);
 return result; }
 case "FoobarDrawPic": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 IntPtr p4=Text(args[4],pointers);
 var result=Function<F_FoobarDrawPic>(114288)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "FindColorE": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindColorE>(120384)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "LeftClick": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_LeftClick>(118096)(instance);
 return result; }
 case "FindShapeE": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindShapeE>(120592)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "KeyUpChar": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_KeyUpChar>(121904)(instance,p0);
 return result; }
 case "SetRowGapNoDict": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetRowGapNoDict>(118256)(instance,p0);
 return result; }
 case "MoveTo": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_MoveTo>(109088)(instance,p0,p1);
 return result; }
 case "KeyPressChar": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_KeyPressChar>(116464)(instance,p0);
 return result; }
 case "RightDown": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_RightDown>(124576)(instance);
 return result; }
 case "ScreenToClient": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_ScreenToClient>(111392)(instance,p0,ref p1,ref p2);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p1},{"y",p2}}}}; }
 case "ImageToBmp": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_ImageToBmp>(109152)(instance,p0,p1);
 return result; }
 case "WheelUp": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_WheelUp>(102688)(instance);
 return result; }
 case "FindWindowEx": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_FindWindowEx>(115408)(instance,p0,p1,p2);
 return result; }
 case "GetWordResultPos": {if(args.Length!=4)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 int p2=0;
 int p3=0;
 var result=Function<F_GetWordResultPos>(114352)(instance,p0,p1,ref p2,ref p3);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p2},{"y",p3}}}}; }
 case "LeftDoubleClick": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_LeftDoubleClick>(101136)(instance);
 return result; }
 case "ReadData": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_ReadData>(111232)(instance,p0,p1,p2);
 return StringResult(result); }
 case "AddDict": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_AddDict>(106336)(instance,p0,p1);
 return result; }
 case "GetWindowProcessId": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_GetWindowProcessId>(124464)(instance,p0);
 return result; }
 case "FindColor": {if(args.Length!=9)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 int p7=0;
 int p8=0;
 var result=Function<F_FindColor>(106112)(instance,p0,p1,p2,p3,p4,p5,p6,ref p7,ref p8);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p7},{"y",p8}}}}; }
 case "MoveR": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_MoveR>(113504)(instance,p0,p1);
 return result; }
 case "IntToData": {if(args.Length!=2)throw new ArgumentException("argument count");
 long p0=Convert.ToInt64(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_IntToData>(122272)(instance,p0,p1);
 return StringResult(result); }
 case "FaqPost": {if(args.Length!=4)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_FaqPost>(107440)(instance,p0,p1,p2,p3);
 return result; }
 case "GetColorHSV": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetColorHSV>(116192)(instance,p0,p1);
 return StringResult(result); }
 case "DecodeFile": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_DecodeFile>(122496)(instance,p0,p1);
 return result; }
 case "GetWordResultStr": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetWordResultStr>(104768)(instance,p0,p1);
 return StringResult(result); }
 case "LoadPic": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_LoadPic>(124128)(instance,p0);
 return result; }
 case "FindStrFast": {if(args.Length!=9)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=0;
 int p8=0;
 var result=Function<F_FindStrFast>(115584)(instance,p0,p1,p2,p3,p4,p5,p6,ref p7,ref p8);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p7},{"y",p8}}}}; }
 case "FindDouble": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 double p2=Convert.ToDouble(args[2]);
 double p3=Convert.ToDouble(args[3]);
 var result=Function<F_FindDouble>(102192)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "CreateFoobarEllipse": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 var result=Function<F_CreateFoobarEllipse>(114592)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "GetColorBGR": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetColorBGR>(100000)(instance,p0,p1);
 return StringResult(result); }
 case "UseDict": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_UseDict>(104656)(instance,p0);
 return result; }
 case "FindDataEx": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 var result=Function<F_FindDataEx>(123200)(instance,p0,p1,p2,p3,p4,p5);
 return StringResult(result); }
 case "BGR2RGB": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_BGR2RGB>(118736)(instance,p0);
 return StringResult(result); }
 case "FindColorEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindColorEx>(103600)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "CmpColor": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 IntPtr p2=Text(args[2],pointers);
 double p3=Convert.ToDouble(args[3]);
 var result=Function<F_CmpColor>(109648)(instance,p0,p1,p2,p3);
 return result; }
 case "OcrInFile": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 var result=Function<F_OcrInFile>(110608)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "MoveWindow": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_MoveWindow>(119648)(instance,p0,p1,p2);
 return result; }
 case "FindStr": {if(args.Length!=9)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=0;
 int p8=0;
 var result=Function<F_FindStr>(110320)(instance,p0,p1,p2,p3,p4,p5,p6,ref p7,ref p8);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p7},{"y",p8}}}}; }
 case "FoobarClearText": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_FoobarClearText>(113072)(instance,p0);
 return result; }
 case "ClientToScreen": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_ClientToScreen>(116512)(instance,p0,ref p1,ref p2);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p1},{"y",p2}}}}; }
 case "GetWordResultCount": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_GetWordResultCount>(103984)(instance,p0);
 return result; }
 case "CapturePng": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 var result=Function<F_CapturePng>(114080)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "KeyDownChar": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_KeyDownChar>(105600)(instance,p0);
 return result; }
 case "CaptureJpg": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 int p5=Convert.ToInt32(args[5]);
 var result=Function<F_CaptureJpg>(106400)(instance,p0,p1,p2,p3,p4,p5);
 return result; }
 case "FindStrEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 var result=Function<F_FindStrEx>(106640)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "FaqCapture": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FaqCapture>(118416)(instance,p0,p1,p2,p3,p4,p5,p6);
 return result; }
 case "SetKeypadDelay": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_SetKeypadDelay>(110256)(instance,p0,p1);
 return result; }
 case "FindWindowByProcessId": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_FindWindowByProcessId>(104176)(instance,p0,p1,p2);
 return result; }
 case "WriteDouble": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 double p2=Convert.ToDouble(args[2]);
 var result=Function<F_WriteDouble>(116048)(instance,p0,p1,p2);
 return result; }
 case "FindWindow": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_FindWindow>(104288)(instance,p0,p1);
 return result; }
 case "FindInt": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 long p2=Convert.ToInt64(args[2]);
 long p3=Convert.ToInt64(args[3]);
 int p4=Convert.ToInt32(args[4]);
 var result=Function<F_FindInt>(106256)(instance,p0,p1,p2,p3,p4);
 return StringResult(result); }
 case "GetNowDict": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_GetNowDict>(101584)(instance);
 return result; }
 case "EnumWindowSuper": {if(args.Length!=7)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_EnumWindowSuper>(107360)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "GetModuleBaseAddr": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_GetModuleBaseAddr>(108848)(instance,p0,p1);
 return result; }
 case "UnBindWindow": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_UnBindWindow>(101904)(instance);
 return result; }
 case "FoobarDrawText": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 IntPtr p5=Text(args[5],pointers);
 IntPtr p6=Text(args[6],pointers);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FoobarDrawText>(119712)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return result; }
 case "SetMinRowGap": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetMinRowGap>(122144)(instance,p0);
 return result; }
 case "LeftUp": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_LeftUp>(113680)(instance);
 return result; }
 case "SetWindowSize": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_SetWindowSize>(98560)(instance,p0,p1,p2);
 return result; }
 case "FaqCaptureFromFile": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 int p5=Convert.ToInt32(args[5]);
 var result=Function<F_FaqCaptureFromFile>(116256)(instance,p0,p1,p2,p3,p4,p5);
 return result; }
 case "GetWindowProcessPath": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_GetWindowProcessPath>(105232)(instance,p0);
 return StringResult(result); }
 case "ClearDict": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_ClearDict>(123152)(instance,p0);
 return result; }
 case "SaveDict": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_SaveDict>(115520)(instance,p0,p1);
 return result; }
 case "GetAveHSV": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_GetAveHSV>(100176)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "FaqIsPosted": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_FaqIsPosted>(102864)(instance);
 return result; }
 case "LeftDown": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_LeftDown>(106736)(instance);
 return result; }
 case "FetchWord": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 var result=Function<F_FetchWord>(117840)(instance,p0,p1,p2,p3,p4,p5);
 return StringResult(result); }
 case "GetDictCount": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_GetDictCount>(99584)(instance,p0);
 return result; }
 case "GetDict": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetDict>(99184)(instance,p0,p1);
 return StringResult(result); }
 case "SetDict": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_SetDict>(121280)(instance,p0,p1);
 return result; }
 case "RightClick": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_RightClick>(101040)(instance);
 return result; }
 case "EnumWindowByProcess": {if(args.Length!=4)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_EnumWindowByProcess>(110192)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "AsmClear": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_AsmClear>(119968)(instance);
 return result; }
 case "GetWindowState": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetWindowState>(100112)(instance,p0,p1);
 return result; }
 case "FindStrFastE": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 var result=Function<F_FindStrFastE>(120288)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "SetColGapNoDict": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetColGapNoDict>(102592)(instance,p0);
 return result; }
 case "FindString": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_FindString>(110752)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "Ocr": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 var result=Function<F_Ocr>(110992)(instance,p0,p1,p2,p3,p4,p5);
 return StringResult(result); }
 case "ReadString": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_ReadString>(121472)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "FoobarUnlock": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_FoobarUnlock>(123952)(instance,p0);
 return result; }
 case "GetResultCount": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_GetResultCount>(116720)(instance,p0);
 return result; }
 case "EnumWindow": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_EnumWindow>(115296)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "GetResultPos": {if(args.Length!=4)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 int p2=0;
 int p3=0;
 var result=Function<F_GetResultPos>(102800)(instance,p0,p1,ref p2,ref p3);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p2},{"y",p3}}}}; }
 case "KeyDown": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_KeyDown>(115120)(instance,p0);
 return result; }
 case "SetWordLineHeightNoDict": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetWordLineHeightNoDict>(103792)(instance,p0);
 return result; }
 case "FoobarTextRect": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 var result=Function<F_FoobarTextRect>(108784)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "GetPointWindow": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_GetPointWindow>(118544)(instance,p0,p1);
 return result; }
 case "FindMultiColorEx": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FindMultiColorEx>(122560)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return StringResult(result); }
 case "FindWindowByProcess": {if(args.Length!=3)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_FindWindowByProcess>(122336)(instance,p0,p1,p2);
 return result; }
 case "GetColorNum": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 var result=Function<F_GetColorNum>(124048)(instance,p0,p1,p2,p3,p4,p5);
 return result; }
 case "SetWindowState": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_SetWindowState>(102736)(instance,p0,p1);
 return result; }
 case "FaqCancel": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_FaqCancel>(113968)(instance);
 return result; }
 case "SetWindowTransparent": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_SetWindowTransparent>(112896)(instance,p0,p1);
 return result; }
 case "StringToData": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_StringToData>(114768)(instance,p0,p1);
 return StringResult(result); }
 case "GetWindowRect": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=0;
 int p2=0;
 int p3=0;
 int p4=0;
 var result=Function<F_GetWindowRect>(122656)(instance,p0,ref p1,ref p2,ref p3,ref p4);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x1",p1},{"y1",p2},{"x2",p3},{"y2",p4}}}}; }
 case "FindPicEx": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FindPicEx>(108160)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return StringResult(result); }
 case "GetWords": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 var result=Function<F_GetWords>(107808)(instance,p0,p1,p2,p3,p4,p5);
 return StringResult(result); }
 case "SetExactOcr": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetExactOcr>(123280)(instance,p0);
 return result; }
 case "FaqCaptureString": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_FaqCaptureString>(106208)(instance,p0);
 return result; }
 case "FoobarTextLineGap": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_FoobarTextLineGap>(124848)(instance,p0,p1);
 return result; }
 case "FoobarDrawLine": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 IntPtr p5=Text(args[5],pointers);
 int p6=Convert.ToInt32(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FoobarDrawLine>(116384)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return result; }
 case "SetPicPwd": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_SetPicPwd>(123712)(instance,p0);
 return result; }
 case "FaqFetch": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_FaqFetch>(117744)(instance);
 return StringResult(result); }
 case "FoobarUpdate": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_FoobarUpdate>(119280)(instance,p0);
 return result; }
 case "ReadDouble": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 var result=Function<F_ReadDouble>(110128)(instance,p0,p1);
 return result; }
 case "DoubleToData": {if(args.Length!=1)throw new ArgumentException("argument count");
 double p0=Convert.ToDouble(args[0]);
 var result=Function<F_DoubleToData>(111856)(instance,p0);
 return StringResult(result); }
 case "SetWordGapNoDict": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetWordGapNoDict>(123392)(instance,p0);
 return result; }
 case "FoobarLock": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_FoobarLock>(109824)(instance,p0);
 return result; }
 case "FindStrWithFont": {if(args.Length!=12)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 IntPtr p7=Text(args[7],pointers);
 int p8=Convert.ToInt32(args[8]);
 int p9=Convert.ToInt32(args[9]);
 int p10=0;
 int p11=0;
 var result=Function<F_FindStrWithFont>(119856)(instance,p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,ref p10,ref p11);
 return new Dictionary<string,object>{{"value",result},{"output",new Dictionary<string,object>{{"x",p10},{"y",p11}}}}; }
 case "GetWindowClass": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_GetWindowClass>(117056)(instance,p0);
 return StringResult(result); }
 case "SetMouseDelay": {if(args.Length!=2)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_SetMouseDelay>(104592)(instance,p0,p1);
 return result; }
 case "ReadInt": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_ReadInt>(112720)(instance,p0,p1,p2);
 return result; }
 case "GetAveRGB": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_GetAveRGB>(118192)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "FindFloatEx": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 float p2=Convert.ToSingle(args[2]);
 float p3=Convert.ToSingle(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_FindFloatEx>(107040)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "FoobarPrintText": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_FoobarPrintText>(108720)(instance,p0,p1,p2);
 return result; }
 case "OcrEx": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 double p5=Convert.ToDouble(args[5]);
 var result=Function<F_OcrEx>(113168)(instance,p0,p1,p2,p3,p4,p5);
 return StringResult(result); }
 case "FreePic": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_FreePic>(103408)(instance,p0);
 return result; }
 case "WriteData": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 var result=Function<F_WriteData>(123040)(instance,p0,p1,p2);
 return result; }
 case "CreateFoobarRoundRect": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 var result=Function<F_CreateFoobarRoundRect>(108352)(instance,p0,p1,p2,p3,p4,p5,p6);
 return result; }
 case "WriteFloat": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 float p2=Convert.ToSingle(args[2]);
 var result=Function<F_WriteFloat>(111920)(instance,p0,p1,p2);
 return result; }
 case "GetDictInfo": {if(args.Length!=4)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_GetDictInfo>(100624)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "KeyPress": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_KeyPress>(118688)(instance,p0);
 return result; }
 case "SetClientSize": {if(args.Length!=3)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 var result=Function<F_SetClientSize>(104896)(instance,p0,p1,p2);
 return result; }
 case "MoveToEx": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_MoveToEx>(120688)(instance,p0,p1,p2,p3);
 return StringResult(result); }
 case "SetDictPwd": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_SetDictPwd>(104128)(instance,p0);
 return result; }
 case "FoobarSetFont": {if(args.Length!=4)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 var result=Function<F_FoobarSetFont>(111632)(instance,p0,p1,p2,p3);
 return result; }
 case "FoobarStartGif": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 IntPtr p3=Text(args[3],pointers);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 var result=Function<F_FoobarStartGif>(117664)(instance,p0,p1,p2,p3,p4,p5);
 return result; }
 case "FindMultiColorE": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FindMultiColorE>(101696)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return StringResult(result); }
 case "SetWordGap": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_SetWordGap>(98624)(instance,p0);
 return result; }
 case "FindStrE": {if(args.Length!=7)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 IntPtr p4=Text(args[4],pointers);
 IntPtr p5=Text(args[5],pointers);
 double p6=Convert.ToDouble(args[6]);
 var result=Function<F_FindStrE>(122400)(instance,p0,p1,p2,p3,p4,p5,p6);
 return StringResult(result); }
 case "KeyUp": {if(args.Length!=1)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 var result=Function<F_KeyUp>(113248)(instance,p0);
 return result; }
 case "FindIntEx": {if(args.Length!=8)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 long p2=Convert.ToInt64(args[2]);
 long p3=Convert.ToInt64(args[3]);
 int p4=Convert.ToInt32(args[4]);
 int p5=Convert.ToInt32(args[5]);
 int p6=Convert.ToInt32(args[6]);
 int p7=Convert.ToInt32(args[7]);
 var result=Function<F_FindIntEx>(107216)(instance,p0,p1,p2,p3,p4,p5,p6,p7);
 return StringResult(result); }
 case "BindWindow": {if(args.Length!=5)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 IntPtr p1=Text(args[1],pointers);
 IntPtr p2=Text(args[2],pointers);
 IntPtr p3=Text(args[3],pointers);
 int p4=Convert.ToInt32(args[4]);
 var result=Function<F_BindWindow>(120080)(instance,p0,p1,p2,p3,p4);
 return result; }
 case "GetPicSize": {if(args.Length!=1)throw new ArgumentException("argument count");
 IntPtr p0=Text(args[0],pointers);
 var result=Function<F_GetPicSize>(114960)(instance,p0);
 return StringResult(result); }
 case "AsmSetTimeout": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_AsmSetTimeout>(117920)(instance,p0,p1);
 return result; }
 case "RightUp": {if(args.Length!=0)throw new ArgumentException("argument count");
 var result=Function<F_RightUp>(111504)(instance);
 return result; }
 case "FoobarTextPrintDir": {if(args.Length!=2)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 var result=Function<F_FoobarTextPrintDir>(103072)(instance,p0,p1);
 return result; }
 case "FoobarFillRect": {if(args.Length!=6)throw new ArgumentException("argument count");
 int p0=Convert.ToInt32(args[0]);
 int p1=Convert.ToInt32(args[1]);
 int p2=Convert.ToInt32(args[2]);
 int p3=Convert.ToInt32(args[3]);
 int p4=Convert.ToInt32(args[4]);
 IntPtr p5=Text(args[5],pointers);
 var result=Function<F_FoobarFillRect>(103136)(instance,p0,p1,p2,p3,p4,p5);
 return result; }
 default:throw new NotSupportedException("此组件未提供接口："+name);}}finally{foreach(var p in pointers)Marshal.FreeHGlobal(p);}}
}
