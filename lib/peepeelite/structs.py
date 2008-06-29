from ptypes import *

## miscellaneous exe structs
class IMAGE_DOS_HEADER(pStruct):
    _fields_ = [
        ( "<H", "e_magic"),
        ( "<H", "e_cblp"),
        ( "<H", "e_cp"),
        ( "<H", "e_crlc"),
        ( "<H", "e_cparhdr"),
        ( "<H", "e_minalloc"),
        ( "<H", "e_maxalloc"),
        ( "<H", "e_ss"),
        ( "<H", "e_sp"),
        ( "<H", "e_csum"),
        ( "<H", "e_ip"),
        ( "<H", "e_cs"),
        ( "<H", "e_lfarlc"),
        ( "<H", "e_ovno"),
        ( "LL", "e_res"),
        ( "<H", "e_oemid"),
        ( "<H", "e_oeminfo"),
        ( "LLLLL", "e_res2"),
        ( "<L", "e_lfanew")
    ]

class IMAGE_FILE_HEADER(pStruct):
    _fields_ = [
        ("<L", "Signature"),
        ("<H", "Machine"),
        ("<H", "NumberOfSections"),
        ("<L", "TimeDateStamp"),
        ("<L", "PointerToSymbolTable"),
        ("<L", "NumberOfSymbols"),
        ("<H", "SizeOfOptionalHeader"),
        ("<H", "Characteristics"),
    ]

class IMAGE_OPTIONAL_HEADER(pStruct):
    _fields_ = [
        ( "<H", "Magic" ),
        ( "<B", "MajorLinkerVersion" ),
        ( "<B", "MinorLinkerVersion" ),
        ( "<L", "SizeOfCode" ),
        ( "<L", "SizeOfInitializedData" ),
        ( "<L", "SizeOfUninitializedData" ),
        ( "<L", "AddressOfEntryPoint" ),
        ( "<L", "BaseOfCode" ),
        ( "<L", "BaseOfData" ),
        ( "<L", "ImageBase" ),
        ( "<L", "SectionAlignment" ),
        ( "<L", "FileAlignment" ),
        ( "<H", "MajorOperatingSystemVersion" ),
        ( "<H", "MinorOperatingSystemVersion" ),
        ( "<H", "MajorImageVersion" ),
        ( "<H", "MinorImageVersion" ),
        ( "<H", "MajorSubsystemVersion" ),
        ( "<H", "MinorSubsystemVersion" ),
        ( "<L", "Win32VersionValue" ),
        ( "<L", "SizeOfImage" ),
        ( "<L", "SizeOfHeaders" ),
        ( "<L", "CheckSum" ),
        ( "<H", "Subsystem" ),
        ( "<H", "DllCharacteristics" ),
        ( "<L", "SizeOfStackReserve" ),
        ( "<L", "SizeOfStackCommit" ),
        ( "<L", "SizeOfHeapReserve" ),
        ( "<L", "SizeOfHeapCommit" ),
        ( "<L", "LoaderFlags" ),
        ( "<L", "NumberOfRvaAndSizes" )
    ]

class IMAGE_DATA_DIRECTORY(pStruct):
    _fields_ = [
        ( "<L", "VirtualAddress" ),
        ( "<L", "Size" )
    ]

class IMAGE_SECTION_HEADER(pStruct):
    _fields_ = [
        ( "Q", "Name" ),
        ( "<L", 'VirtualSize' ),
        ( "<L", 'VirtualAddress' ),
        ( "<L", 'SizeOfRawData' ),
        ( "<L", 'PointerToRawData' ),
        ( "<L", 'PointerToRelocations' ),
        ( "<L", 'PointerToLinenumbers' ),
        ( "<H", 'NumberOfRelocations' ),
        ( "<H", 'NumberOfLinenumbers' ),
        ( "<L", 'Characteristics' )
    ]


class IMAGE_IMPORT_DIRECTORY_ENTRY(pStruct):
    _fields_ = [
        ( "<L", "INT" ),
        ( "<L", "TimeDateStamp" ),
        ( "<L", "ForwarderChain" ),
        ( "<L", "Name" ),
        ( "<L", "IAT" )
    ]

class IMAGE_EXPORT_DIRECTORY(pStruct):
    _fields_ = [
        ( "<L", "Flags" ),
        ( "<L", "TimeDateStamp" ),
        ( "<H", "MajorVersion" ),
        ( "<H", "MinorVersion" ),
        ( "<L", "Name" ),
        ( "<L", "Base" ),
        ( "<L", "NumberOfFunctions" ),
        ( "<L", "NumberOfNames" ),
        ( "<L", "AddressOfFunctions" ),
        ( "<L", "AddressOfNames" ),
        ( "<L", "AddressOfNameOrdinals" )
    ]

