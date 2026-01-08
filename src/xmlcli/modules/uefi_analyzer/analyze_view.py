# coding=utf-8
"""
Entry point for BIOS Analysis and View Generation
"""
import os
import sys
import argparse
import tempfile
from xmlcli.modules.uefi_analyzer import bios_analyzer
from xmlcli.modules.uefi_analyzer import report_generator
from xmlcli.common import configurations

def main():
    parser = argparse.ArgumentParser(description="BIOS Analysis View Generator")
    parser.add_argument("json_files", nargs="+", help="JSON files produced by UefiParser")
    parser.add_argument("--output-dir", help="Directory to store analysis results")
    args = parser.parse_args()

    # Determine output directory
    # User requested temp workspace in LOG_FILE_LOCATION as directory result analytic_view
    # Based on configurations.py and logger.py, we can construct this.
    
    log_dir = os.path.join(configurations.OUT_DIR, "logs")
    default_output_dir = os.path.join(log_dir, "result", "analytic_view")
    
    # Also consider the temp workspace as requested
    temp_workspace = os.path.join(tempfile.gettempdir(), "XmlCliOut", "logs", "result", "analytic_view")
    
    output_dir = args.output_dir or temp_workspace
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Analyzing {len(args.json_files)} files...")
    analyzer = bios_analyzer.BiosAnalyzer(args.json_files)
    analysis_results = analyzer.analyze_all()
    
    # Save the raw analysis JSONs
    analyzer.save_analysis(output_dir)
    
    # Generate the HTML dashboard
    report_file = os.path.join(output_dir, "dashboard.html")
    report_generator.generate_report(analysis_results, report_file)
    
    print(f"Analysis complete.")
    print(f"Results saved to: {output_dir}")
    print(f"Dashboard available at: {report_file}")

if __name__ == "__main__":
    main()
