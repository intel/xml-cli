#!/usr/bin/env python
__author__ = ['ashinde', "Gahan Saraiya"]

# Built-in Imports
import os
import sys
import time
import glob
import copy

# Custom Imports
from . import XmlCliLib as clb
from . import XmlIniParser as prs
from .common import utils
from .common import compress
from .common import configurations
from .common.logger import log


global LogEnabled, FileGuidListDict, FileSystemSaveCount, FwIngredientDict, HiiNvarDict

FwIngredientDict = {}
FwIngredientDict['FlashDescpValid'] = 0
FwIngredientDict['FitTablePtr'] = 0
FwIngredientDict['FlashRegions'] = {}
FwIngredientDict['PCH_STRAPS'] = {}
FwIngredientDict['ME'] = {}
FwIngredientDict['FIT'] = {}
FwIngredientDict['ACM'] = {}
FwIngredientDict['Ucode'] = {}
FwpLogEn = True
FwpPrintEn = False
FileGuidListDict = {}
FileSystemSaveCount = 0
Parse_Print_Uqi = False
PlatInfoMenuDone = False
ForceOutFile = False
MulSetupDrivers = False
SecureProfileEditing = False
ReSigningFile = ''

EFI_GUID_DEFINED_SECTION_HDR_SIZE = 0x18
FFS_FILE_HEADER_SIZE              = 0x18
FFS_FILE_HEADER2_SIZE             = 0x20
FFS_ATTRIB_LARGE_FILE             = 0x01
EFI_COMMON_SECTION_HEADER_SIZE    = 0x04
FV_FILETYPE_FIRMWARE_VOLUME_IMAGE = 0x0B
EFI_FV_HEADER_SIZE                = 0x48
EFI_SECTION_GUID_DEFINED          = 0x02
EFI_SECTION_FIRMWARE_VOLUME_IMAGE = 0x17

# FFS File Attributes.
FFS_ATTRIB_FIXED                  = 0x04
FFS_ATTRIB_DATA_ALIGNMENT         = 0x38
FFS_ATTRIB_CHECKSUM               = 0x40

# FFS_FIXED_CHECKSUM is the checksum value used when the FFS_ATTRIB_CHECKSUM attribute bit is clear
FFS_FIXED_CHECKSUM                = 0xAA

EFI_IFR_FORM_SET_OP               = 0x0E
EFI_IFR_FORM_OP                   = 0x01
EFI_IFR_SUBTITLE_OP               = 0x02
EFI_IFR_TEXT_OP                   = 0x03
EFI_IFR_SUPPRESS_IF_OP            = 0x0A
EFI_IFR_GRAY_OUT_IF_OP            = 0x19
EFI_IFR_REF_OP                    = 0x0F
EFI_IFR_VARSTORE_OP               = 0x24
EFI_IFR_VARSTORE_EFI_OP           = 0x26
EFI_IFR_ONE_OF_OP                 = 0x05
EFI_IFR_CHECKBOX_OP               = 0x06
EFI_IFR_NUMERIC_OP                = 0x07
EFI_IFR_ONE_OF_OPTION_OP          = 0x09
EFI_IFR_STRING_OP                 = 0x1C
EFI_HII_PACKAGE_FORMS             = 0x02
EFI_HII_PACKAGE_STRINGS           = 0x04
EFI_IFR_NUMERIC_SIZE              = 0x03
EFI_IFR_END_OP                    = 0x29
EFI_IFR_TRUE_OP                   = 0x46
EFI_IFR_DEFAULT_OP                = 0x5B
EFI_IFR_GUID_OP                   = 0x5F

EFI_HII_SIBT_END                  = 0x00
EFI_HII_SIBT_STRING_SCSU          = 0x10
EFI_HII_SIBT_STRING_SCSU_FONT     = 0x11
EFI_HII_SIBT_STRINGS_SCSU         = 0x12
EFI_HII_SIBT_STRINGS_SCSU_FONT    = 0x13
EFI_HII_SIBT_STRING_UCS2          = 0x14
EFI_HII_SIBT_STRING_UCS2_FONT     = 0x15
EFI_HII_SIBT_STRINGS_UCS2         = 0x16
EFI_HII_SIBT_STRINGS_UCS2_FONT    = 0x17
EFI_HII_SIBT_DUPLICATE            = 0x20
EFI_HII_SIBT_SKIP2                = 0x21
EFI_HII_SIBT_SKIP1                = 0x22
EFI_HII_SIBT_EXT1                 = 0x30
EFI_HII_SIBT_EXT2                 = 0x31
EFI_HII_SIBT_EXT4                 = 0x32
EFI_HII_SIBT_FONT                 = 0x40

EFI_IFR_TYPE_NUM_SIZE_8           = 0x00
EFI_IFR_TYPE_NUM_SIZE_16          = 0x01
EFI_IFR_TYPE_NUM_SIZE_32          = 0x02
EFI_IFR_TYPE_NUM_SIZE_64          = 0x03
EFI_IFR_TYPE_BOOLEAN              = 0x04

EFI_IFR_OPTION_DEFAULT            = 0x10
EFI_IFR_OPTION_DEFAULT_MFG        = 0x20

Descriptor_Region                 = 0
BIOS_Region                       = 1
ME_Region                         = 2
GBE_Region                        = 3
PDR_Region                        = 4
Device_Expan_Region               = 5
Sec_BIOS_Region                   = 6
SpiRegionMax                      = 7
EC_Region                         = 8
Padding_Region                    = 9
SpiRegionAll                      = 0xFE
Invalid_Region                    = 0xFF
FlashRegionDict                   = {Descriptor_Region: 'Descriptor', BIOS_Region: 'BIOS', ME_Region: 'ME', GBE_Region: 'GBE', PDR_Region: 'PDR', Device_Expan_Region: 'Device Expansion', Sec_BIOS_Region: 'Secondary BIOS', SpiRegionMax: 'SpiRegionMax', EC_Region: 'EC', Padding_Region: 'Padding'}

gEfiFirmwareFileSystemGuid        = [ 0x7A9354D9, 0x0468, 0x444a, 0x81, 0xCE, 0x0B, 0xF6, 0x17, 0xD8, 0x90, 0xDF ]
gEfiFirmwareFileSystem2Guid       = [ 0x8c8ce578, 0x8a3d, 0x4f1c, 0x99, 0x35, 0x89, 0x61, 0x85, 0xc3, 0x2d, 0xd3 ]
gEfiFirmwareFileSystem3Guid       = [ 0x5473c07a, 0x3dcb, 0x4dca, 0xbd, 0x6f, 0x1e, 0x96, 0x89, 0xe7, 0x34, 0x9a ]

gEfiGlobalVariableGuid            = [ 0x8BE4DF61, 0x93CA, 0x11D2, 0xAA, 0x0D, 0x00, 0xE0, 0x98, 0x03, 0x2B, 0x8C ]
gEfiVariableGuid                  = [ 0xddcf3616, 0x3275, 0x4164, 0x98, 0xb6, 0xfe, 0x85, 0x70, 0x7f, 0xfe, 0x7d ]
gEfiIfrTianoGuid                  = [ 0x0f0b1735, 0x87a0, 0x4193, 0xb2, 0x66, 0x53, 0x8c, 0x38, 0xaf, 0x48, 0xce ]
gEdkiiIfrBitVarstoreGuid          = [ 0x82DDD68B, 0x9163, 0x4187, 0x9B, 0x27, 0x20, 0xA8, 0xFD, 0x60, 0xA7, 0x1D ]
gEfiAuthenticatedVariableGuid     = [ 0xaaf32c78, 0x947b, 0x439a, 0xa1, 0x80, 0x2e, 0x14, 0x4e, 0xc3, 0x77, 0x92 ]
gTianoCustomDecompressGuid        = [ 0xA31280AD, 0x481E, 0x41B6, 0x95, 0xE8, 0x12, 0x7F, 0x4C, 0x98, 0x47, 0x79 ]
gLzmaCustomDecompressGuid         = [ 0xEE4E5898, 0x3914, 0x4259, 0x9D, 0x6E, 0xDC, 0x7B, 0xD7, 0x94, 0x03, 0xCF ]
gBrotliCustomDecompressGuid       = [ 0x3D532050, 0x5CDA, 0x4FD0, 0x87, 0x9E, 0x0F, 0x7F, 0x63, 0x0D, 0x5A, 0xFB ]
gNvRamFvGuid                      = [ 0xFFF12B8D, 0x7696, 0x4c8b, 0xa9, 0x85, 0x27, 0x47, 0x07, 0x5b, 0x4f, 0x50 ]
gEfiFirmwareContentsSignedGuid    = [ 0x0f9d89e8, 0x9259, 0x4f76, 0xa5, 0xaf, 0xc,  0x89, 0xe3, 0x40, 0x23, 0xdf ]
gEfiCertTypeRsa2048Sha256Guid     = [ 0xa7717414, 0xc616, 0x4977, 0x94, 0x20, 0x84, 0x47, 0x12, 0xa7, 0x35, 0xbf ]
gEfiHashAlgorithmSha256Guid       = [ 0x51AA59DE, 0xFDF2, 0x4EA3, 0xBC, 0x63, 0x87, 0x5F, 0xB7, 0x84, 0x2E, 0xE9 ]

gBiosCapsuleGuid                  = [ 0xda4b2d79, 0xfee1, 0x42c6, 0x9b, 0x56, 0x92, 0x36, 0x33, 0x39, 0x8a, 0xeb ]

gBiosKnobsDataBinGuid             = [ 0x615E6021, 0x603D, 0x4124, 0xB7, 0xEA, 0xC4, 0x8A, 0x37, 0x37, 0xBA, 0xCD ]
gBiosKnobsCpxDataBinGuid          = [ 0x731DAA2A, 0x9259, 0x4729, 0xA1, 0xB5, 0xF7, 0x72, 0x09, 0xEB, 0xF5, 0x4D ]
# Legacy protocol guid
gXmlCliProtocolGuid               = [ 0xe3e49b8d, 0x1987, 0x48d0, 0x9a, 0x1,  0xed, 0xa1, 0x79, 0xca, 0xb,  0xd6 ]
# Core-5.0.0 onwards protocol guid
gXmlCliInterfaceBufferGuid        = [0xa8cbbbea, 0xf37c, 0x4da4, 0x5e, 0x81, 0x68, 0x4f, 0x6f, 0xc5, 0x12, 0x49]

gXmlCliSetupDriverGuid            = [0xDFB9BF4C, 0x3520, 0x4a80, 0x90, 0x4E, 0x71, 0xD5, 0xF4, 0x2E, 0x86, 0x6A]
gVtioDriverGuid                   = [0x03327D04, 0xC807, 0x4B76, 0x96, 0x5F, 0xB3, 0x00, 0x46, 0xF1, 0x53, 0x91]
gDxePlatformFfsGuid               = [ 0xABBCE13D, 0xE25A, 0x4d9f, 0xA1, 0xF9, 0x2F, 0x77, 0x10, 0x78, 0x68, 0x92 ]
gGnrDxePlatformFfsGuid            = [ 0xDE1E3282, 0xC8D6, 0x40AD, 0x95, 0x7E, 0xFB, 0xED, 0x9A, 0x49, 0x1F, 0x6D ]
gAdvancedPkgListGuid              = [ 0xc09c81cb, 0x31e9, 0x4de6, 0xa9, 0xf9, 0x17, 0xa1, 0x44, 0x35, 0x42, 0x45 ]

gSocketSetupDriverFfsGuid         = [ 0x6B6FD380, 0x2C55, 0x42C6, 0x98, 0xBF, 0xCB, 0xBC, 0x5A, 0x9A, 0xA6, 0x66 ]
gSocketPkgListGuid                = [ 0x5c0083db, 0x3f7d, 0x4b20, 0xac, 0x9b, 0x73, 0xfc, 0x65, 0x1b, 0x25, 0x03 ]

gSvSetupDriverFfsGuid             = [ 0x5498AB03, 0x63AE, 0x41A5, 0xB4, 0x90, 0x29, 0x94, 0xE2, 0xDA, 0xC6, 0x8D ]
gSvPkgListGuid                    = [ 0xaec3ff43, 0xa70f, 0x4e01, 0xa3, 0x4b, 0xee, 0x1d, 0x11, 0xaa, 0x21, 0x69 ]

gFpgaDriverFfsGuid                = [ 0xBCEA6548, 0xE204, 0x4486, 0x8F, 0x2A, 0x36, 0xE1, 0x3C, 0x78, 0x38, 0xCE ]
gFpgaPkgListGuid                  = [ 0x22819110, 0x7f6f, 0x4852, 0xb4, 0xbb, 0x13, 0xa7, 0x70, 0x14, 0x9b, 0x0c ]

gPcGenSetupDriverFfsGuid          = [ 0xCB105C8B, 0x3B1F, 0x4117, 0x99, 0x3B, 0x6D, 0x18, 0x93, 0x39, 0x37, 0x16 ]

gClientSetupFfsGuid               = [ 0xE6A7A1CE, 0x5881, 0x4b49, 0x80, 0xBE, 0x69, 0xC9, 0x18, 0x11, 0x68, 0x5C ]
gClientUiApp1FfsGuid              = [ 0xD89A7D8B, 0xD016, 0x4D26, 0x93, 0xE3, 0xEA, 0xB6, 0xB4, 0xD3, 0xB0, 0xA2 ]
gClientUiApp2FfsGuid              = [ 0x462CAA21, 0x7614, 0x4503, 0x83, 0x6E, 0x8A, 0xB6, 0xF4, 0x66, 0x23, 0x31 ]
gClientTestMenuSetupFfsGuid       = [ 0x21535212, 0x83d1, 0x4d4a, 0xae, 0x58, 0x12, 0xf8, 0x4d, 0x1f, 0x71, 0x0d ]
gDefaultDataOptSizeFileGuid       = [ 0x003e7b41, 0x98a2, 0x4be2, 0xb2, 0x7a, 0x6c, 0x30, 0xc7, 0x65, 0x52, 0x25 ]
gDefaultDataFileGuid              = [ 0x1ae42876, 0x008f, 0x4161, 0xb2, 0xb7, 0x1c, 0xd,  0x15, 0xc5, 0xef, 0x43 ]
gDefaultDataCpxFileGuid           = [ 0x9971614C, 0x8DD6, 0x4275, 0x85, 0x2f, 0xae, 0x7c, 0xbc, 0xd3, 0xad, 0x85 ]
gVpdGuid                          = [ 0xff7db236, 0xf856, 0x4924, 0x90, 0xf8, 0xcd, 0xf1, 0x2f, 0xb8, 0x75, 0xf3 ]

gEfiIfrAttractGuid                = [ 0xd0bc7cb4, 0x6a47, 0x495f, 0xaa, 0x11, 0x71, 0x7,  0x46, 0xda, 0x6,  0xa2 ]
gEfiUniStrAttractGuid             = [ 0x8913c5e0, 0x33f6, 0x4d86, 0x9b, 0xf1, 0x43, 0xef, 0x89, 0xfc, 0x6,  0x66 ]

gEfiSetupVariableGuid             = [ 0xec87d643, 0xeba4, 0x4bb5, 0xa1, 0xe5, 0x3f, 0x3e, 0x36, 0xb2, 0x0d, 0xa9 ]
gEfiBiosIdGuid                    = [ 0xC3E36D09, 0x8294, 0x4b97, 0xA8, 0x57, 0xD5, 0x28, 0x8F, 0xE3, 0x3E, 0x28 ]
gCpPcBiosIdFileGuid               = [ 0x372f8c51, 0xc43b, 0x472a, 0x82, 0xaf, 0x54, 0xb5, 0xc3, 0x23, 0x4d, 0x7f ]

gEmulationDriverFfsGuid           = [ 0x6BB0C4DE, 0xDCA4, 0x4f3e, 0xBC, 0xA8, 0x33, 0x06, 0x35, 0xDA, 0x4E, 0xF3 ]
gEmulatioPkgListGuid              = [ 0x52b3b56e, 0xe716, 0x455f, 0xa5, 0xe3, 0xb3, 0x14, 0xf1, 0x8e, 0x6c, 0x5d ]

gMerlinXAppGuid                   = [ 0xA3D1DDB4, 0xADB2, 0x4a08, 0xA0, 0x38, 0x73, 0x05, 0x67, 0x30, 0xE8, 0x53 ]

ZeroGuid                          = [ 0x00000000, 0x0000, 0x0000, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ]
AllFsGuid                         = [ 0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]
MICRO_CODE_FIRMWARE_GUIDS = [
  (0x4924F856197DB236, 0xF375B82FF1CDF890),
  (0x41fb3b4eb53105f3, 0x97e2f0648f101083),
  (0x475E8179A18F0468, 0x9691036FBD6F86A8),
  (0x43bcc0438c614c1d, 0x276cc2d608a0eb87),
  (0X4F31640B713D38AB, 0X3A2683073E03AB90),
  (0X4E93FE18908F49AD, 0X4A87C0FB74D6598C),
]

