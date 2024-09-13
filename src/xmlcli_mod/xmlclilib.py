#
#  Copyright 2024 Hkxs
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the “Software”), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import os

import binascii
import importlib
import logging

from pathlib import Path

from xmlcli_mod.common import configurations
from xmlcli_mod.common.errors import BiosKnobsDataUnavailable
from xmlcli_mod.common.errors import InvalidAccessMethod
from xmlcli_mod.common.errors import InvalidXmlData
from xmlcli_mod.common.errors import XmlCliNotSupported

logger = logging.getLogger(__name__)

cli_access = None

gDramSharedMbAddr = 0

SHAREDMB_SIG1 = 0xBA5EBA11
SHAREDMB_SIG2 = 0xBA5EBA11
SHARED_MB_LEGMB_SIG_OFF = 0x20
SHARED_MB_LEGMB_ADDR_OFF = 0x24
LEGACYMB_SIG = 0x5A7ECAFE

SHAREDMB_SIG1_OFF = 0x00
SHAREDMB_SIG2_OFF = 0x08
CLI_SPEC_VERSION_MINOR_OFF = 0x14
CLI_SPEC_VERSION_MAJOR_OFF = 0x15
CLI_SPEC_VERSION_RELEASE_OFF = 0x17
LEGACYMB_SIG_OFF = 0x20
LEGACYMB_OFF = 0x24
LEGACYMB_XML_OFF = 0x0C
MERLINX_XML_CLI_ENABLED_OFF = 0x28
LEGACYMB_XML_CLI_TEMP_ADDR_OFF = 0x60
ASCII = 0xA5
HEX = 0x16

CliSpecRelVersion = 0x00
CliSpecMajorVersion = 0x00
CliSpecMinorVersion = 0x00

PAGE_SIZE = 0x1000



class CliLib:
    def __init__(self, access_request):
        access_methods = self.get_available_access_methods()
        if access_request in access_methods:
            config_file_path = Path(configurations.XMLCLI_DIR, access_methods[access_request])

            self.access_config = configurations.config_read(config_file_path)
            access_file = self.access_config.get(access_request.upper(), "file")  # Source file of access method
            access_module_path = f"xmlcli_mod.access.{access_request}.{os.path.splitext(access_file)[0]}"
            access_file = importlib.import_module(access_module_path)  # Import access method
            method_class = self.access_config.get(access_request.upper(), "method_class")
            self.access_instance = getattr(access_file, method_class)(access_request)  # create instance of Access method class
        else:
            raise InvalidAccessMethod(access_request)

    @staticmethod
    def get_available_access_methods():
        """Gather all the available access method name and it's configuration file from defined in tool configuration file

        :return: dictionary structure {access_method_name: config_file}
        """
        return {"linux": "access/linux/linux.ini"}

    def set_cli_access(self, access_request=None):
        access_methods = self.get_available_access_methods()
        if access_request in access_methods:
            access_config = os.path.join(configurations.XMLCLI_DIR, access_methods[access_request])
            if os.path.exists(access_config):
                self.access_config = configurations.config_read(access_config)


def set_cli_access(req_access):
    global cli_access
    if not cli_access:
        logger.debug(f"Using '{req_access.lower()}' access")
        cli_instance = CliLib(req_access.lower())
        cli_access = cli_instance.access_instance


def _check_cli_access():
    global cli_access
    if not cli_access:
        # not going to bother with a custom exception in code that needs to be
        # refactored
        raise SystemError("Uninitialized Access")

def read_mem_block(address, size):
    """
    Reads the data block of given size from target memory
    starting from given address.

    > The read data is in bit format.
    > It is converted in string/ASCII to allow manipulated on byte granularity.

    :param address: address from which memory block needs to be read
    :param size: size of block to be read
    :return:
    """
    global cli_access
    _check_cli_access()
    return cli_access.mem_block(address, size)


def mem_save(filename, address, size):
    """
    Saves the memory block of given byte size to desired file

    :param filename: destination file where fetched data will be stored
    :param address: address from which data is to be copied
    :param size: total amount of data to be read
    :return:
    """
    global cli_access
    _check_cli_access()
    return cli_access.mem_save(filename, address, size)


