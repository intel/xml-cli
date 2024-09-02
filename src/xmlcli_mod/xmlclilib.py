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
import sys
import time
import copy
import binascii
import importlib
import logging
import defusedxml.ElementTree as ET
from xml.etree.ElementTree import ElementTree

from xmlcli_mod.common import utils
from xmlcli_mod.common import configurations
from xmlcli_mod.common.errors import InvalidXmlData
from xmlcli_mod.common.errors import BiosKnobsDataUnavailable
from xmlcli_mod.common.errors import XmlCliNotSupported


log = logging.getLogger(__name__)

cliaccess = None
FlexConCfgFile = False
ForceReInitCliAccess = False
UfsFlag = False
KnobsIniFile = configurations.BIOS_KNOBS_CONFIG
XmlCliToolsDir = configurations.TOOL_DIR
TianoCompressUtility = configurations.TIANO_COMPRESS_BIN
BrotliCompressUtility = configurations.BROTLI_COMPRESS_BIN

TempFolder = configurations.OUT_DIR

KnobsXmlFile = os.path.join(TempFolder, 'BiosKnobs.xml')
PlatformConfigXml = os.path.join(TempFolder, 'PlatformConfig.xml')
PlatformConfigLiteXml = os.path.join(TempFolder, 'PlatformConfigLite.xml')
SvXml = os.path.join(TempFolder, 'SvPlatformConfig.xml')

TmpKnobsIniFile = os.path.join(TempFolder, 'TmpBiosKnobs.ini')
JSON_OUT_FILE = os.path.join(TempFolder, 'json_output.json')
OutBinFile = ''
gDramSharedMbAddr = 0
MerlinxXmlCliEnableAddr = 0
InterfaceType = configurations.ACCESS_METHOD
XmlCliLogFile = os.path.join(TempFolder, 'XmlCli.log')
XmlCliRespFlags = {'Status': 0, 'CantExe': 0, 'WrongParam': 0, 'TimedOut': 0, 'SideEffect': 'NoSideEffect'}
LastErrorSig = 0x0000
LastErrorSigDict = {int(key, 16): value["msg"] for key, value in utils.STATUS_CODE_RECORD.items()}

CliRespFlags = 0

SHAREDMB_SIG1 = 0xBA5EBA11
SHAREDMB_SIG2 = 0xBA5EBA11
SHARED_MB_LEGMB_SIG_OFF = 0x20
SHARED_MB_LEGMB_ADDR_OFF = 0x24
LEGACYMB_SIG = 0x5A7ECAFE
XML_START = '<SYSTEM>'
XML_END = '</SYSTEM>'
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
STRING = 0x51
ASCII = 0xA5
HEX = 0x16
SETUP_KNOBS_ADDR_OFF = 0x13C
SETUP_KNOBS_SIZE_OFF = 0x140
CPUSV_MAILBOX_ADDR_OFF = 0x14C
XML_CLI_DISABLED_SIG = 0xCD15A1ED
SHARED_MB_CLI_REQ_BUFF_SIG = 0xCA11AB1E
SHARED_MB_CLI_RES_BUFF_SIG = 0xCA11B0B0
SHARED_MB_CLI_REQ_BUFF_SIG_OFF = 0x30
SHARED_MB_CLI_RES_BUFF_SIG_OFF = 0x40
SHARED_MB_CLI_REQ_BUFF_ADDR_OFF = 0x34
SHARED_MB_CLI_RES_BUFF_ADDR_OFF = 0x44
SHARED_MB_CLI_REQ_BUFF_SIZE_OFF = 0x38
SHARED_MB_CLI_RES_BUFF_SIZE_OFF = 0x48
CLI_REQ_READY_SIG = 0xC001C001
CLI_RES_READY_SIG = 0xCAFECAFE
CLI_REQ_RES_READY_SIG_OFF = 0x00
CLI_REQ_RES_READY_CMD_OFF = 0x04
CLI_REQ_RES_READY_FLAGS_OFF = 0x06
CLI_REQ_RES_READY_STATUS_OFF = 0x08
CLI_REQ_RES_READY_PARAMSZ_OFF = 0x0C
CLI_REQ_RES_BUFF_HEADER_SIZE = 0x10
WRITE_MSR_OPCODE = 0x11
READ_MSR_OPCODE = 0x21
IO_READ_OPCODE = 0x31
IO_WRITE_OPCODE = 0x32
APPEND_BIOS_KNOBS_CMD_ID = 0x48
RESTOREMODIFY_KNOBS_CMD_ID = 0x49
READ_BIOS_KNOBS_CMD_ID = 0x4A
LOAD_DEFAULT_KNOBS_CMD_ID = 0x4B
PROG_BIOS_CMD_ID = 0xB4
FETCH_BIOS_CMD_ID = 0xB5
BIOS_VERSION_OPCODE = 0xB1
EXE_SV_SPECIFIC_CODE_OPCODE = 0x300
READ_BRT_OPCODE = 0x310
CREATE_FRESH_BRT_OPCODE = 0x311
ADD_BRT_OPCODE = 0x312
DEL_BRT_OPCODE = 0x313
DIS_BRT_OPCODE = 0x314
GET_SET_VARIABLE_OPCODE = 0x9E5E
CLI_KNOB_APPEND = 0x0
CLI_KNOB_RESTORE_MODIFY = 0x1
CLI_KNOB_READ_ONLY = 0x2
CLI_KNOB_LOAD_DEFAULTS = 0x3

CliSpecRelVersion = 0x00
CliSpecMajorVersion = 0x00
CliSpecMinorVersion = 0x00

MAXIMUM_BIOS_MEMORY_MAP = 0xFFFFFFFF
PAGE_SIZE = 0x1000
FIRMWARE_BASE_MASK_ALIGNMENT = (MAXIMUM_BIOS_MEMORY_MAP - PAGE_SIZE + 0x1)

CliCmdDict = {APPEND_BIOS_KNOBS_CMD_ID: 'APPEND_BIOS_KNOBS_CMD_ID',
              RESTOREMODIFY_KNOBS_CMD_ID: 'RESTOREMODIFY_KNOBS_CMD_ID',
              READ_BIOS_KNOBS_CMD_ID: 'READ_BIOS_KNOBS_CMD_ID', LOAD_DEFAULT_KNOBS_CMD_ID: 'LOAD_DEFAULT_KNOBS_CMD_ID',
              PROG_BIOS_CMD_ID: 'PROG_BIOS_CMD_ID', FETCH_BIOS_CMD_ID: 'FETCH_BIOS_CMD_ID',
              BIOS_VERSION_OPCODE: 'BIOS_VERSION_OPCODE', EXE_SV_SPECIFIC_CODE_OPCODE: 'EXE_SV_SPECIFIC_CODE_OPCODE',
              READ_MSR_OPCODE: 'READ_MSR_OPCODE', WRITE_MSR_OPCODE: 'WRITE_MSR_OPCODE',
              IO_READ_OPCODE: 'IO_READ_OPCODE', IO_WRITE_OPCODE: 'IO_WRITE_OPCODE',
              READ_BRT_OPCODE: 'READ_BRT_OPCODE', CREATE_FRESH_BRT_OPCODE: 'CREATE_FRESH_BRT_OPCODE',
              ADD_BRT_OPCODE: 'ADD_BRT_OPCODE',
              DEL_BRT_OPCODE: 'DEL_BRT_OPCODE', DIS_BRT_OPCODE: 'DIS_BRT_OPCODE'}

Xml_Sanitization_Mapping = {0x00: 0x20, 0x01: 0x20, 0x02: 0x20, 0x03: 0x20, 0x04: 0x20, 0x05: 0x20, 0x06: 0x20,
                            0x07: 0x20, 0x08: 0x20, 0x0B: 0x20, 0x0C: 0x20, 0x0E: 0x20, 0x0F: 0x20, 0x10: 0x20,
                            0x11: 0x20, 0x12: 0x20, 0x13: 0x20, 0x14: 0x20, 0x15: 0x20, 0x16: 0x20, 0x17: 0x20,
                            0x18: 0x20, 0x19: 0x20, 0x1A: 0x20, 0x1B: 0x20, 0x1C: 0x20, 0x1D: 0x20, 0x1E: 0x20,
                            0x1F: 0x20, 0x7F: 0x20, 0xB5: 0x75, 0x26: 0x6E, 0xA0: 0x2E, 0xB0: 0x20}

# Constants for Bitwise Knobs
BITWISE_KNOB_PREFIX = 0xC0000


def and_mask(width, unit="byte"):
    """Generate And Mask with all 1's for bit

    :param width: width of the data, default in bytes
    :param unit: unit in which data to be interpreted
    :return:
    all width bits set to 1 for given width
    """
    if unit.lower() in ("byte", "bytes", "b"):
        multiplier = 8
    elif unit.lower() in ("kilobyte", "kilobytes", "kb"):
        multiplier = 8 * 1024
    else:
        multiplier = 1
    return (2 ** (width * multiplier)) - 1


def get_bitwise_knob_details(knob_size, knob_offset, padding=0x8000):
    """Calculate Knob width for bitwise and non-bitwise knobs

    :param knob_size: size of the knob as per bios knobs data bin
    :param knob_offset: offset of the knob as per bios knobs data bin
    :param padding: Add 0x8000 to offset to Set BIT15 of Offset to indicate this is Bitwise knob
    :return: knob_width, knob_offset, bit_offset
    """
    knob_offset = knob_offset & 0x3FFFF
    bit_offset = int(knob_offset % 8)
    knob_offset = int(knob_offset / 8) + padding
    knob_width = bit_offset + knob_size
    if knob_width % 8:
        knob_width = int(knob_width / 8 + 1)
    else:
        knob_width = int(knob_width / 8)
    return knob_width, knob_offset, bit_offset


class CliLib(object):
    def __init__(self, access_request=None, *args, **kwargs):
        access_methods = self.get_available_access_methods()
        error_flag = access_request not in access_methods
        if access_request in access_methods:
            access_config_location = os.path.join(configurations.XMLCLI_DIR, access_methods[access_request])
            access_file_name = os.path.splitext(os.path.basename(access_config_location))[0]
            if os.path.exists(access_config_location):
                self.access_config = configurations.config_read(access_config_location)
                access_file = self.access_config.get(access_file_name.upper(), "file")  # Source file of access method
                access_file_location = "xmlcli_mod.access.{}.{}".format(access_file_name,
                                                                        os.path.splitext(access_file)[0])
                access_file = importlib.import_module(access_file_location)  # Import access method
                method_class = self.access_config.get(access_file_name.upper(), "method_class")
                self.access_instance = getattr(access_file, method_class)(
                    access_file_name)  # create instance of Access method class
            else:
                error_flag = True
        if error_flag:
            raise utils.XmlCliException(error_code="0x3001")  # Refer messages.json for meaning of error code

    @staticmethod
    def get_available_access_methods():
        """Gather all the available access method name and it's configuration file from defined in tool configuration file

        :return: dictionary structure {access_method_name: config_file}
        """
        access_methods = dict(configurations.XMLCLI_CONFIG['ACCESS_METHODS'])
        return access_methods

    def set_cli_access(self, access_request=None):
        access_methods = self.get_available_access_methods()
        if access_request in access_methods:
            access_config = os.path.join(configurations.XMLCLI_DIR, access_methods["access_request"])
            if os.path.exists(access_config):
                self.access_config = configurations.config_read(access_config)


def set_cli_access(req_access=None):
    global cliaccess, InterfaceType, _isExeAvailable, LastErrorSig
    if req_access != None:
        InterfaceType = req_access
        cli_instance = CliLib(InterfaceType.lower())
        cliaccess = cli_instance.access_instance  # Assign access method instance


def _checkCliAccess():
    global cliaccess, ForceReInitCliAccess
    if ((cliaccess == None) or (ForceReInitCliAccess)):
        set_cli_access()


