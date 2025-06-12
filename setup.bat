@ECHO OFF

:: Base package root. All the other relevant folders are relative to this location.
set "ASTROPIX_ANALYSIS_ROOT=%~dp0"

:: Add the root folder to the $PYTHONPATH environmental variable.
set "PYTHONPATH=%ASTROPIX_ANALYSIS_ROOT%;%PYTHONPATH%"

:: Add the bin folder to the $PATH environmental variable.
set "PATH=%ASTROPIX_ANALYSIS_ROOT%\bin;%PATH%"

:: Print the new environment for verification.
echo "ASTROPIX_ANALYSIS_ROOT -> %ASTROPIX_ANALYSIS_ROOT%"
echo "PATH -> %PATH%"
echo "PYTHONPATH -> %PYTHONPATH%"