def mem_read(address, size):
    """
    This function reads data from specific memory.
    It can be used to read Maximum `8 bytes` of data.

    > This function cannot be used to read Blocks of data.

    :param address: source address from which data to be read
    :param size: size of the data to be read
    :return:
    """
    global cli_access
    _check_cli_access()
    return int(cli_access.mem_read(address, size))


def mem_write(address, size, value):
    """
    This function writes data to specific memory.
    It can be used to write Maximum `8 bytes` of data.

    > This function cannot be used to write Blocks of data.

    :param address: source address at which data to be written
    :param size: size of the data to be read
    :param value: value to be written
    :return:
    """
    global cli_access
    _check_cli_access()
    return cli_access.mem_write(address, size, value)


def read_io(address, size):
    """
    Read data from IO ports

    :param address: address of port from which data to be read
    :param size: size of data to be read
    :return: integer value read from address
    """
    global cli_access
    _check_cli_access()
    return int(cli_access.read_io(address, size))


def write_io(address, size, value):
    """
    Write requested value of data to specified IO port

    :param address: address of IO port where data to be written
    :param size: amount of data to be written
    :param value: value of data to write on specified address port
    :return:
    """
    global cli_access
    _check_cli_access()
    return cli_access.write_io(address, size, value)


def trigger_smi(smi_val):
    """
    Triggers the software SMI of desired value. Triggering SMI involves writing
    desired value to port 0x72.
    Internally writing to port achieved by write io api

    :param smi_val: Value with which SMI should be triggered
    :return:
    """
    global cli_access
    _check_cli_access()
    return cli_access.trigger_smi(smi_val)


def read_cmos(register_address):
    """
    Read CMOS register value

    :param register_address: CMOS register address
    :return:
    """
    upper_register_val = 0x0 if register_address < 0x80 else 0x2
    write_io(0x70 + upper_register_val, 1, register_address)
    value = read_io(0x71 + upper_register_val, 1)
    return value


def write_cmos(register_address, value):
    """
    Write value to CMOS address register

    :param register_address: address of CMOS register
    :param value: value to be written on specified CMOS register
    :return:
    """
    if register_address < 0x80:
        write_io(0x70, 1, register_address)
        write_io(0x71, 1, value)

    if register_address >= 0x80:
        write_io(0x72, 1, register_address)
        write_io(0x73, 1, value)


def clear_cmos():
    """
    Clear all CMOS locations to 0 and set CMOS BAD flag.

    Writing 0 to CMOS data port and writing register value to CMOS address port,
    CMOS clearing is achived

    CMOS are accessed through IO ports 0x70 and 0x71. Each CMOS values are
    accessed a byte at a time and each byte is individually accessible.

    :return:
    """
    logger.warning('Clearing CMOS')
    for i in range(0x0, 0x80, 1):
        write_io(0x70, 1, i)
        write_io(0x71, 1, 0)
        value = i | 0x80
        if value in (0xF0, 0xF1):
            # skip clearing the CMOS registers which hold Dram Shared MB address.
            continue
        write_io(0x72, 1, value)
        write_io(0x73, 1, 0)
    write_io(0x70, 1, 0x0E)
    write_io(0x71, 1, 0xC0)  # set CMOS BAD flag

    rtc_reg_pci_address = ((1 << 31) + (0 << 16) + (31 << 11) + (0 << 8) + 0xA4)
    write_io(0xCF8, 4, rtc_reg_pci_address)
    rtc_value = read_io(0xCFC, 2)
    rtc_value = rtc_value | 0x4
    write_io(0xCF8, 4, rtc_reg_pci_address)
    write_io(0xCFC, 2, rtc_value)  # set cmos bad in PCH RTC register