def haltcpu(delay=0):
    """
    This function will check the CPU state only when Interface type is
    debug interface used between host and target.

    If target CPU is already halted then this function
    will return without taking any action.
    If target CPU is running it will issue `halt()` command.

    :param delay: wait time in seconds for command execution
    :return: status of halt action from interface
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.halt_cpu(delay)


def runcpu():
    """
    This function will check the CPU state only when Interface type is
    debug interface used between host and target.

    If target CPU is already halted then this function
    will return without taking any action.
    If target CPU is running it will issue `go()` command.

    :return: status of run cpu action from interface
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.run_cpu()


def InitInterface():
    global cliaccess
    _checkCliAccess()
    return cliaccess.initialize_interface()


def CloseInterface():
    global cliaccess
    _checkCliAccess()
    return cliaccess.close_interface()


def warmreset():
    """
    Resets system without actually interrupting system power.
    Value `0x06` to PCI register `0xCF9` is written to achieve the warm reset.

    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.warm_reset()


def coldreset():
    """
    Cold reset is one of the type of system reboot whereby the power to the system
    is physically turned OFF and back ON again.
    Value `0x0E` to PCI register `0xCF9` is written to achieve the cold reset.

    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.cold_reset()


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
    global cliaccess
    _checkCliAccess()
    return cliaccess.mem_block(address, size)


def memsave(filename, address, size):
    """
    Saves the memory block of given byte size to desired file

    :param filename: destination file where fetched data will be stored
    :param address: address from which data is to be copied
    :param size: total amount of data to be read
    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.mem_save(filename, address, size)


def memdump(address, size, unit=1):
    """
    Dumps the memory content of given byte size in
    respective units on to the console

    :param address: address from which data is to be copied
    :param size: total amount of data to be read
    :param unit: unit length in which data to be displayed (choices are: 1|2|4|8)
    :return:
    """
    TempDataBinFile = os.path.join(os.path.dirname(KnobsXmlFile), 'MemData_%X.bin' % address)
    memsave(TempDataBinFile, address, size)
    with open(TempDataBinFile, 'rb') as TempData:
        ListBuff = list(TempData.read())
    log.debug('________________________________________________________________________________')
    if unit == 1:
        log.debug('             Address | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C | D | E | F |')
        log.debug('---------------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    elif unit == 2:
        log.debug(
            '             Address |       0       |       2       |       4       |       6       |       8       |       A       |       C       |       E       |')
        log.debug('---------------|-------|-------|-------|-------|-------|-------|-------|-------|')
    elif unit == 4:
        log.debug(
            '             Address |               0               |               4               |               8               |               C               |')
        log.debug('---------------|---------------|---------------|---------------|---------------|')
    elif unit == 8:
        log.debug(
            '             Address |                               0                               |                               8                               |')
        log.debug('---------------|-------------------------------|-------------------------------|')
    CurAddr = address
    for count in range(0, int(size / 0x10)):
        Value = ListBuff[(count * 0x10):((count * 0x10) + 16)]
        if unit == 1:
            log.debug(
                ' %13s |%02X  %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X    %02X |' % (
                ('0x%lX' % CurAddr), Value[0], Value[1], Value[2], Value[3], Value[4], Value[5], Value[6], Value[7],
                Value[8], Value[9], Value[10], Value[11], Value[12], Value[13], Value[14], Value[15]))
        elif unit == 2:
            log.debug(
                ' %13s |0x%02X%02X    0x%02X%02X  0x%02X%02X  0x%02X%02X  0x%02X%02X  0x%02X%02X  0x%02X%02X  0x%02X%02X |' % (
                ('0x%lX' % CurAddr), Value[1], Value[0], Value[3], Value[2], Value[5], Value[4], Value[7], Value[6],
                Value[9], Value[8], Value[11], Value[10], Value[13], Value[12], Value[15], Value[14]))
        elif unit == 4:
            log.debug(
                ' %13s |   0x%02X%02X%02X%02X          0x%02X%02X%02X%02X          0x%02X%02X%02X%02X          0x%02X%02X%02X%02X  |' % (
                ('0x%lX' % CurAddr), Value[3], Value[2], Value[1], Value[0], Value[7], Value[6], Value[5], Value[4],
                Value[11], Value[10], Value[9], Value[8], Value[15], Value[14], Value[13], Value[12]))
        elif unit == 8:
            log.debug(
                ' %13s |           0x%02X%02X%02X%02X%02X%02X%02X%02X                         0x%02X%02X%02X%02X%02X%02X%02X%02X           |' % (
                ('0x%lX' % CurAddr), Value[7], Value[6], Value[5], Value[4], Value[3], Value[2], Value[1], Value[0],
                Value[15], Value[14], Value[13], Value[12], Value[11], Value[10], Value[9], Value[8]))
        CurAddr = CurAddr + 0x10

    RemBytes = int(size % 0x10)
    if (RemBytes):
        Value = ListBuff[(CurAddr - address):((CurAddr - address) + RemBytes)]
        ValueStr = ''
        if (unit == 1):
            for cnt in range(0x0, RemBytes):
                ValueStr = ValueStr + '%02X  ' % Value[cnt]
        elif (unit == 2):
            for cnt in range(0x0, int(RemBytes / 2)):
                Index = cnt * 2
                ValueStr = ValueStr + '0x%02X%02X  ' % (Value[Index + 1], Value[Index])
        elif (unit == 4):
            for cnt in range(0x0, int(RemBytes / 4)):
                Index = cnt * 4
                ValueStr = ValueStr + '     0x%02X%02X%02X%02X   ' % (
                Value[Index + 3], Value[Index + 2], Value[Index + 1], Value[Index])
        elif (unit == 8):
            for cnt in range(0x0, int(RemBytes / 8)):
                Index = cnt * 8
                ValueStr = ValueStr + '             0x%02X%02X%02X%02X%02X%02X%02X%02X          ' % (
                Value[Index + 7], Value[Index + 6], Value[Index + 5], Value[Index + 4], Value[Index + 3],
                Value[Index + 2], Value[Index + 1], Value[Index])
        log.debug(f' {(f"0x{CurAddr:X}"):>13} |{ValueStr}')


def memread(address, size):
    """
    This function reads data from specific memory.
    It can be used to read Maximum `8 bytes` of data.

    > This function cannot be used to read Blocks of data.

    :param address: source address from which data to be read
    :param size: size of the data to be read
    :return:
    """
    global cliaccess
    _checkCliAccess()
    return int(cliaccess.mem_read(address, size))


def memwrite(address, size, value):
    """
    This function writes data to specific memory.
    It can be used to write Maximum `8 bytes` of data.

    > This function cannot be used to write Blocks of data.

    :param address: source address at which data to be written
    :param size: size of the data to be read
    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.mem_write(address, size, value)


def load_data(filename, address):
    """
    Loads the given file data to the desired memory address

    :param filename: name of file from which data has to be copied
    :param address: address on which data has to be copied
    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.load_data(filename, address)


def readIO(address, size):
    """
    Read data from IO ports

    :param address: address of port from which data to be read
    :param size: size of data to be read
    :return: integer value read from address
    """
    global cliaccess
    _checkCliAccess()
    return int(cliaccess.read_io(address, size))


def writeIO(address, size, value):
    """
    Write requested value of data to specified IO port

    :param address: address of IO port where data to be written
    :param size: amount of data to be written
    :param value: value of data to write on specified address port
    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.write_io(address, size, value)


def triggerSMI(SmiVal):
    """
    Triggers the software SMI of desired value. Triggering SMI involves writing
    desired value to port 0x72.
    Internally writing to port achieved by write io api

    :param SmiVal: Value with which SMI should be triggered
    :return:
    """
    global cliaccess
    _checkCliAccess()
    return cliaccess.trigger_smi(SmiVal)


def ReadMSR(Ap, MSR_Addr):
    global cliaccess
    _checkCliAccess()
    return int(cliaccess.read_msr(Ap, MSR_Addr))


def WriteMSR(Ap, MSR_Addr, MSR_Val):
    global cliaccess
    _checkCliAccess()
    return cliaccess.write_msr(Ap, MSR_Addr, MSR_Val)


def ReadSmbase():
    """
    Reads the SMBASE address value. Objective is achieved by reading value of
    MSR 0x171

    :return:
    """
    global cliaccess
    _checkCliAccess()
    return int(cliaccess.read_sm_base())


def RemoveFile(file_name):
    """
    Remove/delete file after checking if it really exists

    :param file_name: name of file to be removed
    :return:
    """
    if os.path.isfile(file_name):
        os.remove(file_name)


def RenameFile(file_name, new_file_name):
    """
    File to be renamed
    If new file name exists then it will be removed

    :param file_name: original file name
    :param new_file_name: new file name
    :return:
    """
    if os.path.isfile(new_file_name):
        os.remove(new_file_name)
    os.rename(file_name, new_file_name)


def readcmos(register_address):
    """
    Read CMOS register value

    :param register_address: CMOS register address
    :return:
    """
    upper_register_val = 0x0 if register_address < 0x80 else 0x2
    writeIO(0x70 + upper_register_val, 1, register_address)
    value = readIO(0x71 + upper_register_val, 1)
    return value


def writecmos(register_address, value):
    """
    Write value to CMOS address register

    :param register_address: address of CMOS register
    :param value: value to be written on specified CMOS register
    :return:
    """
    if register_address < 0x80:
        writeIO(0x70, 1, register_address)
        writeIO(0x71, 1, value)

    if register_address >= 0x80:
        writeIO(0x72, 1, register_address)
        writeIO(0x73, 1, value)


def clearcmos():
    """
    Clear all CMOS locations to 0 and set CMOS BAD flag.

    Writing 0 to CMOS data port and writing register value to CMOS address port,
    CMOS clearing is achived

    CMOS are accessed through IO ports 0x70 and 0x71. Each CMOS values are
    accessed a byte at a time and each byte is individually accessible.

    :return:
    """
    log.warning('Clearing CMOS')
    for i in range(0x0, 0x80, 1):
        writeIO(0x70, 1, i)
        writeIO(0x71, 1, 0)
        value = i | 0x80
        if value in (0xF0, 0xF1):
            # skip clearing the CMOS register's which hold Dram Shared MB address.
            continue
        writeIO(0x72, 1, value)
        writeIO(0x73, 1, 0)
    writeIO(0x70, 1, 0x0E)
    writeIO(0x71, 1, 0xC0)  # set CMOS BAD flag

    rtc_reg_pci_address = ((1 << 31) + (0 << 16) + (31 << 11) + (0 << 8) + 0xA4)
    writeIO(0xCF8, 4, rtc_reg_pci_address)
    rtc_value = readIO(0xCFC, 2)
    rtc_value = rtc_value | 0x4
    writeIO(0xCF8, 4, rtc_reg_pci_address)
    writeIO(0xCFC, 2, rtc_value)  # set cmos bad in PCH RTC register


# read all Cmos locations from 0 to 0xFF
def readallcmos():
    Value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    log.debug('Reading CMOS')
    log.debug('      |--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|')
    log.debug('Addr|00|01|02|03|04|05|06|07|08|09|0A|0B|0C|0D|0E|0F|')
    log.debug('----|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|')
    for i in range(0x0, 0x8, 1):
        for j in range(0x0, 0x10, 1):
            writeIO(0x70, 1, ((i << 4) + j))
            Value[j] = readIO(0x71, 1)
        log.debug(
            f' {(i << 4):2X} |{Value[0]:2X} {Value[1]:2X} {Value[2]:2X} {Value[3]:2X} {Value[4]:2X} {Value[5]:2X} {Value[6]:2X} {Value[7]:2X} {Value[8]:2X} {Value[9]:2X} {Value[10]:2X} {Value[11]:2X} {Value[12]:2X} {Value[13]:2X} {Value[14]:2X} {Value[15]:2X}|')
    log.debug(' ---|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|')
    for i in range(0x8, 0x10, 1):
        for j in range(0x0, 0x10, 1):
            writeIO(0x72, 1, ((i << 4) + j))
            Value[j] = readIO(0x73, 1)
        log.debug(
            f' {(i << 4):2X} |{Value[0]:2X} {Value[1]:2X} {Value[2]:2X} {Value[3]:2X} {Value[4]:2X} {Value[5]:2X} {Value[6]:2X} {Value[7]:2X} {Value[8]:2X} {Value[9]:2X} {Value[10]:2X} {Value[11]:2X} {Value[12]:2X} {Value[13]:2X} {Value[14]:2X} {Value[15]:2X}|')
    log.debug(' ---|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|')


