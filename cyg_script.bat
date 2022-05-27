: <<TRAMPOLINE
@echo off
setlocal EnableDelayedExpansion
FOR /F "tokens=*" %%g IN ('where bash') do (SET bash_location=%%g)
"%bash_location%" -c "exit 0" || (echo.No bash found in PATH! & exit /b 1)
for %%i in (%*) do set _args= !_args! "%%~i"
"%bash_location%" -l "%~f0" "%CD%" %_args%
EXIT /b %ERRORLEVEL%
goto :EOF 
TRAMPOLINE
#####################
#!/bin/bash  -- it's traditional!
cd "${1}"
shift 1
cmd=${1}
shift 1
${cmd} "${@}"
exit ${?}