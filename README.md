# PikBinGen
Tool for convertsion between Pikmin 1 binary gen files and (JSON formatted) text files.

# Requirements
* newest version of Python 3 

The newest version as of the making of this file is 3.6.4: https://www.python.org/downloads/ <br>
When installing it on Windows, make sure you check "Add Python to PATH" so that the included .bat files will work properly.

# Usage
## Drag & Drop
if you are on Windows, the provided gen_to_txt.bat and txt_to_gen.bat files allow simply dropping a file on them to convert it.
Drop a .gen file on gen_to_txt.bat to convert it to .json, drop the converted .json file on txt_to_gen.bat to convert it back to .gen. As an example, "default.gen" will be converted to "default.json" by gen_to_txt and "default.json" will be converted to "default.gen" by txt_to_gen. Make backups of the original gen files if you want to keep them.

## Command line usage
```
python pikminBinaryGen.py [-h] [--gen2txt] [--txt2gen] input [output]

positional arguments:
  input       Filepath to the file that should be converted
  output      Filepath to which the result of the conversion will be written

optional arguments:
  -h, --help  show this help message and exit
  --gen2txt   If set, converts a .gen file to a json text file.
  --txt2gen   If set, converts a json text file to .gen
```
  

# About the text file format
A lot about the gen format is unknown so the json text file contains some placeholder/unclear field names. Do you know the purpose of some fields? Open an issue about that and if I can confirm it then I will add better names to the tool.

Keep an eye out for this page http://pikmintkb.shoutwiki.com/wiki/Pikmin_gen_codes (and add your own discoveries if you have any)

## FAQ
* Q: How can I see where I put my objects without starting the game? <br>
I uploaded all the models of Pikmin 1 courses as texture-less OBJs here, ripped straight from the mod files: https://mega.nz/#!edJ2yLLB!HGOsQh47yW--TtZg-bw_W90HKUC2_c6tmm3Ht7PjKO4

* A: You can load them into my Pikmin 2 Routes editor which renders obj files top-down, or load it into any 3D modelling program you prefer, to figure out coordinates for objects. The routes editor can be found here: https://github.com/RenolY2/pikmin-tools/releases


# How to update
The field names are subject to change in future versions of the tool. When they change, text files created with older versions of the tool might not work with newer versions of the tool. If that happens, convert your text file to gen with the last version of the tool that still worked, then convert it back to text with the newest version.