def ReadBuffer(inBuffer, offset, size, inType):
    """
    This function reads the desired format of data of specified size
    from the given offset of buffer.

    > Input buffer is in big endian ASCII format

    :param inBuffer: buffer from which data to be read
    :param offset: start offset from which data to be read
    :param size: size to be read from buffer
    :param inType: format in which data can be read (ascii or hex)

    :return: buffer read from input
    """
    value_buffer = inBuffer[offset:offset + size]
    value_string = ''
    if len(value_buffer) == 0:
        return 0
    if inType == ASCII:
        value_string = "".join(chr(value_buffer[i]) for i in range(len(value_buffer)))
        return value_string
    if inType == HEX:
        # value_string = "".join(f"{value_buffer[i]:02x}" for i in range(len(value_buffer)))
        for count in range(len(value_buffer)):
            value_string = f"{value_buffer[count]:02x}" + value_string
        return int(value_string, 16)
    return 0


def ReadList(inBuffer, offset, size, inType=HEX):
    value_buffer = inBuffer[offset:offset + size]
    if inType == ASCII:
        for count in range(len(value_buffer)):
            if value_buffer[count] == 0:
                return ''.join(value_buffer[0:count])
            value_buffer[count] = chr(value_buffer[count])
        return ''.join(value_buffer)
    for count in range(len(value_buffer)):
        value_buffer[count] = hex(value_buffer[count])[2:].zfill(2)
    return int(''.join(value_buffer[::-1]), 16)


def ListInsertVal(Val):
    return Val & 0xFF


def HexLiFy(String):
    return String.encode().hex()


def UnHexLiFy(Integer):
    return binascii.unhexlify((hex(Integer)[2:]).strip('L')).decode()


def ReadBios(BiosBinListBuff, BinSize, Addr, Size):
    if (BiosBinListBuff == 0):  # Online mode
        return memread(Addr, Size)
    else:  # Offline mode
        return ReadList(BiosBinListBuff, (BinSize - (0x100000000 - Addr)), Size)


def GetCliSpecVersion(DramMbAddr):
    global CliSpecRelVersion, CliSpecMajorVersion, CliSpecMinorVersion, CLI_REQ_READY_SIG, CLI_RES_READY_SIG
    CliSpecRelVersion = memread((DramMbAddr + CLI_SPEC_VERSION_RELEASE_OFF), 1) & 0xF
    CliSpecMajorVersion = memread((DramMbAddr + CLI_SPEC_VERSION_MAJOR_OFF), 2)
    CliSpecMinorVersion = memread((DramMbAddr + CLI_SPEC_VERSION_MINOR_OFF), 1)
    CLI_REQ_READY_SIG = 0xC001C001
    CLI_RES_READY_SIG = 0xCAFECAFE
    if (CliSpecRelVersion == 0):
        if (CliSpecMajorVersion >= 7):
            CLI_REQ_READY_SIG = 0xD055C001
            CLI_RES_READY_SIG = 0xD055CAFE
    else:
        LEGACYMB_XML_OFF = 0x50
        CLI_REQ_READY_SIG = 0xD055C001
        CLI_RES_READY_SIG = 0xD055CAFE
    return f'{CliSpecRelVersion:d}.{CliSpecMajorVersion:d}.{CliSpecMinorVersion:d}'


def FixLegXmlOffset(DramMbAddr):
    global CliSpecRelVersion, CliSpecMajorVersion, CliSpecMinorVersion, LEGACYMB_XML_OFF
    LEGACYMB_XML_OFF = 0x0C
    if (CliSpecRelVersion == 0):
        if (CliSpecMajorVersion >= 7):
            LEGACYMB_XML_OFF = 0x50
            if ((CliSpecMajorVersion == 7) and (CliSpecMinorVersion == 0)):
                LegMbOffset = memread((DramMbAddr + LEGACYMB_OFF), 4)
                if (LegMbOffset < 0xFFFF):
                    LegMbOffset = DramMbAddr + LegMbOffset
                if (memread((LegMbOffset + 0x4C), 4) == 0):
                    LEGACYMB_XML_OFF = 0x50
                else:
                    LEGACYMB_XML_OFF = 0x4C
    else:
        LEGACYMB_XML_OFF = 0x50


def IsLegMbSigValid(DramMbAddr):
    global CliSpecRelVersion, CliSpecMajorVersion, MerlinxXmlCliEnableAddr
    SharedMbSig1 = memread((DramMbAddr + SHAREDMB_SIG1_OFF), 4)
    SharedMbSig2 = memread((DramMbAddr + SHAREDMB_SIG2_OFF), 4)
    if ((SharedMbSig1 == SHAREDMB_SIG1) and (SharedMbSig2 == SHAREDMB_SIG2)):
        cli_spec_version = GetCliSpecVersion(DramMbAddr)
        ShareMbEntry1Sig = memread((DramMbAddr + LEGACYMB_SIG_OFF), 4)
        if (ShareMbEntry1Sig == LEGACYMB_SIG):
            FixLegXmlOffset(DramMbAddr)
            if ((CliSpecRelVersion >= 0) and (CliSpecMajorVersion >= 8)):
                LegMbOffset = int(memread(DramMbAddr + LEGACYMB_OFF, 4))
                if (LegMbOffset > 0xFFFF):
                    MerlinxXmlCliEnableAddr = LegMbOffset + MERLINX_XML_CLI_ENABLED_OFF
                else:
                    MerlinxXmlCliEnableAddr = DramMbAddr + LegMbOffset + MERLINX_XML_CLI_ENABLED_OFF
            return cli_spec_version
    return False


def GetDramMbAddr(display_spec=True):
    """
    Read DRAM shared Mailbox from CMOS location 0xBB [23:16] & 0xBC [31:24]

    :return:
    """
    global gDramSharedMbAddr, InterfaceType, LastErrorSig
    LastErrorSig = 0x0000
    InitInterface()
    writeIO(0x72, 1, 0xF0)  # Write a byte to cmos offset 0xF0
    result0 = int(readIO(0x73, 1) & 0xFF)  # Read a byte from cmos offset 0xBB [23:16]
    writeIO(0x72, 1, 0xF1)  # Write a byte to cmos offset 0xF1
    result1 = int(readIO(0x73, 1) & 0xFF)  # Read a byte from cmos offset 0xBC [31:24]
    dram_shared_mb_address = int((result1 << 24) | (result0 << 16))  # Get bits [31:24] of the Dram MB address
    if IsLegMbSigValid(dram_shared_mb_address):
        CloseInterface()
        return dram_shared_mb_address

    writeIO(0x70, 1, 0x78)  # Write a byte to cmos offset 0x78
    result0 = int(readIO(0x71, 1) & 0xFF)  # Read a byte from cmos offset 0xBB [23:16]
    writeIO(0x70, 1, 0x79)  # Write a byte to cmos offset 0x79
    result1 = int(readIO(0x71, 1) & 0xFF)  # Read a byte from cmos offset 0xBC [31:24]
    dram_shared_mb_address = int((result1 << 24) | (result0 << 16))  # Get bits [31:24] of the Dram MB address
    if IsLegMbSigValid(dram_shared_mb_address):
        CloseInterface()
        log.debug(f'CLI Spec Version = {GetCliSpecVersion(dram_shared_mb_address)}')
        log.debug(f'DRAM_MbAddr = 0x{dram_shared_mb_address:X}')
        return dram_shared_mb_address

    if gDramSharedMbAddr != 0:
        dram_shared_mb_address = int(gDramSharedMbAddr)
        if IsLegMbSigValid(dram_shared_mb_address):
            CloseInterface()
            log.debug(f'CLI Spec Version = {GetCliSpecVersion(dram_shared_mb_address)}')
            log.debug(f'DRAM_MbAddr = 0x{dram_shared_mb_address:X}')
            return dram_shared_mb_address
    CloseInterface()
    LastErrorSig = 0xD9FD  # Dram Shared MailBox Not Found

    return 0


def verify_xmlcli_support():
    InitInterface()
    if not GetDramMbAddr() :
        raise XmlCliNotSupported()
    log.debug('XmlCli is Enabled..')
    CloseInterface()


def TriggerXmlCliEntry():
    global LastErrorSig
    LastErrorSig = 0x0000
    status = 0
    try:
        from .tools.restricted import EnableXmlCli as exc
    except (ModuleNotFoundError, ImportError) as e:
        from .tools import EnableXmlCli as exc
    except ImportError:
        log.error(f'Import error on EnableXmlCli, current Python version {sys.version}')
        LastErrorSig = 0x13E4  # import error
        return 1
    status = exc.XmlCliApiAuthenticate()
    if status:
        LastErrorSig = 0xE7CA  # Error Triggering XmlCli command, Authentication Failed
        return 1
    triggerSMI(0xF6)  # trigger S/W SMI for CLI
    return status


def WaitForCliResponse(CLI_ResBuffAddr, Delay=1, Retries=12, PrintRes=1):
    """
    Whenever any command is requested to execute through Command Line Interface;
    it needs to be checked if that command is responded or not.
    It may take time to respond for a specific command.
    For that a certain delay needs to be introduced. This function waits
    for a certain delay and checks if given command is executed and
    returned Response buffer is returned or not for a certain amount of time
    else it returns  Error.

    :param CLI_ResBuffAddr: Address of CLI response Buffer
    :param Delay: The amount of delay which needs to be introduced
    :param Retries: Number of Retries to be attempt
    :param PrintRes: If this flag is set then function prints CLI response buffer contents.
    :return:
    """
    global CliRespFlags, LastErrorSig
    CliRespFlags = 0
    LastErrorSig = 0x0000
    ret = 0
    CommandSideEffect = ['NoSideEffect', 'WarmResetRequired', 'PowerGoodResetRequired', 'Reserved']

    XmlCliRespFlags['Status'] = 0
    XmlCliRespFlags['TimedOut'] = 0
    XmlCliRespFlags['CantExe'] = 0
    XmlCliRespFlags['WrongParam'] = 0
    XmlCliRespFlags['SideEffect'] = 'NoSideEffect'

    for retryCnt in range(0x0, Retries, 1):
        if UfsFlag:
            time.sleep(Delay)
            haltcpu()
        else:
            haltcpu(delay=Delay)
        ResHeaderbuff = read_mem_block(CLI_ResBuffAddr, CLI_REQ_RES_BUFF_HEADER_SIZE)
        ResReadySig = ReadBuffer(ResHeaderbuff, CLI_REQ_RES_READY_SIG_OFF, 4, HEX)
        if ResReadySig == CLI_RES_READY_SIG:  # Verify if BIOS is done with the request
            if PrintRes == 1:
                ResCmdId = ReadBuffer(ResHeaderbuff, CLI_REQ_RES_READY_CMD_OFF, 2, HEX)
                ResFlags = ReadBuffer(ResHeaderbuff, CLI_REQ_RES_READY_FLAGS_OFF, 2, HEX)
                CliRespFlags = ResFlags
                ResStatus = ReadBuffer(ResHeaderbuff, CLI_REQ_RES_READY_STATUS_OFF, 4, HEX)
                ResParamSize = ReadBuffer(ResHeaderbuff, CLI_REQ_RES_READY_PARAMSZ_OFF, 4, HEX)
                XmlCliRespFlags['Status'] = ResStatus
                XmlCliRespFlags['CantExe'] = ((ResFlags >> 1) & 0x1)
                XmlCliRespFlags['WrongParam'] = (ResFlags & 0x1)
                XmlCliRespFlags['SideEffect'] = CommandSideEffect[int((ResFlags >> 2) & 0xF)]
                log.info('CLI Response Header:')
                log.info(f'     CmdID = 0x{ResCmdId:X} (\"{CliCmdDict.get(ResCmdId, "??")}\") ')
                log.info(
                    f'   Status = 0x{ResStatus:X};  ParamSize = 0x{ResParamSize:X};  Flags.WrongParam = {XmlCliRespFlags["WrongParam"]:X};')
                log.info(
                    f'   Flags.CantExe = {XmlCliRespFlags["CantExe"]:X};    Flags.SideEffects = \"{XmlCliRespFlags["SideEffect"]}\"; ')
                if ((ResFlags & 0x3) == 0) and (ResStatus == 0):
                    log.info('CLI command executed successfully..')
                else:
                    log.error('CLI command executed, but with errors. See Logfile.')
                    if XmlCliRespFlags['Status'] != 0:
                        LastErrorSig = 0xC590  # XmlCli Return Status is Non-Zero
                    elif XmlCliRespFlags['CantExe'] != 0:
                        LastErrorSig = 0xCA8E  # XmlCli Resp. returned Cant Execute
                    elif XmlCliRespFlags['WrongParam'] != 0:
                        LastErrorSig = 0xC391  # XmlCli Resp. returned Wring Parameter
                    ret = 1
            return ret
        else:  # CLI Response is not Ready yet
            if MerlinxXmlCliEnableAddr != 0:
                if int(memread(MerlinxXmlCliEnableAddr,
                               1)) & 0x2 == 0:  # if BIT1 is cleared, this means XmlCli Interface was disabled
                    log.error('XmlCli Interface is Disabled, exiting..')
                    XmlCliRespFlags['TimedOut'] = 1
                    LastErrorSig = 0xC1D1  # XmlCli Interface is Disabled
                    return 1
            log.info('CLI Response not yet ready, retrying..')
        runcpu()
    log.error('CLI Response not ready even after retries, exiting..')
    XmlCliRespFlags['TimedOut'] = 1
    LastErrorSig = 0xC2E0  # XmlCli Resp. Timed-Out even after retries
    return 1


