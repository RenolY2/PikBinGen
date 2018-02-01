SET _output=%~1
SET _output=%_output:~0,-4%
python "%~dp0pikminBinaryGen.py" --gen2txt "%~1" "%_output%.json" 
pause