#!/bin/bash

echo "Creating virtual environment..."
python -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
  echo "Requirements installed successfully."


  echo

  echo "Setting up database..."
  python setup.py
  echo "Scripts ended successful"
  
else
  echo
  echo "Error installing requirements. Exiting."
fi
