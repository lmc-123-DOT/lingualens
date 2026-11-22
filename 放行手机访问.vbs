Option Explicit
' 语镜 LinguaLens — 一次性放行 Windows 防火墙
' 语镜只在双击「启动语镜手机版」后才监听端口；这里放行 8765-8794。
If WScript.Arguments.Named.Exists("check") Then WScript.Quit 0

Dim Q, cmd
Q = Chr(34)
cmd = "netsh advfirewall firewall add rule name=" & Q & "语镜手机版" & Q & " dir=in action=allow protocol=TCP localport=8765-8794 profile=domain,private,public"
CreateObject("Shell.Application").ShellExecute "cmd.exe", "/c " & cmd & " & echo. & echo 已放行语镜端口 8765-8794。 & echo 在公共 Wi-Fi 上用完语镜后，记得退出手机版。 & echo. & pause", "", "runas", 1