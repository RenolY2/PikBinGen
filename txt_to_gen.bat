SET _output=%~1
SET _output=%_output:~0,-5%
python "%~dp0pikminBinaryGen.py" --txt2gen "%~1" "%_output%.gen" 
pause