FFSfileTypesDict     = { 0x00 : 'FV_FILETYPE_ALL', 0x01 : 'FV_FILETYPE_RAW', 0x02 : 'FV_FILETYPE_FREEFORM', 0x03 : 'FV_FILETYPE_SECURITY_CORE', 0x04 : 'FV_FILETYPE_PEI_CORE', 0x05 : 'FV_FILETYPE_DXE_CORE', 0x06 : 'FV_FILETYPE_PEIM', 0x07 : 'FV_FILETYPE_DRIVER', 0x08 : 'FV_FILETYPE_COMBINED_PEIM_DRIVER', 0x09 : 'FV_FILETYPE_APPLICATION', 0x0A : 'FV_FILETYPE_SMM', 0x0B : 'FV_FILETYPE_FIRMWARE_VOLUME_IMAGE', 0x0C : 'FV_FILETYPE_COMBINED_SMM_DXE', 0x0D : 'FV_FILETYPE_SMM_CORE', 0xC0 : 'FV_FILETYPE_OEM_MIN', 0xDF : 'FV_FILETYPE_OEM_MAX', 0xE0 : 'FV_FILETYPE_DEBUG_MIN', 0xEF : 'FV_FILETYPE_DEBUG_MAX', 0xFF : 'FV_FILETYPE_FFS_MAX', 0xF0 : 'FV_FILETYPE_FFS_PAD' }
FFSsectionTypeDict   = { 0x00 : 'EFI_SECTION_ALL', 0x01 : 'EFI_SECTION_COMPRESSION', 0x02 : 'EFI_SECTION_GUID_DEFINED', 0x10 : 'EFI_SECTION_PE32', 0x11 : 'EFI_SECTION_PIC', 0x12 : 'EFI_SECTION_TE', 0x13 : 'EFI_SECTION_DXE_DEPEX', 0x14 : 'EFI_SECTION_VERSION', 0x15 : 'EFI_SECTION_USER_INTERFACE', 0x16 : 'EFI_SECTION_COMPATIBILITY16', 0x17 : 'EFI_SECTION_FIRMWARE_VOLUME_IMAGE', 0x18 : 'EFI_SECTION_FREEFORM_SUBTYPE_GUID', 0x19 : 'EFI_SECTION_RAW', 0x1B : 'EFI_SECTION_PEI_DEPEX', 0x1C : 'EFI_SECTION_SMM_DEPEX' }
GuidedSectAtrbDict   = { 0x01 : 'EFI_GUIDED_SECTION_PROCESSING_REQUIRED', 0x02 : 'EFI_GUIDED_SECTION_AUTH_STATUS_VALID' }
HiiPkgHdrTypeDict    = { 0x00 : 'EFI_HII_PACKAGE_TYPE_ALL', 0x01 : 'EFI_HII_PACKAGE_TYPE_GUID', 0x02 : 'EFI_HII_PACKAGE_FORMS', 0x04 : 'EFI_HII_PACKAGE_STRINGS', 0x05 : 'EFI_HII_PACKAGE_FONTS', 0x06 : 'EFI_HII_PACKAGE_IMAGES', 0x07 : 'EFI_HII_PACKAGE_SIMPLE_FONTS', 0x08 : 'EFI_HII_PACKAGE_DEVICE_PATH', 0x09 : 'EFI_HII_PACKAGE_KEYBOARD_LAYOUT', 0x0A : 'EFI_HII_PACKAGE_ANIMATIONS', 0xDF : 'EFI_HII_PACKAGE_END', 0xE0 : 'EFI_HII_PACKAGE_TYPE_SYSTEM_BEGIN', 0xFF : 'EFI_HII_PACKAGE_TYPE_SYSTEM_END' }
IfrOpcodesDict       = { 0x01 : 'EFI_IFR_FORM_OP', 0x02 : 'EFI_IFR_SUBTITLE_OP', 0x03 : 'EFI_IFR_TEXT_OP', 0x04 : 'EFI_IFR_IMAGE_OP', 0x05 : 'EFI_IFR_ONE_OF_OP', 0x06 : 'EFI_IFR_CHECKBOX_OP', 0x07 : 'EFI_IFR_NUMERIC_OP', 0x08 : 'EFI_IFR_PASSWORD_OP', 0x09 : 'EFI_IFR_ONE_OF_OPTION_OP', 0x0A : 'EFI_IFR_SUPPRESS_IF_OP', 0x0B : 'EFI_IFR_LOCKED_OP', 0x0C : 'EFI_IFR_ACTION_OP', 0x0D : 'EFI_IFR_RESET_BUTTON_OP', 0x0E : 'EFI_IFR_FORM_SET_OP', 0x0F : 'EFI_IFR_REF_OP', 0x10 : 'EFI_IFR_NO_SUBMIT_IF_OP', 0x11 : 'EFI_IFR_INCONSISTENT_IF_OP', 0x12 : 'EFI_IFR_EQ_ID_VAL_OP', 0x13 : 'EFI_IFR_EQ_ID_ID_OP', 0x14 : 'EFI_IFR_EQ_ID_VAL_LIST_OP', 0x15 : 'EFI_IFR_AND_OP', 0x16 : 'EFI_IFR_OR_OP', 0x17 : 'EFI_IFR_NOT_OP', 0x18 : 'EFI_IFR_RULE_OP', 0x19 : 'EFI_IFR_GRAY_OUT_IF_OP', 0x1A : 'EFI_IFR_DATE_OP', 0x1B : 'EFI_IFR_TIME_OP', 0x1C : 'EFI_IFR_STRING_OP', 0x1D : 'EFI_IFR_REFRESH_OP', 0x1E : 'EFI_IFR_DISABLE_IF_OP', 0x1F : 'EFI_IFR_ANIMATION_OP', 0x20 : 'EFI_IFR_TO_LOWER_OP', 0x21 : 'EFI_IFR_TO_UPPER_OP', 0x22 : 'EFI_IFR_MAP_OP', 0x23 : 'EFI_IFR_ORDERED_LIST_OP', 0x24 : 'EFI_IFR_VARSTORE_OP', 0x25 : 'EFI_IFR_VARSTORE_NAME_VALUE_OP', 0x26 : 'EFI_IFR_VARSTORE_EFI_OP', 0x27 : 'EFI_IFR_VARSTORE_DEVICE_OP', 0x28 : 'EFI_IFR_VERSION_OP', 0x29 : 'EFI_IFR_END_OP', 0x2A : 'EFI_IFR_MATCH_OP', 0x2B : 'EFI_IFR_GET_OP', 0x2C : 'EFI_IFR_SET_OP', 0x2D : 'EFI_IFR_READ_OP', 0x2E : 'EFI_IFR_WRITE_OP', 0x2F : 'EFI_IFR_EQUAL_OP', 0x30 : 'EFI_IFR_NOT_EQUAL_OP', 0x31 : 'EFI_IFR_GREATER_THAN_OP', 0x32 : 'EFI_IFR_GREATER_EQUAL_OP', 0x33 : 'EFI_IFR_LESS_THAN_OP', 0x34 : 'EFI_IFR_LESS_EQUAL_OP', 0x35 : 'EFI_IFR_BITWISE_AND_OP', 0x36 : 'EFI_IFR_BITWISE_OR_OP', 0x37 : 'EFI_IFR_BITWISE_NOT_OP', 0x38 : 'EFI_IFR_SHIFT_LEFT_OP', 0x39 : 'EFI_IFR_SHIFT_RIGHT_OP', 0x3A : 'EFI_IFR_ADD_OP', 0x3B : 'EFI_IFR_SUBTRACT_OP', 0x3C : 'EFI_IFR_MULTIPLY_OP', 0x3D : 'EFI_IFR_DIVIDE_OP', 0x3E : 'EFI_IFR_MODULO_OP', 0x3F : 'EFI_IFR_RULE_REF_OP', 0x40 : 'EFI_IFR_QUESTION_REF1_OP', 0x41 : 'EFI_IFR_QUESTION_REF2_OP', 0x42 : 'EFI_IFR_UINT8_OP', 0x43 : 'EFI_IFR_UINT16_OP', 0x44 : 'EFI_IFR_UINT32_OP', 0x45 : 'EFI_IFR_UINT64_OP', 0x46 : 'EFI_IFR_TRUE_OP', 0x47 : 'EFI_IFR_FALSE_OP', 0x48 : 'EFI_IFR_TO_UINT_OP', 0x49 : 'EFI_IFR_TO_STRING_OP', 0x4A : 'EFI_IFR_TO_BOOLEAN_OP', 0x4B : 'EFI_IFR_MID_OP', 0x4C : 'EFI_IFR_FIND_OP', 0x4D : 'EFI_IFR_TOKEN_OP', 0x4E : 'EFI_IFR_STRING_REF1_OP', 0x4F : 'EFI_IFR_STRING_REF2_OP', 0x50 : 'EFI_IFR_CONDITIONAL_OP', 0x51 : 'EFI_IFR_QUESTION_REF3_OP', 0x52 : 'EFI_IFR_ZERO_OP', 0x53 : 'EFI_IFR_ONE_OP', 0x54 : 'EFI_IFR_ONES_OP', 0x55 : 'EFI_IFR_UNDEFINED_OP', 0x56 : 'EFI_IFR_LENGTH_OP', 0x57 : 'EFI_IFR_DUP_OP', 0x58 : 'EFI_IFR_THIS_OP', 0x59 : 'EFI_IFR_SPAN_OP', 0x5A : 'EFI_IFR_VALUE_OP', 0x5B : 'EFI_IFR_DEFAULT_OP', 0x5C : 'EFI_IFR_DEFAULTSTORE_OP', 0x5D : 'EFI_IFR_FORM_MAP_OP', 0x5E : 'EFI_IFR_CATENATE_OP', 0x5F : 'EFI_IFR_GUID_OP', 0x60 : 'EFI_IFR_SECURITY_OP', 0x61 : 'EFI_IFR_MODAL_TAG_OP', 0x62 : 'EFI_IFR_REFRESH_ID_OP', 0x63 : 'EFI_IFR_WARNING_IF_OP' }

PrintLogFile = os.path.join(clb.TempFolder, 'UefiFwParser.log')
TabLevel = 0

def WriteList(buffer, offset, size, Value):
  for count in range (0, size):
    buffer[offset+count] = clb.ListInsertVal(Value >> (count*8))

def PrintLog(String, LogFile):
  global TabLevel
  if(FwpLogEn or FwpPrintEn):
    Tab = ''
    for count in range (0, TabLevel):
      Tab = Tab + '   |'
    String = '|' + Tab + String
    if(FwpPrintEn):
      log.result(f'{String}')
    if ( (LogFile != 0) and FwpLogEn ):
      LogFile.write(String+'\n')

def DelTempFvFfsFiles(Folder):
  DelFileTypes = ['*.fv', '*.ffs', '*.sec', '*.guided', '*.tmp']
  for FileType in DelFileTypes:
    TempFvFileList = glob.glob(os.path.join(Folder, FileType))
    for TempFile in TempFvFileList:
      clb.RemoveFile(TempFile)

