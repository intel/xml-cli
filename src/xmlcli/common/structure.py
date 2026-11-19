# -*- coding: utf-8 -*-

# Built-in imports
import ctypes
from collections import namedtuple

# custom imports
from . import utils
from .logger import log
try:
  from ..restricted.structure_restricted import *
except ModuleNotFoundError as e:
  DescriptorRegion = None

__version__ = "0.0.1"
__author__ = "Gahan Saraiya"


########################################################################################################################
# BEGIN:CONSTANTS ######################################################################################################
FFS_ALIGNMENT = 8
SECTION_ALIGNMENT = 4
FV_BLOCK_ALIGNMENT = 0x1000  # 4 KB
DESC_SIGNATURE = 0x0FF0A55A  # Flash Valid Signature - 0x0ff0a55a [5A A5 F0 0F]
DEFAULT_GUID = "ffffffff-ffff-ffff-ffffffffffffffff"
FV_SIGNATURE = b"_FVH"

# END:CONSTANTS ########################################################################################################


########################################################################################################################
# BEGIN:UTILITIES ######################################################################################################

def is_ifwi(bin_file):
  """Function to Check if the given binary is valid IFWI binary or not

  :param bin_file: binary file
  :return: function will return True if given binary file is valid IFWI binary
  """

  spi_desc = DescriptorRegion.read_from(bin_file)
  return spi_desc.FLVALSIG == DESC_SIGNATURE


def is_bios(bin_file):
  """Function to Check if the given binary is valid BIOS binary or not

  :param bin_file: binary file
  :return: function will return True if given binary file is valid BIOS binary
  """

  bios_header = EfiFirmwareVolumeHeader.read_from(bin_file)
  return FV_SIGNATURE == bios_header.Signature

def struct2stream(target_struct):
    length = ctypes.sizeof(target_struct)
    p = ctypes.cast(ctypes.pointer(target_struct), ctypes.POINTER(ctypes.c_char * length))
    return p.contents.raw

def get_pad_size(size: int, alignment: int):
    if size % alignment == 0:
        return 0
    pad_Size = alignment - size % alignment
    return pad_Size

def read_structure(method, base_structure, buffer, buffer_pointer):
  """Read Valid structure
  Created to ease the re computation of reading valid structure if

  :param method: method which will return correct structure to be parsed based on read data
  :param base_structure: base structure to be used to read data to parse actual structure
  :param buffer: buffer from which structure to be read
  :param buffer_pointer: pointer to start reading the structure
  :return: valid read structure data object
  """
  buffer.seek(buffer_pointer)
  data = base_structure().read_from(buffer)
  modified_structure = method(data)
  buffer.seek(buffer_pointer)
  data = modified_structure.read_from(buffer)
  return data


def section_finder(buffer, buffer_pointer):
  """Find valid section from given buffer

  :param buffer: buffer to read valid section from from
  :param buffer_pointer: pointer to start reading valid section
  :return: valid read section structure object
  """
  buffer.seek(buffer_pointer)
  data = read_structure(method=efi_section_all,
                        base_structure=EfiCommonSectionHeader,
                        buffer=buffer,
                        buffer_pointer=buffer_pointer)
  section_tuple = FFS_SECTION_TYPE_MAP.get(data.section_type)
  modified_structure = section_tuple.structure(data)
  buffer.seek(buffer_pointer)
  data = modified_structure.read_from(buffer)
  return data


def process_efi_firmware_contents_signed_guid(buffer, buffer_pointer, section):
  log.debug(f"buffer_pos - 0x{buffer.tell():x}")
  certificate = WinCertificateEfiPkcs115().read_from(buffer)
  log.debug(certificate)
  buffer_pointer = buffer_pointer + certificate.get_section_size()
  # section_guid = certificate.HashAlgorithm.guid
  section = section_finder(buffer=buffer, buffer_pointer=buffer_pointer)
  log.debug(section)
  if FFS_SECTION_TYPE_MAP.get(section.section_type).name == "EFI_SECTION_RAW":
    # A leaf section that contains an array of zero or more bytes. No particular formatting of these
    # bytes is implied by this section type. EFI_RAW_SECTION2 must be used if the section is 16MB or larger.
    section_guid = 0
    start = buffer_pointer
  else:
    section_guid = section.SectionDefinitionGuid.guid
    start = buffer_pointer + section.DataOffset
  log.debug(f"buffer_pos - 0x{buffer_pointer:x}")
  buffer.seek(buffer_pointer)
  return start, section_guid, section


def process_decompress_guid(buffer, buffer_pointer, section):
  log.debug(f"buffer_pos - 0x{buffer.tell():x}")
  if FFS_SECTION_TYPE_MAP.get(section.section_type).name == "EFI_SECTION_RAW":
    # A leaf section that contains an array of zero or more bytes. No particular formatting of these
    # bytes is implied by this section type. EFI_RAW_SECTION2 must be used if the section is 16MB or larger.
    section_guid = 0
    start = buffer_pointer
  else:
    section_guid = section.SectionDefinitionGuid.guid
    start = buffer_pointer
  return start, section_guid, section