def read_buffer(input_buffer, offset, size, input_type):
    """
    This function reads the desired format of data of specified size
    from the given offset of buffer.

    > Input buffer is in big endian ASCII format

    :param input_buffer: buffer from which data to be read
    :param offset: start offset from which data to be read
    :param size: size to be read from buffer
    :param input_type: format in which data can be read (ascii or hex)

    :return: buffer read from input
    """
    value_buffer = input_buffer[offset:offset + size]
    value_string = ''
    if len(value_buffer) == 0:
        return 0
    if input_type == ASCII:
        value_string = "".join(chr(value_buffer[i]) for i in range(len(value_buffer)))
        return value_string
    if input_type == HEX:
        for count in range(len(value_buffer)):
            value_string = f"{value_buffer[count]:02x}" + value_string
        return int(value_string, 16)
    return 0


def un_hex_li_fy(value):
    return binascii.unhexlify((hex(value)[2:]).strip('L')).decode()


def get_cli_spec_version(dram_mb_addr):
    global CliSpecRelVersion, CliSpecMajorVersion, CliSpecMinorVersion
    CliSpecRelVersion = mem_read((dram_mb_addr + CLI_SPEC_VERSION_RELEASE_OFF), 1) & 0xF
    CliSpecMajorVersion = mem_read((dram_mb_addr + CLI_SPEC_VERSION_MAJOR_OFF), 2)
    CliSpecMinorVersion = mem_read((dram_mb_addr + CLI_SPEC_VERSION_MINOR_OFF), 1)
    return f'{CliSpecRelVersion:d}.{CliSpecMajorVersion:d}.{CliSpecMinorVersion:d}'


def fix_leg_xml_offset(dram_mb_addr):
    global CliSpecRelVersion, CliSpecMajorVersion, CliSpecMinorVersion, LEGACYMB_XML_OFF
    LEGACYMB_XML_OFF = 0x0C
    if CliSpecRelVersion == 0:
        if CliSpecMajorVersion >= 7:
            LEGACYMB_XML_OFF = 0x50
            if (CliSpecMajorVersion == 7) and (CliSpecMinorVersion == 0):
                leg_mb_offset = mem_read((dram_mb_addr + LEGACYMB_OFF), 4)
                if leg_mb_offset < 0xFFFF:
                    leg_mb_offset = dram_mb_addr + leg_mb_offset
                if mem_read((leg_mb_offset + 0x4C), 4) == 0:
                    LEGACYMB_XML_OFF = 0x50
                else:
                    LEGACYMB_XML_OFF = 0x4C
    else:
        LEGACYMB_XML_OFF = 0x50


def is_leg_mb_sig_valid(dram_mb_addr):
    global CliSpecRelVersion, CliSpecMajorVersion
    shared_mb_sig1 = mem_read((dram_mb_addr + SHAREDMB_SIG1_OFF), 4)
    shared_mb_sig2 = mem_read((dram_mb_addr + SHAREDMB_SIG2_OFF), 4)
    if (shared_mb_sig1 == SHAREDMB_SIG1) and (shared_mb_sig2 == SHAREDMB_SIG2):
        cli_spec_version = get_cli_spec_version(dram_mb_addr)
        share_mb_entry1_sig = mem_read((dram_mb_addr + LEGACYMB_SIG_OFF), 4)
        if share_mb_entry1_sig == LEGACYMB_SIG:
            fix_leg_xml_offset(dram_mb_addr)
        return cli_spec_version
    return False


