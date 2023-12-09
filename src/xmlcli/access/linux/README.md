# Linux METHOD

This is access method used for OS with Linux kernel.
Prerequisites would be that OS should expose below files for `root` user (sudoers):
- `/dev/mem` to allow reading physical memory

| Description   | Details              |
| ------------- | -------------------- |
| Access Method | `linux`              |
| Folder Name   | `linux`              |
| Configuration | `linux/linux.ini`    |
| Documentation | `linux/README.md`    |
| Unit Test     | `linux/linuxTest.py` |


## Dependencies:

List out dependencies binaries in order with details. It must answer to basic
question Why is it used?, What is the impact if we don't use it?

1. `libport.lso`
  Linux Shared library file generated from source `port.c` using below commands:
  ```shell
  # 1. Compile `C` source code file to object file
  gcc -c -o port.o port.c
  # 2. Create shared library from object file created in Step 1.
  gcc -shared -o libport.lso port.o
  ```

#### Alternatively to generate library for memory and port use below `Makefile` as below

1. Make sure you are under directory where `Makefile`, `port.c` and `mymem.c` are present i.e. `/linux`
2. Run below shell command:
```shell
make
```