def ProcessBin(BiosBinListBuff=[], BiosFvBase=0x800000, Files2saveGuidList=[], LogFile=0, SkipGuidedSec=False, IsCmprFv=False, BiosRegionEnd=0):
  global TabLevel, FileGuidListDict, FileSystemSaveCount, MulSetupDrivers

  if(BiosRegionEnd == 0):
    BiosRegionEnd = len(BiosBinListBuff)
  PrintLog('-----------------------------------------------------------------------------------------------------', LogFile)
  HeaderGuid = clb.FetchGuid(BiosBinListBuff, BiosFvBase)
  if(HeaderGuid == gBiosCapsuleGuid):
    BiosFvBase = BiosFvBase + clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x10), 4)
  for FvCount in range (0, 8000):
    if (BiosFvBase >= BiosRegionEnd):
      break
    FvZeroVect  = clb.FetchGuid(BiosBinListBuff, BiosFvBase)
    FvGuid  = clb.FetchGuid(BiosBinListBuff, (BiosFvBase + 0x10))
    if( (FvZeroVect == ZeroGuid) and (FvGuid != ZeroGuid) ):    # Every valid FV needs to have this zero vector.
      FvSize = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x20), 8)
      if ( (FvGuid == AllFsGuid) and (FvSize == 0xFFFFFFFFFFFFFFFF) ):
        BiosFvBase = ((BiosFvBase & 0xFFFFF000) + 0x1000)
        continue  # InValid FV, skip this iteration
      if(FvGuid == gEfiFirmwareFileSystemGuid):
        FileSystemTypeFound = 1
      elif(FvGuid == gEfiFirmwareFileSystem2Guid):
        FileSystemTypeFound = 2
      elif(FvGuid == gEfiFirmwareFileSystem3Guid):
        FileSystemTypeFound = 3
      else:
        FileSystemTypeFound = 0
      FvSignature = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x28), 4, clb.ASCII)
      if (FvSignature!='_FVH'): #'_FVH' = 0x4856465F
        BiosFvBase = ((BiosFvBase & 0xFFFFF000) + 0x1000)
        continue # InValid FV, skip this iteration
      FvHdrLen = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x30), 2)
      FVChecksum = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x32), 2)
      ExtHdrOffset = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x34), 2)
      FvRev = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x37), 1)
      FvBlocks = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x38), 4)
      BlockLen = clb.ReadList(BiosBinListBuff, (BiosFvBase + 0x3C), 4)
      if(ExtHdrOffset):
        FvNameGuid = clb.FetchGuid(BiosBinListBuff, (BiosFvBase+ExtHdrOffset))
        ExtHdrSize = clb.ReadList(BiosBinListBuff, (BiosFvBase+ExtHdrOffset+0x10), 4)
        FvHdrLen = ExtHdrOffset + ExtHdrSize
      PrintLog(' BiosFvBase = 0x%08X FvSize : 0x%X FvSignature = \"%s\" FvHdrLen = 0x%X ExtHdrOfst = 0x%X' %(BiosFvBase, FvSize, FvSignature, FvHdrLen, ExtHdrOffset), LogFile)
      if(ExtHdrOffset):
        PrintLog(' FvNameGuid = %s' %clb.GuidStr(FvNameGuid), LogFile)
      PrintLog(' FVChecksum = 0x%X  FvRev = 0x%X  NoOfBlocks = 0x%X  BlockLen = 0x%X  FileSystemType = %d' %(FVChecksum, FvRev, FvBlocks, BlockLen, FileSystemTypeFound), LogFile)
      PrintLog(' FvGuid : %s ' %clb.GuidStr(FvGuid), LogFile)
      BiosFFsbase = BiosFvBase+FvHdrLen
      FileSystembase = (BiosFFsbase + 7 ) & 0xFFFFFFF8    # this is because FileSystem sits on a 8 byte boundary
      if (FileSystembase >= (BiosFvBase + FvSize)):
        TabLevel = TabLevel - 1
        PrintLog('-------------------------------------------------------------------------------------', LogFile)
        BiosFvBase = (BiosFvBase + FvSize)
        continue
      FirstFsGuid = clb.FetchGuid(BiosBinListBuff, FileSystembase)
      if ( FirstFsGuid != AllFsGuid ):
        for FileGuid in Files2saveGuidList:
          if ( FvGuid == FileGuid ):
            FvFileName = os.path.join(clb.TempFolder, '%X_File.fv' %FvGuid[0])
            if(os.path.isfile(FvFileName)):
              FvFileName = os.path.join(clb.TempFolder, '%X_Copy_File.fv' %FvGuid[0])
            PrintLog(' ++++++++++   Saving FV file as %s   ++++++++++   |' %FvFileName, LogFile)
            with open(FvFileName, 'wb') as FfsFile:
              FfsFile.write(bytearray(BiosBinListBuff[BiosFvBase:BiosFvBase+FvSize]))
            FileGuidListDict[FileSystemSaveCount] = {'FileGuid':FileGuid, 'BiosBinPointer':BiosFvBase, 'FileSystemSize':FvSize}
            FileSystemSaveCount = FileSystemSaveCount + 1
            if(FileSystemSaveCount >= len(Files2saveGuidList)):
              TabLevel = 0
              return
            break
      TabLevel = TabLevel + 1
      PrintLog('-------------------------------------------------------------------------------------', LogFile)
      for FfsCount in range (0, 8000):
        if(FileSystemTypeFound == 0):
          PrintLog(' Unknown FileSystem, skipping File System Parsing for current FV....', LogFile)
          break
        BiosFFsbase = (BiosFFsbase + 7 ) & 0xFFFFFFF8    # this is because FFS sits on a 8 byte boundary
        if ((BiosFFsbase >= (BiosFvBase + FvSize)) or ((BiosFFsbase+FFS_FILE_HEADER_SIZE) >= BiosRegionEnd)):
          break
        FFsGuid = clb.FetchGuid(BiosBinListBuff, BiosFFsbase)
        if ( FFsGuid == ZeroGuid ):
          break
        FFShdrChksm = clb.ReadList(BiosBinListBuff, (BiosFFsbase+0x10), 1)
        FFSfileChksm = clb.ReadList(BiosBinListBuff, (BiosFFsbase+0x11), 1)
        FFSfileType = clb.ReadList(BiosBinListBuff, (BiosFFsbase+0x12), 1)
        FFSAttr = clb.ReadList(BiosBinListBuff, (BiosFFsbase+0x13), 1)
        FfsHeaderSize = FFS_FILE_HEADER_SIZE
        FFSsize = clb.ReadList(BiosBinListBuff, BiosFFsbase+0x14, 3)
        if((FFSsize == 0xFFFFFF) or ((FFSAttr & FFS_ATTRIB_LARGE_FILE) == FFS_ATTRIB_LARGE_FILE)):
          FfsHeaderSize = FFS_FILE_HEADER2_SIZE
          FFSsize = clb.ReadList(BiosBinListBuff, BiosFFsbase+FFS_FILE_HEADER_SIZE, 4)
        if ( ((FFsGuid == AllFsGuid) and (FFSsize == 0xFFFFFFFF)) or (FFSsize == 0) ):
          break  # InValid FFS, break from FFS loop
        FFSsectionSize = clb.ReadList(BiosBinListBuff, BiosFFsbase+FfsHeaderSize, 3)
        FFSsectionType = clb.ReadList(BiosBinListBuff, BiosFFsbase+FfsHeaderSize+3, 1)
        for FileGuid in Files2saveGuidList:
          if ( FFsGuid == FileGuid ):
            FfsFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %FFsGuid[0])
            if(os.path.isfile(FfsFileName)):
              if(FileGuid in SetupDriverGuidList):
                MulSetupDrivers = True
              FfsFileName = os.path.join(clb.TempFolder, '%X_Copy_File.ffs' %FFsGuid[0])
            PrintLog(' ++++++++++   Saving FFS file as %s   ++++++++++   |' %FfsFileName, LogFile)
            with open(FfsFileName, 'wb') as FfsFile:
              FfsFile.write(bytearray(BiosBinListBuff[BiosFFsbase:BiosFFsbase+FFSsize]))
            FileGuidListDict[FileSystemSaveCount] = {'FileGuid':FileGuid, 'BiosBinPointer':BiosFFsbase, 'FileSystemSize':FFSsize}
            FileSystemSaveCount = FileSystemSaveCount + 1
            if(FileSystemSaveCount >= len(Files2saveGuidList)):
              TabLevel = 0
              return
            break
        PrintLog(' BiosFFSbase = 0x%08X  FFSsize : 0x%X  FFShdrChksm 0x%X  FFSfileChksm = 0x%X ' %(BiosFFsbase, FFSsize, FFShdrChksm, FFSfileChksm), LogFile)
        PrintLog(' FFSfileType = \"%s\"  FFSAttr = 0x%X ' %(FFSfileTypesDict.get(FFSfileType, 'NA'), FFSAttr), LogFile)
        PrintLog(' FFSsectionSize = 0x%X  FFSsectionType = \"%s\" ' %(FFSsectionSize, FFSsectionTypeDict.get(FFSsectionType, 'NA')), LogFile)
        PrintLog(' FFSguid : %s ' %clb.GuidStr(FFsGuid), LogFile)

        if(FFSfileType == FV_FILETYPE_FIRMWARE_VOLUME_IMAGE):
          TabLevel = TabLevel + 1
          Temp2Buff = BiosBinListBuff
          Temp2BiosFVbase = BiosFvBase
          Temp2BiosFFsbase = BiosFFsbase
          Temp2FFSsize = FFSsize
          Temp2FvSize = FvSize
          TempBinPtr = BiosFFsbase + FfsHeaderSize
          for SecCount in range (0, 0x8000, 1):
            if(TempBinPtr >= (BiosFFsbase+FFSsize)):
              break
            SectionSize = clb.ReadList(BiosBinListBuff, TempBinPtr, 3)
            SectionType = clb.ReadList(BiosBinListBuff, TempBinPtr+3, 1)
            SecHdrSize = 4
            if(SectionSize == 0xFFFFFF):
              SectionSize = clb.ReadList(BiosBinListBuff, TempBinPtr+4, 4)
              SecHdrSize = 8
            if(SectionType == EFI_SECTION_FIRMWARE_VOLUME_IMAGE):
              PrintLog(' Section FIRMWARE_VOLUME_IMAGE Found, parsing start...', LogFile)
              ProcessBin(BiosBinListBuff[(TempBinPtr+SecHdrSize):(TempBinPtr+SectionSize)], 0, Files2saveGuidList, LogFile, False, False)
              PrintLog(' Section FIRMWARE_VOLUME_IMAGE parsing complete...', LogFile)
            TempBinPtr = (TempBinPtr + SectionSize + 3) & 0xFFFFFFFC
          BiosBinListBuff = Temp2Buff
          BiosFvBase = Temp2BiosFVbase
          BiosFFsbase = Temp2BiosFFsbase
          FFSsize = Temp2FFSsize
          FvSize = Temp2FvSize
          TabLevel = TabLevel - 1

        FoundAlgorithmSha256 = False
        if( (FFSsectionType == EFI_SECTION_GUID_DEFINED) and (SkipGuidedSec == False) ):
          SectionGuid  = clb.FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+4))
          FFSsectionDataStart = 0
          if (SectionGuid == gEfiFirmwareContentsSignedGuid):
            SignSecBuffStartOfst = clb.ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+4+0x10), 2)
            SignSecBuffSize = clb.ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+SignSecBuffStartOfst), 4)
            if( (gEfiCertTypeRsa2048Sha256Guid == clb.FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+SignSecBuffStartOfst+8))) and (gEfiHashAlgorithmSha256Guid == clb.FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+SignSecBuffStartOfst+0x18))) ):
              FoundAlgorithmSha256 = True
            FFSsectionDataStart = SignSecBuffStartOfst + SignSecBuffSize
            FFSsectionSize = clb.ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart), 3)
            SectionGuid  = clb.FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+4))
          if (SectionGuid == gEfiCertTypeRsa2048Sha256Guid):
            SignSecBuffStartOfst = clb.ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+4+0x10), 2)
            if(gEfiHashAlgorithmSha256Guid == clb.FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+0x18))):
              FoundAlgorithmSha256 = True
            FFSsectionDataStart = SignSecBuffStartOfst + 0x210
            FFSsectionSize = clb.ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart), 3)
            SectionGuid  = clb.FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+4))
          if ((SectionGuid == gLzmaCustomDecompressGuid) or (SectionGuid == gBrotliCustomDecompressGuid)):
            if (FFSfileType == FV_FILETYPE_FIRMWARE_VOLUME_IMAGE):
              PrintLog(' Current compressed Section is FIRMWARE_VOLUME_IMAGE, decompresing and parsing it...', LogFile)
            LzmaBuffStart = FFSsectionDataStart+clb.ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+4+0x10), 2)
            LzmaFvMainCompactBuff = bytearray(BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+LzmaBuffStart):(BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+FFSsectionSize)])
            FvInFileLocation = os.path.join(clb.TempFolder, 'FwComp.sec')
            FvOutFileLocation = os.path.join(clb.TempFolder, 'FwVol.fv')
            with open(FvInFileLocation, 'wb') as TmpFile:
              TmpFile.write(LzmaFvMainCompactBuff)
            if SectionGuid == gLzmaCustomDecompressGuid:
              PrintLog(' Found LZMA Compressed section', LogFile)
              compress.lzma_decompress(FvInFileLocation, FvOutFileLocation)
            if SectionGuid == gBrotliCustomDecompressGuid:
              PrintLog(' Found Brotli Compressed section', LogFile)
              utils.system_call(cmd_lis=[clb.BrotliCompressUtility, "-d", "-i", FvInFileLocation, "-o", FvOutFileLocation])
            with open(FvOutFileLocation, 'rb') as TmpFile:
              FvMainListBuffer = list(TmpFile.read())

            TabLevel = TabLevel + 1
            TempBuff = BiosBinListBuff
            TempBiosFVbase = BiosFvBase
            TempBiosFFsbase = BiosFFsbase
            TempFFSsize = FFSsize
            TempFvSize = FvSize
            FvMainListSize = len(FvMainListBuffer)
            TempBinPtr = 0
            for SecCount in range (0, 0x8000, 1):
              if(TempBinPtr >= FvMainListSize):
                break
              SectionSize = clb.ReadList(FvMainListBuffer, TempBinPtr, 3)
              SectionType = clb.ReadList(FvMainListBuffer, TempBinPtr+3, 1)
              SecHdrSize = 4
              if(SectionSize == 0xFFFFFF):
                SectionSize = clb.ReadList(FvMainListBuffer, TempBinPtr+4, 4)
                SecHdrSize = 8
              if(SectionType == EFI_SECTION_FIRMWARE_VOLUME_IMAGE):
                PrintLog(' Section FIRMWARE_VOLUME_IMAGE Found, parsing start...', LogFile)
                ProcessBin(FvMainListBuffer[(TempBinPtr+SecHdrSize):(TempBinPtr+SectionSize)], 0, Files2saveGuidList, LogFile, False, True)
                PrintLog(' Section FIRMWARE_VOLUME_IMAGE parsing complete...', LogFile)
              TempBinPtr = (TempBinPtr + SectionSize + 3) & 0xFFFFFFFC

            PrintLog(' Uncompressed FIRMWARE_VOLUME_IMAGE parsing complete...', LogFile)
            BiosBinListBuff = TempBuff
            BiosFvBase = TempBiosFVbase
            BiosFFsbase = TempBiosFFsbase
            FFSsize = TempFFSsize
            FvSize = TempFvSize
            TabLevel = TabLevel - 1
            clb.RemoveFile(FvOutFileLocation)
            clb.RemoveFile(FvInFileLocation)
            if( (FileSystemSaveCount != 0) and (FileSystemSaveCount >= len(Files2saveGuidList)) ):
              TabLevel = 0
              return
        BiosFFsbase = (BiosFFsbase + FFSsize + 7 ) & 0xFFFFFFF8    # this is because FFS sits on a 8 byte boundary
        PrintLog('-------------------------------------------------------------------------------------', LogFile)
      TabLevel = TabLevel - 1
      PrintLog('-----------------------------------------------------------------------------------------------------', LogFile)
      BiosFvBase = (BiosFvBase + FvSize)
    else:
      BiosFvBase = ((BiosFvBase & 0xFFFFF000) + 0x1000)    # InValid FV, Adjust FvBaseAccrodingly

def UpdateBiosId(BiosBinaryFile=0, NewMajorVer='', NewMinorVer='', OutFolder=0, NewBiosVer='', NewTsVer='', NewXxYy=''):
  global FileGuidListDict, FwpPrintEn
  tmpPrintSts = FwpPrintEn
  FwpPrintEn = False
  FileGuidListDict = {}
  BiosIdFfsToSave  = [ gEfiBiosIdGuid ]
  BiosIdString = 'Unknown'
  NewBiosId = BiosIdString
  clb.OutBinFile = ''

  if(OutFolder == 0):
    OutFolder = clb.TempFolder
  DelTempFvFfsFiles(clb.TempFolder)
  with open(BiosBinaryFile, 'rb') as BiosBinFile:
    BiosBinListBuff = list(BiosBinFile.read())
  BiosFileName = os.path.basename(BiosBinaryFile)
  FlashRegionInfo(BiosBinListBuff, False)
  if (FwIngredientDict['FlashDescpValid'] != 0):
    BiosRegionBase = FwIngredientDict['FlashRegions'][BIOS_Region]['BaseAddr']
    BiosEnd = FwIngredientDict['FlashRegions'][BIOS_Region]['EndAddr'] + 1
  else:
    BiosRegionBase = 0
    BiosEnd = len(BiosBinListBuff)

  if(len(BiosBinListBuff) != 0):
    ProcessBin(BiosBinListBuff, BiosRegionBase, BiosIdFfsToSave, 0, True, BiosRegionEnd=BiosEnd)
    for FileGuid in BiosIdFfsToSave:    # Delete the file once done, dont want the stale file affecting subsequent operation
      clb.RemoveFile(os.path.join(clb.TempFolder, '%X_File.ffs' %FileGuid[0]))
      clb.RemoveFile(os.path.join(clb.TempFolder, '%X_File.fv' %FileGuid[0]))
    for FileCountId in FileGuidListDict:
      if(FileGuidListDict[FileCountId]['FileGuid'] == gEfiBiosIdGuid):
        BiosIdSecBase = FileGuidListDict[FileCountId]['BiosBinPointer'] + FFS_FILE_HEADER_SIZE + EFI_COMMON_SECTION_HEADER_SIZE
        FfsSize = FileGuidListDict[FileCountId]['FileSystemSize']
        BiosIdString = ''
        BiosIdSig = clb.ReadList(BiosBinListBuff, BiosIdSecBase, 8)
        if(BiosIdSig != 0):
          for count in range (0, (FfsSize-FFS_FILE_HEADER_SIZE-EFI_COMMON_SECTION_HEADER_SIZE)):
            ChrVal = clb.ReadList(BiosBinListBuff, (BiosIdSecBase+8+(count*2)), 1)
            if(ChrVal == 0):
              break
            BiosIdString = BiosIdString + chr(ChrVal)
        log.info( 'Current BIOS ID String is %s' %(BiosIdString))
        NewBiosId = BiosIdString.split('.')
        if(BiosIdString != 'Unknown'):
          if ((NewBiosVer != '') or (NewMajorVer != '') or (NewMinorVer != '') or (NewTsVer != '')) or ((len(NewBiosId) == 6) and (NewXxYy !='')):
            SkipNewBiosVer = False
            if(len(NewBiosId) == 6):
              TStmpPos = 5
              SkipNewBiosVer = True
              if(NewXxYy != ''):
                NewBiosId[4] = NewXxYy.zfill(4)[0:4]
            else:
              TStmpPos = 4
            if(NewMajorVer != ''):
              NewBiosId[2] = NewMajorVer.zfill(4)[0:4]
            if(NewMinorVer != ''):
              NewBiosId[3] = NewMinorVer.zfill(3)[0:3]
            if(SkipNewBiosVer == False):
              if(NewBiosVer != ''):
                NewBiosId[1] = NewBiosVer.zfill(3)[0:3]
              else:
                NewBiosId[1] = 'E9I'  # indicates that the BIOS ID was updated using external Tool.
            if(NewTsVer != ''):
              NewBiosId[TStmpPos] = NewTsVer.zfill(10)[0:10]
            else:
              CurTime = time.localtime()
              NewBiosId[TStmpPos] = '%02d%02d%02d%02d%02d' %((CurTime[0]-2000), CurTime[1], CurTime[2], CurTime[3], CurTime[4])
            NewBiosIdString = '.'.join(NewBiosId)
            log.info(f'Updated BIOS ID String is {NewBiosIdString}')
            for count in range (0, len(NewBiosIdString)):
              ChrVal = clb.ReadList(BiosBinListBuff, (BiosIdSecBase+8+(count*2)), 1)
              if(ChrVal == 0):
                break
              BiosBinListBuff.pop((BiosIdSecBase+8+(count*2)))
              BiosBinListBuff.insert((BiosIdSecBase+8+(count*2)), clb.ListInsertVal(int(clb.HexLiFy(NewBiosIdString[count]), 16)))
            NewBiosFileName = BiosFileName.replace(BiosIdString, NewBiosIdString)
            if(NewBiosFileName == BiosFileName):
              NewBiosFileName = NewBiosIdString+'.bin'
            NewBiosBinFile = os.path.join(OutFolder, NewBiosFileName)
            clb.OutBinFile = NewBiosBinFile
            with open(NewBiosBinFile, 'wb') as ModBiosBinFile:
              ModBiosBinFile.write(bytearray(BiosBinListBuff))
            log.info(f'Bios Binary with updated BIOS ID is saved under {NewBiosBinFile}')
          else:
            log.info('Ver, Major, Minor, and TS are empty, so no action taken.')
          break
  FwpPrintEn = tmpPrintSts
