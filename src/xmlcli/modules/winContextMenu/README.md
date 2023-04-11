Context Menu Support
====================

Supported OS: `Windows`
Currently supported interface: `Offline [binary file only]`

Instruction of Installation
---------------------------

#### Step 1: Execute `install_context_menu.py` with python as below:

```shell
python install_context_menu.py
```

> It is recommended that you are executing it from path within module then it
> would appear as below result

```shell
C:\>python
Python 3.8.8 (tags/v3.8.8:024d805, Feb 19 2021, 13:18:16) [MSC v.1928 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> from xmlcli import XmlCli as cli
>>> cli
<module 'xmlcli.XmlCli' from 'C:\\Users\\gsaraiya\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\xmlcli\\XmlCli.py'>
>>> cli.helpers.install_context_menu()
script used from: <module 'xmlcli.XmlCli' from 'C:\\Users\\gsaraiya\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\xmlcli\\XmlCli.py'>
script path: C:\Users\gsaraiya\AppData\Local\Programs\Python\Python38\lib\site-packages\xmlcli
Registry install status = 0
0
>>>
```

#### Step 2: Allow permission for adding in registry

You will be prompted to ask permission for registry editor.

As we are modifying Windows registry to add context menu it requires
elevated privilege and confirmation.
You shall see prompt awaiting your response as in this snapshot:

![image](https://github.com/intel-innersource/applications.validation.platform-automation.xmlcli.xmlcli/assets/8687603/d5ecd536-ddfa-47f7-afe8-efd316ab202d)

##### Step 3: Allow modification

![image](https://github.com/intel-innersource/applications.validation.platform-automation.xmlcli.xmlcli/assets/8687603/39bfd218-0ede-4032-be01-eb9dd9f780a0)

##### Step 4: Success

Observe success response as below:

![image](https://github.com/intel-innersource/applications.validation.platform-automation.xmlcli.xmlcli/assets/8687603/ea78e5ae-ca39-40eb-81c6-3f1dbf36af18)



Usage
-----

#### Step 1: Right-click to launch context menu for any valid binary (BIOS/IFWI) as below:

![image](https://github.com/intel-innersource/applications.validation.platform-automation.xmlcli.xmlcli/assets/8687603/0daffa7f-b4ea-4494-bcfd-8afc484ef54b)

You can find here various options of your choice and use as shortcut instead of using commandline everytime.