def process_efi_cert_type_rsa2048_sha256_guid(buffer, buffer_pointer, section):
  log.debug(f"Buffer position: 0x{buffer.tell():x}")
  certificate = EfiCertRsa2048Sha256().read_from(buffer)
  log.debug(certificate)
  log.debug(f"class size: 0x{certificate.cls_size:x}")
  buffer_pos = buffer.tell()
  section_content = section_finder(buffer=buffer,
                                   buffer_pointer=buffer_pos)
  log.debug(section_content)
  start = buffer_pointer + certificate.cls_size
  section_tuple = FFS_SECTION_TYPE_MAP.get(section.section_type)
  if section_tuple.name == "EFI_SECTION_RAW" or not hasattr(section_content, "get_guid"):
    # A leaf section that contains an array of zero or more bytes. No particular formatting of these
    # bytes is implied by this section type. EFI_RAW_SECTION2 must be used if the section is 16MB or larger.
    section_guid = 0
  else:
    section_guid = section_content.get_guid.guid
    start += section_content.DataOffset
  return start, section_guid, section_content

# END:UTILITIES ########################################################################################################


########################################################################################################################
# BEGIN:STRUCTURES #####################################################################################################


# source : Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
MAX_SECTION_SIZE = 0xffffff  # if section size beyond this; header will have extended header info
MAX_FFS_SIZE = 0xffffff  # if ffs size beyond this; header will have extended header info
CHAR16 = ctypes.c_ushort
EFI_FVB_ATTRIBUTES_2 = ctypes.c_uint32
EFI_FV_FILETYPE = ctypes.c_uint8
EFI_FFS_FILE_ATTRIBUTES = ctypes.c_uint8
EFI_FFS_FILE_STATE = ctypes.c_uint8
EFI_SECTION_TYPE = ctypes.c_uint8

# source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
EFI_FV_FILE_ATTRIBUTES = ctypes.c_uint32
EFI_FV_FILE_ATTRIB_ALIGNMENT = 0x0000001F
EFI_FV_FILE_ATTRIB_FIXED = 0x00000100
EFI_FV_FILE_ATTRIB_MEMORY_MAPPED = 0x00000200
# i.e. EFI_FVB2_ALIGNMENT_128 will be 0x00070000
EFI_FVB2_ALIGNMENT = lambda size=None: "0x001F0000" if not size else f"0x{size:0>4x}0000"
EFI_FVB2_WEAK_ALIGNMENT = 0x80000000
EFI_FVB2_ERASE_POLARITY = 0x00000800


class EfiTime(utils.StructureHelper):  # 16 bytes
  # source: Edk2/MdePkg/Include/Uefi/UefiBaseType.h
  _fields_ = [
    ("Year", ctypes.c_uint16),  # 2 bytes
    ("Month", ctypes.c_uint8),  # 1 byte
    ("Day", ctypes.c_uint8),  # 1 byte
    ("Hour", ctypes.c_uint8),  # 1 byte
    ("Minute", ctypes.c_uint8),  # 1 byte
    ("Second", ctypes.c_uint8),  # 1 byte
    ("Pad1", ctypes.c_uint8),  # 1 byte
    ("Nanosecond", ctypes.c_uint32),  # 4 bytes
    ("TimeZone", ctypes.c_uint16),  # 2 bytes
    ("Daylight", ctypes.c_uint8),  # 1 byte
    ("Pad2", ctypes.c_uint8),  # 1 byte
  ]


# creating alias
EfiGuid = utils.Guid  # source: Edk2/BaseTools/Source/C/Include/Common/UefiBaseTypes.h


class TianoCompressHeader(utils.StructureHelper):
  # source: UEFI Spec 2.8 -> Page 953 -> Fig. 64
  _fields_ = [
    ("CompressedSize", ctypes.c_uint32),
    ("OriginalSize", ctypes.c_uint32)
  ]


