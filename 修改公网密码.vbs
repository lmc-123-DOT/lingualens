Option Explicit
' 语镜 LinguaLens — 自己修改公网访问密码（重启服务，公网地址不变）
' 双击运行；也可以带参数：cscript 修改公网密码.vbs /pwd:新密码 /silent
If WScript.Arguments.Named.Exists("check") Then WScript.Quit 0

Dim fso, sh, base, py, app, Q, newPwd, i, url, http, wmi, procs, p, env, urlFile, f, txt, silent
silent = WScript.Arguments.Named.Exists("silent")
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
Q = Chr(34)
base = fso.GetParentFolderName(WScript.ScriptFullName)
py = base & "\runtime\pythonw.exe"
app = base & "\app\launcher.py"
urlFile = base & "\data\server.url"

If Not fso.FileExists(py) Then
  If Not silent Then MsgBox "找不到语镜的运行文件，请确认文件夹完整。", 16, "语镜公网密码"
  WScript.Quit 1
End If

If WScript.Arguments.Named.Exists("pwd") Then
  newPwd = WScript.Arguments.Named("pwd")
Else
  newPwd = InputBox("输入新的访问密码（至少 8 位，建议字母 + 数字）：" & vbCrLf & vbCrLf & "改完后手机用新密码登录，公网地址不变。", "修改语镜公网密码", "")
End If
If newPwd = "" Then WScript.Quit 0
If Len(newPwd) < 8 Then
  If Not silent Then MsgBox "密码太短了，至少 8 位。", 48, "语镜公网密码"
  WScript.Quit 1
End If

' 停掉旧的语镜实例（只动语镜自己的 pythonw）
On Error Resume Next
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set procs = wmi.ExecQuery("SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name='pythonw.exe'")
For Each p In procs
  If Not IsNull(p.CommandLine) Then
    If InStr(LCase(p.CommandLine), "lingualens-portable") > 0 Then
      sh.Run "taskkill /PID " & p.ProcessId & " /F", 0, True
    End If
  End If
Next
On Error GoTo 0
WScript.Sleep 2500
If fso.FileExists(urlFile) Then fso.DeleteFile urlFile, True

' 用新密码启动
Set env = sh.Environment("PROCESS")
env("LINGUALENS_PASSWORD") = newPwd
env("LINGUALENS_REQUIRE_AUTH") = "1"
sh.Run Q & py & Q & " " & Q & app & Q & " --lan --no-browser", 0, False

' 等服务就绪
url = ""
For i = 1 To 50
  WScript.Sleep 500
  If fso.FileExists(urlFile) Then
    Set f = fso.OpenTextFile(urlFile, 1)
    If Not f.AtEndOfStream Then url = Trim(f.ReadAll)
    f.Close
  End If
  If Len(url) > 0 Then
    On Error Resume Next
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.setTimeouts 1000, 1000, 2000, 2000
    http.Open "GET", url & "/api/health", False
    http.Send
    If Err.Number = 0 And http.Status = 200 Then Exit For
    On Error GoTo 0
    url = ""
  End If
Next

If Len(url) = 0 Then
  If Not silent Then MsgBox "服务没能启动。请查看：" & base & "\logs\app.log", 16, "语镜公网密码"
  WScript.Quit 1
End If

txt = ""
If fso.FileExists(base & "\data\public-url.txt") Then
  Set f = fso.OpenTextFile(base & "\data\public-url.txt", 1)
  If Not f.AtEndOfStream Then txt = Trim(f.ReadAll)
  f.Close
End If

If Not silent Then
  MsgBox "密码已更新，服务已用新密码重启。" & vbCrLf & vbCrLf & _
         "公网地址（不变）：" & vbCrLf & txt & vbCrLf & vbCrLf & _
         "手机登录页：用户名 lingualens，密码用刚才输入的新密码。", 64, "语镜公网密码"
End If