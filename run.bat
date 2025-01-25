@echo off

set current_dir=%~dp0
set venv_activated=

if not "%VIRTUAL_ENV%"=="" (
  set venv_activated=1
)

if "%venv_activated%"=="" (
  if exist "%current_dir%venv" (
    call "%current_dir%venv\Scripts\activate"
    if not "%VIRTUAL_ENV%"=="" (
        set venv_activated=1
    )

  )
)


if "%venv_activated%"=="" (
    if exist "%current_dir%.venv" (
      call "%current_dir%.venv\Scripts\activate"
      if not "%VIRTUAL_ENV%"=="" (
          set venv_activated=1
      )
    )
)


if "%venv_activated%"=="" (
  python "%~f0" %*
  goto :eof
)

python "%~f0" %*