class EfiCapsuleHeader(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/UefiCapsule.h
  _fields_ = [
    ("CapsuleGuid", utils.Guid),
    ("HeaderSize", ctypes.c_uint32),
    ("Flags", ctypes.c_uint32),
    ("CapsuleImageSize", ctypes.c_uint32)
  ]

  @property
  def get_guid(self):
    return self.CapsuleGuid


class Checksum(utils.StructureHelper):
  # source : Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
  _fields_ = [
    ("Header", ctypes.c_uint8),
    ("File", ctypes.c_uint8)
  ]


class EfiFfsIntegrityCheck(utils.StructureHelper):
  # source : Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
  _pack_ = 1
  _fields_ = [
    ("Checksum", Checksum),  # ignoring this structure for now for ease of parsing
    # ("Checksum16", ctypes.c_uint16)
  ]


class EfiFfsFileHeader(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
  # _pack_ = 8  # aligned at 8-byte boundary
  _pack_ = 1
  _fields_ = [
    ("Name", utils.Guid),  # 16 bytes
    ("IntegrityCheck", EfiFfsIntegrityCheck),  # EFI_FFS_INTEGRITY_CHECK , 2 bytes
    ("Type", EFI_FV_FILETYPE),  # UINT8
    ("Attributes", EFI_FFS_FILE_ATTRIBUTES),  # UINT8
    ("Size", ctypes.ARRAY(ctypes.c_uint8, 3)),  # Length of file in bytes including header
    ("State", EFI_FFS_FILE_STATE),  # UINT8
  ]

  def dump_dict(self):
    result = super(EfiFfsFileHeader, self).dump_dict()
    result.pop("IntegrityCheck")
    ffs_tuple = FFS_FILE_TYPE_MAP.get(self.Type)
    if ffs_tuple:
      # Add extra keys to dictionary for ffs type and description
      result["Type"] = ffs_tuple.name
      result["Description"] = ffs_tuple.description
    return result

  @property
  def get_guid(self):
    return self.Name

  @property
  def size(self):
    size = self.array_to_int(self.Size)
    return int(size, 16)


class EfiFfsFileHeader2(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
  _pack_ = 1
  _fields_ = [
    ("Name", utils.Guid),
    ("IntegrityCheck", EfiFfsIntegrityCheck),  # EFI_FFS_INTEGRITY_CHECK
    ("Type", EFI_FV_FILETYPE),
    ("Attributes", EFI_FFS_FILE_ATTRIBUTES),
    ("Size", ctypes.ARRAY(ctypes.c_uint8, 3)),
    ("State", EFI_FFS_FILE_STATE),
    ("ExtendedSize", ctypes.c_uint64),
  ]

  def dump_dict(self):
    result = super(EfiFfsFileHeader2, self).dump_dict()
    result.pop("IntegrityCheck")
    return result

  @property
  def get_guid(self):
    return self.Name

  @property
  def size(self):
    return self.ExtendedSize


def efi_ffs_file_header(structure_content):
  if structure_content.Name.guid == DEFAULT_GUID:
    return EfiFfsFileHeader()
  # if size of FFS size exceeds MAX_FFS_SIZE (0xffFFff) or
  # having attributes bit 0 set to high (1) (i.e. is FFS_ATTRIB_LARGE_FILE) then
  # hence return structure with ExtendedSize field
  if structure_content.size > MAX_FFS_SIZE or structure_content.Attributes & 0x1:
    return EfiFfsFileHeader2()
  else:
    return EfiFfsFileHeader()


class SectionHelper(utils.StructureHelper):
  """Helper Class created to hold methods which are used for
  every section having CommonHeader
  """
  def get_section_size(self):
    return getattr(self, "CommonHeader").get_section_size()

  @property
  def section_type(self):
    if hasattr(self, "CommonHeader"):
      return getattr(self, "CommonHeader").Type
    elif hasattr(self, "Type"):
      return self.Type
    else:
      return 0x00

  def dump_dict(self):
    result = super(SectionHelper, self).dump_dict()
    section_tuple = FFS_SECTION_TYPE_MAP.get(self.section_type)
    if section_tuple:
      result["SectionType"] = section_tuple.name
      result["Description"] = section_tuple.description
      result["FileNameString"] = ""
    return result


class EfiCommonSectionHeader(utils.StructureHelper):
  """
  source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h

  Used for below structures too:
  EFI_PE32_SECTION                - contains PE32+ image
  EFI_PIC_SECTION                 - contains PIC image
  EFI_PEI_DEPEX_SECTION           - to determine dispatch order of PEIMs
  EFI_DXE_DEPEX_SECTION           - to determine dispatch order of DXEs
  EFI_PEI_TE_SECTION              - contains the position-independent-code image
  EFI_PEI_RAW_SECTION             - contains an array of zero or more bytes
  EFI_COMPATIBILITY16_SECTION     - contains an IA-32 16-bit executable image
  """
  _pack_ = 1
  _fields_ = [
    ("Size", ctypes.ARRAY(ctypes.c_uint8, 3)),  # size including header
    ("Type", EFI_SECTION_TYPE),
  ]

  def get_section_size(self):
    return int(self.array_to_int(self.Size), 16)

  @property
  def section_type(self):
    return self.Type


class EfiCommonSectionHeader2(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
  # For section whose size is equal or greater than 0x1000000 (greater than MAX_SECTION_SIZE 0xffffff)
  _pack_ = 1
  _fields_ = [
    ("Size", ctypes.ARRAY(ctypes.c_uint8, 3)),  # Size will be 0xffffff for EFI_COMMON_SECTION_HEADER2
    ("Type", EFI_SECTION_TYPE),
    ("ExtendedSize", ctypes.c_uint32),
  ]

  def get_section_size(self):
    return self.ExtendedSize

  @property
  def section_type(self):
    return self.Type


def efi_section_all(structure_content):
  class EfiCommonSection(SectionHelper):
    _fields_ = [
      ("CommonHeader", EfiCommonSectionHeader2 if structure_content.get_section_size() >= MAX_SECTION_SIZE else EfiCommonSectionHeader),
    ]

  return EfiCommonSection()


efi_section_raw = efi_section_smm_depex = efi_section_pei_depex = efi_section_firmware_volume_image = efi_section_compatibility16 = efi_section_dxe_depex = efi_section_te = efi_section_pic = efi_section_pe32 = efi_section_disposable = efi_section_all


def efi_compression_section(structure_content):
  class EfiCompressionSection(SectionHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
    _fields_ = [
      ("CommonHeader", EfiCommonSectionHeader2 if structure_content.get_section_size() >= MAX_SECTION_SIZE else EfiCommonSectionHeader),
      ("UncompressedLength", ctypes.c_uint32),  # size of data after decompression
      ("CompressionType", ctypes.c_uint8)  # compression algorithm
    ]

  return EfiCompressionSection()


def efi_free_form_sub_type_guid_section(structure_content):
  class EfiFreeFormSubTypeGuidSection(SectionHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
    _fields_ = [
      ("CommonHeader", EfiCommonSectionHeader2 if structure_content.get_section_size() >= MAX_SECTION_SIZE else EfiCommonSectionHeader),
      ("SubTypeGuid", utils.Guid),
    ]

    @property
    def get_guid(self):
      return self.SubTypeGuid

  return EfiFreeFormSubTypeGuidSection()


def efi_guid_defined_section(structure_content):
  class EfiGuidDefinedSection(SectionHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
    _fields_ = [
      ("CommonHeader", EfiCommonSectionHeader2 if structure_content.get_section_size() >= MAX_SECTION_SIZE else EfiCommonSectionHeader),
      ("SectionDefinitionGuid", utils.Guid),
      ("DataOffset", ctypes.c_uint16),
      ("Attributes", ctypes.c_uint16)  # 0x01 or 0x02
      # GuidSpecificHeaderFields - Zero or more bytes of data that are defined by the section’s GUID. An example of this
      # data would be a digital signature and manifest.
      # contains an identifying GUID, followed by an arbitrary amount of data.
      # It is an encapsulation section in which the method of encapsulation is defined by the GUID
    ]

    @property
    def get_guid(self):
      return self.SectionDefinitionGuid

  return EfiGuidDefinedSection()


class PrePiExtractGuidedSectionData(utils.StructureHelper):
  # source: Edk2/EmbeddedPkg/Library/PrePiExtractGuidedSectionLib/PrePiExtractGuidedSectionLib.c
  # PRE_PI_EXTRACT_GUIDED_SECTION_DATA
  _fields_ = [
    ("NumberOfExtractHandler", ctypes.c_uint32),
    ("ExtractHandlerGuidTable", utils.Guid),
    ("ExtractDecodeHandlerTable", utils.Guid),  # EXTRACT_GUIDED_SECTION_DECODE_HANDLER
    ("ExtractGetInfoHandlerTable", utils.Guid),  # EXTRACT_GUIDED_SECTION_GET_INFO_HANDLER
  ]


class SignedSectionBufferSize(utils.StructureHelper):
  _fields_ = [
    ("BufferSize", ctypes.c_uint32),
  ]

  def get_section_size(self):
    return self.BufferSize


def efi_user_interface_section(structure_content):
  class EfiUserInterfaceSection(SectionHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
    _fields_ = [
      ("CommonHeader", EfiCommonSectionHeader2 if structure_content.get_section_size() >= MAX_SECTION_SIZE else EfiCommonSectionHeader),
      ("FileNameString", ctypes.ARRAY(CHAR16, (structure_content.get_section_size() - structure_content.cls_size)//2))
    ]

    def dump_dict(self):
      result = super(EfiUserInterfaceSection, self).dump_dict()
      result["FileNameString"] = self.parse_name()
      return result

    def parse_name(self):
      val = ""
      for i in self.FileNameString[:]:
        if i == 0:
          break
        else:
          val += chr(i)
      return val

  return EfiUserInterfaceSection()


def efi_version_section(structure_content):
  class EfiVersionSection(SectionHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareFile.h
    _fields_ = [
      ("CommonHeader", EfiCommonSectionHeader2 if structure_content.get_section_size() >= MAX_SECTION_SIZE else EfiCommonSectionHeader),
      ("BuildNumber", ctypes.c_uint16),
      ("VersionString", ctypes.ARRAY(CHAR16, 1))
    ]

  return EfiVersionSection()


class EfiFvBlockMapEntry(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("NumBlocks", ctypes.c_uint32),
    ("Length", ctypes.c_uint32)
  ]


class EfiFirmwareVolumeHeader(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("ZeroVector", ctypes.ARRAY(ctypes.c_uint8, 16)),
    ("FileSystemGuid", utils.Guid),  # EFI_GUID
    ("FvLength", ctypes.c_uint64),
    ("Signature", ctypes.ARRAY(ctypes.c_char, 4)),  # actually it's a signature of 4 characters... (UINT32 Signature)
    ("Attributes", EFI_FVB_ATTRIBUTES_2),  # UINT32 EFI_FVB_ATTRIBUTES_2
    ("HeaderLength", ctypes.c_uint16),
    ("Checksum", ctypes.c_uint16),
    ("ExtHeaderOffset", ctypes.c_uint16),
    ("Reserved", ctypes.ARRAY(ctypes.c_uint8, 1)),
    ("Revision", ctypes.c_uint8),
    ("BlockMap", ctypes.ARRAY(EfiFvBlockMapEntry, 1))  # EFI_FV_BLOCK_MAP_ENTRY
  ]

  @property
  def get_guid(self):
    return self.FileSystemGuid

  def dump_dict(self):
    result = super(EfiFirmwareVolumeHeader, self).dump_dict()
    result.pop("BlockMap")
    result.pop("Checksum")
    return result

def Refine_EfiFirmwareVolumeHeader(nums):
  class EfiFirmwareVolumeHeader(utils.StructureHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
    _fields_ = [
      ("ZeroVector", ctypes.ARRAY(ctypes.c_uint8, 16)),
      ("FileSystemGuid", utils.Guid),  # EFI_GUID
      ("FvLength", ctypes.c_uint64),
      ("Signature", ctypes.ARRAY(ctypes.c_char, 4)),  # actually it's a signature of 4 characters... (UINT32 Signature)
      ("Attributes", EFI_FVB_ATTRIBUTES_2),  # UINT32 EFI_FVB_ATTRIBUTES_2
      ("HeaderLength", ctypes.c_uint16),
      ("Checksum", ctypes.c_uint16),
      ("ExtHeaderOffset", ctypes.c_uint16),
      ("Reserved", ctypes.ARRAY(ctypes.c_uint8, 1)),
      ("Revision", ctypes.c_uint8),
      ("BlockMap", ctypes.ARRAY(EfiFvBlockMapEntry, nums))  # EFI_FV_BLOCK_MAP_ENTRY
    ]

    @property
    def get_guid(self):
      return self.FileSystemGuid

    def dump_dict(self):
      result = super(EfiFirmwareVolumeHeader, self).dump_dict()
      result.pop("BlockMap")
      result.pop("Checksum")
      return result
  return EfiFirmwareVolumeHeader

class EfiFirmwareVolumeExtHeader(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("FvName", utils.Guid),
    ("ExtHeaderSize", ctypes.c_uint32)
  ]

  @property
  def get_guid(self):
    return self.FvName


class EfiFirmwareVolumeExtEntry(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("ExtEntrySize", ctypes.c_uint16),
    ("ExtEntryType", ctypes.c_uint16)
  ]


class EfiFirmwareVolumeExtEntryOemType(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("Hdr", EfiFirmwareVolumeExtEntry),
    ("TypeMask", ctypes.c_uint32)
  ]

def Refine_FV_EXT_ENTRY_OEM_TYPE_Header(nums: int):
  class EfiFirmwareVolumeExtEntryOemType(utils.StructureHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
    _fields_ = [
      ("Hdr", EfiFirmwareVolumeExtEntry),
      ("TypeMask", ctypes.c_uint32),
      ('Types',    ctypes.ARRAY(utils.Guid, nums))
      ]
  return EfiFirmwareVolumeExtEntryOemType()

class EfiFirmwareVolumeExtEntryGuidType(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("Hdr", EfiFirmwareVolumeExtEntry),
    ("FormatType", utils.Guid)
  ]

  @property
  def get_guid(self):
    return self.FormatType

def Refine_FV_EXT_ENTRY_GUID_TYPE_Header(nums: int):
  class EfiFirmwareVolumeExtEntryGuidType(utils.StructureHelper):
    # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
    _fields_ = [
      ("Hdr", EfiFirmwareVolumeExtEntry),
      ("FormatType", utils.Guid),
      ('Data',       ctypes.ARRAY(ctypes.c_uint8, nums))
    ]
    @property

    def get_guid(self):
      return self.FormatType

  return EfiFirmwareVolumeExtEntryGuidType()

class EfiFirmwareVolumeExtEntryUsedSizeType(utils.StructureHelper):
  # source: Edk2/BaseTools/Source/C/Include/Common/PiFirmwareVolume.h
  _fields_ = [
    ("Hdr", EfiFirmwareVolumeExtEntry),
    ("UsedSize", ctypes.c_uint32)
  ]


class EfiCertRsa2048Sha256(utils.StructureHelper):  # 528 bytes
  # source: Edk2/MdePkg/Include/Guid/WinCertificate.h
  _fields_ = [
    ("HashType", utils.Guid),  # 16 bytes
    ("PublicKey", ctypes.ARRAY(ctypes.c_uint8, 256)),  # 256 bytes
    ("Signature", ctypes.ARRAY(ctypes.c_uint8, 256))  # 256 bytes
  ]

  @property
  def get_guid(self):
    return self.HashType


class WinCertificate(utils.StructureHelper):  # 8 bytes
  # source: Edk2/MdePkg/Include/Uefi/UefiMultiPhase.h
  _fields_ = [
    ("dwLength", ctypes.c_uint32),
    ("wRevision", ctypes.c_uint16),
    ("wCertificateType", ctypes.c_uint16),
    # //UINT8 bCertificate[ANYSIZE_ARRAY];
  ]

  def get_section_size(self):
    return self.dwLength


# def win_certificate_efi_pkcs(structure_content):
class WinCertificateEfiPkcs115(utils.StructureHelper):  # 152 bytes
  # source: Edk2/MdePkg/Include/Uefi/UefiMultiPhase.h > WIN_CERTIFICATE_EFI_PKCS1_15
  _fields_ = [
    ("Hdr", WinCertificate),  # 8 bytes
    ("HashAlgorithm", utils.Guid),  # 16 bytes
    # ("Signature", ctypes.ARRAY(ctypes.c_uint8, 128))  # 128 bytes
  ]

  @property
  def get_guid(self):
    return self.HashAlgorithm

  def get_section_size(self):
    return self.Hdr.get_section_size()


class WinCertificateUefiGuid(utils.StructureHelper):  # 25 bytes
  # source: Edk2/MdePkg/Include/Uefi/UefiMultiPhase.h
  _fields_ = [
    ("Hdr", WinCertificate),  # 8 bytes
    ("CertType", utils.Guid),  # 16 bytes
    ("CertData", ctypes.ARRAY(ctypes.c_uint8, 1))  # 1 byte
  ]

  @property
  def get_guid(self):
    return self.CertType


class EfiVariableAuthentication(utils.StructureHelper):
  # source: Edk2/MdePkg/Include/Uefi/UefiMultiPhase.h
  _fields_ = [
    ("MonotonicCount", ctypes.c_uint64),  # 8 bytes
    ("AuthInfo", WinCertificateUefiGuid)  # 25 bytes
  ]


class EfiVariableAuthentication2(utils.StructureHelper):  # 41 bytes
  # source: Edk2/MdePkg/Include/Uefi/UefiMultiPhase.h
  _fields_ = [
    ("TimeStamp", EfiTime),  # 16 bytes
    ("AuthInfo", WinCertificateUefiGuid)  # 25 bytes
  ]


###############################################################################
# IFWI Descriptor Region Structures
###############################################################################

class IfwiDescriptorRegion(utils.StructureHelper):
  """Structure to read IFWI descriptor region
  lying at offset 0x0 to 0x0FFF

  References:
    - https://sites.google.com/site/uefiforth/bios/uefi/platform-initialization-pi-specification/volume-3-shared-architectural-elements/2-firmware-storage-design-discussion/2-1-firmware-storage-introduction/2-1-1-firmware-devices/2-1-1-1-flash/spi-flash/spi-programming-guide/02-pch-spi-flash-architecture/2-3-flash-regions
    - https://opensecuritytraining.info/IntroBIOS_files/Day2_02_Advanced%20x86%20-%20BIOS%20and%20SMM%20Internals%20-%20Flash%20Descriptor.pdf
    - https://github-wiki-see.page/m/ISpillMyDrink/UEFI-Repair-Guide/wiki/Flash-Layout

  other IFWI size is yet to be tested out!
  """
  _fields_ = [
    ("Unknown", ctypes.ARRAY(ctypes.c_uint8, 16)),  # raw bytes
    ("FLVALSIG", ctypes.c_uint32),  # Flash Valid Signature - 0x0ff0a55a [5A A5 F0 0F]
    ("FLMAP0", ctypes.ARRAY(ctypes.c_uint8, 4)),  # Flash Map 0 - 4 bytes (@ 0x14)
    ("FLMAP1", ctypes.ARRAY(ctypes.c_uint8, 4)),  # Flash Map 1 - 4 bytes (@ 0x18)
    ("FLMAP2", ctypes.ARRAY(ctypes.c_uint8, 4)),  # Flash Map 2 - 4 bytes (@ 0x1C)
    ("Unknown", ctypes.ARRAY(ctypes.c_uint8, 16)),  # raw bytes
    ("FCBA", ctypes.ARRAY(ctypes.c_uint8, 16)),  # Flash Component Base Address - 16 bytes (@ 0x30)
    ("FRBA", ctypes.ARRAY(ctypes.c_uint8, 40)),  # Flash Region Base Address - 40 bytes - (@ 0x40)
  ]

  @property
  def bios_address(self):
    # Method not supported
    return 0x0

  @property
  def bios_end_address(self):
    # Method not supported
    return 0x0


if not DescriptorRegion:
  DescriptorRegion = IfwiDescriptorRegion


class FitEntry(utils.StructureHelper):
  """Structure for FIT Entry  information
  Below is reference link for structure:
  https://www.intel.com/content/dam/develop/external/us/en/documents/firmware-interface-table-bios-specification-r1p2p1.pdf
  """

  FIT_OFFSET = -0x40  # FIT Pointer Location
  FIT_SIGNATURE = b'_FIT_   '

  _fields_ = [
    ('Address', ctypes.c_uint64),  # 8 bytes
    ('Size', ctypes.c_uint32),  # Bits[31:24] Reserved
    ('Version', ctypes.c_uint16),  # 2 bytes
    ('Type', ctypes.c_uint8),  # Bit[7] = C_V
    ('Checksum', ctypes.c_uint8),  # 1 byte
  ]


###############################################################################
# EFI Variable Structure
###############################################################################
def efi_variable_structure(name_length=0, data_length=0):
  """Structure for EFI Variable stored in NVRAM region

  REF: edk2/BaseTools/Source/C/Include/Protocol/HiiFramework.h

  :param name_length: Length data bytes for efi variable name
  :param data_length: data size of the given variable
  :return:
  """
  class EfiVariableStructure(utils.StructureHelper):
    _pack_ = 1
    _fields_ = [
      # read bits
      ("unknown", ctypes.ARRAY(ctypes.c_uint8, 0x21)),  # Unknown size between two structures
      ## Offset -- 0x47
      ("State", ctypes.c_uint8),         #--> 00
      ("Attribute", ctypes.c_uint32),    #--> 00 00 00 00
      ("name_length", ctypes.c_uint32),  #--> 00 00 00 0C
      ("data_length", ctypes.c_uint32),  #--> 00 00 10 56
      ("guid", utils.Guid),  # 16 Bytes
      ("name", ctypes.ARRAY(ctypes.c_uint8, name_length)),  # 12 Bytes
      ("data", ctypes.ARRAY(ctypes.c_uint8, data_length)), # 4182 Byes
    ]

    @property
    def get_name(self):
      return ''.join([chr(i) for i in self.name]).replace("\x00", "")

    def get_value(self, name):
      if name == "name":
        return self.get_name
      else:
        return super().get_value(name)

  return EfiVariableStructure()


# END:STRUCTURES #######################################################################################################


# BEGIN:MAPPING ########################################################################################################
########################################################################################################################

FfsFileAttributes = namedtuple("FfsFileAttributes", ["value", "name", "method", "description"])

FFS_ATTRIB_MAP = {
  0x01: FfsFileAttributes(0x01, "FFS_ATTRIB_LARGE_FILE", EfiFfsFileHeader2,  "Indicates that large files are supported and the EFI_FFS_FILE_HEADER2 is in use"),
  0x04: FfsFileAttributes(0x04, "FFS_ATTRIB_FIXED", EfiFfsFileHeader, "Indicates that the file may not be moved from its present location"),
  0x38: FfsFileAttributes(0x38, "FFS_ATTRIB_DATA_ALIGNMENT", EfiFfsFileHeader, "Indicates that the beginning of the file data (not the file header) must be aligned on a particular boundary relative to the firmware volume base"),
  0x40: FfsFileAttributes(0x40, "FFS_ATTRIB_CHECKSUM", EfiFfsFileHeader, "Determines the interpretation of IntegrityCheck.Checksum.File. See the IntegrityCheck definition above for specific usage."),
}


FileType = namedtuple("FileType", ["value", "name", "description"])

FFS_FILE_TYPE_MAP = {
  0x00: FileType(0x00, "FV_FILETYPE_ALL", "NA"),
  0x01: FileType(0x01, "FV_FILETYPE_RAW", "Binary Data"),
  0x02: FileType(0x02, "FV_FILETYPE_FREEFORM", "Sectioned Data"),
  0x03: FileType(0x03, "FV_FILETYPE_SECURITY_CORE", "Platform core code used during the SEC phase"),
  0x04: FileType(0x04, "FV_FILETYPE_PEI_CORE", "PEI Foundation"),
  0x05: FileType(0x05, "FV_FILETYPE_DXE_CORE", "DXE Foundation"),
  0x06: FileType(0x06, "FV_FILETYPE_PEIM", "PEI Module (PEIM)"),
  0x07: FileType(0x07, "FV_FILETYPE_DRIVER", "DXE Driver"),
  0x08: FileType(0x08, "FV_FILETYPE_COMBINED_PEIM_DRIVER", "Combined PEIM/DXE Driver"),
  0x09: FileType(0x09, "FV_FILETYPE_APPLICATION", "Application"),  # loaded using the UEFI Boot Service LoadImage()
  0x0A: FileType(0x0A, "FV_FILETYPE_SMM", "Contains a PE32+ image that will be loaded into MMRAM in MM Traditional Mode"),
  0x0B: FileType(0x0B, "FV_FILETYPE_FIRMWARE_VOLUME_IMAGE", "Firmware Volume Image"),
  # Enables sharing code between PEI and DXE to reduce firmware storage requirements
  0x0C: FileType(0x0C, "FV_FILETYPE_COMBINED_SMM_DXE", "Contains PE32+ image that will be dispatched by the DXE Dispatcher and will also be loaded into MMRAM in MM Tradition Mode"),
  0x0D: FileType(0x0D, "FV_FILETYPE_SMM_CORE", "MM Foundation that support MM Traditional Mode"),
  0x0E: FileType(0x0E, "EFI_FV_FILETYPE_MM_STANDALONE", "Contains PE32+ image that will be loaded into MMRAM in MM Standalone Mode"),
  0x0F: FileType(0x0F, "EFI_FV_FILETYPE_MM_CORE_STANDALONE", "Contains PE32+ image that support MM Tradition Mode and MM Standalone Mode"),
  0xC0: FileType(0xC0, "FV_FILETYPE_OEM_MIN", "OEM File Type"),  # 0xC0 to 0xDF
  0xDF: FileType(0xDF, "FV_FILETYPE_OEM_MAX", "OEM File Type"),
  0xE0: FileType(0xE0, "FV_FILETYPE_DEBUG_MIN", "Debug/Test File Type"),  # 0xE0 to 0xEF
  0xEF: FileType(0xEF, "FV_FILETYPE_DEBUG_MAX", "Debug/Test File Type"),
  0xF1: FileType(0XF0, "FV_FILETYPE_FFS_MIN", "Firmware File System Specific File Type"),  # 0xF0 to 0xFF
  0xFF: FileType(0XFF, "FV_FILETYPE_FFS_MAX", "Firmware File System Specific File Type"),
  0xF0: FileType(0xF0, "FV_FILETYPE_FFS_PAD", "Pad file for FFS")
}

SignedSectionGuids = namedtuple("SignedSectionGuids", ["name", "guid", "method"])

SIGNED_SECTION_GUIDS = {
  "0f9d89e8-9259-4f76-a5af0c89e34023df": SignedSectionGuids("EFI_FIRMWARE_CONTENTS_SIGNED_GUID", [0x0f9d89e8, 0x9259, 0x4f76, 0xa5, 0xaf, 0xc, 0x89, 0xe3, 0x40, 0x23, 0xdf], process_efi_firmware_contents_signed_guid),
  "a7717414-c616-4977-9420844712a735bf": SignedSectionGuids("EFI_CERT_TYPE_RSA2048_SHA256_GUID", [0xa7717414, 0xc616, 0x4977, 0x94, 0x20, 0x84, 0x47, 0x12, 0xa7, 0x35, 0xbf], process_efi_cert_type_rsa2048_sha256_guid),
  "4aafd29d-68df-49ee-8aa9347d375665a7": SignedSectionGuids("EFI_CERT_TYPE_PKCS7_GUID", [0x4aafd29d, 0x68df, 0x49ee, 0x8a, 0xa9, 0x34, 0x7d, 0x37, 0x56, 0x65, 0xa7], SignedSectionBufferSize),
  "ee4e5898-3914-4259-9d6edc7bd79403cf": SignedSectionGuids("LZMA_CUSTOM_DECOMPRESS_GUID", [0xEE4E5898, 0x3914, 0x4259, 0x9D, 0x6E, 0xDC, 0x7B, 0xD7, 0x94, 0x03, 0xCF], process_decompress_guid),
  "3d532050-5cda-4fd0-879e0f7f630d5afb": SignedSectionGuids("BROTLI_CUSTOM_DECOMPRESS_GUID", [0x3D532050, 0x5CDA, 0x4FD0, 0x87, 0x9E, 0x0F, 0x7F, 0x63, 0x0D, 0x5A, 0xFB], process_decompress_guid),
}


FileSectionType = namedtuple("FileSectionType", ["value", "name", "structure", "is_encapsulated", "description"])

FFS_SECTION_TYPE_MAP = {
  # The section type EFI_SECTION_ALL is a pseudo type. It is used as a wild card when retrieving sections. The section type EFI_SECTION_ALL matches all section types.
  0x00: FileSectionType(0x00, "EFI_SECTION_ALL", efi_section_all, False, ""),
  # Encapsulation section Type values
  0x01: FileSectionType(0x01, "EFI_SECTION_COMPRESSION", efi_compression_section, True, "Encapsulation section where other sections are compressed"),
  0x02: FileSectionType(0x02, "EFI_SECTION_GUID_DEFINED", efi_guid_defined_section, True, "Encapsulation section used during the build process but not required for execution"),
  0x03: FileSectionType(0x03, "EFI_SECTION_DISPOSABLE", efi_section_disposable, True, "Encapsulation section used during the build process but not required for execution"),
  # Leaf section Type values
  0x10: FileSectionType(0x10, "EFI_SECTION_PE32", efi_section_pe32, False, "PE32+ Executable image"),
  0x11: FileSectionType(0x11, "EFI_SECTION_PIC", efi_section_pic, False, "Position-Independent Code"),
  0x12: FileSectionType(0x12, "EFI_SECTION_TE", efi_section_te, False, "Terse Executable Image"),
  0x13: FileSectionType(0x13, "EFI_SECTION_DXE_DEPEX", efi_section_dxe_depex, False, "DXE Dependency Expression"),
  0x14: FileSectionType(0x14, "EFI_SECTION_VERSION", efi_version_section, False, "Version, Text and numeric"),
  0x15: FileSectionType(0x15, "EFI_SECTION_USER_INTERFACE", efi_user_interface_section, False, "User-Friendly name of the driver"),
  0x16: FileSectionType(0x16, "EFI_SECTION_COMPATIBILITY16", efi_section_compatibility16, False, "DOS-style 16-bit EXE"),
  0x17: FileSectionType(0x17, "EFI_SECTION_FIRMWARE_VOLUME_IMAGE", efi_section_firmware_volume_image, False, "PI Firmware Volume Image"),
  0x18: FileSectionType(0x18, "EFI_SECTION_FREEFORM_SUBTYPE_GUID", efi_free_form_sub_type_guid_section, False, "Raw data with GUID in header to define format"),
  0x19: FileSectionType(0x19, "EFI_SECTION_RAW", efi_section_raw, False, "Raw data"),
  0x1B: FileSectionType(0x1B, "EFI_SECTION_PEI_DEPEX", efi_section_pei_depex, False, "PEI Dependency Expression"),
  0x1C: FileSectionType(0x1C, "EFI_SECTION_SMM_DEPEX", efi_section_smm_depex, False, "Leaf section type for determining the dispatch order for an MM Traditional driver in MM Traditional Mode or MM Standaline driver in MM Standalone Mode."),
}


FILE_SYSTEM_GUID_MAP = {
  "7a9354d9-0468-444a-81ce0bf617d890df": 1,
  "8c8ce578-8a3d-4f1c-9935896185c32dd3": 2,
  "5473c07a-3dcb-4dca-bd6f1e9689e7349a": 3
}

COMPRESSION_TYPE_MAP = {
  0x00: "EFI_NOT_COMPRESSED",
  0x01: "EFI_STANDARD_COMPRESSION"
}


def guid_section_header_attrib_bits(attrib):
  if attrib & 0x01:
    # processing required to obtain meaningful data from section content
    return "EFI_GUIDED_SECTION_PROCESSING_REQUIRED"
  elif attrib & 0x02:
    # section contains authentication data
    return "EFI_GUIDED_SECTION_AUTH_STATUS_VALID"

# END:MAPPING ##########################################################################################################


if __name__ == "__main__":
  pass