VARIABLE_HEADER_ALIGNMENT         = 4
VARIABLE_DATA                     = 0x55AA
VARIABLE_STORE_FORMATTED          = 0x5a
VARIABLE_STORE_HEALTHY            = 0xfe
VAR_IN_DELETED_TRANSITION         = 0xfe  # Variable is in obsolete transition.
VAR_DELETED                       = 0xfd  # Variable is obsolete.
VAR_HEADER_VALID_ONLY             = 0x7f  # Variable header has been valid.
VAR_ADDED                         = 0x3f  # Variable has been completely added.
VARIABLE_STORE_HEADER_SIZE        = 0x1C
VARIABLE_HEADER2_SIZE             = 0x3C
VARIABLE_HEADER_SIZE              = 0x20

def ParseNvram(NvRamFvListBuffer, BiosKnobDict, NvRamPointer=0, LogFile=0):
  BiosKnobDictLen = len(BiosKnobDict)
  PrintLog(' Parse Full NvRam VarStores and Knob details ', LogFile)
  NvRamDict = {}
  VarCount = 0
  if(NvRamPointer == 0):
    for CurrPtr in range (NvRamPointer, (len(NvRamFvListBuffer)-0x10)):
      VarStoreHdrGuid = clb.FetchGuid(NvRamFvListBuffer, CurrPtr)
      if( (VarStoreHdrGuid == gEfiGlobalVariableGuid) or (VarStoreHdrGuid == gEfiAuthenticatedVariableGuid) or (VarStoreHdrGuid == gEfiVariableGuid) ):
        NvRamPointer = CurrPtr
        PrintLog(' Found NvRam Start at 0x%X offset' %NvRamPointer, LogFile)
        break
  for VarStrHdrCount in range (0, 0x100):
    if(NvRamPointer >= (len(NvRamFvListBuffer)-VARIABLE_STORE_HEADER_SIZE)):
      return NvRamDict
    VarStoreHdrGuid = clb.FetchGuid(NvRamFvListBuffer, NvRamPointer)
    VarStoreSize = clb.ReadList(NvRamFvListBuffer, (NvRamPointer+0x10), 4)
    if( (VarStoreHdrGuid == AllFsGuid) or (VarStoreSize == 0xFFFFFFFF) ):
      break
    if( (VarStoreHdrGuid == gEfiGlobalVariableGuid) or (VarStoreHdrGuid == gEfiAuthenticatedVariableGuid) ):
      HdrSize = VARIABLE_HEADER2_SIZE
      NameSzOffst = 0x24
      DataSzOffst = 0x28
      GuidOffset = 0x2C
    elif(VarStoreHdrGuid == gEfiVariableGuid):
      HdrSize = VARIABLE_HEADER_SIZE
      NameSzOffst = 0x08
      DataSzOffst = 0x0C
      GuidOffset = 0x10
    else:
      HdrSize = VARIABLE_HEADER_SIZE
      NameSzOffst = 0x08
      DataSzOffst = 0x0C
      GuidOffset = 0x10
    VarStoreFormat = clb.ReadList(NvRamFvListBuffer, (NvRamPointer+0x14), 1)
    VarStoreState = clb.ReadList(NvRamFvListBuffer, (NvRamPointer+0x15), 1)
    PrintLog(' CurrPtr = 0x%X  VarStoreSize = 0x%X' %(NvRamPointer, VarStoreSize), LogFile)
    PrintLog(' VarStoreHdr Guid = %s ' %clb.GuidStr(VarStoreHdrGuid), LogFile)
    if( (VarStoreFormat != VARIABLE_STORE_FORMATTED) or (VarStoreState != VARIABLE_STORE_HEALTHY) ):
      NvRamPointer = NvRamPointer + VarStoreSize
      break
    CurVarPtr = ((NvRamPointer + VARIABLE_STORE_HEADER_SIZE + 3) & 0xFFFFFFFC)  # this one is 4 bytes or dword aligned always
    PrintLog ('------------|--------|------------|------------|--------------------------------|-------------', LogFile)
    PrintLog (' CurrentPtr | State  | Attribute  | NvarDataSz | VarName                        | VarGuid     ', LogFile)
    PrintLog ('------------|--------|------------|------------|--------------------------------|-------------', LogFile)
    for count in range (0, 200):
      if(CurVarPtr >= len(NvRamFvListBuffer)):
        break
      StartId = clb.ReadList(NvRamFvListBuffer, CurVarPtr, 2)
      if(StartId != VARIABLE_DATA):
        CurVarPtr = CurVarPtr + HdrSize
        break
      VarState = clb.ReadList(NvRamFvListBuffer, (CurVarPtr+0x2), 1)
      VarAtri = clb.ReadList(NvRamFvListBuffer, (CurVarPtr+0x4), 4)
      VarNameSize = clb.ReadList(NvRamFvListBuffer, (CurVarPtr+NameSzOffst), 4)
      VarDataSize = clb.ReadList(NvRamFvListBuffer, (CurVarPtr+DataSzOffst), 4)
      VarGuid = clb.FetchGuid(NvRamFvListBuffer, (CurVarPtr+GuidOffset))
      VarName = ''
      for index in range (0, int(VarNameSize/2)):
        Val = clb.ReadList(NvRamFvListBuffer, (CurVarPtr+HdrSize+(index*2)), 1)
        if(Val == 0):
          break
        VarName = VarName + chr(Val)
      PrintLog (' 0x%-8X |  0x%02X  | 0x%08X | 0x%-8X | %-30s | %s' %(CurVarPtr, VarState, VarAtri, VarDataSize, VarName, clb.GuidStr(VarGuid)), LogFile)
      PrintLog ('------------|--------|------------|------------|--------------------------------|-------------', LogFile)
      if(BiosKnobDictLen):
        for VarId in BiosKnobDict:
          if( (VarName == BiosKnobDict[VarId]['NvarName']) and ((BiosKnobDict[VarId]['NvarGuid'] == ZeroGuid) or (VarGuid == BiosKnobDict[VarId]['NvarGuid'])) ):
            NvRamDict[VarId] = { 'NvarName':VarName, 'NvarGuid':VarGuid, 'NvarSize':VarDataSize, 'VarAttri':VarAtri, 'NvarDataBufPtr':(CurVarPtr+HdrSize+VarNameSize) }
            break
      else:
        NvRamDict[VarCount] = { 'NvarName':VarName, 'NvarGuid':VarGuid, 'NvarSize':VarDataSize, 'VarAttri':VarAtri, 'NvarDataBufPtr':(CurVarPtr+HdrSize+VarNameSize) }
        VarCount = VarCount + 1
      CurVarPtr = (CurVarPtr + HdrSize + VarNameSize + VarDataSize + 3) & 0xFFFFFFFC
    NvRamPointer = NvRamPointer + VarStoreSize
  return NvRamDict

def GetIfrFormsHdr(HiiDbBinListBuff, HiiDbPointer=0):
  if( HiiDbBinListBuff == 0 ):
    return 0
  ReturnAddrDict = { 'IfrList' : [], 'StrPkgHdr' : 0, 'UqiPkgHdr' : 0}
  BufLen = len(HiiDbBinListBuff)
  while(HiiDbPointer < BufLen):
    Guid_LowHalf = clb.ReadList(HiiDbBinListBuff, HiiDbPointer, 4)
    if (Guid_LowHalf == gEfiIfrTianoGuid[0]):
      HiiLstGuid  = clb.FetchGuid(HiiDbBinListBuff, HiiDbPointer)
      if(HiiLstGuid == gEfiIfrTianoGuid):
        IfrOpcode = clb.ReadList(HiiDbBinListBuff, HiiDbPointer - 2, 1)
        if (IfrOpcode == EFI_IFR_GUID_OP):
          TmpHiiDbPtr = HiiDbPointer - 2
          StartAddress = 0
          if(clb.ReadList(HiiDbBinListBuff, HiiDbPointer - 2 - 0x27, 2) == 0xA70E):  # Check if we Find formset opcode
            StartAddress = HiiDbPointer - 2 - 0x27
          StartFound = False
          for count in range (0, 0x1000):
            IfrOpcode = clb.ReadList(HiiDbBinListBuff, TmpHiiDbPtr, 1)
            IfrOpLen = (clb.ReadList(HiiDbBinListBuff, (TmpHiiDbPtr+1), 1) & 0x7F)
            if ( (IfrOpcode == EFI_IFR_VARSTORE_OP) or (IfrOpcode == EFI_IFR_VARSTORE_EFI_OP) ):
              StartFound = True
              break
            TmpHiiDbPtr = TmpHiiDbPtr + IfrOpLen
          if(StartFound):
            if(StartAddress != 0):
              ReturnAddrDict['IfrList'].append(StartAddress)
            HiiDbPointer = TmpHiiDbPtr
    if (Guid_LowHalf == 0x552D6E65):    # compare with 'en-US'
      StringPkgLang = clb.ReadList(HiiDbBinListBuff, HiiDbPointer, 6)
      if (StringPkgLang == 0x53552D6E65):    # compare with 'en-US'
        StringHdr = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer+0x6), 1)
        PromptLow = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer+0x7), 8)
        PromptHigh = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer+0x7+0x8), 8)
        if( (StringHdr == EFI_HII_SIBT_STRING_UCS2) and (PromptLow == 0x6C0067006E0045) and (PromptHigh == 0x6800730069) ):    # EFI_HII_SIBT_STRING_UCS2 and 'E.n.g.l.i.s.h'
          StringPkgType = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer-0x2B), 1)
          StringOffset = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer-0x26), 4)
          if(StringPkgType == EFI_HII_PACKAGE_STRINGS):
            ReturnAddrDict['StrPkgHdr'] = ((HiiDbPointer + 6) - StringOffset)
    if ( (Guid_LowHalf == 0x697175) and (Parse_Print_Uqi) ):    # compare with 'uqi'
      StringHdr = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer+0x4), 1)
      PromptLow = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer+0x5), 6)
      if( (StringHdr == EFI_HII_SIBT_STRING_UCS2) and (PromptLow == 0x6900710075) ):    # EFI_HII_SIBT_STRING_UCS2 and 'u.q.i'
        StringPkgType = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer-0x2B), 1)
        StringOffset = clb.ReadList(HiiDbBinListBuff, (HiiDbPointer-0x26), 4)
        if(StringPkgType == EFI_HII_PACKAGE_STRINGS):
          ReturnAddrDict['UqiPkgHdr'] = ((HiiDbPointer + 4) - StringOffset)
    HiiDbPointer = HiiDbPointer + 1
  return ReturnAddrDict