def readxmldetails(dram_shared_mailbox_buffer):
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
    SharedMbSig1 = ReadBuffer(dram_shared_mailbox_buffer, SHAREDMB_SIG1_OFF, 4, HEX)
    SharedMbSig2 = ReadBuffer(dram_shared_mailbox_buffer, SHAREDMB_SIG2_OFF, 4, HEX)
    GBT_XML_Addr = 0
    GBT_XML_Size = 0
    if (SharedMbSig1 == SHAREDMB_SIG1) and (SharedMbSig2 == SHAREDMB_SIG2):
        ShareMbEntry1Sig = ReadBuffer(dram_shared_mailbox_buffer, LEGACYMB_SIG_OFF, 4, HEX)
        if ShareMbEntry1Sig == LEGACYMB_SIG:
            LegMbOffset = ReadBuffer(dram_shared_mailbox_buffer, LEGACYMB_OFF, 4, HEX)
            if LegMbOffset > 0xFFFF:
                GBT_XML_Addr = memread(LegMbOffset + LEGACYMB_XML_OFF, 4) + 4
            else:
                GBT_XML_Addr = ReadBuffer(dram_shared_mailbox_buffer, LegMbOffset + LEGACYMB_XML_OFF, 4, HEX) + 4
            GBT_XML_Size = memread(GBT_XML_Addr - 4, 4)
    return GBT_XML_Addr, GBT_XML_Size


def isxmlvalid(gbt_xml_address, gbt_xml_size):
    """
    Check if Target XML is Valid or not

    :param gbt_xml_address: Address of GBT XML
    :param gbt_xml_size: Size of GBT XML
    :return:
    """
    global LastErrorSig
    LastErrorSig = 0x0000
    try:
        temp_buffer = read_mem_block(gbt_xml_address, 0x08)  # Read/save parameter buffer
        SystemStart = ReadBuffer(temp_buffer, 0, 0x08, ASCII)
        temp_buffer = read_mem_block(gbt_xml_address + gbt_xml_size - 0xB, 0x09)  # Read/save parameter buffer
        SystemEnd = ReadBuffer(temp_buffer, 0, 0x09, ASCII)
        if (SystemStart == XML_START) and (SystemEnd == XML_END):
            return True
        else:
            LastErrorSig = 0x8311  # Xml data is in-valid
            return False
    except Exception as e:
        log.error(f'Exception detected when determining if xml is valid.\n {e}')
        LastErrorSig = 0xEC09  # Exception detected
        return False


def readclireqbufAddr(dram_shared_mailbox_buffer):
    """
    Reads CLI Request Buffer Address from the Shared Mailbox temp buffer

    Request buffer address is present at offset of SHARED_MB_CLI_REQ_BUFF_ADDR_OFF.
    First signature of buffer will be checked with valid signature
    SHARED_MB_CLI_REQ_BUFF_SIG; and if it matches CLI request buffer address
    will be collected in temporary buffer.


    :param dram_shared_mailbox_buffer: pointer to dram shared mailbox buffer from
                                                    where CLI Request Buffer address can be retrieved
    :return:
    """
    cli_request_buffer_address = 0
    if ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_REQ_BUFF_SIG_OFF, 4, HEX) == SHARED_MB_CLI_REQ_BUFF_SIG:
        cli_request_buffer_address = ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_REQ_BUFF_ADDR_OFF, 4, HEX)
    return cli_request_buffer_address


def readclireqbufSize(dram_shared_mailbox_buffer):
    """
    Reads CLI Request Buffer Address from the Shared Mailbox temp buffer

    :param dram_shared_mailbox_buffer: pointer to dram shared mailbox buffer from
                                                    where CLI Request Buffer to be read
    :return:
    """
    cli_request_buffer_size = 0
    if ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_REQ_BUFF_SIG_OFF, 4, HEX) == SHARED_MB_CLI_REQ_BUFF_SIG:
        cli_request_buffer_size = ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_REQ_BUFF_SIZE_OFF, 4, HEX)
    return cli_request_buffer_size


def readcliresbufAddr(dram_shared_mailbox_buffer):
    """
    Reads CLI Response Buffer Address from the Shared Mailbox temp buffer

    Response buffer address is present at offset of `SHARED_MB_CLI_RES_BUFF_ADDR_OFF` (0x44).

    First signature check done which received from accessing `dram_shared_mailbox_buffer` with
    `SHARED_MB_CLI_RES_BUFF_SIG`; and if it matches CLI response buffer address
    will be collected in temporary buffer.

    :param dram_shared_mailbox_buffer: pointer to dram shared mailbox buffer
    :return:
    """
    cli_response_buffer_address = 0
    if ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_RES_BUFF_SIG_OFF, 4, HEX) == SHARED_MB_CLI_RES_BUFF_SIG:
        cli_response_buffer_address = ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_RES_BUFF_ADDR_OFF, 4, HEX)
    return cli_response_buffer_address


def readcliresbufSize(dram_shared_mailbox_buffer):
    """
    Reads CLI Response Buffer Size from the Shared Mailbox temp buffer

    :param dram_shared_mailbox_buffer: pointer to dram shared mailbox buffer
    :return:
    """
    cli_response_buffer_size = 0
    if ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_RES_BUFF_SIG_OFF, 4, HEX) == SHARED_MB_CLI_RES_BUFF_SIG:
        cli_response_buffer_size = ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_CLI_RES_BUFF_SIZE_OFF, 4, HEX)
    return cli_response_buffer_size


def readLegMailboxAddrOffset(dram_shared_mailbox_buffer):
    """
    Get Legacy DRAM Mailbox Address offset from the Shared Mailbox temporary buffer

    Legacy Mailbox address offset is present at offset of
    `SHARED_MB_LEGMB_ADDR_OFF` (0x24).

    First signature check done which received from accessing
    `dram_shared_mailbox_buffer` with LEGACYMB_SIG; and if it matches
    CLI request buffer address will be collected in temporary buffer.

    :param dram_shared_mailbox_buffer: pointer to dram shared mailbox buffer
    :return:
    """
    legacy_mailbox_address_offset = 0
    if ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_LEGMB_SIG_OFF, 4, HEX) == LEGACYMB_SIG:
        legacy_mailbox_address_offset = ReadBuffer(dram_shared_mailbox_buffer, SHARED_MB_LEGMB_ADDR_OFF, 4, HEX)
    return legacy_mailbox_address_offset


def PatchXmlData(XmlListBuff, XmlAddr, XmlSize):
    XmlPatchDataFound = 0
    NewXmlPatchDataFound = 0
    PacketAddr = ((XmlAddr + XmlSize + 0xFFF) & 0xFFFFF000)
    for count in range(0, 4):
        PacketHdr = int(memread(PacketAddr, 8))
        PacketSize = ((PacketHdr >> 40) & 0xFFFFFF)
        if (((PacketHdr & 0xFFFFFFFFFF) == 0x4c444B5824) and (PacketSize != 0)):  # cmp with $XKDL
            XmlKnobsDeltaBuff = read_mem_block((PacketAddr + 8), PacketSize)
            XmlPatchDataFound = 1
            break
        if (((PacketHdr & 0xFFFFFFFFFF) == 0x54444B5824) and (PacketSize != 0)):  # cmp with $XKDT
            XmlKnobsDeltaBuff = read_mem_block((PacketAddr + 8), PacketSize)
            NewXmlPatchDataFound = 1
            break
        PacketAddr = ((PacketAddr + 8 + PacketSize + 0xFFF) & 0xFFFFF000)
    if ((XmlPatchDataFound == 1) or (NewXmlPatchDataFound == 1)):
        offset = 0
        while (1):  # read and print the return knobs entry parameters from CLI's response buffer
            if (offset >= PacketSize):
                break
            KnobEntryOffset = ReadBuffer(XmlKnobsDeltaBuff, offset + 0, 3, HEX)
            Data16 = ReadBuffer(XmlKnobsDeltaBuff, offset + 3, 2, HEX)
            DataOfst = KnobEntryOffset + (Data16 & 0xFFF)
            if (NewXmlPatchDataFound):
                DataSize = ReadBuffer(XmlKnobsDeltaBuff, offset + 5, 1, HEX)
                ValueToReplace = ReadBuffer(XmlKnobsDeltaBuff, offset + 6, DataSize, HEX)
            else:
                DataSize = (Data16 >> 12) & 0xF
                ValueToReplace = ReadBuffer(XmlKnobsDeltaBuff, offset + 5, DataSize, HEX)
            StrValToReplace = hex(ValueToReplace)[2::].strip('L').zfill(DataSize * 2).upper()
            XmlListBuff[DataOfst:DataOfst + (DataSize * 2)] = list(StrValToReplace.encode())
            if (NewXmlPatchDataFound):
                offset = offset + 6 + DataSize
            else:
                offset = offset + 5 + DataSize
        log.info(f'Patch buffer data size = {PacketSize:d} bytes')


InValidXmlChar = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0B', '\x0C', '\x0E',
                  '\x0F', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1A',
                  '\x1B', '\x1C', '\x1D', '\x1E', '\x1F', '\x7F', '\x80', '\x81', '\x82', '\x83', '\x84', '\x86',
                  '\x87', '\x88', '\x89', '\x8A', '\x8B', '\x8C', '\x8D', '\x8E', '\x8F', '\x90', '\x91', '\x92',
                  '\x93', '\x94', '\x95', '\x96', '\x97', '\x98', '\x99', '\x9A', '\x9B', '\x9C', '\x9D', '\x9E',
                  '\x9F', '\xAE', '\xB0']