def get_dram_mb_addr():
    """
    Read DRAM shared Mailbox from CMOS location 0xBB [23:16] & 0xBC [31:24]

    :return:
    """
    global gDramSharedMbAddr
    write_io(0x72, 1, 0xF0)  # Write a byte to cmos offset 0xF0
    result0 = int(read_io(0x73, 1) & 0xFF)  # Read a byte from cmos offset 0xBB [23:16]
    write_io(0x72, 1, 0xF1)  # Write a byte to cmos offset 0xF1
    result1 = int(read_io(0x73, 1) & 0xFF)  # Read a byte from cmos offset 0xBC [31:24]
    dram_shared_mb_address = int((result1 << 24) | (result0 << 16))  # Get bits [31:24] of the Dram MB address
    if is_leg_mb_sig_valid(dram_shared_mb_address):
        return dram_shared_mb_address

    write_io(0x70, 1, 0x78)  # Write a byte to cmos offset 0x78
    result0 = int(read_io(0x71, 1) & 0xFF)  # Read a byte from cmos offset 0xBB [23:16]
    write_io(0x70, 1, 0x79)  # Write a byte to cmos offset 0x79
    result1 = int(read_io(0x71, 1) & 0xFF)  # Read a byte from cmos offset 0xBC [31:24]
    dram_shared_mb_address = int((result1 << 24) | (result0 << 16))  # Get bits [31:24] of the Dram MB address
    if is_leg_mb_sig_valid(dram_shared_mb_address):
        logger.debug(f'CLI Spec Version = {get_cli_spec_version(dram_shared_mb_address)}')
        logger.debug(f'DRAM_MbAddr = 0x{dram_shared_mb_address:X}')
        return dram_shared_mb_address

    if gDramSharedMbAddr != 0:
        dram_shared_mb_address = int(gDramSharedMbAddr)
        if is_leg_mb_sig_valid(dram_shared_mb_address):
            logger.debug(f'CLI Spec Version = {get_cli_spec_version(dram_shared_mb_address)}')
            logger.debug(f'DRAM_MbAddr = 0x{dram_shared_mb_address:X}')
            return dram_shared_mb_address

    return 0


def verify_xmlcli_support():
    if not get_dram_mb_addr():
        raise XmlCliNotSupported()
    logger.debug('XmlCli is Enabled')


def read_xml_details(dram_shared_mailbox_buffer):
    """
    Get XML Base Address & XML size details from the Shared Mailbox temp buffer

    We will retrieve shared mailbox signature 1 and signature 2 through offsets
    `SHAREDMB_SIG1_OFF` and `SHAREDMB_SIG2_OFF`. If retrieved data matches with
    signatures then we will check for Shared Mailbox entry signature.
    If it matches we will collect XML base address and XML size details
    from `LEGACYMB_OFF` and `LEGACYMB_XML_OFF`.

    :param dram_shared_mailbox_buffer: Shared Mailbox temporary buffer address
    :return:
    """
    shared_mb_sig1 = read_buffer(dram_shared_mailbox_buffer, SHAREDMB_SIG1_OFF, 4, HEX)
    shared_mb_sig2 = read_buffer(dram_shared_mailbox_buffer, SHAREDMB_SIG2_OFF, 4, HEX)
    gbt_xml_addr = 0
    gbt_xml_size = 0
    if (shared_mb_sig1 == SHAREDMB_SIG1) and (shared_mb_sig2 == SHAREDMB_SIG2):
        share_mb_entry1_sig = read_buffer(dram_shared_mailbox_buffer, LEGACYMB_SIG_OFF, 4, HEX)
        if share_mb_entry1_sig == LEGACYMB_SIG:
            logger.debug(f"Legacy MB signature found: {share_mb_entry1_sig}")
            leg_mb_offset = read_buffer(dram_shared_mailbox_buffer, LEGACYMB_OFF, 4, HEX)
            if leg_mb_offset > 0xFFFF:
                gbt_xml_addr = mem_read(leg_mb_offset + LEGACYMB_XML_OFF, 4) + 4
            else:
                gbt_xml_addr = read_buffer(dram_shared_mailbox_buffer, leg_mb_offset + LEGACYMB_XML_OFF, 4, HEX) + 4
            gbt_xml_size = mem_read(gbt_xml_addr - 4, 4)
    return gbt_xml_addr, gbt_xml_size


def is_xml_valid(gbt_xml_address, gbt_xml_size):
    """
    Check if Target XML is Valid or not

    :param gbt_xml_address: Address of GBT XML
    :param gbt_xml_size: Size of GBT XML
    :return:
    """
    try:
        temp_buffer = read_mem_block(gbt_xml_address, 0x08)  # Read/save parameter buffer
        system_start = read_buffer(temp_buffer, 0, 0x08, ASCII)
        temp_buffer = read_mem_block(gbt_xml_address + gbt_xml_size - 0xB, 0x09)  # Read/save parameter buffer
        system_end = read_buffer(temp_buffer, 0, 0x09, ASCII)
        if (system_start == "<SYSTEM>") and (system_end == "</SYSTEM>"):
            return True
        else:
            return False
    except Exception as e:
        logger.error(f'Exception detected when determining if xml is valid.\n {e}')
        return False


