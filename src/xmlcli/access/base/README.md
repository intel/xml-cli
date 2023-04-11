# BASE ACCESS METHOD

Every new access Interface which is designed to be integrated with XmlCli must include the file and folder structure from this pattern

Below are the key parameter to be focused on:

`<method-name>` defines method name
below must be the structure and mandatory checklist to complete to add integrate any new access method to xmlcli:

|               | Syntax                               | Example              |
|---------------|--------------------------------------|----------------------|
| Access Method | `<method-name>`                      | `linux`              |
| Folder Name   | `<method-name>`                      | `linux`              |
| Configuration | `<method-name>/<method-name>.ini`    | `linux/linux.ini`    |
| Documentation | `<method-name>/README.md`            | `linux/README.md`    |
| Unit Test     | `<method-name>/<method-name>Test.py` | `linux/linuxTest.py` |

Any other dependency binary file should be part of this access folder itself.

## Dependencies:

List out dependencies binaries in order with details. It must answer to basic
question Why is it used?, What is the impact if we don't use it?

1. Dependency A
  - Details about dependency A
2. Dependency B
  - Details about dependency B

