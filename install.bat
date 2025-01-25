@echo off

echo Creating virtual environment...
python -m venv .venv

if %ERRORLEVEL% == 0 (
  echo Activating virtual environment...
  .venv\Scripts\activate

  echo Installing requirements...
  python -r requirements.txt

  if %ERRORLEVEL% == 0 (
    echo Requirements installed successfully.

    echo Creating db.sqlite3...
    type nul > db.sqlite3  
    if exist db.sqlite3 (
      echo db.sqlite3 created successfully.
    ) else (
      echo Error creating db.sqlite3. Exiting.
      goto :eof
    )
    

    echo.

    echo Setuping...
    python setup.py
    echo Running main.py...
    python main.py

    if %ERRORLEVEL% == 0 (
      echo.
      echo Script completed successfully.
    ) else (
      echo.
      echo Error running main.py. Exiting.
    )
  ) else (
    echo.
    echo Error installing requirements. Exiting.
  )

  .venv\Scripts\deactivate
) else (
  echo.
  echo Error creating virtual environment. Exiting.
)

pause