def ParseIfrForms(HiiDbBinListBuff, BiosKnobDict, HiiStrDict, IfrOpHdrAddr, IfrOpHdrEndAddr, BiosFfsFvBase, FfsFilecount, FrontPageForm, LogFile, outXml=''):
  global TabLevel, PlatInfoMenuDone
  TabLevel = 0
  SetupPgDict = {}
  if(IfrOpHdrEndAddr == 0):
    IfrOpHdrEndAddr = len(HiiDbBinListBuff)
  PrintLog('=========================  Start IFR Forms Parsing  =========================|', LogFile)
  for VarId in BiosKnobDict:
    BiosKnobDict[VarId]['HiiVarId'] = 0xFF

  FormSetCapture = False
  bit_wise_form = False
  for OpcodeCount in range (0, 0xFFFFF):
    if (IfrOpHdrAddr >= IfrOpHdrEndAddr):
      break
    IfrOpcode = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
    if bit_wise_form and IfrOpcode == EFI_IFR_END_OP:
        bit_wise_form = False
    if IfrOpcode == EFI_IFR_GUID_OP and clb.FetchGuid(HiiDbBinListBuff, (IfrOpHdrAddr + 2)) == gEdkiiIfrBitVarstoreGuid:
        bit_wise_form = True
        IfrOpHdrAddr = IfrOpHdrAddr + 0x12
        continue
    if (IfrOpcodesDict.get(IfrOpcode, 'N.A.') == 'N.A.'):
      PrintLog('=========================   End IFR Forms Parsing   =========================|', LogFile)
      break
    IfrOpcodeSize = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
    if ( (IfrOpcode == EFI_IFR_SUPPRESS_IF_OP) or (IfrOpcode == EFI_IFR_GRAY_OUT_IF_OP) ):
      Scope = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
      if(Scope):
        ScopeLvl = 1
      IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
      IfrOpcode = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
      IfrOpcodeSize = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
      Scope = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
      if ( (IfrOpcode == EFI_IFR_TRUE_OP) and (Scope == 0) ):
        while(ScopeLvl):  # go till end of Suppress if TRUE, we need to skip all that stuff
          IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
          IfrOpcode = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
          IfrOpcodeSize = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
          Scope = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
          if(Scope):
            ScopeLvl = ScopeLvl + 1
          if(IfrOpcode == EFI_IFR_END_OP):
            ScopeLvl = ScopeLvl - 1
    if (IfrOpcode == EFI_IFR_FORM_SET_OP):
      FormSetTitle = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x12, 2)
      PrintLog('FormSet = %s  (0x%X)' %(HiiStrDict.get(FormSetTitle), FormSetTitle), LogFile)
      FormSetCapture = True
    if (IfrOpcode == EFI_IFR_FORM_OP):
      CurrentFormId = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
      TitlePrompt = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
      if(FormSetCapture):
        FrontPageForm.append(TitlePrompt)
        FormSetCapture = False
      PrintLog('\t\tForm = %s  (0x%X)' %(HiiStrDict.get(TitlePrompt), TitlePrompt), LogFile)
      if(PlatInfoMenuDone == False):
        if(HiiStrDict.get(TitlePrompt) == 'Platform Information Menu'):
          outXml += '\t<%s>\n' %(HiiStrDict.get(TitlePrompt).replace(' ', '_'))
          IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
          ScopeLvl = 1
          for count in range (0, 0x100, 1): # while(endform)
            if(ScopeLvl <= 0):
              PlatInfoMenuDone = True
              outXml += '\t</%s>\n' %(HiiStrDict.get(TitlePrompt).replace(' ', '_'))
              break
            CurrIfrOpcode = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
            CurrIfrOpcodeSize = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
            Scope = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
            if(Scope):
              ScopeLvl = ScopeLvl + 1
            if(CurrIfrOpcode == EFI_IFR_END_OP):
              ScopeLvl = ScopeLvl - 1
            if(CurrIfrOpcode == EFI_IFR_SUBTITLE_OP):
              Pmpt = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
              Hlp = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
              if((HiiStrDict.get(Pmpt, 'NF') == 'NF') or (HiiStrDict.get(Pmpt, 'NF') == '')):
                outXml += '\n'
              else:
                outXml += '\t\t<!--%s-->\n' %(HiiStrDict.get(Pmpt, 'NF'))
            if(CurrIfrOpcode == EFI_IFR_TEXT_OP):
              Pmpt = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
              Hlp = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
              Text2 = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 2)
              if((HiiStrDict.get(Pmpt, 'NF') != 'NF') and (HiiStrDict.get(Pmpt, 'NF') != '')):
                outXml += '\t\t<!--%s:%s-->\n' %(HiiStrDict.get(Pmpt, 'NF'), HiiStrDict.get(Text2, 'NF'))
            IfrOpHdrAddr = IfrOpHdrAddr + CurrIfrOpcodeSize
      SetupPgDict[CurrentFormId] = {'Prompt': TitlePrompt, 'PromptList': []}
    if (IfrOpcode == EFI_IFR_REF_OP):
      GotoPrompt = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
      PrintLog('\tGotoForm = %s  (0x%X)' %(HiiStrDict.get(GotoPrompt), GotoPrompt), LogFile)
      FormId = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0xD, 2)
      SetupPgDict[CurrentFormId][FormId] = {'Prompt': GotoPrompt}
    if ( (IfrOpcode == EFI_IFR_VARSTORE_OP) or (IfrOpcode == EFI_IFR_VARSTORE_EFI_OP) ):
      if(IfrOpcode == EFI_IFR_VARSTORE_OP):
        VarGuidOffset = 2
        VarIdOffset = 0x12
        VarSizeOffset = 0x14
        VarNameOffset = 0x16
      else:
        VarIdOffset = 2
        VarGuidOffset = 4
        VarSizeOffset = 0x18
        VarNameOffset = 0x1A
      IfrVarStoreGuid = clb.FetchGuid(HiiDbBinListBuff, (IfrOpHdrAddr+VarGuidOffset))
      IfrVarStoreId = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+VarIdOffset, 2)
      IfrVarStoreSize = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+VarSizeOffset, 2)
      IfrVarStoreName = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+VarNameOffset, (IfrOpcodeSize-VarNameOffset), clb.ASCII)
      for VarId in BiosKnobDict:
        if ( (BiosKnobDict[VarId]['NvarName'] == IfrVarStoreName) and (BiosKnobDict[VarId]['HiiVarId'] == 0xFF) and ((BiosKnobDict[VarId]['NvarGuid'] == ZeroGuid) or (IfrVarStoreGuid == BiosKnobDict[VarId]['NvarGuid'])) ):
          BiosKnobDict[VarId]['HiiVarId'] = IfrVarStoreId
          BiosKnobDict[VarId]['HiiVarSize'] = IfrVarStoreSize
          break
    if ( (IfrOpcode == EFI_IFR_ONE_OF_OP) or (IfrOpcode == EFI_IFR_NUMERIC_OP) or (IfrOpcode == EFI_IFR_CHECKBOX_OP) or (IfrOpcode == EFI_IFR_STRING_OP) ):
      IfrPrompt = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
      IfrHelp = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
      IfrVarId = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+8, 2)
      KnobOffset = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0A, 2)
      if bit_wise_form:
        KnobOffset = clb.BITWISE_KNOB_PREFIX + KnobOffset
        bit_size = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0D, 1) & 0x3F
      SupportedVarFound = False
      for VarIndex in BiosKnobDict:
        if(BiosKnobDict[VarIndex]['HiiVarId'] == IfrVarId):
          CurrIntVarId = VarIndex
          SupportedVarFound = True
          break
      if(SupportedVarFound == False):
        IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
        continue  # not part of supported VarID
      try:
        XmlKnobName = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobName']
      except KeyError:
        XmlKnobName = 'NotFound(%d_0x%04X)' %(CurrIntVarId, KnobOffset)
        IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
        continue
      OneOfNumericKnobSz = 0
      CurSetupTypeBin = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['SetupTypeBin']
      if( (CurSetupTypeBin != clb.INVALID_KNOB_SIZE) and (IfrOpcode != CurSetupTypeBin) ):
        IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
        continue
      if ( (IfrOpcode == EFI_IFR_ONE_OF_OP) or (IfrOpcode == EFI_IFR_NUMERIC_OP) ):
        IfrOneOfFlags = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0D, 1)
        OneOfNumericKnobSz = (1 << (IfrOneOfFlags & EFI_IFR_NUMERIC_SIZE))
        CurKnobSzBin = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzBin']
        if( ((CurKnobSzBin != clb.INVALID_KNOB_SIZE) and (OneOfNumericKnobSz != CurKnobSzBin)) and (bit_wise_form and (bit_size != CurKnobSzBin)) ):
          IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
          continue
      KnobProcessed = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][0]
      if(KnobProcessed >= 1):
        if(IfrOpcode != BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][1]):
          IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
          continue
        CurKnobInDupList = False
        for DupIndex in sorted(BiosKnobDict[CurrIntVarId]['DupKnobDict']):
          if(XmlKnobName == BiosKnobDict[CurrIntVarId]['DupKnobDict'][DupIndex]['DupKnobName']):
            CurKnobInDupList = True
            break
        if(CurKnobInDupList == False):
          IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
          continue
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Prompt'] = IfrPrompt
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Help'] = IfrHelp
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['SetupTypeHii'] = IfrOpcode
      if(len(SetupPgDict[CurrentFormId]['PromptList']) == 0):
        PromptList = []
        ExitAllLoops = False
        CurFormId = CurrentFormId
        PreviousForms = []
        while(1):
          ProcessCnt = 0
          for FormId in SetupPgDict:
            ProcessCnt = ProcessCnt + 1
            if FormId not in PreviousForms:
              if (FormId in SetupPgDict):
                if (CurFormId in SetupPgDict[FormId]):
                  PromptList.append(SetupPgDict[FormId][CurFormId]['Prompt'])
                  PreviousForms.append(FormId)
                  CurFormId = FormId
                  break
            if (ProcessCnt == len(SetupPgDict)):
              PromptList.append(SetupPgDict[CurFormId]['Prompt'])
              if(SetupPgDict[CurFormId]['Prompt'] not in FrontPageForm):
                PromptList.append(0x10000)  # we need to initialize this to '??'
              ExitAllLoops = True
              break
          if(ExitAllLoops):
            break
        SetupPgDict[CurrentFormId]['PromptList'] = PromptList
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['ParentPromptList'] = SetupPgDict[CurrentFormId]['PromptList']
      CurrOpcode = IfrOpcode
      if (IfrOpcode == EFI_IFR_CHECKBOX_OP):
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzHii'] = 1
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = (clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0xD, 1) & 1)
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['FvMainOffHiiDb'] = BiosFfsFvBase+IfrOpHdrAddr+0xD
      elif (IfrOpcode == EFI_IFR_STRING_OP):
        Max = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0E, 1)
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Min'] = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0D, 1)
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Max'] = Max
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzHii'] = (Max * 2)
      elif ( (IfrOpcode == EFI_IFR_ONE_OF_OP) or (IfrOpcode == EFI_IFR_NUMERIC_OP) ):
        BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzHii'] = OneOfNumericKnobSz
        if(IfrOpcode == EFI_IFR_NUMERIC_OP):
          if bit_wise_form:
            OneOfNumericKnobSz = 4      # for BitWise, the Width for min, max, step fields remain UINT32.
          BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Min'] = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr+0x0E), OneOfNumericKnobSz)
          BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Max'] = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr+0x0E+OneOfNumericKnobSz), OneOfNumericKnobSz)
          BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Step'] = clb.ReadList(HiiDbBinListBuff, (IfrOpHdrAddr+0x0E+OneOfNumericKnobSz+OneOfNumericKnobSz), OneOfNumericKnobSz)
          while (IfrOpcode != EFI_IFR_END_OP):
            if(IfrOpcode == EFI_IFR_DEFAULT_OP):
              NumValSize = (clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 1) & 0x0F)
              if bit_wise_form:
                NumValSize = EFI_IFR_TYPE_NUM_SIZE_32      # for BitWise, the Width fields remain UINT32.
              DefValue = 0
              if(NumValSize == EFI_IFR_TYPE_BOOLEAN):
                DefValue = int(clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 1) != 0)
              elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_8):
                DefValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 1)
              elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_16):
                DefValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 2)
              elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_32):
                DefValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 4)
              elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_64):
                DefValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 8)
              BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = DefValue
              BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['FvMainOffHiiDb'] = BiosFfsFvBase+IfrOpHdrAddr+0x5
            IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
            IfrOpcode = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
            IfrOpcodeSize = (clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x7F)
        elif(IfrOpcode == EFI_IFR_ONE_OF_OP):
          OneOfScopeLvl = 0
          OneOfScope = (clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x80) >> 7
          if(OneOfScope):
            OneOfScopeLvl = OneOfScopeLvl + 1
          if(IfrOpcode == EFI_IFR_END_OP):
            OneOfScopeLvl = OneOfScopeLvl - 1
          BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobProcessed] = {}
          BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['FvMainOffHiiDb'] = BiosFfsFvBase+IfrOpHdrAddr
          OptionsCount = 0
          while (OneOfScopeLvl > 0):
            IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
            IfrOpcode = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
            IfrOpcodeSize = (clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x7F)
            OneOfScope = (clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x80) >> 7
            if(OneOfScope):
              OneOfScopeLvl = OneOfScopeLvl + 1
            if(IfrOpcode == EFI_IFR_END_OP):
              OneOfScopeLvl = OneOfScopeLvl - 1
            if(IfrOpcode == EFI_IFR_ONE_OF_OPTION_OP):
              OptionTextPromt = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
              OptionFlag = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 1)
              OptionTextValSize = (OptionFlag & 0x0F)
              if bit_wise_form:
                OptionTextValSize = EFI_IFR_TYPE_NUM_SIZE_32      # for BitWise, the Width fields remain UINT32.
              TextValue = 0
              if(OptionTextValSize == EFI_IFR_TYPE_BOOLEAN):
                TextValue = int(clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 1) != 0)
              elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_8):
                TextValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 1)
              elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_16):
                TextValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 2)
              elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_32):
                TextValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 4)
              elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_64):
                TextValue = clb.ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 8)
              if( (OptionFlag & EFI_IFR_OPTION_DEFAULT) != 0 ):
                BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = TextValue
              BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobProcessed][OptionsCount] = { 'OptionText': OptionTextPromt, 'OptionVal':TextValue }
              OptionsCount = OptionsCount + 1
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][0] = (KnobProcessed+1)
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][1] = CurrOpcode
      BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][2] = FfsFilecount
      PrintLog('\t\t\tKnob = %s' %(BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobName']), LogFile)
    IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
  return IfrOpHdrAddr, outXml

def ParseIfrStrings(HiiDbBinListBuff=0, StringHdrPtr=0, LogFile=0):
  HiiStringDict = {}
  Prompt = 1
  if(StringHdrPtr == 0):
    return HiiStringDict
  StringPkgSize = clb.ReadList(HiiDbBinListBuff, StringHdrPtr, 3)
  StringOffset = clb.ReadList(HiiDbBinListBuff, (StringHdrPtr+0x8), 4)
  CurrStringPtr = (StringHdrPtr + StringOffset)
  PrintLog('===========    Hii String Package Parsing Start = 0x%X    ==========|' %StringHdrPtr, LogFile)
  while(CurrStringPtr < (StringHdrPtr+StringPkgSize)):
    BlockType = clb.ReadList(HiiDbBinListBuff, (CurrStringPtr), 1)
    CurrStringPtr = CurrStringPtr + 1
    if(BlockType == EFI_HII_SIBT_END):  # end of string block?
      break
    elif(BlockType == EFI_HII_SIBT_STRING_SCSU):
      StrSize = 0
      String = ''
      while(1):
        ChrValue = clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)
        StrSize = StrSize + 1
        if(ChrValue):
          String = String + chr(ChrValue)
        else:
          break
      HiiStringDict[Prompt] = String.replace('<=', ' &lte; ').replace('>=', ' &gte; ').replace('&', 'n').replace('\"', '&quot;').replace('\'', '').replace('\x13', '').replace('\x19', '').replace('\xB5', 'u').replace('\xAE', '').replace('<', ' &lt; ').replace('>', ' &gt; ').replace('\r\n', ' ').replace('\n', ' ')
      Prompt = Prompt + 1
      CurrStringPtr = CurrStringPtr + StrSize
    elif(BlockType == EFI_HII_SIBT_STRING_UCS2):
      StrSize = 0
      String = ''
      while(1):
        ChrValue = clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)
        StrSize = StrSize + 2
        if(ChrValue):
          String = String + chr(ChrValue & 0xFF)
        else:
          break
      HiiStringDict[Prompt] = String.replace('<=', ' &lte; ').replace('>=', ' &gte; ').replace('&', 'n').replace('\"', '&quot;').replace('\'', '').replace('\x13', '').replace('\x19', '').replace('\xB5', 'u').replace('\xAE', '').replace('<', ' &lt; ').replace('>', ' &gt; ').replace('\r\n', ' ').replace('\n', ' ')
      Prompt = Prompt + 1
      CurrStringPtr = CurrStringPtr + StrSize
    elif(BlockType == EFI_HII_SIBT_STRING_SCSU_FONT):
      StrSize = 0
      String = ''
      CurrStringPtr = CurrStringPtr + 1
      while(clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)):
        StrSize = StrSize + 1
      CurrStringPtr = CurrStringPtr + StrSize + 1
    elif(BlockType == EFI_HII_SIBT_STRING_UCS2_FONT):
      StrSize = 0
      String = ''
      CurrStringPtr = CurrStringPtr + 1
      while(clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)):
        StrSize = StrSize + 2
      CurrStringPtr = CurrStringPtr + StrSize + 2
    elif(BlockType == EFI_HII_SIBT_SKIP1):
      Prompt = Prompt + clb.ReadList(HiiDbBinListBuff, CurrStringPtr, 1)
      CurrStringPtr = CurrStringPtr + 1
    elif(BlockType == EFI_HII_SIBT_SKIP2):
      Prompt = Prompt + clb.ReadList(HiiDbBinListBuff, CurrStringPtr, 2)
      CurrStringPtr = CurrStringPtr + 2
    elif(BlockType == EFI_HII_SIBT_DUPLICATE):
      CurrStringPtr = CurrStringPtr + 2
    elif(BlockType == EFI_HII_SIBT_EXT1):
      CurrStringPtr = CurrStringPtr + 1 + 1
    elif(BlockType == EFI_HII_SIBT_EXT2):
      CurrStringPtr = CurrStringPtr + 1 + 2
    elif(BlockType == EFI_HII_SIBT_EXT4):
      CurrStringPtr = CurrStringPtr + 1 + 4
    elif(BlockType == EFI_HII_SIBT_STRINGS_SCSU):
      StrSize = 0
      StrCount = clb.ReadList(HiiDbBinListBuff, CurrStringPtr, 2)
      CurrStringPtr = CurrStringPtr + 2
      CurStrCnt = 0
      while(CurStrCnt < StrCount):
        while(clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)):
          StrSize = StrSize + 1
        StrSize = StrSize + 1
        CurStrCnt = CurStrCnt + 1
      CurrStringPtr = CurrStringPtr + StrSize
    elif(BlockType == EFI_HII_SIBT_STRINGS_SCSU_FONT):
      StrSize = 0
      StrCount = clb.ReadList(HiiDbBinListBuff, CurrStringPtr+1, 2)
      CurrStringPtr = CurrStringPtr + 3
      CurStrCnt = 0
      while(CurStrCnt < StrCount):
        while(clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)):
          StrSize = StrSize + 1
        StrSize = StrSize + 1
        CurStrCnt = CurStrCnt + 1
      CurrStringPtr = CurrStringPtr + StrSize
    elif(BlockType == EFI_HII_SIBT_STRINGS_UCS2):
      StrSize = 0
      StrCount = clb.ReadList(HiiDbBinListBuff, CurrStringPtr, 2)
      CurrStringPtr = CurrStringPtr + 2
      CurStrCnt = 0
      while(CurStrCnt < StrCount):
        while(clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)):
          StrSize = StrSize + 2
        StrSize = StrSize + 2
        CurStrCnt = CurStrCnt + 1
      CurrStringPtr = CurrStringPtr + StrSize
    elif(BlockType == EFI_HII_SIBT_STRINGS_UCS2_FONT):
      StrSize = 0
      StrCount = clb.ReadList(HiiDbBinListBuff, CurrStringPtr+1, 2)
      CurrStringPtr = CurrStringPtr + 3
      CurStrCnt = 0
      while(CurStrCnt < StrCount):
        while(clb.ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)):
          StrSize = StrSize + 2
        StrSize = StrSize + 2
        CurStrCnt = CurStrCnt + 1
      CurrStringPtr = CurrStringPtr + StrSize
  PrintLog('===========    Hii String Package Parsing End = 0x%X    ==========|' %CurrStringPtr, LogFile)
  return HiiStringDict

