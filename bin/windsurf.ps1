$ShimDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$GuarPy = Join-Path (Split-Path -Parent $ShimDir) "guar.py"
python "$GuarPy" wrap windsurf $args
exit $LASTEXITCODE
