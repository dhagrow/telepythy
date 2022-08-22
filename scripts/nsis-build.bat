@echo off

set NSIS="C:\Program Files (x86)\NSIS\makensis.exe"

mkdir -force dist
%NSIS% setup/telepythy.nsi