# TODO this seems helpful in some way, it can/should be used to determine if
# everything is setup properly on the platform
def is_xml_generated():
    status = 0
    dram_mb_addr = get_dram_mb_addr()  # Get DRam Mailbox Address from Cmos.
    logger.debug(f'CLI Spec Version = {get_cli_spec_version(dram_mb_addr)}')
    logger.debug(f'dram_mb_addr = 0x{dram_mb_addr:X}')
    if dram_mb_addr == 0x0:
        logger.error('Dram Shared Mailbox not Valid, hence exiting')
        return 1
    dram_shared_m_bbuf = read_mem_block(dram_mb_addr, 0x200)  # Read/save parameter buffer
    xml_addr, xml_size = read_xml_details(dram_shared_m_bbuf)  # read GBTG XML address and Size
    if xml_addr == 0:
        logger.error('Platform Configuration XML not yet generated, hence exiting')
        return 1
    if is_xml_valid(xml_addr, xml_size):
        logger.debug('Xml Is Generated and it is Valid')
    else:
        logger.error(f'XML is not valid or not yet generated ADDR = 0x{xml_addr:X}, SIZE = 0x{xml_size:X}')
        status = 1
    return status


def get_xml():

    # TODO add verification of DRAM address using verify_xmlcli_support
    dram_mb_addr = get_dram_mb_addr()  # Get DRam Mailbox Address from Cmos.

    dram_shared_memory_buf = read_mem_block(dram_mb_addr, 0x200)  # Read/save parameter buffer
    xml_addr, xml_size = read_xml_details(dram_shared_memory_buf)  # read GBTG XML address and Size

    logger.debug(f"XML Addr={xml_addr:#x}, XML Size={xml_size:#x}")
    if not xml_addr:
        raise BiosKnobsDataUnavailable()

    if is_xml_valid(xml_addr, xml_size):
        logger.debug("Valid XML data")
        xml_bytearray = read_mem_block(xml_addr, int(xml_size))
        xml_data = xml_bytearray.decode()
    else:
        raise InvalidXmlData(
            f'XML is not valid or not yet generated xml_addr = 0x{xml_addr:X}, xml_size = 0x{xml_size:X}')

    return xml_data


# TODO I see potential on this, but the implementation was really bad
def get_bios_details():
    """
    Extract BIOS Version details from XML.

    Bios details will give detailed description of BIOS populated on platform.
    This description involves Platform Name, Bios Name, BIOS Time Stamp.

    Design Description:
    Get DRAM Mailbox address from CMOS then Read and save parameters buffer.
    After validating xml; first 512 bytes will be copied in temporary buffer
    assuming BIOS attributes will be found within first 512 bytes.

    Then respective attributes will be copied in already allocated temporary buffers.

    :return: Tuple of (Platform name, Bios Name, Bios Timestamp)
    """


def get_efi_compatible_table_base():
    """Search for the EFI Compatible tables in 0xE000/F000 segments

    Use-case would be to find DramMailbox in legacy way
    :return:
    """
    efi_com_tbl_sig = 0x24454649
    index = 0
    for index in range(0, 0x1000, 0x10):
        sig1 = mem_read(0xE0000 + index, 4)
        sig2 = mem_read(0xF0000 + index, 4)
        if sig1 == efi_com_tbl_sig:
            base_address = 0xE0000 + index
            logger.debug(f'Found EfiCompatibleTable Signature at 0x{base_address:X}')
            return base_address
        if sig2 == efi_com_tbl_sig:
            base_address = 0xF0000 + index
            logger.debug(f'Found EfiCompatibleTable Signature at 0x{base_address:X}')
            return base_address
    logger.debug(hex(index))
    return 0