def GenerateKnobsSection(BiosKnobDict, HiiStrDict, HiiUqiStrDict, NvRamFvListBuffer, NvramTblDict, outXmlList, AllXmlKnobs, LogFile=0):
  for VarCount in sorted(BiosKnobDict):
    for KnobOffset in sorted(BiosKnobDict[VarCount]['KnobDict']):
      if(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobPrsd'][0] == 0):
        continue  # Skip current Iteration, since current entry was not processed by IFR parser.
      CurSetupType = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['SetupTypeHii']
      CurSetupTypeStr = clb.SetupTypeHiiDict.get(CurSetupType, 'Unknown')
      if( CurSetupTypeStr == 'Unknown' ):
        continue  # don't publish unsupported Setup Type
      CurKnobName  = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobName']
      if(CurKnobName not in AllXmlKnobs):
        AllXmlKnobs.append(CurKnobName)
      else:
        continue
      nvram_knob_size = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobSzHii']
      xml_knob_size = nvram_knob_size
      CurDepex  = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Depex']
      IfrPrompt = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Prompt']
      IfrHelp = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Help']
      HiiDefVal = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['HiiDefVal']
      PromptList = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['ParentPromptList']
      SetupPgPtr = HiiStrDict.get(IfrPrompt, 'N.A.')
      for cnt in range(0, len(PromptList)):
        SetupPgPtr = HiiStrDict.get(PromptList[cnt], '???') + '/' + SetupPgPtr
      DefaultVal = HiiDefVal
      bit_offset = 0
      knob_offset_str = '0x%04X' %KnobOffset
      nvram_knob_offset = KnobOffset
      is_bitwise = False
      xml_knob_size = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobSzBin']
      nvram_knob_size = xml_knob_size
      if KnobOffset >= clb.BITWISE_KNOB_PREFIX:  # bitwise knob?
        is_bitwise = True
        knob_offset_str = '0x%05X' % KnobOffset
        nvram_knob_offset = int((KnobOffset & 0x3FFFF) / 8)
        bit_offset = ((KnobOffset & 0x3FFFF) % 8)
        nvram_knob_size = bit_offset + xml_knob_size
        if nvram_knob_size % 8:
          nvram_knob_size = int(nvram_knob_size/8 + 1)
        else:
          nvram_knob_size = int(nvram_knob_size/8)
      if len(NvramTblDict):
        try:  # Use the Default value from NVRAM FV or Default Data FFS or VPD Region (whichever is availaible and applicable), Default tagging in .hrf/.vfr will be EOL soon.
          if is_bitwise:
            DefaultVal = (clb.ReadList(NvRamFvListBuffer, (NvramTblDict[VarCount]['NvarDataBufPtr']+nvram_knob_offset), nvram_knob_size) >> bit_offset) & (clb.and_mask(nvram_knob_size) >> ((nvram_knob_size*8) - xml_knob_size))
          else:
            DefaultVal = clb.ReadList(NvRamFvListBuffer, (NvramTblDict[VarCount]['NvarDataBufPtr']+nvram_knob_offset), nvram_knob_size)
        except KeyError:
          pass
      CurrentVal = DefaultVal
      if not HiiUqiStrDict:
        outXmlList.append('\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" Nvar=\"%s\" prompt=\"%s\" description=\"%s\" size=\"%d\" offset=\"%s\" depex=\"%s\" SetupPgPtr = \"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\"' %(CurSetupTypeStr, CurKnobName, VarCount, BiosKnobDict[VarCount]['NvarName'], HiiStrDict.get(IfrPrompt, 'NotFound(0x%04X)' %IfrPrompt), HiiStrDict.get(IfrHelp, 'NotFound(0x%04X)' %IfrHelp), xml_knob_size, knob_offset_str, CurDepex, SetupPgPtr, (nvram_knob_size*2), DefaultVal, (nvram_knob_size*2), CurrentVal))
      else:
        outXmlList.append('\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" Nvar=\"%s\" prompt=\"%s\" description=\"%s\" UqiVal=\"%s\" size=\"%d\" offset=\"%s\" depex=\"%s\" SetupPgPtr = \"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\"' %(CurSetupTypeStr, CurKnobName, VarCount, BiosKnobDict[VarCount]['NvarName'], HiiStrDict.get(IfrPrompt, 'NotFound(0x%04X)' %IfrPrompt), HiiStrDict.get(IfrHelp, 'NotFound(0x%04X)' %IfrHelp), HiiUqiStrDict.get(IfrPrompt, ''), xml_knob_size, knob_offset_str, CurDepex, SetupPgPtr, (nvram_knob_size*2), DefaultVal, (nvram_knob_size*2), CurrentVal))
      if(CurSetupType == EFI_IFR_ONE_OF_OP):
        outXmlList.append('>\n')
        KnobInstances = len(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'])
        CurInst = 1
        for KnobPrsCnt in range (0, KnobInstances):
          PrintOptionList = False
          if( KnobInstances > 1 ):
            FoundInstance = 1
            if(KnobPrsCnt == 0):
              PrintOptionList = True
            else:
              for DupIndex in sorted(BiosKnobDict[VarCount]['DupKnobDict']):
                if(CurKnobName == BiosKnobDict[VarCount]['DupKnobDict'][DupIndex]['DupKnobName']):
                  if(KnobPrsCnt == FoundInstance):
                    PrintOptionList = True
                    CurDepex = BiosKnobDict[VarCount]['DupKnobDict'][DupIndex]['DupDepex']
                    CurInst = CurInst + 1
                    DupXmlKnobName = CurKnobName + '_inst_%d' %CurInst
                    if (HiiUqiStrDict == {}):
                      outXmlList.append('\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" Nvar=\"%s\" prompt=\"%s\" description=\"%s\" size=\"%d\" offset=\"%s\" depex=\"%s\" SetupPgPtr = \"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\">\n' %(CurSetupTypeStr, DupXmlKnobName, VarCount, BiosKnobDict[VarCount]['NvarName'], HiiStrDict.get(IfrPrompt, 'NotFound(0x%04X)' %IfrPrompt), HiiStrDict.get(IfrHelp, 'NotFound(0x%04X)' %IfrHelp), xml_knob_size, knob_offset_str, CurDepex, SetupPgPtr, (nvram_knob_size*2), DefaultVal, (nvram_knob_size*2), CurrentVal))
                    else:
                      outXmlList.append('\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" Nvar=\"%s\" prompt=\"%s\" description=\"%s\" UqiVal=\"%s\" size=\"%d\" offset=\"%s\" depex=\"%s\" SetupPgPtr = \"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\">\n' %(CurSetupTypeStr, DupXmlKnobName, VarCount, BiosKnobDict[VarCount]['NvarName'], HiiStrDict.get(IfrPrompt, 'NotFound(0x%04X)' %IfrPrompt), HiiStrDict.get(IfrHelp, 'NotFound(0x%04X)' %IfrHelp), HiiUqiStrDict.get(IfrPrompt, ''), xml_knob_size, knob_offset_str, CurDepex, SetupPgPtr, (nvram_knob_size*2), DefaultVal, (nvram_knob_size*2), CurrentVal))
                    break
                  FoundInstance = FoundInstance + 1
          else:
            PrintOptionList = True
          outXmlList.append('\t\t\t<options>\n')
          if (PrintOptionList):
            for OptionCount in sorted(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt]):
              OptionText = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt][OptionCount]['OptionText']
              outXmlList.append('\t\t\t\t<option text=\"%s\" value=\"0x%X\"/>\n' %(HiiStrDict.get(OptionText, 'NotFound(0x%04X)' %OptionText), BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt][OptionCount]['OptionVal']))
            outXmlList.append('\t\t\t</options>\n')
          outXmlList.append('\t\t</knob>\n')
      elif(CurSetupType == EFI_IFR_NUMERIC_OP):
        outXmlList.append(' min=\"0x%X\" max=\"0x%X\" step=\"%d\"/>\n' %(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Min'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Max'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Step']))
      elif(CurSetupType == EFI_IFR_STRING_OP):
        outXmlList.append(' minsize=\"0x%X\" maxsize=\"0x%X\"/>\n' %(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Min'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Max']))
      elif(CurSetupType == EFI_IFR_CHECKBOX_OP):
        outXmlList.append('/>\n')
      else:
        outXmlList.append('/>\n')

def FetchBiosId(BinaryFile, PcBiosId=False):
  FileExt = os.path.splitext(BinaryFile)[1][1:].lower()
  BiosIdString = 'Unknown'
  if (FileExt != 'ffs'):
    BiosIdFfsToSave  = [ gEfiBiosIdGuid, gCpPcBiosIdFileGuid ]
    DelTempFvFfsFiles(clb.TempFolder)
    with open(BinaryFile, 'rb') as BiosBinFile:
      BiosBinListBuff = list(BiosBinFile.read())
    FlashRegionInfo(BiosBinListBuff, False)
    if (FwIngredientDict['FlashDescpValid'] != 0):
      BiosRegionBase = FwIngredientDict['FlashRegions'][BIOS_Region]['BaseAddr']
      BiosEnd = FwIngredientDict['FlashRegions'][BIOS_Region]['EndAddr'] + 1
    else:
      BiosRegionBase = 0
      BiosEnd = len(BiosBinListBuff)
    if(len(BiosBinListBuff) != 0):
      ProcessBin(BiosBinListBuff, BiosRegionBase, BiosIdFfsToSave, 0, True, BiosRegionEnd=BiosEnd)
      BinaryFile = os.path.join(clb.TempFolder, '%X_File.ffs' %gEfiBiosIdGuid[0])
      if(not os.path.isfile(BinaryFile)):
        PcBiosId = True
        BinaryFile = os.path.join(clb.TempFolder, '%X_File.ffs' %gCpPcBiosIdFileGuid[0])

  if(os.path.isfile(BinaryFile)):
    with open(BinaryFile, 'rb') as BiosIdFile:
      BiosIdListBuff = list(BiosIdFile.read())
    FfsSize = clb.ReadList(BiosIdListBuff, 0x14, 3)
    BiosIdString = ''
    CharSz = 2
    CharStart = 0x24
    if(PcBiosId):
      CharSz = 1
      CharStart = 0x1C
    if (FfsSize < 0x100):
      for count in range (0, 100):
        ChrVal = clb.ReadList(BiosIdListBuff, (CharStart+(count*CharSz)), 1)
        if(ChrVal == 0):
          break
        BiosIdString = BiosIdString + chr(ChrVal)
    else:
      BiosIdString = 'Unknown'
  return BiosIdString

def ReplOneOfDefFlag(DbBinListBuffer, IfrOpHdrAddr, ReqValue):
  IfrOpcodeSize = (clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+1, 1) & 0x7F)
  CurIfrOpcode = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr, 1)
  while (CurIfrOpcode != EFI_IFR_END_OP):
    if(CurIfrOpcode == EFI_IFR_ONE_OF_OPTION_OP):
      OptionFlag = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+4, 1)
      OptionTextValSize = (OptionFlag & 0x0F)
      OneOfDefVal = 0
      NewOptionFlag = 0
      if(OptionTextValSize == EFI_IFR_TYPE_BOOLEAN):
        OneOfDefVal = int(clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 1) != 0)
      elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_8):
        OneOfDefVal = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 1)
      elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_16):
        OneOfDefVal = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 2)
      elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_32):
        OneOfDefVal = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 4)
      elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_64):
        OneOfDefVal = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 8)
      if(ReqValue == OneOfDefVal):
        NewOptionFlag = (OptionFlag|EFI_IFR_OPTION_DEFAULT | EFI_IFR_OPTION_DEFAULT_MFG)
      else:
        NewOptionFlag = (OptionFlag & (~(EFI_IFR_OPTION_DEFAULT | EFI_IFR_OPTION_DEFAULT_MFG) & 0xFF))
      WriteList(DbBinListBuffer, IfrOpHdrAddr+4, 1, NewOptionFlag)
    IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
    IfrOpcodeSize = (clb.ReadList(DbBinListBuffer, IfrOpHdrAddr+1, 1) & 0x7F)
    CurIfrOpcode = clb.ReadList(DbBinListBuffer, IfrOpHdrAddr, 1)

FileGuidListtoSave  = [ gNvRamFvGuid, gXmlCliSetupDriverGuid, gVtioDriverGuid, gDxePlatformFfsGuid, gGnrDxePlatformFfsGuid, gBiosKnobsDataBinGuid, gBiosKnobsCpxDataBinGuid, gSocketSetupDriverFfsGuid, gSvSetupDriverFfsGuid, gFpgaDriverFfsGuid, gEfiBiosIdGuid, gCpPcBiosIdFileGuid, gDefaultDataOptSizeFileGuid, gDefaultDataFileGuid, gDefaultDataCpxFileGuid, gVpdGuid, gClientSetupFfsGuid, gClientTestMenuSetupFfsGuid, gPcGenSetupDriverFfsGuid, gEmulationDriverFfsGuid, gClientUiApp1FfsGuid, gClientUiApp2FfsGuid, gMerlinXAppGuid ]
SetupDriverGuidList = [ gXmlCliSetupDriverGuid, gVtioDriverGuid, gDxePlatformFfsGuid, gGnrDxePlatformFfsGuid, gSocketSetupDriverFfsGuid, gSvSetupDriverFfsGuid, gFpgaDriverFfsGuid, gClientSetupFfsGuid, gClientTestMenuSetupFfsGuid , gPcGenSetupDriverFfsGuid, gEmulationDriverFfsGuid, gClientUiApp1FfsGuid, gClientUiApp2FfsGuid ]

