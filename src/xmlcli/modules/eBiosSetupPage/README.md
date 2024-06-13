# XmlCli's Virtual BIOS Setup Page Gui - Usage for `eBiosSetupPage.py`
======================================================================

> Prerequisite for online mode - BIOS Knobs `XmlCliSupport` and `PublishSetupPgPtr` needs to be set to enable

- open python prompt and run gui

```python
from modules.eBiosSetupPage.eBiosSetupPage import gen_gui  # import method which generates gui
gen_gui()  # generates GUI to launch the virtual setup page
```

- Select valid options in GUI prompt

  - working mode

    - `online`
      - for host system
      - select valid access method for online mode from GUI dropdown menu

    - `offline`
      - for xml/bin/rom file

  - Publish all knobs
    - user can select whether to publish all knobs or not (applicable for **online** mode, and for **bin/rom** file for offline mode)

> Note: For XML or BIOS binary File as input All knobs will be published

#### Prefix of dropdown Knob options selection values in GUI are as below

| Prefix | Interpretation                    |
|--------|-----------------------------------|
| ◇      | Default Value of knob             |
| ◈      | Current value of knob             |
| ◆      | current and default value of knob |

#### Interpretation of buttons on Virtual Setup Page GUI

| Button          | Interpretation                                                                                               |
|-----------------|--------------------------------------------------------------------------------------------------------------|
| Push Changes    | Apply changes to system if online mode else to `bin/rom` file, (N/A for offline xml)                         |
| View Changes    | View saved changes in new window                                                                             |
| Exit            | Exit the GUI                                                                                                 |
| Reload          | Reload the GUI                                                                                               |
| Discard Changes | Discard any change made, any value if modified are restored to current value (`CurrentVal`) of knob xml file |
| Load Defaults   | Restore to default values and revert any changes made                                                        |

#### Status of buttons and action on Virtual Setup Page GUI on various modes/scenarios

| Button          | Online                                 | Offline `.xml` | Online `.xml`                                    | `.bin` or `.rom` file             |
|-----------------|----------------------------------------|----------------|--------------------------------------------------|-----------------------------------|
| Push Changes    | ✔  changes directly written to the SUT | ❌              | ❌ (if _Publish all_ selected in previous option) | ✔ changes written to new bin file |
| View Changes    | ✔                                      | ✔              | ✔                                                | ✔                                 |
| Exit            | ✔                                      | ✔              | ✔                                                | ✔                                 |
| Reload          | ✔                                      | ✔              | ✔                                                | ✔                                 |
| Discard Changes | ✔                                      | ✔              | ✔                                                | ✔                                 |
| Load Defaults   | ✔                                      | ❌              | ❌                                                | ❌                                 |