def SanitizeXml(filename):
    """
    Function to sanitize the given xmlfile
    :param filename: platform_config xml file path
    :return: None
    """
    try:
        MyTree = ET.parse(filename)
        log.info('SanitizeXml(): No XML syntax errors found with source XML file.')
    except:
        log.info('SanitizeXml(): Fixing XML syntax errors found with source XML file.')
        with open(filename, mode='r', newline='') as input_file, open(filename + '.clean', mode='w',
                                                                      newline='') as output_file:
            for line in input_file.readlines():
                cleaned_content = line.translate(Xml_Sanitization_Mapping)
                output_file.write(cleaned_content)
        RenameFile(f"{filename}", f"{filename}.raw")
        RenameFile(f"{filename}.clean", f"{filename}")


def IsXmlGenerated():
    global LastErrorSig
    LastErrorSig = 0x0000
    Status = 0
    InitInterface()
    DRAM_MbAddr = GetDramMbAddr()  # Get DRam Mailbox Address from Cmos.
    log.debug(f'CLI Spec Version = {GetCliSpecVersion(DRAM_MbAddr)}')
    log.debug(f'DRAM_MbAddr = 0x{DRAM_MbAddr:X}')
    if (DRAM_MbAddr == 0x0):
        log.error('Dram Shared Mailbox not Valid, hence exiting')
        CloseInterface()
        return 1
    DramSharedMBbuf = read_mem_block(DRAM_MbAddr, 0x200)  # Read/save parameter buffer
    (XmlAddr, XmlSize) = readxmldetails(DramSharedMBbuf)  # read GBTG XML address and Size
    if (XmlAddr == 0):
        log.error('Platform Configuration XML not yet generated, hence exiting')
        CloseInterface()
        LastErrorSig = 0x8AD0  # Xml Address is Zero
        return 1
    if (isxmlvalid(XmlAddr, XmlSize)):
        log.debug('Xml Is Generated and it is Valid')
    else:
        log.error(f'XML is not valid or not yet generated XmlAddr = 0x{XmlAddr:X}, XmlSize = 0x{XmlSize:X}')
        Status = 1
    CloseInterface()
    return Status


EFI_IFR_ONE_OF_OP = 0x05
EFI_IFR_CHECKBOX_OP = 0x06
EFI_IFR_NUMERIC_OP = 0x07
EFI_IFR_STRING_OP = 0x1C
BIOS_KNOBS_DATA_BIN_HDR_SIZE_OLD = 0x10
INVALID_KNOB_SIZE = 0xFF
BIOS_KNOBS_DATA_BIN_HDR_SIZE = 0x40
BIOS_KNOBS_DATA_BIN_HDR_SIZE_V03 = 0x50
BIOS_KNOB_BIN_REVISION_OFFSET = 0x0F
NVAR_NAME_OFFSET = 0x0E
NVAR_SIZE_OFFSET = 0x10
BIOS_KNOB_BIN_GUID_OFFSET = 0x12

ZeroGuid = [0x00000000, 0x0000, 0x0000, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
SetupTypeHiiDict = {EFI_IFR_ONE_OF_OP: 'oneof', EFI_IFR_NUMERIC_OP: 'numeric', EFI_IFR_CHECKBOX_OP: 'checkbox',
                    EFI_IFR_STRING_OP: 'string', 0xF: 'ReadOnly'}
SetupTypeBinDict = {0x5: 'oneof', 0x7: 'numeric', 0x6: 'checkbox', 0x8: 'string', 0xF: 'ReadOnly'}
SetupTypeBin2ValDict = {0x5: EFI_IFR_ONE_OF_OP, 0x7: EFI_IFR_NUMERIC_OP, 0x6: EFI_IFR_CHECKBOX_OP,
                        0x8: EFI_IFR_STRING_OP}
OldBinNvarNameDict = {0: 'Setup', 1: 'ServerMgmt'}
OldBinNvarNameDictPly = {0: 'Setup', 1: 'SocketIioConfig', 2: 'SocketCommonRcConfig', 3: 'SocketMpLinkConfig',
                         4: 'SocketMemoryConfig', 5: 'SocketMiscConfig', 6: 'SocketPowerManagementConfig',
                         7: 'SocketProcessorCoreConfig', 8: 'SvOtherConfiguration', 9: 'SvPchConfiguration'}


def GuidStr(GuidList):
    GuidString = '{ 0x%08X, 0x%04X, 0x%04X, { 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X }}' % (
    GuidList[0], GuidList[1], GuidList[2], GuidList[3], GuidList[4], GuidList[5], GuidList[6], GuidList[7], GuidList[8],
    GuidList[9], GuidList[10])
    return GuidString


def FetchGuid(BufferList, Offset):
    GuidList = []
    if (len(BufferList) > (Offset + 0x10)):
        GuidList.append(ReadList(BufferList, (Offset + 0x0), 4))
        GuidList.append(ReadList(BufferList, (Offset + 0x4), 2))
        GuidList.append(ReadList(BufferList, (Offset + 0x6), 2))
        GuidList.append(ReadList(BufferList, (Offset + 0x8), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0x9), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0xA), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0xB), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0xC), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0xD), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0xE), 1))
        GuidList.append(ReadList(BufferList, (Offset + 0xF), 1))
    else:
        GuidList = ZeroGuid
    return GuidList


def KnobsDataToXmlFile(OutFile, BiosKnobDict={}):
    NoOfVars = len(BiosKnobDict)
    if (NoOfVars != 0):
        result = '\t<!--XmlLite Bios Knobs from BiosKnobsData Bin File -->\n'
        result += '\t<Nvars>\n'
        for VarId in BiosKnobDict:
            if (BiosKnobDict[VarId]['Status'] != 0):
                continue
            result += f'\t\t<Nvar varstoreIndex=\"{VarId:02d}\" name=\"{BiosKnobDict[VarId]["NvarName"]}\" size=\"0x{BiosKnobDict[VarId]["NvarSize"]:04X}\" attribute=\"0x{BiosKnobDict[VarId]["NvarAttri"]:08X}\" KnobCount=\"{BiosKnobDict[VarId]["KnobCount"]:d}\" guid=\"{GuidStr(BiosKnobDict[VarId]["NvarGuid"])}\"/>\n'
        result += '\t</Nvars>\n\t<biosknobs>\n'
        for VarId in BiosKnobDict:
            if (BiosKnobDict[VarId]['Status'] != 0):
                continue
            for KnobOfst in BiosKnobDict[VarId]['KnobDict']:
                KnobSize = BiosKnobDict[VarId]['KnobDict'][KnobOfst]['KnobSzBin']
                KnobWidth = KnobSize
                if (KnobOfst >= BITWISE_KNOB_PREFIX):
                    KnobOffsetStr = '0x%05X' % KnobOfst
                    KnobWidth = int((KnobOfst & 0x3FFFF) % 8) + KnobSize
                    if KnobWidth % 8:
                        KnobWidth = int(KnobWidth / 8) + 1
                    else:
                        KnobWidth = int(KnobWidth / 8)
                else:
                    KnobOffsetStr = '0x%04X' % KnobOfst
                if ('DefVal' in BiosKnobDict[VarId]['KnobDict'][KnobOfst]):
                    DefVal = BiosKnobDict[VarId]['KnobDict'][KnobOfst]['DefVal']
                    CurVal = BiosKnobDict[VarId]['KnobDict'][KnobOfst]['CurVal']
                else:
                    DefVal = 0
                    CurVal = 0
                result += '\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" size=\"%d\" offset=\"%s\" depex=\"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\"/>\n' % (
                SetupTypeHiiDict.get(BiosKnobDict[VarId]['KnobDict'][KnobOfst]['SetupTypeBin'], '??'),
                BiosKnobDict[VarId]['KnobDict'][KnobOfst]['KnobName'], VarId, KnobSize, KnobOffsetStr,
                BiosKnobDict[VarId]['KnobDict'][KnobOfst]['Depex'].replace('&', '_BitAnd_'), (KnobWidth * 2), DefVal,
                (KnobWidth * 2), CurVal)
        result += '\t</biosknobs>\n'
    OutFile.write(result)


