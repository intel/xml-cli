# coding=utf-8
"""
Unified CLI for UEFI Firmware Analysis
Takes a binary as input, parses it, analyzes it, and opens the dashboard.
"""
import os
import sys
import webbrowser
import tempfile
import argparse
from xmlcli.common import bios_fw_parser
from xmlcli.modules.uefi_analyzer import bios_analyzer
from xmlcli.modules.uefi_analyzer import report_generator

def analyze_binary(bin_file, output_dir=None, open_browser=True):
    bin_file = os.path.abspath(bin_file)
    if not os.path.exists(bin_file):
        print(f"Error: File not found: {bin_file}")
        return None

    is_json = bin_file.lower().endswith('.json')

    if output_dir is None:
        if is_json:
            output_dir = os.path.dirname(bin_file)
        else:
            output_dir = os.path.join(tempfile.gettempdir(), "XmlCliOut", "logs", "result", "analytic_view")
    
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    json_path = bin_file
    if not is_json:
        print(f"--- Step 1: Parsing Binary {os.path.basename(bin_file)} ---")
        # Ensure we don't accidentally double-parse if given a JSON
        uefi_parser = bios_fw_parser.UefiParser(bin_file=bin_file, clean=False)
        output_dict = uefi_parser.parse_binary()
        output_dict = uefi_parser.sort_output_fv(output_dict)
        
        # Use filename without doubling .json
        base_name = os.path.splitext(os.path.basename(bin_file))[0]
        json_path = os.path.abspath(os.path.join(output_dir, f"{base_name}.json"))
        
        # Ensure directory exists again just in case
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Writing JSON result to: {json_path}")
        uefi_parser.write_result_to_file(json_path, output_dict=output_dict)
        print(f"JSON saved successfully.")
    else:
        print(f"--- Step 1: Using provided JSON {os.path.basename(bin_file)} ---")

    print(f"--- Step 2: Analyzing Structure ---")
    analyzer = bios_analyzer.BiosAnalyzer([json_path])
    analysis_results = analyzer.analyze_all()
    # Save the analysis summary next to our JSON
    analyzer.save_analysis(output_dir)

    print(f"--- Step 3: Generating Dashboard ---")
    report_file = os.path.abspath(os.path.join(output_dir, "dashboard.html"))
    report_generator.generate_report(analysis_results, report_file)
    
    print(f"\nAnalysis complete!")
    print(f"HTML Dashboard: {report_file}")
    
    if open_browser:
        print("Opening dashboard in browser...")
        webbrowser.open(f"file:///{report_file}")
    
    return report_file

def main():
    parser = argparse.ArgumentParser(description="UEFI Firmware Analysis Tool")
    parser.add_argument("binary", help="Path to UEFI firmware binary (.bin, .rom, .fd)")
    parser.add_argument("--output-dir", help="Optional output directory")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    
    args = parser.parse_args()
    analyze_binary(args.binary, output_dir=args.output_dir, open_browser=not args.no_browser)

if __name__ == "__main__":
    main()
