# UFFAF - UEFI Firmware Foundational Automation Framework (formerly XmlCli)

UFFAF allows firmware modification as an efficient operation with scriptable approach through various interfaces with an intention to reduce manual interventions. Entire Client and Server ecosystem ranging from Silicon Validation teams to Tools teams running on different OS. UFFAF (formerly XmlCli) Interface is basically a combination of 2 methodologies, XML (System or Platform Information to be consumed in XML format) & CLI (BIOS Command Line Interface protocol which acts as an interface between BIOS & outside environment via S/W SMI or UEFI runtime interface). In short UFFAF (formerly XML CLI) is the interface methodology between BIOS & External world Tool is the combination of Python Scripts and utilities that helps the end user/automation to perform desired operations using available BIOS Driver interface.



These reference scripts provides several capabilities including but not limited to:
>- Parsing Information of UEFI BIOS Firmware as per [Platform Initialization Specification](https://uefi.org/specs/PI/1.8/)
>- Context Menu Integration for Windows


---

## User Guidelines for usage

For Offline Binary modification, these scripts provide easier way to interpret and update the data bytes of binary.
Irrespective of these scripts, changing undesired data in binary could be result to unexpected behavior hence, it is individual's responsibility to make sure to use valid configuration.

## Supported Interface Types

Interface means the way to access memory and I/O of target system.
This scripts needs to read/write memory in order to achieve communication with BIOS driver.
These interface works only when running with elevated privileges are available.
It is responsibility of user to make sure to act with caution before making modification to avoid
corrupting memory/registers with unwanted data.

- Windows
- LINUX
- Offline mode (or stub mode, to enable BIOS/IFWI Editing)

## Prerequisites

- [Python](https://www.python.org/downloads/) software version 3.6 or above
- For Interface setup please refer README document within interface folder itself.

## Installation

Before proceeding with installation, make sure you have updated python setuptools:

```shell
python -m pip install --upgrade setuptools
```

Now Proceed to installation of XmlCli as

```shell
python -m pip install <xmlcli-x.x.x.whl> --proxy <proxy-url>
```

Refer [Installation-Steps](docs/user_guide/installation.md) for more alternate installation instruction.

## Additional Feature and Modules

These modules are extension of core XmlCli API also shows example of how it can be consumed in any independent modules.

| Feature/Module                                                             | Information |
|----------------------------------------------------------------------------| ----------- |
| [Context Menu for Windows OS](src/xmlcli/modules/winContextMenu/README.md) | Installing context menu in windows OS for frequently used APIs |
| [UEFI Binary Parsing](docs/user_guide/uefi_binary_parsing.md)              | Parsing UEFI BIOS Binary file as json information, extracting firmware volumes, ffs etc. |
| [Customizing Logging](docs/user_guide/log_configuration.md)                | Instruction guide on customizing logging |
| [Data analysis of 2 JSON outputs] (docs/user_guide/analytics.md)           | Instructions on performing binary data analysis |