def BiosKnobsDataBinParser(BiosKnobBinFile, BiosIdString='', StartOfst=0x1C, parselite=False):
    with open(BiosKnobBinFile, 'rb') as BiosKnobFile:
        BiosKnobBinBuff = list(BiosKnobFile.read())
    BiosKnobDict = {}
    TmpKnobDict = {}
    TmpDupKnobDict = {}
    if (StartOfst == 0x1C):
        BiosKnobBinEndAddr = ReadList(BiosKnobBinBuff, 0x18, 3)
    else:
        BiosKnobBinEndAddr = len(BiosKnobBinBuff)
    BiosKnobBinPtr = StartOfst
    OldBinFileFormat = False
    KnobBinRevision = 0
    DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE_OLD
    while (BiosKnobBinPtr < BiosKnobBinEndAddr):
        BinHdrSig = ReadList(BiosKnobBinBuff, BiosKnobBinPtr, 5, ASCII)
        VarId = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + 5, 1)
        KnobCount = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + 6, 2)
        if (((BinHdrSig == '$NVAR') or ((parselite == True) and (BinHdrSig == '$NVRO'))) and (KnobCount != 0)):
            DupKnobBufOff = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + 8, 3)
            NvarPktSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + 0xB, 3)
            NvarSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + 0xE, 2)
            NvarGuid = ZeroGuid
            if (NvarSize == 0):
                OldBinFileFormat = True
                DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE_OLD
                if (BiosIdString[0:3] == 'PLY'):
                    NvarName = OldBinNvarNameDictPly[
                        VarId]  # this is an assumption if we still have old Bin format, so that we are backward compatible
                else:
                    NvarName = OldBinNvarNameDict[
                        VarId]  # this is an assumption if we still have old Bin format, so that we are backward compatible
                tmpBiosKnobBinPtr = BiosKnobBinPtr + DataBinHdrSize
            else:  # New Format
                OldBinFileFormat = False
                KnobBinRevision = ReadList(BiosKnobBinBuff, (BiosKnobBinPtr + BIOS_KNOB_BIN_REVISION_OFFSET), 1)
                if (KnobBinRevision >= 2):  # revision equal or higher than 0.2?
                    NvarGuid = FetchGuid(BiosKnobBinBuff, (BiosKnobBinPtr + BIOS_KNOB_BIN_GUID_OFFSET))
                    NvarSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + NVAR_SIZE_OFFSET, 2)
                NvarNameOfst = ReadList(BiosKnobBinBuff, (BiosKnobBinPtr + NVAR_NAME_OFFSET), 1)
                NvarName = ''
                for VarSizeCount in range(0, 0x30):
                    Val = ReadList(BiosKnobBinBuff, (BiosKnobBinPtr + NvarNameOfst + VarSizeCount), 1)
                    if (Val == 0):
                        break
                    NvarName = NvarName + chr(Val)
                if (KnobBinRevision >= 3):  # revision equal or higher than 0.3?
                    DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE_V03
                else:
                    DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE
                tmpBiosKnobBinPtr = BiosKnobBinPtr + DataBinHdrSize
            TmpKnobDict = {}
            if (parselite):
                if ((BinHdrSig != '$NVRO') or (VarId not in BiosKnobDict)):
                    KnobNameList = {}
                    BiosKnobDict[VarId] = {'KnobDict': {}, 'KnobNameList': {}, 'NvarName': NvarName,
                                           'NvarGuid': NvarGuid, 'NvarSize': NvarSize, 'NvarAttri': 0, 'Status': 0,
                                           'KnobCount': KnobCount}
                else:
                    KnobNameList = BiosKnobDict[VarId]['KnobNameList']
                    TmpKnobDict = BiosKnobDict[VarId]['KnobDict']
            else:
                BiosKnobDict[VarId] = {'HiiVarId': 0xFF, 'HiiVarSize': 0, 'KnobDict': {}, 'DupKnobDict': {},
                                       'NvarName': NvarName, 'NvarGuid': NvarGuid, 'NvarSize': NvarSize,
                                       'KnobCount': KnobCount}
            while (tmpBiosKnobBinPtr < (BiosKnobBinPtr + DupKnobBufOff)):
                KnobOffset = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, 2)
                if (OldBinFileFormat):
                    tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + 2
                    KnobSize_bin = INVALID_KNOB_SIZE
                    SetupTypeBin = INVALID_KNOB_SIZE
                else:
                    KnobInfo = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr + 2, 1)
                    tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + 3
                    KnobType_bin = ((KnobInfo >> 4) & 0xF)
                    if (KnobType_bin >= 0x8):
                        KnobType_bin = 0x8
                        KnobSize_bin = (KnobInfo & 0x7F) * 2
                    else:
                        KnobSize_bin = (KnobInfo & 0x0F)
                        if ((KnobBinRevision >= 3) and (KnobType_bin < 0x4)):
                            KnobType_bin = KnobType_bin + 0x4  # This indicates that current Knob entry is part of Depex, Adjust the Type accordingly.
                        if KnobSize_bin >= 0xC:  # this indicates that the given Knob is Bitwise and is of Size mentioned in subsequent fields
                            BitData = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, 1)  # Bitsize[7:3] BitOffset[2:0]
                            tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + 1
                            KnobSize_bin = ((KnobSize_bin & 0x1) << 5) + ((BitData >> 3) & 0x1F)
                            KnobOffset = BITWISE_KNOB_PREFIX + (KnobOffset * 8) + (
                                        BitData & 0x7)  # Knob Offset will now indicate 20 bit wide Value that represents Bit Offset.
                    SetupTypeBin = SetupTypeBin2ValDict.get(KnobType_bin, INVALID_KNOB_SIZE)
                if (BinHdrSig == '$NVRO'):
                    SetupTypeBin = 0xF  # indicates its "Readonly" Type
                StrSize = 0
                while (ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr + StrSize, 1)):
                    StrSize = StrSize + 1
                if (StrSize):
                    KnobName = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize, ASCII)
                else:
                    KnobName = ''
                tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
                StrSize = 0
                while (ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr + StrSize, 1)):
                    StrSize = StrSize + 1
                if (StrSize):
                    KnobDepex = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize, ASCII)
                else:
                    KnobDepex = 'TRUE'
                tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
                if (parselite):
                    if (KnobOffset not in TmpKnobDict):
                        KnobNameList[KnobName] = KnobOffset
                        TmpKnobDict[KnobOffset] = {'SetupTypeBin': SetupTypeBin, 'KnobName': KnobName,
                                                   'KnobSzBin': KnobSize_bin, 'Depex': KnobDepex, 'DefVal': 0,
                                                   'CurVal': 0}
                else:
                    TmpKnobDict[KnobOffset] = {'SetupTypeHii': 0, 'SetupTypeBin': SetupTypeBin, 'KnobName': KnobName,
                                               'KnobSzHii': 0, 'KnobSzBin': KnobSize_bin, 'HiiDefVal': 0,
                                               'Depex': KnobDepex, 'Prompt': 0, 'Help': 0, 'ParentPromptList': [],
                                               'Min': 0, 'Max': 0, 'Step': 0, 'KnobPrsd': [0, 0, 0xFF],
                                               'OneOfOptionsDict': {}}
            BiosKnobDict[VarId]['KnobDict'] = TmpKnobDict
            if (parselite):
                BiosKnobDict[VarId]['KnobNameList'] = KnobNameList

            tmpBiosKnobBinPtr = (BiosKnobBinPtr + DupKnobBufOff)  # Parse Duplicate list
            TmpDupKnobDict = {}
            DupCount = 0
            while (tmpBiosKnobBinPtr < (BiosKnobBinPtr + NvarPktSize)):
                StrSize = 0
                while (ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr + StrSize, 1)):
                    StrSize = StrSize + 1
                if (StrSize):
                    DupKnobName = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize, ASCII)
                else:
                    DupKnobName = ''
                tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
                StrSize = 0
                while (ReadList(BiosKnobBinBuff, (tmpBiosKnobBinPtr + StrSize), 1)):
                    StrSize = StrSize + 1
                if (StrSize):
                    DupKnobDepex = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize, ASCII)
                else:
                    DupKnobDepex = 'TRUE'
                tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
                TmpDupKnobDict[DupCount] = {'DupKnobName': DupKnobName, 'DupDepex': DupKnobDepex}
                DupCount = DupCount + 1
            BiosKnobDict[VarId]['DupKnobDict'] = TmpDupKnobDict
            BiosKnobBinPtr = BiosKnobBinPtr + NvarPktSize
        elif (BinHdrSig == '$NVRO'):
            NvarPktSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr + 0xB, 3)
            BiosKnobBinPtr = BiosKnobBinPtr + NvarPktSize
        else:
            BiosKnobBinPtr = BiosKnobBinPtr + DataBinHdrSize
    return BiosKnobDict


def LittEndian(HexVal):
    NewStr = ''
    for count in range(0, len(HexVal), 2):
        NewStr = HexVal[count:count + 2] + NewStr
    return NewStr


def Str2Int(StrVal):
    StrVal = StrVal.strip()
    if (len(StrVal) > 2):
        if (StrVal[0:2] == '0x'):
            return int(StrVal, 16)
    return int(StrVal)


