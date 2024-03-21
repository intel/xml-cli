import os

from xmlcli import XmlCli as cli
from xmlcli.common import bios_fw_parser

workspace_dir = r"D:\PublicShare\gahan\_debug\NVL_bios_data_bin"
bin_file = os.path.join(workspace_dir, "BIOS_NVL_S_Internal_0462.00_Dispatch_VS__PreProd.rom")
# bin_file = os.path.join(workspace_dir, "MTL_FSPWRAPPER_3184_01_R.rom")
output_xml = f"{bin_file}.xml"
output_json = f"{bin_file}.json"

uefi_parser = bios_fw_parser.UefiParser(bin_file=bin_file,
                                        parsing_level=0,
                                        base_address=0x0,
                                        guid_to_store=[cli.fwp.gBiosKnobsDataBinGuid]
                                        )
# parse binary
output_dict = uefi_parser.parse_binary()
output_dict = uefi_parser.sort_output_fv(output_dict)
# write content to json file
uefi_parser.write_result_to_file(output_json, output_dict=output_dict)

cli.savexml(output_xml, bin_file)
