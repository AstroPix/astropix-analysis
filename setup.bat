:: Setup for window - will be removed at some point
@echo off

:: Base package root. Change it for your directory
set ASTROPIX_ANALYSIS_ROOT=C:\Users\sgro\work\AstroPix\astropix-analysis

:: This is were i store data
set ASTROPIX_DATA=C:\Users\sgro\work\AstroPix\astropix-outdata

:: AstroPix library package root. Change it for your directory
set ASTROPIX_PYTHON_ROOT=C:\Users\sgro\work\AstroPix\astropix-python

:: Add the root folder to the $PYTHONPATH to import  the relevant modules.
set PYTHONPATH=%ASTROPIX_ANALYSIS_ROOT%;%ASTROPIX_PYTHON_ROOT%
