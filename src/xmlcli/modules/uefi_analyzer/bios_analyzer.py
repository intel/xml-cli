# coding=utf-8
"""
BIOS Analyzer utility to calculate:
- Free Space (FV, FFS, Sections)
- Compression Ratio
- Comparing multiple JSON files
"""

import os
import json
from collections import OrderedDict

class BiosAnalyzer:
    def __init__(self, json_files=None):
        self.json_files = json_files or []
        self.analyzed_data = {}

    def load_json(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def analyze_all(self):
        for file_path in self.json_files:
            data = self.load_json(file_path)
            name = data.get("name", os.path.basename(file_path))
            # Analyze and also keep raw JSON for UI tree view
            analysis = self.analyze_data(data)
            analysis["raw"] = data  # store original JSON payload
            self.analyzed_data[name] = analysis
        return self.analyzed_data

    def analyze_data(self, data):
        """Analyze a full JSON payload.
        Separates Flash (Physical) and Logical (Decompressed) metrics.
        """
        inner_data = data.get("data", {})
        total_binary_size = data.get("size", 0) # Top level size (e.g. 32MB)
        
        # 1. Identify all nested FVs to exclude from physical summary
        nested_fv_keys = set()
        def find_nested_fvs(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k == "FV" and isinstance(v, dict):
                        nested_fv_keys.update(v.keys())
                    find_nested_fvs(v)
        find_nested_fvs(inner_data)

        # 2. Identify root-level FVs
        root_fv_entries = []
        for key, value in inner_data.items():
            if "-FVI-" in key and key not in nested_fv_keys:
                root_fv_entries.append((key, value))
        
        root_fv_entries.sort(key=lambda x: int(x[0].split('-')[0], 16))

        # 3. Calculate Physical Allocation
        # Sum of sizes of root FVs is "Total Used Space" in flash context
        root_fv_total_allocated = sum(int(k.split('-')[2], 16) for k, _ in root_fv_entries)
        physical_free = total_binary_size - root_fv_total_allocated if total_binary_size else 0

        # 4. Deep Analysis (Collect all FVs and Drivers)
        all_fv_analyses = {}
        def collect_fvs(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if "-FVI-" in k and k not in all_fv_analyses:
                        all_fv_analyses[k] = self.analyze_fv(k, v)
                    collect_fvs(v)
        collect_fvs(inner_data)

        # 5. Build Summaries
        logical_used = 0
        logical_free = 0
        logical_driver_counts = {}
        logical_space_by_type = {}
        
        # Breakdown of what's inside root FVs (for charts)
        physical_driver_counts = {}
        physical_space_by_type = {}

        # Physical: Based on root FVs
        for k, _ in root_fv_entries:
            if k in all_fv_analyses:
                info = all_fv_analyses[k]
                for t, s in info["space_by_type"].items():
                    physical_space_by_type[t] = physical_space_by_type.get(t, 0) + s
                for t, c in info["driver_counts"].items():
                    physical_driver_counts[t] = physical_driver_counts.get(t, 0) + c

        # Logical: Based on ALL FVs (including decompressed)
        for k, info in all_fv_analyses.items():
            logical_used += info["used_space"]
            logical_free += info["free_space"]
            for t, s in info["space_by_type"].items():
                logical_space_by_type[t] = logical_space_by_type.get(t, 0) + s
            for t, c in info["driver_counts"].items():
                logical_driver_counts[t] = logical_driver_counts.get(t, 0) + c

        analysis = {
            "total_size": total_binary_size,
            "fvs": [all_fv_analyses[k] for k in sorted(all_fv_analyses.keys())],
            "root_fv_keys": [k for k, _ in root_fv_entries],
            "summary": {
                "physical": {
                    "total_size": total_binary_size,
                    "used_space": root_fv_total_allocated,
                    "free_space": max(0, physical_free),
                    "driver_counts": physical_driver_counts,
                    "space_by_type": physical_space_by_type
                },
                "logical": {
                    "used_space": logical_used,
                    "free_space": logical_free,
                    "driver_counts": logical_driver_counts,
                    "space_by_type": logical_space_by_type
                }
            }
        }
        
        # Compatibility layers
        analysis["summary"]["total_used_space"] = root_fv_total_allocated
        analysis["summary"]["total_free_space"] = max(0, physical_free)
        
        return analysis

    def analyze_fv(self, fv_key, fv_data):
        # Key format: 0x<addr>-FVI-0x<size>
        parts = fv_key.split('-')
        addr = int(parts[0], 16)
        size = int(parts[2], 16)
        
        fv_info = {
            "address": addr,
            "size": size,
            "name": fv_data.get("FvNameGuid", "Unknown"),
            "ffs": [],
            "free_space": 0,
            "used_space": 0,
            "ffs_count": 0,
            "pad_file_space": 0,
            "space_by_type": {},
            "driver_counts": {},
            "compression_info": []
        }

        # Look for FFS entries
        for sub_key, sub_val in fv_data.items():
            if any(x in sub_key for x in ["FFS1", "FFS2", "FFS3"]):
                for ffs_key, ffs_val in sub_val.items():
                    ffs_info = self.analyze_ffs(ffs_key, ffs_val)
                    fv_info["ffs"].append(ffs_info)
                    
                    ffs_type = ffs_info["type"]
                    fv_info["space_by_type"][ffs_type] = fv_info["space_by_type"].get(ffs_type, 0) + ffs_info["size"]
                    fv_info["driver_counts"][ffs_type] = fv_info["driver_counts"].get(ffs_type, 0) + 1
                    
                    if ffs_type == "FV_FILETYPE_FFS_PAD":
                        fv_info["pad_file_space"] += ffs_info["size"]
                    else:
                        fv_info["used_space"] += ffs_info["size"]
                    
                    # Track compression
                    for sec in ffs_info["sections"]:
                        if sec["is_compressed"]:
                            fv_info["compression_info"].append({
                                "ffs_guid": ffs_info["guid"],
                                "compressed_size": sec["size"],
                                "uncompressed_size": sec["uncompressed_size"],
                                "ratio": sec["compression_ratio"]
                            })
        
        fv_info["ffs_count"] = len(fv_info["ffs"])
        # Free space = Total size - Used space (excluding Pad files which are technically free)
        fv_info["free_space"] = size - fv_info["used_space"]
        if fv_info["free_space"] < 0: fv_info["free_space"] = 0
        
        return fv_info

    def analyze_ffs(self, ffs_key, ffs_data):
        parts = ffs_key.split('-')
        size = int(parts[2], 16)
        
        ffs_info = {
            "size": size,
            "type": ffs_data.get("Type", "Unknown"),
            "guid": ffs_data.get("Name", "Unknown"),
            "sections": [],
            "compressed_sections": []
        }

        if "section" in ffs_data:
            for sec_key, sec_val in ffs_data["section"].items():
                sec_info = self.analyze_section(sec_key, sec_val)
                ffs_info["sections"].append(sec_info)
                if sec_info["is_compressed"]:
                    ffs_info["compressed_sections"].append(sec_info)
        
        return ffs_info

    def analyze_section(self, sec_key, sec_data):
        parts = sec_key.split('-')
        size = int(parts[2], 16)
        
        sec_info = {
            "size": size,
            "type": sec_data.get("SectionType", "Unknown"),
            "is_compressed": False,
            "uncompressed_size": size,
            "compression_ratio": 1.0,
            "sub_fvs": []
        }

        if sec_info["type"] == "EFI_SECTION_COMPRESSION":
            sec_info["is_compressed"] = True
            sec_info["uncompressed_size"] = sec_data.get("UncompressedLength", size)
            if size > 0:
                sec_info["compression_ratio"] = sec_info["uncompressed_size"] / size
        
        if "encapsulation" in sec_data:
            # Recursively analyze encapsulated sections
            for enc_key, enc_val in sec_data["encapsulation"].items():
                enc_info = self.analyze_section(enc_key, enc_val)
                # If any encapsulated section is compressed, bubble it up or handle it
                if enc_info["is_compressed"]:
                    sec_info["is_compressed"] = True
                    sec_info["uncompressed_size"] = enc_info["uncompressed_size"]
                    sec_info["compression_ratio"] = enc_info["compression_ratio"]

        if "FV" in sec_data:
            for fv_key, fv_val in sec_data["FV"].items():
                fv_info = self.analyze_fv(fv_key, fv_val)
                sec_info["sub_fvs"].append(fv_info)

        return sec_info

    def compare(self, name1, name2):
        if name1 not in self.analyzed_data or name2 not in self.analyzed_data:
            return {"error": "Files not analyzed"}
        
        data1 = self.analyzed_data[name1]
        data2 = self.analyzed_data[name2]
        
        comparison = {
            "name1": name1,
            "name2": name2,
            "fv_diff": []
        }
        
        fvs1 = {fv["name"]: fv for fv in data1["fvs"]}
        fvs2 = {fv["name"]: fv for fv in data2["fvs"]}
        
        all_fv_names = set(fvs1.keys()) | set(fvs2.keys())
        
        for fv_name in all_fv_names:
            fv1 = fvs1.get(fv_name)
            fv2 = fvs2.get(fv_name)
            
            diff = {
                "name": fv_name,
                "size_diff": (fv2["size"] - fv1["size"]) if fv1 and fv2 else None,
                "free_space_diff": (fv2["free_space"] - fv1["free_space"]) if fv1 and fv2 else None,
                "used_space_diff": (fv2["used_space"] - fv1["used_space"]) if fv1 and fv2 else None,
                "status": "changed" if fv1 and fv2 else ("added" if fv2 else "removed")
            }
            comparison["fv_diff"].append(diff)
            
        return comparison

    def save_analysis(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for name, data in self.analyzed_data.items():
            output_file = os.path.join(output_dir, f"{name}_analysis.json")
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
        
        # Save comparison if multiple files
        if len(self.analyzed_data) >= 2:
            names = list(self.analyzed_data.keys())
            for i in range(len(names)):
                for j in range(i+1, len(names)):
                    comp = self.compare(names[i], names[j])
                    comp_file = os.path.join(output_dir, f"compare_{names[i]}_vs_{names[j]}.json")
                    with open(comp_file, 'w') as f:
                        json.dump(comp, f, indent=4)