# save XmlLite generated from BiosKnobsData bin to desired file.
def SaveXmlLite(filename=PlatformConfigLiteXml, Operation='savexml', UserKnobsDict={}):
    global LastErrorSig
    LastErrorSig = 0x0000
    Binfilename = os.path.join(TempFolder, "BiosKnobsData.bin")
    RemoveFile(Binfilename)
    Status = 0
    InitInterface()
    DRAM_MbAddr = GetDramMbAddr()  # Get DRam MAilbox Address from Cmos.
    if (DRAM_MbAddr == 0x0):
        log.error('Dram Shared Mailbox not Valid, hence exiting')
        CloseInterface()
        return 1
    DramSharedMBbuf = read_mem_block(DRAM_MbAddr, 0x200)  # Read/save parameter buffer
    (XmlAddr, XmlSize) = readxmldetails(DramSharedMBbuf)  # read GBTG XML address and Size
    if (XmlAddr == 0):
        log.error('Platform Configuration XML not yet generated, hence exiting')
        CloseInterface()
        LastErrorSig = 0x8AD0  # Xml Address is Zero
        return 1
    IndependentLite = False
    if (isxmlvalid(XmlAddr, XmlSize)):
        if (XmlSize > (0x1000 - 4)):
            IndependentLite = True
    else:
        XmlSize = 0
        IndependentLite = True
    ComprXmlFound = False
    PacketAddr = ((XmlAddr + XmlSize + 0xFFF) & 0xFFFFF000)
    for count in range(0, 2):
        PacketHdr = int(memread(PacketAddr, 8))
        PacketSize = ((PacketHdr >> 40) & 0xFFFFFF)
        if (((PacketHdr & 0xFFFFFFFFFF) == 0x424B4E5424) and (PacketSize != 0)):  # cmp with $TNKB
            if Operation == "savexml":
                log.info('Found Tiano Compressed BiosKnobsData Bin, Downloading it')
            TempInFile = os.path.join(TempFolder, "CmpBiosKnobsData.bin")
            memsave(TempInFile, (PacketAddr + 8), int(PacketSize))
            try:
                utils.system_call(cmd_lis=[TianoCompressUtility, "-d", "-q", TempInFile, "-o", Binfilename])
                RemoveFile(TempInFile)
                if os.path.getsize(Binfilename):
                    ComprXmlFound = True
                    if Operation == "savexml":
                        log.info('Tiano Compressed BiosKnobsData Bin Decompressed Successfully')
            except:
                log.error('Decompression Failed!...')
            break
        PacketAddr = ((PacketAddr + 8 + PacketSize + 0xFFF) & 0xFFFFF000)
    if (ComprXmlFound):
        pass
    else:
        log.error('Compressed Data is not supported, aborting')
        CloseInterface()
        LastErrorSig = 0x8311  # Xml is invalid
        return 1

    MyKnobsDict = {}
    MyKnobsDict = BiosKnobsDataBinParser(Binfilename, BiosIdString='', StartOfst=0, parselite=True)

    if (Operation != 'savexml'):
        if (len(UserKnobsDict) == 0):
            Operation = 'savexml'
            log.warning('Input Knob String is empty, just saving the XML for now')
        else:
            if (Operation == 'prog'):
                for NvarCount in MyKnobsDict:
                    MyKnobsDict[NvarCount]['Status'] = 0xFF  # initialize initially as Invalid Status
                UserNvarDict = {}
                for KnobName in UserKnobsDict:
                    for NvarCount in MyKnobsDict:
                        if (KnobName in MyKnobsDict[NvarCount]['KnobNameList']):
                            KnobOfst = MyKnobsDict[NvarCount]['KnobNameList'][KnobName]
                            KnobType = SetupTypeHiiDict.get(
                                MyKnobsDict[NvarCount]['KnobDict'][KnobOfst]['SetupTypeBin'], '??')
                            if (KnobType == 'Readonly' or KnobType == '??'):
                                break  # invalid knob Type
                            ReqVal = Str2Int(UserKnobsDict[KnobName])
                            KnobSize = MyKnobsDict[NvarCount]['KnobDict'][KnobOfst]['KnobSzBin']
                            if (len(hex(ReqVal)[2:]) <= (KnobSize * 2)):
                                if (NvarCount not in UserNvarDict):
                                    UserNvarDict[NvarCount] = {}
                                UserNvarDict[NvarCount][KnobName] = {'KnobOfst': KnobOfst, 'KnobSize': KnobSize,
                                                                     'ReqVal': ReqVal}
                            break

    FinalNvarBuffStr = ''
    VarCount = 0
    MyVarList = sorted(MyKnobsDict)
    Opcode = 0
    if (Operation == 'prog'):
        MyVarList = sorted(UserNvarDict)
        Opcode = 2

    for NvarCount in MyVarList:
        if (len(MyKnobsDict[NvarCount]['NvarName']) >= 48):
            continue
        ProgListBuff = ''
        VarSize = 0
        if Operation == 'prog' and UserNvarDict:
            for Knob in UserNvarDict.get(NvarCount, []):
                KnobOfst = UserNvarDict[NvarCount][Knob]['KnobOfst']
                KnobSize = UserNvarDict[NvarCount][Knob]['KnobSize']
                KnobWidth = KnobSize
                if (KnobOfst >= BITWISE_KNOB_PREFIX):  # bitwise knob?
                    KnobWidth, KnobOfst, BitOfst = get_bitwise_knob_details(KnobSize, KnobOfst)
                    KnobSize = ((KnobSize & 0x1F) << 3) + (BitOfst & 0x7)
                ProgListBuff = ProgListBuff + LittEndian('%04X' % KnobOfst) + '%02X' % KnobSize + LittEndian(
                    '%0*X' % ((KnobWidth * 2), UserNvarDict[NvarCount][Knob]['ReqVal']))
            VarSize = int(len(ProgListBuff) / 2)
        NvarBuffHeaderStr = LittEndian('%04X' % MyKnobsDict[NvarCount]['NvarGuid'][1]) + LittEndian(
            '%04X' % MyKnobsDict[NvarCount]['NvarGuid'][2]) + '%02X%02X%02X%02X%02X%02X%02X%02X' % (
                            MyKnobsDict[NvarCount]['NvarGuid'][3], MyKnobsDict[NvarCount]['NvarGuid'][4],
                            MyKnobsDict[NvarCount]['NvarGuid'][5], MyKnobsDict[NvarCount]['NvarGuid'][6],
                            MyKnobsDict[NvarCount]['NvarGuid'][7], MyKnobsDict[NvarCount]['NvarGuid'][8],
                            MyKnobsDict[NvarCount]['NvarGuid'][9], MyKnobsDict[NvarCount]['NvarGuid'][10]) + '00'.zfill(
            8)
        FinalNvarBuffStr = FinalNvarBuffStr + LittEndian(
            '%08X' % MyKnobsDict[NvarCount]['NvarGuid'][0]) + NvarBuffHeaderStr + LittEndian(
            '%08X' % VarSize) + '00'.zfill(8) + '%02X' % Opcode + HexLiFy(
            MyKnobsDict[NvarCount]['NvarName']) + '00'.zfill(2) + ProgListBuff
        VarCount = VarCount + 1
        FinalNvarBuffStr = FinalNvarBuffStr + '1D90FADE' + NvarBuffHeaderStr + '00'.zfill(18) + HexLiFy(
            'Def' + MyKnobsDict[NvarCount]['NvarName']) + '00'.zfill(2)
        VarCount = VarCount + 1
    if (FinalNvarBuffStr != ''):
        binfile = os.path.join(TempFolder, 'NvarReqBuff.bin')
        with open(binfile, 'wb') as file_ptr:
            file_ptr.write(binascii.unhexlify(FinalNvarBuffStr))

    DRAM_MbAddr = GetDramMbAddr()  # Get DRam Mailbox Address.
    dram_shared_mailbox_buffer = read_mem_block(DRAM_MbAddr, 0x200)  # Read/save parameter buffer
    CLI_ReqBuffAddr = readclireqbufAddr(DramSharedMBbuf)  # Get CLI Request Buffer Address
    CLI_ResBuffAddr = readcliresbufAddr(DramSharedMBbuf)  # Get CLI Response Buffer Address
    if Operation != "savexml":
        log.debug(f'CLI Spec Version = {GetCliSpecVersion(DRAM_MbAddr)}')
        log.info(f'CLI Request Buffer Addr = 0x{CLI_ReqBuffAddr:X}   CLI Response Buffer Addr = 0x{CLI_ResBuffAddr:X}')
    if ((CLI_ReqBuffAddr == 0) or (CLI_ResBuffAddr == 0)):
        if Operation != "savexml":
            log.error('CLI buffers are not valid or not supported, Aborting due to Error!')
        CloseInterface()
        LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
        return 1

    binfile = os.path.join(TempFolder, 'NvarReqBuff.bin')
    ClearCliBuff(CLI_ReqBuffAddr, CLI_ResBuffAddr)
    memwrite(CLI_ReqBuffAddr + CLI_REQ_RES_READY_PARAMSZ_OFF, 4, VarCount)
    # log.info('Req Buffer Bin file used is %s' %binfile)
    load_data(binfile, CLI_ReqBuffAddr + CLI_REQ_RES_READY_PARAMSZ_OFF + 4)
    memwrite(CLI_ReqBuffAddr + CLI_REQ_RES_READY_CMD_OFF, 4, GET_SET_VARIABLE_OPCODE)
    memwrite(CLI_ReqBuffAddr + CLI_REQ_RES_READY_SIG_OFF, 4, CLI_REQ_READY_SIG)
    if Operation != "savexml":
        log.info('CLI Mailbox programmed, issuing S/W SMI to program knobs...')

    Status = TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
    if (Status):
        log.error('Error while triggering CLI Entry Point, Aborting....')
        CloseInterface()
        return 1
    if (WaitForCliResponse(CLI_ResBuffAddr, 2, 3, PrintRes=bool(Operation != "savexml")) != 0):
        log.error('CLI Response not ready, Aborting....')
        CloseInterface()
        return 1

    CurParamSize = int(memread(CLI_ResBuffAddr + CLI_REQ_RES_READY_PARAMSZ_OFF, 4))
    if (CurParamSize != 0):
        CurParambuff = read_mem_block((CLI_ResBuffAddr + CLI_REQ_RES_BUFF_HEADER_SIZE), CurParamSize)
        ResBufFilename = os.path.join(TempFolder, 'NvarRespBuff.bin')
        with open(ResBufFilename, 'wb') as out_file:  # opening for writing
            out_file.write(CurParambuff)
        CurParamList = list(CurParambuff)
        RespBuffPtr = 0
        for Varcount in range(0, 0x100):
            if (RespBuffPtr >= CurParamSize):
                break
            CurNvarGuid = FetchGuid(CurParamList, RespBuffPtr)
            CurNvarAttri = ReadList(CurParamList, RespBuffPtr + 0x10, 4)
            CurNvarSize = ReadList(CurParamList, RespBuffPtr + 0x14, 4)
            CurNvarStatus = ReadList(CurParamList, RespBuffPtr + 0x18, 4)
            if (CurNvarStatus != 0):
                CurNvarSize = 0
            CurNvarName = ''
            for VarSizeCount in range(0, 0x30):
                Val = ReadList(CurParamList, (RespBuffPtr + 0x1D + VarSizeCount), 1)
                if (Val == 0):
                    RespBuffPtr = RespBuffPtr + 0x1D + VarSizeCount + 1
                    break
                CurNvarName = CurNvarName + chr(Val)
            for VarId in MyKnobsDict:
                if ((CurNvarGuid == MyKnobsDict[VarId]['NvarGuid']) and (
                        CurNvarName == MyKnobsDict[VarId]['NvarName'])):
                    MyKnobsDict[VarId]['NvarSize'] = CurNvarSize
                    MyKnobsDict[VarId]['NvarAttri'] = CurNvarAttri
                    MyKnobsDict[VarId]['Status'] = CurNvarStatus
                    if ((CurNvarStatus == 0) and (CurNvarName != '')):
                        for KnobOfst in MyKnobsDict[VarId]['KnobDict']:
                            KnobSize = MyKnobsDict[VarId]['KnobDict'][KnobOfst]['KnobSzBin']
                            if KnobOfst >= BITWISE_KNOB_PREFIX:  # bitwise knob?
                                KnobWidth, CurOffset, BitOfst = get_bitwise_knob_details(KnobSize, KnobOfst, padding=0)
                                MyKnobsDict[VarId]['KnobDict'][KnobOfst]['CurVal'] = (ReadList(CurParamList, (
                                            RespBuffPtr + CurOffset), KnobWidth) >> BitOfst) & (and_mask(KnobWidth) >> (
                                            (KnobWidth * 8) - KnobSize))
                            else:
                                MyKnobsDict[VarId]['KnobDict'][KnobOfst]['CurVal'] = ReadList(CurParamList,
                                                                                              (RespBuffPtr + KnobOfst),
                                                                                              KnobSize)
                            MyKnobsDict[VarId]['KnobDict'][KnobOfst]['DefVal'] = \
                            MyKnobsDict[VarId]['KnobDict'][KnobOfst]['CurVal']
                    break
            if ((CurNvarStatus == 0) and (CurNvarName[0:3] == 'Def')):
                for VarId in MyKnobsDict:
                    DefGuid = copy.deepcopy(MyKnobsDict[VarId]['NvarGuid'])
                    DefGuid[0] = 0xDEFA901D
                    if ((CurNvarGuid == DefGuid) and (CurNvarName == ('Def' + MyKnobsDict[VarId]['NvarName'])) and (
                            MyKnobsDict[VarId]['Status'] == 0)):
                        for KnobOfst in MyKnobsDict[VarId]['KnobDict']:
                            KnobSize = MyKnobsDict[VarId]['KnobDict'][KnobOfst]['KnobSzBin']
                            if KnobOfst >= BITWISE_KNOB_PREFIX:  # bitwise knob?
                                KnobWidth, CurOffset, BitOfst = get_bitwise_knob_details(KnobSize, KnobOfst, padding=0)
                                MyKnobsDict[VarId]['KnobDict'][KnobOfst]['DefVal'] = (ReadList(CurParamList, (
                                            RespBuffPtr + CurOffset), KnobWidth) >> BitOfst) & (and_mask(KnobWidth) >> (
                                            (KnobWidth * 8) - KnobSize))
                            else:
                                MyKnobsDict[VarId]['KnobDict'][KnobOfst]['DefVal'] = ReadList(CurParamList,
                                                                                              (RespBuffPtr + KnobOfst),
                                                                                              KnobSize)
                        break
            RespBuffPtr = RespBuffPtr + CurNvarSize

    if not IndependentLite:
        memsave(filename, XmlAddr, (XmlSize - 0xB))
    mode = 'w' if IndependentLite else 'a'
    with open(filename, mode) as OutFile:
        if IndependentLite:
            OutFile.write('<SYSTEM>\n')
        KnobsDataToXmlFile(OutFile, BiosKnobDict=MyKnobsDict)
        OutFile.write('</SYSTEM>\n')

    if Operation == 'savexml':
        log.info(f'Saved XML Lite Data as {filename}')
    CloseInterface()
    return Status


def get_xml():
    InitInterface()

    # TODO add verification of DRAM address using verify_xmlcli_support
    dram_mb_addr = GetDramMbAddr()  # Get DRam MAilbox Address from Cmos.

    dram_shared_memory_buf = read_mem_block(dram_mb_addr, 0x200)  # Read/save parameter buffer
    xml_addr, xml_size = readxmldetails(dram_shared_memory_buf)  # read GBTG XML address and Size

    if not xml_addr:
        CloseInterface()
        raise BiosKnobsDataUnavailable()

    if isxmlvalid(xml_addr, xml_size):
        xml_bytearray = read_mem_block(xml_addr, int(xml_size))
        defused_xml = ET.fromstring(xml_bytearray.decode())

        # we're converting an element to a tree, we can safely use built-in xml
        # module because, at this point, it's already being parsed by defusedxml
        xml_data = ElementTree(defused_xml)
    else:
        CloseInterface()
        raise InvalidXmlData(f'XML is not valid or not yet generated xml_addr = 0x{xml_addr:X}, xml_size = 0x{xml_size:X}')

    CloseInterface()
    return xml_data


def XmlCmp(filename, XmlAddr):
    """
    Create or Compare and Save Target XML Header to file.

    If given XML is not present in target memory it creates new XML
    else if its present then function compares the same
    and if it is different XML is overwritten.

    :param filename: given xml file
    :param XmlAddr: address from which xml has to be downloaded
    :return:
    """
    HdrCmpLen = 0x140
    targetbuff = list(read_mem_block(XmlAddr, HdrCmpLen))
    if (os.path.isfile(filename)) and (os.path.getsize(filename) > 0x800):
        log.info('File Exists:  comparing target & host XML header')
        with open(filename, 'rb') as HostXML:
            hbuffer = list(HostXML.read(HdrCmpLen))
        if hbuffer[0:HdrCmpLen - 1] == targetbuff[0:HdrCmpLen - 1]:  # compare host & target XML header
            return True  # indicates Target XML was unchanged
    return False  # indicates Target XML file was not yet created


# Extract knob name from given KnobEntry pointer.
def findKnobName(KnobEntryAdd):
    KnobEntryBuff = read_mem_block(KnobEntryAdd, 0x100)  # copy first 256 chars in temp buffer
    Type = Name = ''
    for i in range(0x0, 0x100, 1):  # assuming the name attribute will be found within first 256 chars
        Knobname = ReadBuffer(KnobEntryBuff, i, 11, HEX)  # read 11 chars from buffer
        if (Knobname == 0x223D657079547075746573):  # compare with setupType='
            for j in range(0x0, 0x80, 1):  # assuming max knob name size of 128 chars
                if (ReadBuffer(KnobEntryBuff, i + 11 + j, 1, HEX) == 0x22):  # save till next '
                    Type = ReadBuffer(KnobEntryBuff, i + 11, j, ASCII)  # return Knob name
                    break
    for i in range(0x0, 0x100, 1):  # assuming the name attribute will be found within first 256 chars
        Knobname = ReadBuffer(KnobEntryBuff, i, 0x06, HEX)  # read 6 chars from buffer
        if (Knobname == 0x223D656D616E):  # compare with name='
            for j in range(0x0, 0x80, 1):  # assuming max knob name size of 128 chars
                if (ReadBuffer(KnobEntryBuff, i + 6 + j, 1, HEX) == 0x22):  # save till next '
                    Name = ReadBuffer(KnobEntryBuff, i + 6, j, ASCII)  # return Knob name
                    break
    return (Type, Name)


