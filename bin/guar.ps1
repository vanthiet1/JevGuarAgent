$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$ScriptDir\..\guar.ps1" @args
