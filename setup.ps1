
# Base package root. All the other relevant folders are relative to this location.
$env:ASTROPIX_ANALYSIS_ROOT = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent

# Add the root folder to the $PYTHONPATH environmental variable.
$env:PYTHONPATH = "$env:ASTROPIX_ANALYSIS_ROOT;$env:PYTHONPATH"

# Add the bin folder to the $PATH environmental variable.
$env:PATH = "$env:ASTROPIX_ANALYSIS_ROOT\bin;$env:PATH"

# Print the new environment for verification.
Write-Output "ASTROPIX_ANALYSIS_ROOT: $env:ASTROPIX_ANALYSIS_ROOT"
Write-Output "PATH: $env:PATH"
Write-Output "PYTHONPATH: $env:PYTHONPATH"