def getBiosDetails():
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
    global LastErrorSig
    LastErrorSig = 0x0000
    Platformname = ''
    BiosName = ''
    BiosTimestamp = ''
    InitInterface()
    DRAM_MbAddr = GetDramMbAddr()  # Get DRam Mailbox Address from Cmos.
    log.debug(f'CLI Spec Version = {GetCliSpecVersion(DRAM_MbAddr)}')
    log.debug(f'DRAM_MbAddr = 0x{DRAM_MbAddr:X}')
    if DRAM_MbAddr == 0x0:
        log.error('Dram Shared Mailbox not Valid, hence exiting')
        CloseInterface()
        return Platformname, BiosName, BiosTimestamp  # empty strings
    DramSharedMBbuf = read_mem_block(DRAM_MbAddr, 0x200)  # Read/save parameter buffer
    (XmlAddr, XmlSize) = readxmldetails(DramSharedMBbuf)
    if XmlAddr == 0:
        log.error('Platform Configuration XML not ready, hence exiting')
        LastErrorSig = 0x8AD0  # Xml Address is Zero
        runcpu()
        CloseInterface()
        return Platformname, BiosName, BiosTimestamp  # empty Strings
    if isxmlvalid(XmlAddr, XmlSize):
        XmlEntryBuff = read_mem_block(XmlAddr, 0x200)  # copy first 512 chars in temp buffer
        for i in range(0x0, 0x200, 1):  # assuming the name attribute will be found within first 512 chars
            Platformnametmp = ReadBuffer(XmlEntryBuff, i, 15, ASCII)  # read 16 chars from buffer
            BiosDetailstmp = ReadBuffer(XmlEntryBuff, i, 10, ASCII)  # read 16 chars from buffer
            if (Platformnametmp == '<PLATFORM NAME=') and (Platformname == ''):  # compare with name='
                for j in range(0x0, 0x80, 1):  # assuming max Platform name size of 128 chars
                    if ReadBuffer(XmlEntryBuff, i + 16 + j, 1, HEX) == 0x22:  # save till next '
                        Platformname = ReadBuffer(XmlEntryBuff, i + 16, j, ASCII)  # return Knob name
                        log.debug(f'Platform Name = {Platformname}')
                        break
            if ((BiosDetailstmp == '<CPUSVBIOS') or (BiosDetailstmp[0:7] == '<SVBIOS') or (
                    BiosDetailstmp[0:5] == '<BIOS')
            ) and (BiosName == '') and (BiosTimestamp == ''):  # compare with name='
                if BiosDetailstmp == '<CPUSVBIOS':
                    AtriLen = 11
                elif BiosDetailstmp[0:7] == '<SVBIOS':
                    AtriLen = 8
                elif BiosDetailstmp[0:5] == '<BIOS':
                    AtriLen = 6
                for j in range(0x0, 0x100, 1):  # assuming max BIOS name size of 256 chars
                    BiosNametmp = ReadBuffer(XmlEntryBuff, i + AtriLen + j, 8, ASCII)  # read 16 chars from buffer
                    BiosTimestamptmp = ReadBuffer(XmlEntryBuff, i + AtriLen + j, 7, ASCII)  # read 16 chars from buffer
                    if (BiosNametmp == 'VERSION=') and (BiosName == ''):
                        for k in range(0x0, 0x80, 1):  # assuming max BIOS name size of 128 chars
                            if ReadBuffer(XmlEntryBuff, i + AtriLen + j + 9 + k, 1, HEX) == 0x22:  # save till next '
                                BiosName = ReadBuffer(XmlEntryBuff, i + AtriLen + j + 9, k, ASCII)  # return Knob name
                                log.debug(f'Bios Version = {BiosName}')
                                break
                    if (BiosTimestamptmp == 'TSTAMP=') and (BiosTimestamp == ''):
                        for k in range(0x0, 0x80, 1):  # assuming max BIOS name size of 128 chars
                            if ReadBuffer(XmlEntryBuff, i + AtriLen + j + 8 + k, 1, HEX) == 0x22:  # save till next '
                                BiosTimestamp = ReadBuffer(XmlEntryBuff, i + AtriLen + j + 8, k,
                                                           ASCII)  # return Knob name
                                log.debug(f'Bios Timestamp = {BiosTimestamp}')
                                break
    CloseInterface()
    return Platformname, BiosName, BiosTimestamp


def ClearCliBuff(cli_request_buffer_address, cli_response_buffer_address):
    """
    This function clears CLI Request and Response buffers.
    This can be done by writing `0` to the buffer.

    :param cli_request_buffer_address: address of CLI Request buffer
    :param cli_response_buffer_address: address of CLI Response buffer
    :return:
    """
    memwrite(cli_request_buffer_address, 8, 0)
    memwrite(cli_request_buffer_address + 8, 8, 0)
    memwrite(cli_response_buffer_address, 8, 0)
    memwrite(cli_response_buffer_address + 8, 8, 0)


def getEfiCompatibleTableBase():
    """Search for the EFI Compatible tables in 0xE000/F000 segments

    Use-case would be to find DramMailbox in legacy way
    :return:
    """
    global LastErrorSig
    LastErrorSig = 0x0000
    EfiComTblSig = 0x24454649
    for Index in range(0, 0x1000, 0x10):
        Sig1 = memread(0xE0000 + Index, 4)
        Sig2 = memread(0xF0000 + Index, 4)
        if (Sig1 == EfiComTblSig):
            BaseAddress = 0xE0000 + Index;
            log.debug(f'Found EfiCompatibleTable Signature at 0x{BaseAddress:X}')
            return BaseAddress
        if (Sig2 == EfiComTblSig):
            BaseAddress = 0xF0000 + Index;
            log.debug(f'Found EfiCompatibleTable Signature at 0x{BaseAddress:X}')
            return BaseAddress
    log.debug(hex(Index))
    LastErrorSig = 0xEFC9  # EfiCompatibleTable Not Found
    return 0


def get_bin_file(access_method, **kwargs):
    """Stores chunk of memory consisting the bios

    :param access_method: specify valid interface type
    :param kwargs:
        - max_bios_size: (optional) specifies size of bios in bytes
        - memory_size: (optional) specifies size of memory in bytes boundary where end of bios lies
        - output_bin_file: (optional) specifies location of storing chunk of memory
    :return: location of binary file stored

    Usage:
    >>> get_bin_file(access_method="winhwa")    # specifies access method and stores result

    Optional parameters can also be used to override default values as below
    >>> get_bin_file(access_method="winhwa", max_bios_size=12 * (1024**2))  # overrides bios size to 12 MB and will store only 12 MB chunk ending at memory address

    Multiple optional arguments can also be used to override default parameters
    >>> get_bin_file(access_method="winhwa", max_bios_size=12 * (1024**2), bin_file="path/to/store/bin_file.bin")  # overrides default location of binary file to store and bios size
    """
    max_bios_size = kwargs.get("max_bios_size", 32 * (1024 ** 2))  # default: 32 MB
    memory_size = kwargs.get("memory_size", 4 * (1024 ** 3))  # default: 4 GB
    bin_file = kwargs.get("output_bin_file", os.path.join(TempFolder, "online_bios.bin"))
    if access_method not in utils.VALID_ACCESS_METHODS:
        err_msg = "Invalid Access Method: {}".format(access_method)
        log.error(err_msg)
        raise Exception(err_msg)
    else:
        set_cli_access(access_method)
        status = InitInterface()
        log.debug("Status of XmlCli (init interface..): {}".format(status))
        start = memory_size - max_bios_size  # start address of chunk to parse bios region
        log.debug("Start of BIOS at memory: 0x{:x}".format(start))
        memsave(bin_file, start, max_bios_size)
        if os.path.exists(bin_file):
            log.info("Memory dump from 0x{:x} of size 0x{:x} is stored at: {}".format(start, max_bios_size, bin_file))
        CloseInterface()
        return bin_file


def SearchForSystemTableAddress():
    for Address in range(0x20000000, 0xE0000000, 0x400000):  # EFI_SYSTEM_TABLE_POINTER address is 4MB aligned
        Signature = memread(Address, 8)
        if (Signature == 0x5453595320494249):  # EFI System Table Signature = 'IBI SYST'
            Address = memread((Address + 8), 8)
            return Address
    return 0


def readDramMbAddrFromEFI():
    DramSharedMailBoxGuidLow = 0x4D2C18789D99A394
    DramSharedMailBoxGuidHigh = 0x3379C48E6BC1E998
    log.debug('Searching for Dram Shared Mailbox address from gST EfiConfigTable..')
    gST = SearchForSystemTableAddress()
    if (gST == 0):
        EfiCompatibleTableBase = getEfiCompatibleTableBase()
        if (EfiCompatibleTableBase == 0):
            return 0
        gST = memread(EfiCompatibleTableBase + 0x14, 4)
    Signature = memread(gST, 8)
    if (Signature != 0x5453595320494249):  # EFI System Table Signature = 'IBI SYST'
        return 0
    log.debug(
        f'EFI SYSTEM TABLE Address = 0x{gST:X}  Signature = \"{UnHexLiFy(Signature)[::-1]}\"    Revision = {memread(gST + 8, 2):d}.{memread(gST + 0xA, 2):d}')
    count = 0
    FirmwarePtr = memread(gST + 0x18, 8)
    FirmwareRevision = memread(gST + 0x20, 4)
    BiosStr = ''
    while (1):
        Value = int(memread(FirmwarePtr + count, 2))
        if (Value == 0):
            break
        BiosStr = BiosStr + chr((Value & 0xFF))
        count = count + 2
    log.debug(f'Firmware : {BiosStr}')
    log.debug(f'Firmware Revision: 0x{FirmwareRevision:X}')
    EfiConfigTblEntries = memread(gST + 0x68, 8)
    EfiConfigTbl = memread(gST + 0x70, 8)
    log.debug(f'EfiConfigTblEntries = {EfiConfigTblEntries:d}  EfiConfigTbl Addr = 0x{EfiConfigTbl:X}')
    Offset = 0
    DramMailboxAddr = 0
    for Index in range(0, EfiConfigTblEntries):
        GuidLow = memread(EfiConfigTbl + Offset, 8)
        GuidHigh = memread(EfiConfigTbl + 8 + Offset, 8)
        if ((GuidLow == DramSharedMailBoxGuidLow) and (GuidHigh == DramSharedMailBoxGuidHigh)):
            DramMailboxAddr = int(memread(EfiConfigTbl + 16 + Offset, 8))
            log.info(f'Found Dram Shared MailBox Address = 0x{DramMailboxAddr:X} from EfiConfigTable')
            break
        Offset = Offset + 0x18
    return DramMailboxAddr


def PrintE820Table():
    """Legacy function for printing E820 table for memory type identification using
    legacy efi compatible table

    EFI ST offset = 0x14
    ACPI table offset = 0x1C
    E820 Table offset = 0x22
    E820 table Length = 0x26

    :return:
    """
    Offset = 0
    Index = 0
    E820TableList = {}
    EfiCompatibleTableBase = getEfiCompatibleTableBase()
    E820Ptr = memread(EfiCompatibleTableBase + 0x22, 4)
    Size = memread(EfiCompatibleTableBase + 0x26, 4)
    log.debug(',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,')
    log.debug('E820[no]: Start Block Address ---- End Block Address , Type = Mem Type')
    log.debug('``````````````````````````````````````````````````````````````````````')
    while (1):
        BaseAddr = memread(E820Ptr + Offset, 8)
        Length = memread(E820Ptr + Offset + 8, 8)
        Type = memread(E820Ptr + Offset + 16, 4)
        log.debug(f'E820[{Index:2d}]:  0x{BaseAddr:16X} ---- 0x{(BaseAddr + Length):<16X}, Type = 0X{Type:x} ')
        E820TableList[Index] = [BaseAddr, Length, Type]
        Index = Index + 1
        Offset = Offset + 20
        if (Offset >= Size):
            break
    log.debug(',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,')
    return E820TableList
