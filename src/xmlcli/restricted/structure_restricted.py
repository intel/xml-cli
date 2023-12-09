# -*- coding: utf-8 -*-

# Built-in imports
import ctypes

# custom imports
from ..common import utils


class FlashMap0(utils.StructureHelper):
  """Structure to read FLMAP0 - Flash Map 0 Register
  from IFWI descriptor region lying at offset 0x14

  Offset 014h: FLMAP0 - Flash MAP 0
  000014 0x00040003

  Flash Region Base Address (FRBA)      [23:16] = 04
  FRBA Region starting address                  = 000040
  FP sensor on shared flash/TPM SPI bus [12]    = 0b
  Touch on dedicated SPI bus            [11]    = 0b
  Touch on shared flash/TPM SPI bus     [10]    = 0b
  Number Of Components (NC)             [9:8]   = 0h
  Flash Component Base Address (FCBA)   [7:0]   = 3h
  FCBA Region starting address                  = 000030

  """
  _fields_ = [
    ("FlashComponentBaseAddress", ctypes.c_uint8),  # Flash Component Base Address
    # read values by bits
    ("NumberOfComponents", ctypes.c_uint8, 2),  # Number Of Components (NC) - 2 bits
    ("TouchOnSharedFlash", ctypes.c_uint8, 1),  # Touch on shared flash/TPM SPI bus - 1 bit
    ("TouchOnSharedFlashTpmSpiBus", ctypes.c_uint8, 1),  # Touch on shared flash/TPM SPI bus - 1 bit
    ("TouchOnDedicatedSpiBus", ctypes.c_uint8, 1),  # Touch on dedicated SPI bus - 1 bit
    ("FpSensorOnSharedFlashTpmSpiBus", ctypes.c_uint8, 1),  # FP Sensor on shared flash/TPM SPI bus - 1 bit
    ("data", ctypes.c_uint8, 2),  # not aware of what it is!
    # byte read
    ("FlashRegionBaseAddress", ctypes.c_uint8),  # Flash Region Base Address
    ("data", ctypes.c_uint8),  # not aware of what it is!
  ]

  @property
  def flash_region_starting_address(self):
    return self.FlashRegionBaseAddress << 4

  @property
  def flash_component_starting_address(self):
    return self.FlashComponentBaseAddress << 4


class FlashMap1(utils.StructureHelper):
  """Structure to read FLMAP1 - Flash Map 1 Register
  from IFWI descriptor region lying at offset 0x18

  Offset 018h: FLMAP1 - Flash MAP 1
  000018 0x42100208

  PCH Strap Length (PSL):               [31:24] = 42h
  Flash PCH Strap Base Address (FPSBA)  [23:16] = 10h
  FPSBA Region starting address                 = 000100
  Number Of Masters (NM):               [10:8]  = 02h
  Flash Master Base Address (FMBA)      [7:0]   = 08h
  FMBA Region starting address                  = 000080
  """
  _fields_ = [
    ("FlashMasterBaseAddress", ctypes.c_uint8),  # Flash Master Base Address (FMBA)
    # read bits
    ("NumberOfMasters", ctypes.c_uint8, 3),  # Number Of Masters (NM)
    ("data", ctypes.c_uint8, 5),  # not aware of what it is!
    # read bytes
    ("FlashPchStrapBaseAddress", ctypes.c_uint8),  # Flash PCH Strap Base Address (FPSBA)
    ("PchStrapLength", ctypes.c_uint8),  # PCH Strap Length (PSL)
  ]

  @property
  def flash_master_start_address(self):
    return self.FlashMasterBaseAddress << 4

  @property
  def flash_pch_strap_start_address(self):
    return self.FlashPchStrapBaseAddress << 4