def GetsetBiosKnobsFromBin(BiosBinaryFile=0, BiosOutSufix=0, Operation='genxml', XmlFilename=0, IniFile=0, UpdateHiiDbDef=False, BiosOut='', KnobsStrList=[], BuildType=0xFF, KnobsVerify=False):
  global FileGuidListDict, FileSystemSaveCount, FwpPrintEn, FwIngredientDict, PlatInfoMenuDone, MulSetupDrivers
  clb.LastErrorSig = 0x0000
  FileGuidListDict = {}
  KnobLis = []
  FileSystemSaveCount = 0
  LogFile = open(PrintLogFile, 'w')
  clb.OutBinFile = ''
  MulSetupDrivers = False
  DelTempFvFfsFiles(clb.TempFolder)

  BiosXmlCliVer = '?.?.?'
  with open(BiosBinaryFile, 'rb') as BiosBinFile:
    BiosBinListBuff = list(BiosBinFile.read())
  FetchFwIngrediantInfo(BiosBinListBuff, False)
  if (FwIngredientDict['FlashDescpValid'] != 0):
    BiosRegionBase = FwIngredientDict['FlashRegions'][BIOS_Region]['BaseAddr']
    BiosEnd = FwIngredientDict['FlashRegions'][BIOS_Region]['EndAddr'] + 1
  else:
    BiosRegionBase = 0
    BiosEnd = len(BiosBinListBuff)
  ProcessBin(BiosBinListBuff, BiosRegionBase, FileGuidListtoSave, LogFile, BiosRegionEnd=BiosEnd)
  BiosIDFile = os.path.join(clb.TempFolder, '%X_File.ffs' %gEfiBiosIdGuid[0])
  FoundPcBuild = False
  if(os.path.isfile(BiosIDFile)):
    BiosIdString = FetchBiosId(os.path.join(clb.TempFolder, '%X_File.ffs' %gEfiBiosIdGuid[0]))
  else:
    FoundPcBuild = True
    BiosIdString = FetchBiosId(os.path.join(clb.TempFolder, '%X_File.ffs' %gCpPcBiosIdFileGuid[0]), True)

  log.info(' Fetching Firmware Info from the given Bios Binary...')
  if (XmlFilename == 0):
    XmlFilename = os.path.join(clb.TempFolder, '%s_FwInfo.xml' %BiosIdString)
  file_content = '<SYSTEM>\n'
  '\t<PLATFORM NAME=\"Generated by XmlCli Ref. Scripts Version %d.%d.%d - xmlcli.UefiFwParser.py\"/>\n' %(clb.__version__.version[0], clb.__version__.version[1], clb.__version__.version[2])
  BiosIdLst = BiosIdString.split('.')
  BiosDate = BiosIdLst[len(BiosIdLst)-1]
  if(FoundPcBuild):
    file_content += '\t<BIOS VERSION=\"%s\" TSTAMP=\"%s.%s.%s at %s:%s Hrs\"/>\n' %(BiosIdString, BiosDate[0:2], BiosDate[2:4], BiosDate[4:8], BiosDate[8:10], BiosDate[10:12])
  else:
    file_content += '\t<BIOS VERSION=\"%s\" TSTAMP=\"%s.%s.%s at %s:%s Hrs\"/>\n' %(BiosIdString, BiosDate[2:4], BiosDate[4:6], '20'+BiosDate[0:2], BiosDate[6:8], BiosDate[8:10])
  file_content += '\t<GBT Version=\"3.0002\" TSTAMP=\"March 26 2013\" Type=\"Offline\" XmlCliVer=\"%s\" XmlCliType=\"Full\"/>\n' %BiosXmlCliVer

  if (FwIngredientDict['FlashDescpValid'] != 0):
    file_content += '\t<FlashRegions>\n'
    for Entry in sorted(FwIngredientDict['FlashRegions']):
      if(FwIngredientDict['FlashRegions'][Entry]['BaseAddr'] == FwIngredientDict['FlashRegions'][Entry]['EndAddr']):
        continue
      file_content += '\t\t<Region Name=\"%s\" Base=\"0x%08X\" End=\"0x%08X\"/>\n' %(FwIngredientDict['FlashRegions'][Entry]['Name'], FwIngredientDict['FlashRegions'][Entry]['BaseAddr'], FwIngredientDict['FlashRegions'][Entry]['EndAddr'])
    file_content += '\t</FlashRegions>\n'
    if(len(FwIngredientDict['ME']) != 0):
      file_content += '\t<ME Version=\"%s\" TSTAMP=\"%s\" Type=\"%s\"/>\n' %(FwIngredientDict['ME']['Version'], FwIngredientDict['ME']['Date'], FwIngredientDict['ME']['Type'])
  file_content += '\t<PchStrapsBlock FlashDescriptorValid=\"%d\">\n' %(FwIngredientDict['FlashDescpValid'])
  if (FwIngredientDict['FlashDescpValid'] != 0):
    for StrapNo in sorted(FwIngredientDict['PCH_STRAPS']):
      file_content += '\t\t<Strap Number=\"%02d\" Value=\"0x%08X\"/>\n' %(StrapNo, FwIngredientDict['PCH_STRAPS'][StrapNo])
  file_content += '\t</PchStrapsBlock>\n'

  file_content += '\t<FIT>\n'
  for Entry in sorted(FwIngredientDict['FIT']):
    if(FwIngredientDict['FIT'][Entry]['Type'] == FIT_TBL_ENTRY_TYPE_0):
      continue
    file_content += '\t\t<Entry Name=\"%s\" Type=\"%d\" Address=\"0x%X\" Size=\"0x%X\"/>\n' %(FwIngredientDict['FIT'][Entry]['Name'], FwIngredientDict['FIT'][Entry]['Type'], FwIngredientDict['FIT'][Entry]['Address'], FwIngredientDict['FIT'][Entry]['Size'])
  file_content += '\t</FIT>\n'
  if (FwIngredientDict['FlashDescpValid'] != 0):
    if(len(FwIngredientDict['ACM']) != 0):
      file_content += '\t<ACM Version=\"%s\" TSTAMP=\"%s\" Type=\"%s\" VendorId=\"0x%X\"/>\n' %(FwIngredientDict['ACM']['Version'], FwIngredientDict['ACM']['Date'], FwIngredientDict['ACM']['Type'], FwIngredientDict['ACM']['VendorId'])
  file_content += '\t<UcodeEntries>\n'
  for Entry in sorted(FwIngredientDict['Ucode']):
    file_content += '\t\t<Ucode CpuId=\"0x%X\" Version=\"0x%08X\" TSTAMP=\"%s\" Size=\"0x%X\"/>\n' %(FwIngredientDict['Ucode'][Entry]['CpuId'], FwIngredientDict['Ucode'][Entry]['Version'], FwIngredientDict['Ucode'][Entry]['Date'], FwIngredientDict['Ucode'][Entry]['UcodeSize'])
  file_content += '\t</UcodeEntries>\n'

  if(MulSetupDrivers):
    ForLoopCnt = 2
    log.info(' Found BIOS with Unified Binary Build (Build 0 & Build 1)...')
    if(BuildType != 0xFF):
      log.info(f' Request is to Process Build Type {BuildType:d} ')
  else:
    ForLoopCnt = 1
    BuildType = 0xFF
  BiosDictArray = {}
  BiosKnobDict = {}
  CreateOutFile = False
  BiosKnobsTag = 'biosknobs'
  BldType = None
  AllXmlKnobs = []
  for FvMainCopyCount in range (0, ForLoopCnt, 1):
    if(BuildType != 0xFF):
      if(BuildType != FvMainCopyCount):
        continue
    if(FvMainCopyCount == 0):
      BiosKnobsDataFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %gBiosKnobsDataBinGuid[0])
    else:
      BiosKnobsDataFileName = os.path.join(clb.TempFolder, '%X_Copy_File.ffs' %gBiosKnobsDataBinGuid[0])
      if (os.path.isfile(BiosKnobsDataFileName) == False):
        BiosKnobsDataFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %gBiosKnobsCpxDataBinGuid[0])
    if (os.path.isfile(BiosKnobsDataFileName)):
      BiosKnobDict = clb.BiosKnobsDataBinParser(BiosKnobsDataFileName, BiosIdString)
    else:
      LogFile.close()
      log.error('BiosKnobsDataBin not found in the binary, Aborting due to Error!')
      clb.LastErrorSig = 0xFE90  # BiosKnobsDataBin not found
      file_content += '</SYSTEM>\n'
      with open(XmlFilename,'w') as outXml:
        outXml.write(file_content)
      clb.SanitizeXml(XmlFilename)
      return 1
    NvRamFileName = os.path.join(clb.TempFolder, '%X_File.fv' %gNvRamFvGuid[0])
    with open(NvRamFileName, 'rb') as NvRamFile:
      NvRamFvListBuffer = list(NvRamFile.read())
    NvRamDefDataFileGuid = gNvRamFvGuid
    NvramTblDict = ParseNvram(NvRamFvListBuffer, BiosKnobDict, 0x48, LogFile)
    if(len(NvramTblDict) == 0):
      NvRamDefDataFileGuid = gDefaultDataOptSizeFileGuid
      NvRamFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %NvRamDefDataFileGuid[0])
      if (os.path.isfile(NvRamFileName) == False):
        NvRamDefDataFileGuid = gDefaultDataFileGuid
        NvRamFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %NvRamDefDataFileGuid[0])
      if (os.path.isfile(NvRamFileName) == False):
        NvRamDefDataFileGuid = gVpdGuid
      if( (NvRamDefDataFileGuid == gDefaultDataFileGuid) and (FvMainCopyCount == 1) ):
        NvRamDefDataFileGuid = gDefaultDataCpxFileGuid
      NvRamFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %NvRamDefDataFileGuid[0])
      if (os.path.isfile(NvRamFileName)):
        with open(NvRamFileName, 'rb') as NvRamFile:
          NvRamDefDataFileDict = {}
          NvRamFvListBuffer = list(NvRamFile.read())
        NvramTblDict = ParseNvram(NvRamFvListBuffer, BiosKnobDict, 0, LogFile)
    BiosDictArray[FvMainCopyCount] = {}
    KnobStartTag = False
    FrontPageForm = []
    outXmlList = []
    for count in range (0, len(SetupDriverGuidList)):
      if(FvMainCopyCount == 0):
        CurFfsFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %SetupDriverGuidList[count][0])
      else:
        CurFfsFileName = os.path.join(clb.TempFolder, '%X_Copy_File.ffs' %SetupDriverGuidList[count][0])
      if (os.path.isfile(CurFfsFileName) == False):
        continue  # didnt found this file, maybe unsupported driver for following binary
      BiosKnobDictNew = copy.deepcopy(BiosKnobDict)
      with open(CurFfsFileName, 'rb') as HiiDbBinFile:
        HiiDbBinListBuff = list(HiiDbBinFile.read())
      PrintLog('=============== Now Parsing %s binary ================|' %(os.path.join(clb.TempFolder, '%X_File.ffs' %SetupDriverGuidList[count][0])), LogFile)
      HiiPkgAddrDict = GetIfrFormsHdr(HiiDbBinListBuff)
      for FileCountId in FileGuidListDict:
        if(FileGuidListDict[FileCountId]['FileGuid'] == SetupDriverGuidList[count]):
          BiosFfsFvBase = FileGuidListDict[FileCountId]['BiosBinPointer']
          if(MulSetupDrivers and (FvMainCopyCount == 0)):
            pass
          else:
            break
      PlatInfoMenuDone = False
      StringHdrPtr = HiiPkgAddrDict['StrPkgHdr']
      HiiStrDict = ParseIfrStrings(HiiDbBinListBuff, StringHdrPtr, LogFile)
      HiiUqiStrDict = {}
      if(Parse_Print_Uqi):
        HiiUqiStrDict = ParseIfrStrings(HiiDbBinListBuff, HiiPkgAddrDict['UqiPkgHdr'], LogFile)
      for IfrFormPkgCount in range (0, (len(HiiPkgAddrDict['IfrList']))):
        IfrOpHdrAddr, file_content = ParseIfrForms(HiiDbBinListBuff, BiosKnobDictNew, HiiStrDict, HiiPkgAddrDict['IfrList'][IfrFormPkgCount], 0, BiosFfsFvBase, count, FrontPageForm, LogFile, file_content)
      PrintLog('======  Overall End of IFR parsing for Setup Driver count No: %d  ==============' %(count), LogFile)
      if(KnobStartTag == False):
        if(MulSetupDrivers):
          BldType='%d' %FvMainCopyCount
          outXmlList.append('\t<%s BuildType="%s">\n' %(BiosKnobsTag, BldType))
        else:
          BldType = None
          outXmlList.append('\t<%s>\n' %BiosKnobsTag)
        KnobStartTag = True
      GenerateKnobsSection(BiosKnobDictNew, HiiStrDict, HiiUqiStrDict, NvRamFvListBuffer, NvramTblDict, outXmlList, AllXmlKnobs, LogFile)
      BiosDictArray[FvMainCopyCount][count] = BiosKnobDictNew
    if(KnobStartTag):
      outXmlList.append('\t</%s>\n' %BiosKnobsTag)
    file_content += ''.join(outXmlList)
    if(FvMainCopyCount == (ForLoopCnt-1)):
      file_content += '</SYSTEM>\n'
      with open(XmlFilename,'w') as outXml:
        outXml.write(file_content)
      clb.SanitizeXml(XmlFilename)
      log.info(f' Fetching Firmware Info Done in {XmlFilename} ')
    if( (Operation == 'prog') or (Operation == 'readonly') ):
      tmpPrintSts = FwpPrintEn
      FwpPrintEn = True
      ProgBinfileName=os.path.join(clb.TempFolder, 'biosKnobsdata.bin')
      if(IniFile == 0):
        if(len(KnobsStrList) != 0):
          with open(clb.TmpKnobsIniFile, 'w') as IniFilePart:
            IniFilePart.write(
              ';-----------------------------------------------------------------\n'
              '; FID XmlCli contact: xmlcli@intel.com\n'
              '; XML Shared MailBox settings for XmlCli based setup\n'
              '; The name entry here should be identical as the name from the XML file (retain the case)\n'
              ';-----------------------------------------------------------------\n'
              '[BiosKnobs]\n'
              )
            for KnobString in KnobsStrList:
              IniFilePart.write('%s\n' %KnobString)
          IniFile = clb.TmpKnobsIniFile
        else:
          IniFile = configurations.BIOS_KNOBS_CONFIG
      if(MulSetupDrivers):
        KnobXmlFile = clb.KnobsXmlFile
        with open(KnobXmlFile,'w') as tmpFile:
          tmpFile.write(f'<SYSTEM>\n{"".join(outXmlList)}</SYSTEM>\n')
      else:
        KnobXmlFile = XmlFilename
      if(clb.FlexConCfgFile):
        prs.generate_bios_knobs_config(KnobXmlFile, IniFile, clb.TmpKnobsIniFile, build_type=BldType)
        IniFile = clb.TmpKnobsIniFile
      TmpBuff = prs.parse_cli_ini_xml(KnobXmlFile, IniFile, ProgBinfileName, build_type=BldType)
      if(len(TmpBuff) == 0):
        log.error('Aborting due to Error!')
        FwpPrintEn = tmpPrintSts
        DelTempFvFfsFiles(clb.TempFolder)
        FileGuidListDict = {}
        FileSystemSaveCount = 0
        LogFile.close()
        clb.LastErrorSig = 0xFE91  # GetsetBiosKnobsFromBin: Empty Input Knob List
        return 1
      with open(ProgBinfileName, 'rb') as ProgBinfile:
        KnobsProgListBuff = list(ProgBinfile.read())
      NvRamUpdateFlag = 0
      if(MulSetupDrivers):
        PrintLog(' see below for the results on Build %d...' %FvMainCopyCount, LogFile)
      else:
        PrintLog(' see below for the results..', LogFile)
      PrintLog('|--|-----|----------------------------------------|--|-----------|-----------|', LogFile)
      PrintLog('|VI|Ofset|                 Knob Name              |Sz|   DefVal  |   CurVal  |', LogFile)
      PrintLog('|--|-----|----------------------------------------|--|-----------|-----------|', LogFile)
      UnProcessedKnobs = []
      for DriverFilecount in range (0, len(SetupDriverGuidList)):
        CurFfsFileName = os.path.join(clb.TempFolder, '%X_File.ffs' %SetupDriverGuidList[DriverFilecount][0])
        if (os.path.isfile(CurFfsFileName) == False):
          continue  # didnt found this file, maybe unsupported driver for following binary

        if( (Operation == 'prog') or (Operation == 'readonly') ):
          if(len(KnobsProgListBuff) > 8):
            EntryCount = clb.ReadList(KnobsProgListBuff, 0, 4)
            KnobBinPtr = 0x4
            for Count in range (0, EntryCount):
              VarStore = clb.ReadList(KnobsProgListBuff, KnobBinPtr, 1)
              Offset = clb.ReadList(KnobsProgListBuff, KnobBinPtr+1, 2)
              KnobSize = clb.ReadList(KnobsProgListBuff, KnobBinPtr + 3, 1)
              NvramOffset = Offset
              is_bitwise = False
              if Offset & 0x8000:
                is_bitwise = True
                NvramOffset = Offset & 0x7FFF
                Offset = clb.BITWISE_KNOB_PREFIX + ((Offset & 0x7FFF) * 8) + (KnobSize & 0x7)
                BitOfst = KnobSize & 0x7
                BitSize = (KnobSize >> 3) & 0x1F
                BitEnd = BitOfst + BitSize
                if BitEnd % 8:
                  KnobSize = int(BitEnd / 8) + 1
                else:
                  KnobSize = int(BitEnd / 8)
              ReqValue = clb.ReadList(KnobsProgListBuff, KnobBinPtr+4, KnobSize)
              if (is_bitwise):
                ReqValue = ReqValue & (clb.and_mask(KnobSize) >> ((KnobSize * 8) - BitSize))
              if( (NvramOffset < BiosDictArray[FvMainCopyCount][DriverFilecount][VarStore]['HiiVarSize']) and (BiosDictArray[FvMainCopyCount][DriverFilecount][VarStore]['KnobDict'][Offset]['KnobPrsd'][2] == DriverFilecount) ):
                KnobName = BiosDictArray[FvMainCopyCount][DriverFilecount][VarStore]['KnobDict'][Offset]['KnobName']
                HiiDefVal = BiosDictArray[FvMainCopyCount][DriverFilecount][VarStore]['KnobDict'][Offset]['HiiDefVal']
                DefVal = HiiDefVal
                if(len(NvramTblDict)):
                  try:  # Use the Default value from NVRAM FV or Default Data FFS or VPD Region (whichever is availaible and applicable), Default tagging in .hrf/.vfr will be EOL soon.
                    DefVal = clb.ReadList(NvRamFvListBuffer, (NvramTblDict[VarStore]['NvarDataBufPtr']+NvramOffset), KnobSize)
                    if (is_bitwise):
                      DefVal = (DefVal >> BitOfst) & (clb.and_mask(KnobSize) >> ((KnobSize * 8) - BitSize))
                    CurValue = DefVal
                  except:
                    if(Operation == 'readonly'):
                      CurValue = HiiDefVal
                    else:
                      UnProcessedKnobs.append(KnobName)
                      KnobBinPtr = KnobBinPtr + 4 + KnobSize
                      continue
                else:
                  CurValue = HiiDefVal
                KnobLis.append({
                  "KnobName": KnobName,
                  "ReqValue": ReqValue,
                  "CurValue": CurValue,
                })

                if(Operation != 'readonly'):
                  if( (CurValue != ReqValue) and (len(NvramTblDict)) ):
                    WriteVal = ReqValue
                    if (is_bitwise):  # if BitWise read modify bit range and then write.
                      WriteVal = (ReqValue << BitOfst) | (
                          clb.ReadList(NvRamFvListBuffer, (NvramTblDict[VarStore]['NvarDataBufPtr'] + NvramOffset),
                                       KnobSize) & (
                            ~((clb.and_mask(KnobSize) >> ((KnobSize * 8) - BitSize)) << BitOfst)))
                    WriteList(NvRamFvListBuffer, (NvramTblDict[VarStore]['NvarDataBufPtr']+NvramOffset), KnobSize, WriteVal)
                    NvRamUpdateFlag = NvRamUpdateFlag + 1
                else:
                  ReqValue = CurValue
                if(is_bitwise):
                  PrintLog('|%2X|%5X|%40s|%2X| %8X  | %8X  |' % (VarStore, Offset, KnobName, BitSize, DefVal, ReqValue), LogFile)
                else:
                  PrintLog('|%2X|%4X|%40s|%2X| %8X  | %8X  |' %(VarStore, Offset, KnobName, KnobSize, DefVal, ReqValue), LogFile)
                PrintLog('|--|-----|----------------------------------------|--|-----------|-----------|', LogFile)
              KnobBinPtr = KnobBinPtr + 4 + KnobSize
            if( clb.ReadList(KnobsProgListBuff, KnobBinPtr, 4) != 0xE9D0FBF4):
              PrintLog('error parsing KnobsProgListBuff', LogFile)
      if (len(UnProcessedKnobs) != 0):
        PrintLog ('Following Knobs dont exist in Defaut Offline NVRAM Data, hence ignoring them..', LogFile)
        PrintLog ('\t [ %s ]' %', '.join(UnProcessedKnobs), LogFile)
      if(NvRamUpdateFlag != 0):
        for FileCountId in FileGuidListDict:
          if(FileGuidListDict[FileCountId]['FileGuid'] == NvRamDefDataFileGuid):
            BiosBinBase = FileGuidListDict[FileCountId]['BiosBinPointer']
            FileSystemSz = FileGuidListDict[FileCountId]['FileSystemSize']
            BiosBinListBuff[BiosBinBase: (BiosBinBase+FileSystemSz)] = NvRamFvListBuffer[0:FileSystemSz]
            break
        CreateOutFile = True
      FwpPrintEn = tmpPrintSts
  tmpPrintSts = FwpPrintEn
  FwpPrintEn = True
  if(CreateOutFile == False):
    PrintLog ('No Changes detected/applied', LogFile)
    if((Operation == 'prog') and ForceOutFile):
      PrintLog ('ForceOutFile variable enabled, Preparing to Copy the binary to out folder anyways', LogFile)
      CreateOutFile = True
  if(CreateOutFile):
    BiosFileName, BiosFileExt = os.path.splitext(os.path.basename(BiosBinaryFile))
    NewBiosFileName = BiosFileName.replace(BiosIdString, 'Found')
    if(NewBiosFileName == BiosFileName):
      NewBiosFileName = BiosFileName + '_' + BiosIdString
    else:
      NewBiosFileName = BiosFileName
    BiosOutFolder = clb.TempFolder
    ModBiosBinFileName = ''
    if(BiosOut != ''):
      if(os.path.lexists(BiosOut)):
        BiosOutFolder = BiosOut
      elif(os.path.isdir(os.path.dirname(BiosOut))):
        ModBiosBinFileName = BiosOut
    if(ModBiosBinFileName == ''):
      if(BiosOutSufix == 0):
        ModBiosBinFileName = os.path.join(BiosOutFolder, '%s_New%s' %(NewBiosFileName, BiosFileExt))
      else:
        ModBiosBinFileName = os.path.join(BiosOutFolder, '%s_%s%s' %(NewBiosFileName, BiosOutSufix, BiosFileExt))
    if(SecureProfileEditing):
      if(os.path.isfile(ReSigningFile)):
        TempRom = os.path.join(clb.TempFolder, 'TempBIOS.rom')
        with open(TempRom, 'wb') as TempRomFile:
          TempRomFile.write(bytearray(BiosBinListBuff[BiosRegionBase:BiosEnd]))
        TempBIOS_resign = os.path.join(clb.TempFolder, 'TempBIOS_resign.rom')
        if(os.path.isfile(TempBIOS_resign)):
          clb.RemoveFile(TempBIOS_resign)
        try:
          utils.system_call(cmd_lis=[ReSigningFile, TempRom, TempBIOS_resign])
        except:
          PrintLog ('Error Running the Re-signing process, Skip Re-signing..', LogFile)
        if(os.path.isfile(TempBIOS_resign)):
          with open(TempBIOS_resign, 'rb') as TempRomFile:
            BiosBinListBuff[BiosRegionBase:BiosEnd] = list(TempRomFile.read())
          PrintLog ('\n Resigning Process completed Successfully\n', LogFile)
        else:
          PrintLog ('OutFile not created by Re-signing process, please make sure correct re-signing Pkg and .bat is used\n  continue without re-signing...', LogFile)
      else:
        PrintLog ('SecureProfileEditing Set to True, but cli.fwp.ReSigningFile is empty, skipping the Re-signing process', LogFile)
    else:
      PrintLog ('SecureProfileEditing Set to False, Please note that the re-generated binary maynot boot with Secure Profile IFWI (Pls ignore this message if Server BIOS)', LogFile)
    clb.OutBinFile = ModBiosBinFileName
    with open(ModBiosBinFileName, 'wb') as ModBiosBinFile:
      ModBiosBinFile.write(bytearray(BiosBinListBuff))
    PrintLog ('Created New updated Bios File %s with desired knob settings' %ModBiosBinFileName, LogFile)
  FwpPrintEn = tmpPrintSts
  DelTempFvFfsFiles(clb.TempFolder)
  FileGuidListDict = {}
  FileSystemSaveCount = 0
  LogFile.close()
  ReturnVal = 0
  if KnobsVerify and Operation == 'readonly':
    VerifyErrCnt = 0
    for KnobCount in range (0, len(KnobLis)):
      if(KnobLis[KnobCount]['ReqValue'] != KnobLis[KnobCount]['CurValue']):
        VerifyErrCnt = VerifyErrCnt + 1
        log.result(
          f'Verify Fail: Knob = {KnobLis[KnobCount]["KnobName"]}  ExpectedVal = 0x{KnobLis[KnobCount]["ReqValue"]:X}    CurrVal = 0x{KnobLis[KnobCount]["CurValue"]:X} ')
    if (VerifyErrCnt == 0):
      log.result('Verify Passed!')
    else:
      log.result('Verify Failed!')
      ReturnVal = 1
      clb.LastErrorSig = 0xC42F  # XmlCli Knobs Verify Operation Failed
  return ReturnVal

