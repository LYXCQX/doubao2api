' Doubao 2API - Windows 后台静默启动脚本 (无黑窗)
' 双击此脚本即可在后台静默运行 start_server.bat，不保留任何 CMD 窗口
Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
ws.Run "cmd /c start_server.bat", 0, False
Set ws = Nothing