class FlashMap2(utils.StructureHelper):
  """Structure to read FLMAP2 - Flash Map 2 Register
  from IFWI descriptor region lying at offset 0x1c

  Offset 01Ch: FLMAP2 - Flash MAP 2
  00001c 0x001101a0

  Register Init Length (RIL)            [31:24] = 00h
  Register Init Base Address (RIBA)     [23:16] = 11h
  RIBA Region starting address                  = 000110
  CPU Strap Length (CPUSL)              [15:8]  = 01h
  Flash CPU Strap Base Address (FCPUSBA)[7:0]   = a0h
  FCPUSBA Region starting address               = 000a00
  """
  _fields_ = [
    ("FlashCpuStrapBaseAddress", ctypes.c_uint8),  # Flash CPU Strap Base Address (FCPUSBA)
    ("CpuStrapLength", ctypes.c_uint8),  # CPU Strap Length (CPUSL)
    ("RegisterInitBaseAddress", ctypes.c_uint8),  # Register Init Base Address (RIBA)
    ("RegisterInitLength", ctypes.c_uint8),  # Register Init Length (RIL)
  ]

  @property
  def flash_cpu_strap_start_address(self):
    return self.FlashCpuStrapBaseAddress << 4

  @property
  def flash_register_init_start_address(self):
    return self.RegisterInitBaseAddress << 4


class FlashComponentBaseAddress(utils.StructureHelper):
  """Structure to read Flash Component Base Address (FCBA)
  from IFWI descriptor region lying at offset 0x30

  Offset 030h: Flash Component Base Address (FCBA):
  000030 0x2490f0f6

  Dual Output Fast Read Support:        [30]    = 0b Dual Output Fast Read is not Supported
  Read ID and Read Status Clock Freq    [29:27] = 4h 30MHz
  Write and Erase Clock Frequency       [26:24] = 4h 30MHz
  Fast Read Clock Frequency             [23:21] = 4h 30MHz
  Fast Read Support                     [20]    = 1b Fast Read is supported
  Read Clock Frequency                  [19:17] = 0h 120MHz (not supported in SPT)
  Component 1 Density                   [7:4]   = fh 2nd flash component not present
  Component 0 Density                   [3:0]   = 6h 32MB

  """
  _fields_ = [
    # read bits
    ("Component0Density", ctypes.c_uint8, 4),  # Component 0 Density
    ("Component1Density", ctypes.c_uint8, 4),  # Component 1 Density

    ("data", ctypes.c_uint8),  # not aware of what it is!

    ("data", ctypes.c_uint8, 1),  # not aware of what it is!
    ("ReadClockFrequency", ctypes.c_uint8, 3),  # Read Clock Frequency
    ("FastReadSupport", ctypes.c_uint8, 1),  # Fast Read Support
    ("FastReadClockFrequency", ctypes.c_uint8, 3),  # Fast Read Clock Frequency

    ("WriteAndEraseClockFrequency", ctypes.c_uint8, 3),  # Write and Erase Clock Frequency
    ("ReadIdAndReadStatusClockFreq", ctypes.c_uint8, 3),  # Read ID and Read Status Clock Freq
    ("DualOutputFastReadSupport", ctypes.c_uint8, 1),  # Dual Output Fast Read Support
    ("data", ctypes.c_uint8, 1),  # not aware of what it is!

    ("data", ctypes.ARRAY(ctypes.c_uint8, 12)),  # not aware of what it is!
  ]


class CommonFlashDescriptorRegion(utils.StructureHelper):
  """Structure to read Flash Region
  """
  _fields_ = [
    ("RegionBase", ctypes.c_uint32, 15),  # Region Base
    ("data", ctypes.c_uint32, 1),  # not aware of what it is!
    ("RegionLimit", ctypes.c_uint32, 15),  # Region Limit
    ("data", ctypes.c_uint32, 1),  # not aware of what it is!
  ]


class FlashDescriptorRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG0 - Flash Region 0 - Flash Descriptor

  000040 0x00000000
  Offset FRBA + 000h: FLREG0 - Flash Region 0 - Flash Descriptor
  Region Limit:                         [30:16] = 0x0000
  Region Base:                          [14:0]  = 0x0000
  """
  pass


class BIOSRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG1 - Flash Region 1 - BIOS

  000044 0x1fff1400
  Offset FRBA + 004h: FLREG1 - Flash Region 1 - BIOS
  Region Limit:                         [30:16] = 0x1fff
  Region Base:                          [14:0]  = 0x1400
  """
  @property
  def bios_address(self):
    return (self.RegionBase & 0x7FFF) << 12

  @property
  def bios_end_address(self):
    return ((self.RegionLimit & 0x7FFF) << 12) | 0xFFF


class CsmeRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG2 - Flash Region 2 – Converged Security and Manageability Engine (CSME)

  000048 0x10820083
  Offset FRBA + 008h: FLREG2 - Flash Region 2 – Converged Security and Manageability Engine (CSME)
  Region Limit:                         [30:16] = 0x1082
  Region Base:                          [14:0]  = 0x0083
  """
  pass


class GbERegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG3 - Flash Region 3 - GbE

  00004c 0x00820081
  Offset FRBA + 00Ch: FLREG3 - Flash Region 3 - GbE
  Region Limit:                         [30:16] = 0x0082
  Region Base:                          [14:0]  = 0x0081
  """
  pass


class PlatformDataRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG4 - Flash Region 4 - Platform Data

  000050 0x00007fff
  Offset FRBA + 010h: FLREG4 - Flash Region 4 - Platform Data
  Region Limit:                         [30:16] = 0x0000
  Region Base:                          [14:0]  = 0x7fff
  """
  pass


class DeviceExpansionRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG5 - Flash Region 5 – Device Expansion

  000054 0x00007fff
  Offset FRBA + 014h: FLREG5 - Flash Region 5 – Device Expansion
  Region Limit:                         [30:16] = 0x0000
  Region Base:                          [14:0]  = 0x7fff
  """
  pass


class SecondaryBIOSRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG6 - Flash Region 6 – Secondary BIOS

  000058 0x00007fff
  Offset FRBA + 018h: FLREG6 - Flash Region 6 – Secondary BIOS
  Region Limit:                         [30:16] = 0x0000
  Region Base:                          [14:0]  = 0x7fff
  """
  pass


class UcodePatchRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG7 - Flash Region 7 - uCode patch

  00005c 0x00007fff
  Offset FRBA + 01Ch: FLREG7 - Flash Region 7 - uCode patch
  Region Limit:                         [30:16] = 0x0000
  Region Base:                          [14:0]  = 0x7fff
  """
  pass


class ECRegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG8 - Flash Region 8 - EC

  000060 0x00800001
  Offset FRBA + 020h: FLREG8 - Flash Region 8 - EC
  Region Limit:                         [30:16] = 0x0080
  Region Base:                          [14:0]  = 0x0001
  """
  pass


class IERegion(CommonFlashDescriptorRegion):
  """Structure to read FLREG9 - Flash Region 9 - IE

  000064 0x13ff1083
  Offset FRBA + 024h: FLREG9 - Flash Region 9 - IE
  Region Limit:                         [30:16] = 0x13ff
  Region Base:                          [14:0]  = 0x1083
  """
  pass


class FlashRegionBaseAddress(utils.StructureHelper):
  """Structure to read Flash Region Base Address (FRBA)
  from IFWI descriptor region lying at offset 0x40
  """
  _fields_ = [
    ("FlashDescriptor", FlashDescriptorRegion),  # FLREG0 - Flash Region 0 - 4 bytes
    ("Bios", BIOSRegion),  # FLREG1 - Flash Region 1 - 4 bytes
    ("Csme", CsmeRegion),  # FLREG2 - Flash Region 2 - 4 bytes
    ("GbE", GbERegion),  # FLREG3 - Flash Region 3 - 4 bytes
    ("PlatformData", PlatformDataRegion),  # FLREG4 - Flash Region 4 - 4 bytes
    ("DeviceExpansion", DeviceExpansionRegion),  # FLREG5 - Flash Region 5 - 4 bytes
    ("SecondaryBIOS", SecondaryBIOSRegion),  # FLREG6 - Flash Region 6 - 4 bytes
    ("UcodePatch", UcodePatchRegion),  # FLREG7 - Flash Region 7 - 4 bytes
    ("EC", ECRegion),  # FLREG8 - Flash Region 8 - 4 bytes
    ("IE", IERegion),  # FLREG9 - Flash Region 9 - 4 bytes
  ]

  def dump_dict(self):
    result = super(FlashRegionBaseAddress, self).dump_dict()
    result["extra_info"] = {
      "BIOSAddress": self.bios_address,
      "BIOSEndAddress": self.bios_end_address
    }

  @property
  def bios_address(self):
    return self.Bios.bios_address

  @property
  def bios_end_address(self):
    return self.Bios.bios_end_address


class DescriptorRegion(utils.StructureHelper):
  """Structure to read IFWI descriptor region
  lying at offset 0x0 to 0x0FFF

  Note: this is referred from 32 MB IFWI and from source:
  https://wiki.ith.intel.com/display/BIOSBKM/Descriptor+Area
  https://github.com/ISpillMyDrink/UEFI-Repair-Guide/wiki/Flash-Layout

  other IFWI size is yet to be tested out!
  """
  _fields_ = [
    ("Unknown", ctypes.ARRAY(ctypes.c_uint8, 16)),  # Not aware of 0x0 to 0x10 bytes of IFWI
    ("FLVALSIG", ctypes.c_uint32),  # Flash Valid Signature - 0x0ff0a55a [5A A5 F0 0F]
    ("FLMAP0", FlashMap0),  # Flash Map 0 - 4 bytes (@ 0x14)
    ("FLMAP1", FlashMap1),  # Flash Map 1 - 4 bytes (@ 0x18)
    ("FLMAP2", FlashMap2),  # Flash Map 2 - 4 bytes (@ 0x1C)
    ("Unknown", ctypes.ARRAY(ctypes.c_uint8, 16)),  # not know what data it is! (0x1f to 0x30)
    ("FCBA", FlashComponentBaseAddress),  # Flash Component Base Address - 16 bytes (@ 0x30)
    ("FRBA", FlashRegionBaseAddress),  # Flash Region Base Address - 40 bytes - (@ 0x40)
  ]

  @property
  def bios_address(self):
    return self.FRBA.bios_address

  @property
  def bios_end_address(self):
    return self.FRBA.bios_end_address


class AcmHeader(utils.StructureHelper):
  """Structure to read ACM Header Information
  """

  _fields_ = [
    ('ModuleType', ctypes.c_uint16),  # 2 bytes
    ('ModuleSubType', ctypes.c_uint16),  # 2 bytes
    ('HeaderLen', ctypes.c_uint32),  # 4 bytes
    ('HeaderVersion', ctypes.c_uint32),  # 4 bytes
    ('ChipsetID', ctypes.c_uint16),  # 2 bytes
    ('Flags', ctypes.c_uint16),  # 2 bytes
    ('ModuleVendor', ctypes.c_uint32),  # 2 bytes
    ('Day', ctypes.c_uint8),  # 1 byte
    ('Month', ctypes.c_uint8),  # 1 byte
    ('Year', ctypes.c_uint16),  # 2 bytes
    ('Size', ctypes.c_uint32)  # 4 bytes
  ]

  @property
  def get_date_str(self):
    return f'{self.Day:02X}-{self.Month:02X}-{self.Year:02X}'

  @property
  def get_acm_size(self):
    return self.Size * 0x04  # Module size (in multiples of four bytes) according to ACM specification

  @property
  def get_value_list(self):
    return [hex(self.HeaderVersion), hex(self.ModuleSubType), hex(self.ChipsetID), hex(self.Flags),
                 hex(self.ModuleVendor), self.get_date_str, hex(self.get_acm_size)]


class AcmGuidStructure(utils.StructureHelper):
  """Structure for ACM GUID and version information
  """

  _fields_ = [
    ("AcmGuid", utils.Guid),
    ("Unknown", ctypes.ARRAY(ctypes.c_uint8, 21)),
    ("Major", ctypes.c_uint8),
    ("Minor", ctypes.c_uint8),
    ("Micro", ctypes.c_uint8)
  ]

  @property
  def get_version_str(self):
    return f"{self.Major}.{self.Minor}.{self.Micro}"