FIT_TBL_ENTRY_TYPE_0               = 0
UCODE_ENTRY_TYPE_1                 = 1
ACM_ENTRY_TYPE_2                   = 2
START_UP_BIOS_MODULE_TYPE_ENTRY_7  = 7
TPM_POLICY_TYPE_8                  = 8
BIOS_POLICY_TYPE_9                 = 9
TXT_POLICY_TYPE_A                  = 0xA
KEY_MANIFEST_TYPE_B                = 0xB
BOOT_POLICY_TYPE_C                 = 0xC
BIOS_DATA_AREA_TYPE_D              = 0xD
UNUSED_ENTRY_TYPE_7F               = 0x7F
FITChkSum   = 0
FitDict     = {FIT_TBL_ENTRY_TYPE_0: 'FIT', UCODE_ENTRY_TYPE_1: 'Ucode', ACM_ENTRY_TYPE_2: 'ACM', START_UP_BIOS_MODULE_TYPE_ENTRY_7: 'Start Up Bios Module', TPM_POLICY_TYPE_8: 'TPM Policy', BIOS_POLICY_TYPE_9: 'Bios Policy', TXT_POLICY_TYPE_A: 'TXT Policy', KEY_MANIFEST_TYPE_B: 'Key Manifest', BOOT_POLICY_TYPE_C: 'Boot Policy', BIOS_DATA_AREA_TYPE_D: 'Bios Data', UNUSED_ENTRY_TYPE_7F: 'Unused'}
AcmTypeDict = {0x4: 'NPW', 0x8: 'Debug'}

def GetFitTableEntries(BiosBinListBuff):
  global FITChkSum, FwIngredientDict
  FwIngredientDict['FIT']={}
  FwIngredientDict['FitTablePtr'] = 0
  FitTableDict = {}
  if (BiosBinListBuff != 0):
    BinSize = len(BiosBinListBuff)
  else:
    BinSize = 0
  FitSig = 0
  FitTablePtr = int(clb.ReadBios(BiosBinListBuff, BinSize, 0xFFFFFFC0, 4))
  if (FitTablePtr >= 0xFF000000):
    FitSig = clb.ReadBios(BiosBinListBuff, BinSize, FitTablePtr, 8)
  if (FitSig == 0x2020205F5449465F): # '_FIT_   '
    FwIngredientDict['FitTablePtr'] = FitTablePtr & 0xFFFFFFF0  # Has to be 16 Byte aligned address
    Entries = clb.ReadBios(BiosBinListBuff, BinSize, FitTablePtr+8, 4) & 0xFFFFFF
    if(clb.ReadBios(BiosBinListBuff, BinSize, FitTablePtr+0x0E, 1) & 0x80):    # FIT Table Checksum bit Valid?
      CheckSum = clb.ReadBios(BiosBinListBuff, BinSize, (FitTablePtr+0x0F), 1)
      CurChkSum = 0
      for bytecount in range (0, ((Entries*16))):
        CurChkSum = (CurChkSum + clb.ReadBios(BiosBinListBuff, BinSize, (FitTablePtr+bytecount), 1)) & 0xFF
      FITChkSum = CurChkSum
      if(CurChkSum != 0):
        log.warning('FIT Table checksum (0x%X) is not valid, Table seems to be corrupted!' %(CheckSum))
        log.warning('Ignoring FIT Table checksum for now!')
      # return FitTableDict
    for  Count in range (0, Entries):
      EntryAddr = clb.ReadBios(BiosBinListBuff, BinSize, (FitTablePtr+(Count*0x10)), 8)
      Size = (clb.ReadBios(BiosBinListBuff, BinSize, FitTablePtr+(Count*0x10)+0x8, 4) & 0xFFFFFF)
      EntryType = (clb.ReadBios(BiosBinListBuff, BinSize, FitTablePtr+(Count*0x10)+0x0E, 1) & 0x7F)
      FitTableDict[Count] = {'Type': EntryType, 'Name': FitDict.get(EntryType, 'reserved') , 'Address': EntryAddr, 'Size': Size}
  FwIngredientDict['FIT'] = FitTableDict
  return FitTableDict

def FlashAcmInfo(UefiFwBinListBuff, PrintEn=True):
  global FwIngredientDict
  FwIngredientDict['ACM']={}
  BinSize = len(UefiFwBinListBuff)
  FitTableEntries = GetFitTableEntries(UefiFwBinListBuff)
  AcmBase = 0
  for count in FitTableEntries:
    if(FitTableEntries[count]['Type'] == ACM_ENTRY_TYPE_2):
      AcmBase = FitTableEntries[count].get('Address', 0)
      break
  if(AcmBase == 0):
    log.result('ACM Entry not Found in FIT Table!')
    return
  ACM_ModuleId = clb.ReadBios(UefiFwBinListBuff, BinSize, AcmBase+0x0C, 4)
  ACM_VendorId = clb.ReadBios(UefiFwBinListBuff, BinSize, AcmBase+0x10, 4)
  ACM_Bld_Date = clb.ReadBios(UefiFwBinListBuff, BinSize, AcmBase+0x14, 4)
  ACM_Bld_Date_Str = '%02X.%02X.%04X' %(((ACM_Bld_Date >> 8) & 0xFF), (ACM_Bld_Date & 0xFF), ((ACM_Bld_Date >> 16) & 0xFFFF))
  FwIngredientDict['ACM'] = {'VendorId': ACM_VendorId, 'ModuleId': ACM_ModuleId, 'Version': '??.??.??', 'Date': ACM_Bld_Date_Str, 'Type': AcmTypeDict.get(((ACM_ModuleId >> 28) & 0xFF), '???')}
  if PrintEn:
    log.info(
      f'ACM Module Id = 0x{ACM_ModuleId:X}  ACM Vendor Id = 0x{ACM_VendorId:X}  ACM Build Date = {ACM_Bld_Date_Str}')

def FlashRegionInfo(UefiFwBinListBuff, PrintEn=True):
  global FwIngredientDict
  clb.LastErrorSig = 0x0000
  FwIngredientDict['FlashRegions']={}
  FwIngredientDict['FlashDescpValid'] = 0
  DescBase = 0x00
  FlashValSig = clb.ReadList(UefiFwBinListBuff, (DescBase+0x10), 4)
  if(FlashValSig != 0x0FF0A55A):
    log.warning('Invalid Flash descriptor section!')
    FwIngredientDict['FlashDescpValid'] = 0
    clb.LastErrorSig = 0x1FD4  # FlashRegionInfo: Invalid Falsh descriptor section
    return 1
  FwIngredientDict['FlashDescpValid'] = 1
  FlashRegBaseOfst = (clb.ReadList(UefiFwBinListBuff, (DescBase+0x16), 1) << 4)
  NoOfRegions = ((clb.ReadList(UefiFwBinListBuff, (DescBase+0x17), 1) & 0x7) + 1)
  if(NoOfRegions < 10):
    NoOfRegions = 10    # temp patch, as some binaries dont have this set correctly.
  for region in range (0, NoOfRegions):
    RegBase  = (clb.ReadList(UefiFwBinListBuff, (DescBase+FlashRegBaseOfst+(region*4)+0), 2) & 0x7FFF)
    RegLimit = (clb.ReadList(UefiFwBinListBuff, (DescBase+FlashRegBaseOfst+(region*4)+2), 2) & 0x7FFF)
    if( (RegBase == 0x7FFF) and (RegLimit == 0) ):
      if PrintEn:
        log.info(f'Unused or Invalid Region ({region:d})')
      FwIngredientDict['FlashRegions'][region] = {'Name': FlashRegionDict[region], 'BaseAddr': 0xFFFFFFFF, 'EndAddr': 0xFFFFFFFF}
      continue
    FwIngredientDict['FlashRegions'][region] = {'Name': FlashRegionDict[region], 'BaseAddr': (RegBase << 12), 'EndAddr': ((RegLimit << 12) | 0xFFF)}
  if PrintEn:
    log.info('|--------|------------------|------------|------------|')
    log.info('| Region |   Region Name    |  BaseAddr  |  End Addr  |')
    log.info('|--------|------------------|------------|------------|')
    for FlashRegion in FwIngredientDict['FlashRegions']:
      log.info(
        f'|   {FlashRegion:d}    | {FlashRegionDict[FlashRegion]:<16} | 0x{FwIngredientDict["FlashRegions"][FlashRegion]["BaseAddr"]:<8X} | 0x{FwIngredientDict["FlashRegions"][FlashRegion]["EndAddr"]:<8X} |')
    log.info('|--------|------------------|------------|------------|')
  return 0

def GetMeInfo(UefiFwBinListBuff, PrintEn=True):
  global FwIngredientDict
  FwIngredientDict['ME']={}
  MeBase = FwIngredientDict['FlashRegions'][ME_Region]['BaseAddr']
  if((MeBase >= len(UefiFwBinListBuff)) or (MeBase == 0) ):
    return
  FPT_Sig = clb.ReadList(UefiFwBinListBuff, (MeBase+0x10), 4)
  FTPR_Sig = clb.ReadList(UefiFwBinListBuff, (MeBase+0x30), 4)
  if( (FPT_Sig == 0x54504624) and (FTPR_Sig == 0x52505446) ):    # compare with '$FPT' & 'FTPR'
    CodePartitionOfst = clb.ReadList(UefiFwBinListBuff, (MeBase+0x38), 4)
    CodePartitionPtr = MeBase + CodePartitionOfst
    CodePartitionSig1 = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr), 4)
    CodePartitionSig2 =clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+0x10), 8)
    if( (CodePartitionSig1 == 0x44504324) and (CodePartitionSig2 == 0x6e616d2e52505446) ):    # compare with '$CPD' & 'FTPR.man'
      FTPRmanOfst = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+0x1C), 4)
      ME_Bld_Date = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+FTPRmanOfst+0x14), 4)
      ME_Version = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+FTPRmanOfst+0x24), 8)
      MeBldDateStr = '%02X.%02X.%04X' %(((ME_Bld_Date >> 8) & 0xFF), (ME_Bld_Date & 0xFF), ((ME_Bld_Date >> 16) & 0xFFFF))
      MeVerStr = '%d.%d.%d.%d' %((ME_Version & 0xFFFF), ((ME_Version >> 16) & 0xFFFF), ((ME_Version >> 32) & 0xFFFF) , ((ME_Version >> 48)  & 0xFFFF))
      if PrintEn:
        log.info(f'ME Version = {MeVerStr}    ME Build Date = {MeBldDateStr} ')
      FwIngredientDict['ME']={'Version': MeVerStr, 'Type': '???', 'Date': MeBldDateStr}    # ME Type is tbd

def GetPchStrapsInfo(UefiFwBinListBuff):
  global FwIngredientDict
  clb.LastErrorSig = 0x0000
  FwIngredientDict['PCH_STRAPS']={}
  DescBase = 0x00
  FlashValSig = clb.ReadList(UefiFwBinListBuff, (DescBase+0x10), 4)
  if(FlashValSig != 0x0FF0A55A):
    log.warning('Invalid Falsh descriptor section!')
    clb.LastErrorSig = 0x1FD4  # FlashRegionInfo: Invalid Falsh descriptor section
    return 1
  PchStrapsBaseOfst = (clb.ReadList(UefiFwBinListBuff, (DescBase+0x1A), 1) << 4)
  NoOfPchStraps = clb.ReadList(UefiFwBinListBuff, (DescBase+0x1B), 1)
  for StrapNo in range (0, NoOfPchStraps):
    FwIngredientDict['PCH_STRAPS'][StrapNo] = clb.ReadList(UefiFwBinListBuff, (DescBase+PchStrapsBaseOfst+(StrapNo*4)), 4)

def FetchFwIngrediantInfo(FwBinListBuff, PrintEn=True):
  global FwIngredientDict
  FwIngredientDict = {}
  FwIngredientDict['FlashDescpValid'] = 0
  FwIngredientDict['FitTablePtr'] = 0
  FwIngredientDict['FlashRegions'] = {}
  FwIngredientDict['PCH_STRAPS'] = {}
  FwIngredientDict['ME'] = {}
  FwIngredientDict['FIT'] = {}
  FwIngredientDict['ACM'] = {}
  FwIngredientDict['Ucode'] = {}
  BiosBase = 0
  BiosLimit = len(FwBinListBuff)
  Status = FlashRegionInfo(FwBinListBuff, PrintEn)
  if(Status == 0):
    GetPchStrapsInfo(FwBinListBuff)
    GetMeInfo(FwBinListBuff, PrintEn)
    FlashAcmInfo(FwBinListBuff, PrintEn)
    BiosBase = FwIngredientDict['FlashRegions'][BIOS_Region]['BaseAddr']
    BiosLimit = FwIngredientDict['FlashRegions'][BIOS_Region]['EndAddr']
