## Usage instruction for Uefi Parser

The parser is able to generate the json representation from BIOS or IFWI image.

Key features:
-   JSON representation, lightweight database with keys and values with ease of readability
-   Works with both SUT and offline image
-   Replace new driver in a bios image.

Working with SUT:

Below command to be executed only after enabling applicable access method:

```python
from xmlcli import XmlCli as cli

max_bios_size = 12 * (1024**2)  # 12 MB - configure based on the platform used
# If max_bios_size argument is not specified then by default it uses 32 MB dump to lookup for BIOS image
bios_image = cli.clb.get_bin_file("linux", max_bios_size=max_bios_size)  # variable will have location of bios image dump stored from memory
```

Initiate the Parsing with below commands:

```python
from xmlcli.common import bios_fw_parser

bios_image = "absolute-path/to/bios-image.rom"

uefi_parser = bios_fw_parser.UefiParser(bin_file=bios_image,  # binary file to parse
                                parsing_level=0,  # parsing level to manage number of parsing features
                                base_address=0,  # (optional) provide base address of bios FV region to start the parsing (default 0x0)
                                guid_to_store=[]  # if provided the guid for parsing then parser will look for every GUID in the bios image
                                )
# parse binary
output_dict = uefi_parser.parse_binary()
output_dict = uefi_parser.sort_output_fv(output_dict)  # (optional) only to sort output by FV address
# write content to json file
output_file = "absolute-path/to/output.json"
uefi_parser.write_result_to_file(output_file, output_dict=output_dict)
# Below code block is only to store map result to json for FV region(s) extracted by guid lookup
if uefi_parser.guid_to_store:
    # additional test for GUIDs to store
    result = uefi_parser.guid_store_dir  # result of passed guid
    user_guid_out_file = "absolute-path/to/guid-stored/output.json"
    # Store guid stored result to json file
    uefi_parser.write_result_to_file(user_guid_out_file, output_dict=uefi_parser.stored_guids)
```



Replace the Driver Ffs in Binary with below commands:
```python
from xmlcli.common import bios_fw_parser

bios_image = "absolute-path/to/bios-image.rom"
driver_image = "absolute-path/to/driver_image.ffs"
output_image = "absolute-path/to/replaced_bios_image.rom"

uefi_parser = bios_fw_parser.UefiParser(bin_file=bios_image,  # binary file to parse
                                parsing_level=0,  # parsing level to manage number of parsing features
                                base_address=0,  # (optional) provide base address of bios FV region to start the parsing (default 0x0)
                                guid_to_store=[]  # if provided the guid for parsing then parser will look for every GUID in the bios image
                                )

newffs_parser = bios_fw_parser.UefiParser(bin_file=driver_image,  # binary file to parse
                                parsing_level=0,  # parsing level to manage number of parsing features
                                base_address=0,  # (optional) provide base address of bios FV region to start the parsing (default 0x0)
                                guid_to_store=[]  # if provided the guid for parsing then parser will look for every GUID in the bios image
                                )

# parse bios image into a binary_tree
bios_output_dict = uefi_parser.parse_binary()

# parse driver ffs image into a binary tree node
ffs_output_dict = newffs_parser.parse_binary()
# get the target ffs guid through ffs file, extract the target tree node
TargetFfsGuid = newffs_parser.binary_tree.Position.ChildNodeList[0].Data.Name
newffsnode = newffs_parser.binary_tree.Position.ChildNodeList[0]

# replace the target ffs with new one
uefi_parser.find_ffs_node(TargetFfsGuid)
uefi_parser.ReplaceFfs(newffsnode, uefi_parser.TargetFfsList[0])
uefi_parser.binary_tree.WholeTreeData = b''
uefi_parser.Encapsulate_binary(uefi_parser.binary_tree)
# dump the bios image with replaced ffs info
uefi_parser.dump_binary(replaced_image)
```