def search_for_system_table_address():
    for address in range(0x20000000, 0xE0000000, 0x400000):  # EFI_SYSTEM_TABLE_POINTER address is 4MB aligned
        signature = mem_read(address, 8)
        if signature == 0x5453595320494249:  # EFI System Table signature = 'IBI SYST'
            address = mem_read((address + 8), 8)
            return address
    return 0


# TODO this also seems kind of helpful
def read_dram_mb_addr_from_efi():
    dram_shared_mail_box_guid_low = 0x4D2C18789D99A394
    dram_shared_mail_box_guid_high = 0x3379C48E6BC1E998
    logger.debug('Searching for Dram Shared Mailbox address from g_st EfiConfigTable..')
    g_st = search_for_system_table_address()
    if g_st == 0:
        efi_compatible_table_base = get_efi_compatible_table_base()
        if efi_compatible_table_base == 0:
            return 0
        g_st = mem_read(efi_compatible_table_base + 0x14, 4)
    signature = mem_read(g_st, 8)
    if signature != 0x5453595320494249:  # EFI System Table signature = 'IBI SYST'
        return 0
    logger.debug(
        f'EFI SYSTEM TABLE Address = 0x{g_st:X}  signature = \"{un_hex_li_fy(signature)[::-1]}\"    Revision = {mem_read(g_st + 8, 2):d}.{mem_read(g_st + 0xA, 2):d}')
    count = 0
    firmware_ptr = mem_read(g_st + 0x18, 8)
    firmware_revision = mem_read(g_st + 0x20, 4)
    bios_str = ''
    while 1:
        value = int(mem_read(firmware_ptr + count, 2))
        if value == 0:
            break
        bios_str = bios_str + chr((value & 0xFF))
        count = count + 2
    logger.debug(f'Firmware : {bios_str}')
    logger.debug(f'Firmware Revision: 0x{firmware_revision:X}')
    efi_config_tbl_entries = mem_read(g_st + 0x68, 8)
    efi_config_tbl = mem_read(g_st + 0x70, 8)
    logger.debug(f'efi_config_tbl_entries = {efi_config_tbl_entries:d}  efi_config_tbl Addr = 0x{efi_config_tbl:X}')
    offset = 0
    dram_mailbox_addr = 0
    for Index in range(0, efi_config_tbl_entries):
        guid_low = mem_read(efi_config_tbl + offset, 8)
        guid_high = mem_read(efi_config_tbl + 8 + offset, 8)
        if (guid_low == dram_shared_mail_box_guid_low) and (guid_high == dram_shared_mail_box_guid_high):
            dram_mailbox_addr = int(mem_read(efi_config_tbl + 16 + offset, 8))
            logger.info(f'Found Dram Shared MailBox Address = 0x{dram_mailbox_addr:X} from EfiConfigTable')
            break
        offset = offset + 0x18
    return dram_mailbox_addr


# TODO I want to revisit this method to learn about this legacy memory map
def print_e820_table():
    """Legacy function for printing E820 table for memory type identification using
    legacy efi compatible table

    EFI ST offset = 0x14
    ACPI table offset = 0x1C
    E820 Table offset = 0x22
    E820 table length = 0x26

    :return:
    """
    offset = 0
    index = 0
    e820_table_list = {}
    efi_compatible_table_base = get_efi_compatible_table_base()
    e820_ptr = mem_read(efi_compatible_table_base + 0x22, 4)
    size = mem_read(efi_compatible_table_base + 0x26, 4)
    logger.debug(',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,')
    logger.debug('E820[no]: Start Block Address ---- End Block Address , type = Mem type')
    logger.debug('``````````````````````````````````````````````````````````````````````')
    while 1:
        base_addr = mem_read(e820_ptr + offset, 8)
        length = mem_read(e820_ptr + offset + 8, 8)
        mem_type = mem_read(e820_ptr + offset + 16, 4)
        logger.debug(f'E820[{index:2d}]:  0x{base_addr:16X} ---- 0x{(base_addr + length):<16X}, mem type = 0X{mem_type:x} ')
        e820_table_list[index] = [base_addr, length, mem_type]
        index = index + 1
        offset = offset + 20
        if offset >= size:
            break
    logger.debug(',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,')
    return e820_table_list
