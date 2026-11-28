Option Explicit
' 语镜 LinguaLens — 手机 / 平板局域网启动器
' 双击后：服务改为监听局域网，并打开「手机访问」连接页。
If WScript.Arguments.Named.Exists("check") Then WScript.Quit 0

Dim fso, sh, base, py, app, edge, Q, url, urlFile, dataDir, i, f, tmp, fwText
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
Q = Chr(34)
base = fso.GetParentFolderName(WScript.ScriptFullName)
py = base & "\runtime\pythonw.exe"
app = base & "\app\launcher.py"
edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
If Not fso.FileExists(edge) Then edge = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"

If Not fso.FileExists(py) Then
  MsgBox "找不到语镜的运行文件，请确认文件夹完整。", 16, "语镜手机版"
  WScript.Quit 1
End If

dataDir = base & "\data"
If Not fso.FolderExists(dataDir) Then
  dataDir = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\LinguaLens\data"
End If
urlFile = dataDir & "\lan.url"
If fso.FileExists(urlFile) Then fso.DeleteFile urlFile, True

' --lan 会监听 0.0.0.0；如果之前开的是仅本机模式，launcher 会先退出旧实例。
sh.Run Q & py & Q & " " & Q & app & Q & " --lan --no-browser", 0, False

url = ""
For i = 1 To 50
  WScript.Sleep 500
  If fso.FileExists(urlFile) Then
    Set f = fso.OpenTextFile(urlFile, 1)
    If Not f.AtEndOfStream Then url = Trim(f.ReadAll)
    f.Close
    If Len(url) > 0 Then Exit For
  End If
Next

If Len(url) = 0 Then
  MsgBox "手机版没能启动（等了 25 秒）。" & vbCrLf & vbCrLf & "请查看日志：" & base & "\logs\app.log", 16, "语镜手机版"
  WScript.Quit 1
End If

' 第一次使用：检查防火墙规则，没有就问一句
tmp = sh.ExpandEnvironmentStrings("%TEMP%") & "\ll_fw.txt"
sh.Run "cmd /c netsh advfirewall firewall show rule name=" & Q & "语镜手机版" & Q & " > " & Q & tmp & Q & " 2>&1", 0, True
fwText = ""
If fso.FileExists(tmp) Then
  Set f = fso.OpenTextFile(tmp, 1)
  If Not f.AtEndOfStream Then fwText = f.ReadAll
  f.Close
  fso.DeleteFile tmp, True
End If
If InStr(fwText, "语镜手机版") = 0 Then
  If MsgBox("手机要连进来，需要先放行 Windows 防火墙。" & vbCrLf & vbCrLf & "现在设置吗？会弹出一次管理员确认。", 4 + 32, "语镜手机版") = 6 Then
    sh.Run Q & base & "\放行手机访问.vbs" & Q, 1, False
  End If
End If

If fso.FileExists(edge) Then
  sh.Run Q & edge & Q & " --app=" & url & " --window-size=980,880", 1, False
Else
  sh.Run Q & url & Q, 1, False
End If