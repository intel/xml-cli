# UEFI Firmware Analyzer

The UEFI Firmware Analyzer is a comprehensive tool within the `xml-cli` framework designed to parse, analyze, and visualize the structure and space utilization of UEFI firmware binaries.

## Features

- **Physical Flash Analysis**: Calculates space occupancy based on the actual flash layout (32MB/16MB/etc).
- **Deep Analysis Mode**: Visualizes decompressed components, providing a "logical" view of the firmware (often exceeding the physical size due to decompression).
- **Interactive Dashboard**: A self-contained HTML report with dynamic charts, progress bars for every level of hierarchy, and real-time search.
- **Smart Search**: Search by Driver Name, GUID, or `FileNameString`. Matching items are automatically expanded for easy discovery.
- **Address Mapping**: Displays absolute hexadecimal start and end address ranges for every component in the hierarchy.

## Quick Start

### 1. Command Line (Unified Flow)
You can analyze a **binary firmware** or an **existing JSON report** in one command:
```powershell
# Run the analysis (if installed in environment)
uefi-analyze "C:\path\to\bios.bin"
```
*Note: This generates the JSON, calculates metrics, and automatically opens your browser.*

### 2. Windows Context Menu
Analyze any `.bin`, `.rom`, `.fd`, or `.json` file directly from Windows Explorer:
1. **Install Menu**: Run `python src/xmlcli/modules/winContextMenu/install_context_menu.py`.
2. **Right-Click**: Select `XmlCli Menu` > `Analyze UEFI Firmware and View`.
3. **Result**: The tool detects the file type and opens the interactive dashboard immediately.

## Advanced Workflow

If you need to perform steps manually:

### Step 1: Parse the Binary to JSON
```python
from xmlcli.common.bios_fw_parser import UefiParser
parser = UefiParser(bin_file="path/to/bios.bin")
output_dict = parser.parse_binary()
parser.write_result_to_file("output.json", output_dict=output_dict)
```

### Step 2: Generate the Analysis Dashboard
```powershell
uefi-analyze "C:\path\to\output.json"
```

## Output Locations
Results (JSON and HTML) are saved to:
- `C:\Users\<user>\AppData\Local\Temp\XmlCliOut\logs\result\analytic_view\`
