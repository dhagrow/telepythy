@echo off

set NSIS="C:\Program Files (x86)\NSIS\makensis.exe"

mkdir dist
%NSIS% setup/telepythy.nsi
