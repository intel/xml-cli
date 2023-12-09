# WinRWe METHOD

This is access method used for Windows OS Runtime.

Prerequisites:
- Download Portable version of RWEverything compatible to your system from [http://rweverything.com/download/](http://rweverything.com/download/):

| Description   | Details                |
| ------------- | ---------------------- |
| Access Method | `winrwe`               |
| Folder Name   | `winrwe`               |
| Configuration | `winrwe/winrwe.ini`    |
| Documentation | `winrwe/README.md`     |
| Unit Test     | `winrwe/winrweTest.py` |

> Note: Limitation of this interface is that you should not use any system path which may have **space character (`' '`)** in it.

## Dependencies:

1. `RW_EXE` under configuration `winrwe.ini`
2. `RW_INI` under configuration `winrwe.ini`
   1. RWEverything Read & Write Everything
      Compressed file can be acquired from: http://rweverything.com/download/
   2. Make sure to extract executable under the appropriate relative path
      - If you are placing it at some unknown location or renaming file please
      make sure to modify value of key `RW_EXE` under configuration `winrwe.ini`
3. `TEMP_DATA_BIN`
   1. Location to store temporary Data
4. `RESULT_TEXT`
   1. Redirecting result to text location
