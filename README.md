# XmlCli-Module

This project is a fork from [UFFAF (UEFI Firmware Foundational Automation
Framework)](https://github.com/intel/xml-cli) tool from Intel(R) (formerly
XmlCli), unfortunately, the original project seems to be intended as a
standalone tool rather than a Python module, this project aims to update the
tool to make it easier to work with on any other Python project.

This module is intended to be used to read BIOS knobs and system information
with an easy-to-use API.

> [!NOTE] 
> Not all the functionality of XmlCli will be ported since the scope of
> the projects are different, XmlCli-Module is intended to be used to read BIOS
> knobs and some other system information, while XmlCli can be used for several
> more things that are out-of-scope of this project.

## Pre-Requisites
This module requires XmlCli BIOS driver enabled and ROOT privileges.

## Usage

To use this module simply create an instance of XmlCli:
```
>>> # Create instance f XmlCli
>>> from xmlcli_knob import XmlCli
>>> xmlcli = XmlCli()
>>> 
>>> # Read one BIOS Knob
>>> xmlcli.get_knob("WheaErrorInjSupportEn")
Knob(name='WheaErrorInjSupportEn', type='scalar', description='Enable/Disable WHEA Error Injection Support', default=0, value=1, _size='01', _offset='0x00AD')
>>> 
>>> # get_kobs returns a dataclass for later usage
>>> knob = xmlcli.get_knob("WheaErrorInjSupportEn") 
>>> knob.description
'Enable/Disable WHEA Error Injection Support'
>>> knob.value
1
>>> 
>>> # It is possible to compare a knob (using it's name) to a value
>>> xmlcli.compare_knob("WheaErrorInjSupportEn", 0)
False
>>> xmlcli.compare_knob("WheaErrorInjSupportEn", 1)
True
>>> 
>>> # The RAW xml data can be saved to a file
>>> xmlcli.save_xml_knobs("some_file.xml")
>>> 
```
