# UFFAF - UEFI Firmware Foundational Automation Framework (formerly XmlCli)

UFFAF allows firmware modification as an efficient operation with scriptable approach through various interfaces with an intention to reduce manual interventions. Entire Client and Server ecosystem ranging from Silicon Validation teams to Tools teams running on different OS. UFFAF (formerly XmlCli) Interface is basically a combination of 2 methodologies, XML (System or Platform Information to be consumed in XML format) & CLI (BIOS Command Line Interface protocol which acts as an interface between BIOS & outside environment via S/W SMI or UEFI runtime interface). In short UFFAF (formerly XML CLI) is the interface methodology between BIOS & External world Tool is the combination of Python Scripts and utilities that helps the end user/automation to perform desired operations using available BIOS Driver interface.



These reference scripts provides several capabilities including but not limited to:
>- Parsing Information of UEFI BIOS Firmware as per [Platform Initialization Specification](https://uefi.org/specs/PI/1.8/)
>- Programming/Reading BIOS knobs with CLI and GUI
>- Fetching Platform XML from target
>- System information
>- CommandLine and web based GUI support for get and set NVAR (UEFI NVRAM variable)
>- Context Menu Integration for Windows

These scripts are generic and platform/program independent (as long as BIOS on SUT BIOS supports XML CLI interface).

---

## User Guidelines for usage

These scripts are provided as reference scripts and requires to have bios driver  enabled in order to use the functionality.

As scripts require to read/write memory of the target device/system, valid access interface would be required which can be configured at [config file](src/xmlcli/xmlcli.config).

For Offline Binary modification, these scripts provide easier way to interpret and update the data bytes of binary.
Irrespective of these scripts, changing undesired data in binary could be result to unexpected behavior hence, it is individual's responsibility to make sure to use valid configuration.

As Accessing target SUT is only possible at **Elevated Privilege**, we recommend proceeding with caution if service API of these scripts are exposed over network.

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
- If running on Online mode; **elevated privileges** are required to execute commands as it involves accessing hardware memory resource.
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


## Setting Interface Type

Need to select the interface to indicate the scripts on which access method to use (depending on which environment we expect the script to operate in).

```python
from xmlcli import XmlCli as cli
cli.clb._setCliAccess("<access-method>")
```

Below are listed valid `<access-method>`:

| Access Method | Remarks |
| --- | --- |
| `linux` | For using linux as interface, need to open Python Prompt in root permissions. |
| `winrwe` | For using `RW.exe` as Windows interface (**slow**, least recommended). For more details refer [winrwe/README.md](src/xmlcli/access/winrwe/README.md) |


## Running popular commands

After initializing the desired interface, the use may run following commands.

If the commands `return 0`, it means the operation was `successful`, else there was an error.

### Standard import steps

```python
from xmlcli import XmlCli as cli
cli.clb._setCliAccess("linux")  # Set desired Interface (for example `linux` if using on `linux` SUT)
```

### Step to check XmlCli capability on current System

```python
from xmlcli import XmlCli as cli
cli.clb.ConfXmlCli()  # Check if XmlCli is supported &/ Enabled on the current system.
```

| Return value of `cli.clb.ConfXmlCli` | Meaning |
| --- | --- |
| 0 | XmlCli is already **supported & enabled**. |
| 1 | XmlCli is **not supported** on the current BIOS or the System BIOS has not completed Boot. |
| 2 | XmlCli is **supported** but was **not enabled**, the script has now enabled it and **SUT needs reboot** to make use of XmlCli. |

### To Save Target XML file

```python
from xmlcli import XmlCli as cli
# For Online
# Run common import steps and make sure `cli.clb.ConfXmlCli()` returns `0`
cli.savexml()  # Save Target XML as `<Path_To_XmlCliRefScripts>/out/PlatformConfig.xml` file.
cli.savexml(r"path/to/file.xml")  # Save Target XML as absolute file location for `path/to/file.xml`.

# For Offline
cli.savexml(0, r"path/to/ifwi-or-bios.bin")  # Extract the XML data from desired BIOS or IFWI binary. Will Save Target XML in `<Path_To_XmlCliRefScripts>/out/` folder.
cli.savexml(r"path/to/file.xml", r"path/to/ifwi-or-bios.bin")  # Extract the XML data from desired BIOS or IFWI binary. Will Save Target XML as `path/to/file.xml`.
```

### To Read BIOS settings

> For **Online** command to run successfully, the target must complete BIOS boot.
> For **Offline** mode, you need to pass the link to BIOS or IFWI binary.

- `Knob_A` & `Knob_B` in the below examples are the knob names taken from the `name` attribute from the `<biosknobs>` section in the XML, it is **case sensitive**.

```python
from xmlcli import XmlCli as cli
cli.CvReadKnobs("Knob_A=Val_1, Knobs_B=Val_2") # Reads the desired Knob_A & Knob_B settings from the SUT and verifies them against Val_1 & Val_2 respectively.
cli.CvReadKnobs()  # same as above, just that the Knob entries will be read from the default cfg file (`<Path_To_XmlCliRefScripts>/cfg/BiosKnobs.ini`).
# For Offline
cli.CvReadKnobs("Knob_A=Val_1, Knobs_B=Val_2", r"path/to/ifwi-or-bios.bin")  # Reads & verifies the desired knob settings from the given BIOS or IFWI binary.
cli.CvReadKnobs(0, r"path/to/ifwi-or-bios.bin") # same as above, just that the Knob entries will be read from the `cli.clb.KnobsIniFile` cfg file instead.

# the default cfg file pointer can be programed to desired cfg file via following command.
cli.clb.KnobsIniFile = r"path/to/bios-config.ini"
```

### To Program BIOS settings

> For **Online** command to run successfully, the target must complete BIOS boot.
> For **Offline** mode, you need to pass the link to BIOS or IFWI binary.

- `Knob_A` & `Knob_B` in the below examples are the knob names taken from the `name` attribute from the `<biosknobs>` section in the XML, it is **case sensitive**.

```python
from xmlcli import XmlCli as cli
cli.CvProgKnobs("Knob_A=Val_1, Knobs_B=Val_2")  # Programs the desired Knob_A & Knob_B settings on the SUT and verifies them against Val_1 & Val_2 respectively.
cli.CvProgKnobs()  # same as above, just that the Knob entries will be Programed from the default cfg file (<Path_To_XmlCliRefScripts>\cfg\BiosKnobs.ini).
# For Offline
cli.CvProgKnobs("Knob_A=Val_1, Knobs_B=Val_2", r"path/to/ifwi-or-bios.bin")  # Program the desired knob settings as new default value, operates on BIOS or IFWI binary, new BIOS or IFWI binary will be generated with desired settings.
cli.CvProgKnobs(0, r"path/to/ifwi-or-bios.bin")  # same as above, just that the Knob entries will be Programed from the cli.clb.KnobsIniFile cfg file instead.

# the default cfg file pointer can be programed to desired cfg file via following command.
cli.clb.KnobsIniFile = r"path/to/bios-config.ini"

# To Load Default BIOS settings on the SUT. Offline mode not supported or not Applicable.
cli.CvLoadDefaults()  # Loads/Restores the default value back on the system, also shows which values were restored back to its default Value.
```

### To Program only desired BIOS settings and reverting rest all settings back to its default value

> **Offline** mode not supported or not Applicable.

- `Knob_A` & `Knob_B` in the below examples are the knob names taken from the `name` attribute from the `<biosknobs>` section in the XML, it is **case sensitive**.

```python
from xmlcli import XmlCli as cli
cli.CvRestoreModifyKnobs("Knob_A=Val_1, Knobs_B=Val_2")  # Programs the desired Knob_A & Knob_B settings and restores everything else back to its default value.
cli.CvRestoreModifyKnobs()  # same as above, just that the Knob entries will be Programed from the cli.clb.KnobsIniFile cfg file instead.
# the default cfg file pointer can be programed to desired cfg file via following command.
cli.clb.KnobsIniFile = r"path/to/bios-config.ini"
```

> Offline editing of BIOS will update FV_BB section of BIOS.
> This is an expected to produce boot issue with Secure Boot profiles (i.e. Secure Profile images)

To make sure offline Edited BIOSes for Knob changes boot fine with Secure Profile IFWI's,
user need to supply the re-signing script/pkg. This is user's full responsibility to manage an executable script
which syntax should follow as:

```shell
file/to/executable/signing-resigning.bat input.bin output/path.bin
```

```python
from xmlcli import XmlCli as cli

cli.fwp.SecureProfileEditing = True   # if not set to True, Re-Signing Process will be skipped
cli.fwp.ReSigningFile = r'path/to/resigning/executable/ResignIbbForBtG.bat'  # by default this variable is empty, please populate this variable with Re-Signing Script File Ptr
cli.CvProgKnobs('BootFirstToShell=1, EfiNetworkSupport=3', r'path/to/ifwi-or-bios.bin')
```

> **Note** - Providing Secure Profile resigning script/executable is out of scope of XmlCli,
> User need to gather required executable in order to utilize this functionality on SecureProfile.


### Add MSR & IO Read/Write CLI functions (`Only for DCG`)

#### Usage Syntax

```python
from xmlcli import XmlCli as cli

cli.IoAccess("<operation>", "<IoPort>", "<Size>", "<IoValue>")
cli.MsrAccess("<operation>", "<MsrNumber>", "<ApicId>", "<MsrValue>")
```

#### Example

```python
from xmlcli import XmlCli as cli

cli.IoAccess(cli.clb.IO_WRITE_OPCODE, 0x84, 1, 0xFA)
cli.IoAccess(cli.clb.IO_READ_OPCODE, 0x84, 1)
cli.MsrAccess(cli.clb.READ_MSR_OPCODE, 0x53, 0)
cli.MsrAccess(cli.clb.WRITE_MSR_OPCODE, 0x1A0, 0, 0x1)
```

## Execution under EFI Shell

### Using XmlCli EFI App

EFI App is located under `tools/XmlCliKnobs.efi`, below commands can be executed on UEFI Shell:

| Command | Description |
| ------- | ----------- |
| `XmlCliKnobs.efi CX` | Ensure XmlCli is enabled, if it's not enable, this command helps to enable XmlCli, Reboot SUT if XmlCli was not enabled. |
| `XmlCliKnobs.efi -v` | Get version information of the efi App |
| `XmlCliKnobs.efi GX` | Generate Bios Knobs xml dump |
| `XmlCliKnobs.efi` | List out all possible available commands |


## Additional Feature and Modules

These modules are extension of core XmlCli API also shows example of how it can be consumed in any independent modules.

| Feature/Module                                                             | Information                                                                              |
|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [UEFI Variable Modification GUI](src/xmlcli/modules/webgui/README.md)      | Web based GUI implementation for UEFI Variable modification APIs                         |
| [Context Menu for Windows OS](src/xmlcli/modules/winContextMenu/README.md) | Installing context menu in windows OS for frequently used APIs                           |
| [UEFI Binary Parsing](docs/user_guide/uefi_binary_parsing.md)              | Parsing UEFI BIOS Binary file as json information, extracting firmware volumes, ffs etc. |
| [Customizing Logging](docs/user_guide/log_configuration.md)                | Instruction guide on customizing logging |

