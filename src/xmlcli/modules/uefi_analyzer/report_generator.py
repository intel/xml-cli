# coding=utf-8
"""
HTML Report Generator for UEFI Firmware Analysis
"""
import os
import json

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UEFI Firmware Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f1f5f9;
            --accent-color: #38bdf8;
            --secondary-color: #94a3b8;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--card-bg);
            padding-bottom: 20px;
        }
        h1 { margin: 0; font-weight: 700; color: var(--accent-color); }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .card h2 { margin-top: 0; font-size: 1.2rem; color: var(--secondary-color); }
        .stats {
            font-size: 2rem;
            font-weight: 800;
            margin: 10px 0;
        }
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #334155;
        }
        th { color: var(--secondary-color); font-weight: 600; }
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-success { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
        .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .badge-danger { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        
        .fv-item {
            margin-bottom: 20px;
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
        }
        .fv-header {
            padding: 15px 20px;
            background: rgba(255,255,255,0.03);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .fv-content {
            padding: 15px 20px;
        }
        .nested-item {
            margin-left: 20px;
            border-left: 1px solid #334155;
            padding-left: 10px;
            margin-top: 8px;
        }
        .item-header-wrapper {
            cursor: pointer;
            padding: 6px;
            border-radius: 8px;
            transition: background 0.2s;
        }
        .item-header-wrapper:hover { background: rgba(255,255,255,0.04); }
        .item-header {
            display: flex;
            align-items: center;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .item-header:hover { background: rgba(255,255,255,0.05); }
        .toggle-icon {
            width: 16px;
            height: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 5px;
            color: var(--secondary-color);
        }
        .tag {
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 8px;
            text-transform: uppercase;
        }
        .tag-compressed { background: #ea580c; color: #fff; }
        .tag-fv { background: #0284c7; color: #fff; }
        .tag-ffs { background: #4f46e5; color: #fff; }
        .tag-sec { background: #059669; color: #fff; }
        
        .controls {
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        input[type="text"] {
            background: var(--card-bg);
            border: 1px solid #334155;
            color: #fff;
            padding: 8px 12px;
            border-radius: 6px;
            flex-grow: 1;
        }
        .filter-btn {
            background: #334155;
            color: #fff;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
        }
        .filter-btn.active { background: var(--accent-color); color: var(--bg-color); font-weight: 600; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>UEFI Firmware Analysis Dashboard</h1>
            <div id="file-info"></div>
        </header>

        <div class="grid" id="summary-cards"></div>

        <div class="grid">
            <div class="card">
                <h2>Space Distribution by Type</h2>
                <div class="chart-container"><canvas id="typeChart"></canvas></div>
            </div>
            <div class="card">
                <h2>Free/Used Ratio</h2>
                <div class="chart-container"><canvas id="freeSpaceChart"></canvas></div>
            </div>
        </div>

        <div class="controls">
            <input type="text" id="search" placeholder="Search by GUID or Name...">
            <button id="toggle-deep" class="filter-btn">Deep Analysis (Compressed)</button>
        </div>

        <div id="fv-container"></div>
    </div>

    <script>
        const data = {{DATA_JSON}};
        let currentFile = Object.keys(data)[0];
        let showCompressedOnly = false;
        let deepAnalysis = false; // Toggle for logical/decompressed view

        function formatSize(bytes) {
            if (!bytes || bytes <= 0) return '0 B';
            const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            const index = Math.min(Math.max(0, i), sizes.length - 1);
            return parseFloat((bytes / Math.pow(k, index)).toFixed(2)) + ' ' + sizes[index];
        }

        function createSummaryCard(label, value, subtext = '') {
            return `<div class="card"><h2>${label}</h2><div class="stats">${value}</div>${subtext ? `<div style="color:var(--secondary-color); font-size:0.9rem;">${subtext}</div>` : ''}</div>`;
        }

        function createTreeItem(key, value, isCompressed = false, analysisData = null) {
            const isFv = key.includes('-FVI-');
            const isFfs = key.includes('-FFS-');
            const isSec = key.includes('-SEC-');
            
            const keyParts = key.split('-');
            const addrStr = keyParts[0];
            const size = keyParts.length >= 3 ? parseInt(keyParts[2], 16) : 0;
            const startAddr = parseInt(addrStr, 16);
            
            let rangeStr = '';
            if (!isNaN(startAddr) && size > 0) {
                rangeStr = ` <span style="color:var(--secondary-color); font-size:0.75rem;">(0x${startAddr.toString(16)} - 0x${(startAddr + size).toString(16)})</span>`;
            }
            
            let label = addrStr;
            let tags = '';
            let children = [];
            let usedSize = 0;
            
            const fileName = value.FileNameString || value.FileName;
            
            if (isFv) {
                tags += `<span class="tag tag-fv">FV</span>`;
                label = value.FvNameGuid || addrStr;
                if (fileName) label += ` [${fileName}]`;
                ['FFS1', 'FFS2', 'FFS3'].forEach(k => {
                    if (value[k]) Object.entries(value[k]).forEach(([ck, cv]) => {
                        const child = createTreeItem(ck, cv, isCompressed, analysisData);
                        children.push(child);
                        if (cv.Type !== "FV_FILETYPE_FFS_PAD") {
                            usedSize += (parseInt(ck.split('-')[2], 16) || 0);
                        }
                    });
                });
            } else if (isFfs) {
                tags += `<span class="tag tag-ffs">FFS</span>`;
                label = value.Name || addrStr;
                if (fileName) label += ` [${fileName}]`;
                if (value.section) Object.entries(value.section).forEach(([ck, cv]) => {
                    const child = createTreeItem(ck, cv, isCompressed, analysisData);
                    children.push(child);
                    usedSize += (parseInt(ck.split('-')[2], 16) || 0);
                });
            } else if (isSec) {
                tags += `<span class="tag tag-sec">SEC</span>`;
                label = value.SectionType || addrStr;
                if (fileName) label += ` [${fileName}]`;
                const innerCompressed = label.includes('EFI_SECTION_COMPRESSION');
                if (innerCompressed) tags += `<span class="tag tag-compressed">Compressed</span>`;
                if (value.encapsulation) Object.entries(value.encapsulation).forEach(([ck, cv]) => {
                    const child = createTreeItem(ck, cv, isCompressed || innerCompressed, analysisData);
                    children.push(child);
                    usedSize += (parseInt(ck.split('-')[2], 16) || 0);
                });
                if (value.FV) Object.entries(value.FV).forEach(([ck, cv]) => {
                    const child = createTreeItem(ck, cv, isCompressed || innerCompressed, analysisData);
                    children.push(child);
                    usedSize += (parseInt(ck.split('-')[2], 16) || 0);
                });
            } else {
                label = key;
                if (fileName) label += ` [${fileName}]`;
                if (typeof value === 'object' && value !== null) {
                    Object.entries(value).forEach(([ck, cv]) => children.push(createTreeItem(ck, cv, isCompressed, analysisData)));
                } else {
                    label = `${label}: <span style="color:var(--secondary-color)">${value}</span>`;
                }
            }

            const progress = size > 0 ? (usedSize / size * 100).toFixed(1) : 0;
            const isPad = value.Type === "FV_FILETYPE_FFS_PAD";

            if (showCompressedOnly && !isCompressed && !tags.includes('tag-compressed') && children.every(c => c.hidden)) {
                return { html: '', hidden: true };
            }

            const hasChildren = children.some(c => !c.hidden);
            const childrenHtml = children.map(c => c.html).join('');
            
            const html = `
                <div class="nested-item ${showCompressedOnly && !isCompressed && !tags.includes('tag-compressed') && !hasChildren ? 'hidden' : ''}">
                    <div class="item-header-wrapper" onclick="const c = this.nextElementSibling; if(c) { c.classList.toggle('hidden'); const t = this.querySelector('.toggle-icon'); if(t) t.innerText = c.classList.contains('hidden') ? '▶' : '▼'; }">
                        <div class="item-header">
                            <span class="toggle-icon">${hasChildren ? '▶' : '•'}</span>
                            <span style="color:var(--accent-color); font-weight:600;">${label}</span>
                            ${rangeStr}
                            ${tags}
                            ${size > 0 ? `<span style="margin-left:auto; color:var(--secondary-color); font-size:0.8rem;">${formatSize(size)}</span>` : ''}
                        </div>
                        ${size > 0 ? `
                        <div class="progress-bar" style="margin: 4px 0 8px 21px; height: 4px; background: rgba(255,255,255,0.05);">
                            <div class="progress-fill" style="width: ${progress}%; height: 100%; background: ${isPad ? '#475569' : 'var(--accent-color)'};"></div>
                        </div>` : ''}
                    </div>
                    <div class="children-container hidden">${childrenHtml}</div>
                </div>
            `;
            return { html, hidden: false, isCompressed: isCompressed || tags.includes('tag-compressed') };
        }

        function renderFile(fileName) {
            currentFile = fileName;
            const analysis = data[fileName];
            const summary = deepAnalysis ? analysis.summary.logical : analysis.summary.physical;
            const modeName = deepAnalysis ? "Logical (Decompressed)" : "Physical (Flash Area)";

            // Summary Cards
            const cards = document.getElementById('summary-cards');
            if (deepAnalysis) {
                cards.innerHTML = 
                    createSummaryCard('Total Logical Space', formatSize(summary.used_space + summary.free_space), `Expanded BIOS components`) +
                    createSummaryCard('Logical Used', formatSize(summary.used_space), `Sum of all files`) +
                    createSummaryCard('Logical Free', formatSize(summary.free_space), `Padding inside volumes`);
            } else {
                cards.innerHTML = 
                    createSummaryCard('Total Binary Size', formatSize(summary.total_size), `As specified in JSON source`) +
                    createSummaryCard('Flash Occupancy', formatSize(summary.used_space), `Total size of top-level FVs`) +
                    createSummaryCard('Unallocated Flash', formatSize(summary.free_space), `Space outside of any FV`);
            }

            renderCharts(summary);

            // FV Container
            const container = document.getElementById('fv-container');
            container.innerHTML = `<h2>First Layer View (${deepAnalysis ? 'All' : 'Physical'} FVs)</h2>`;
            
            const rawData = analysis.raw || {};
            const innerData = rawData.data || {};
            const rootKeys = analysis.root_fv_keys || [];
            
            // Render root FVs or fallback to raw JSON
            let foundBiosRecords = false;
            Object.entries(innerData).forEach(([key, value]) => {
                if (!key.includes('-FVI-')) return;
                if (!deepAnalysis && !rootKeys.includes(key)) return;
                
                foundBiosRecords = true;
                const fvItem = createTreeItem(key, value);
                const size = parseInt(key.split('-')[2], 16);
                const analyzedFv = analysis.fvs.find(f => `0x${f.address.toString(16).toLowerCase()}-FVI-0x${f.size.toString(16).toLowerCase()}` === key.toLowerCase());
                const progress = analyzedFv ? (analyzedFv.used_space / analyzedFv.size * 100).toFixed(1) : 0;
                
                const section = document.createElement('div');
                section.className = 'fv-item';
                section.innerHTML = `
                    <div class="fv-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
                        <div class="item-header-wrapper" style="width:100%">
                            <div class="item-header">
                                <span class="toggle-icon">▶</span>
                                <strong style="color:var(--accent-color)">${value.FvNameGuid || key.split('-')[0]}</strong>
                                <span class="tag tag-fv">FV</span>
                                <span style="margin-left:auto; color:var(--secondary-color); font-size:0.8rem;">${formatSize(size)}</span>
                            </div>
                            <div class="progress-bar" style="margin: 4px 0 0 21px; height: 6px; background: rgba(255,255,255,0.05);">
                                <div class="progress-fill" style="width: ${progress}%; height: 100%; background: var(--accent-color);"></div>
                            </div>
                        </div>
                    </div>
                    <div class="fv-content hidden">${fvItem.html}</div>
                `;
                container.appendChild(section);
            });

            // Fallback: If no BIOS-style FVI records found, show everything as Raw JSON tree
            if (!foundBiosRecords) {
                Object.entries(innerData).forEach(([key, value]) => {
                    const rawItem = createTreeItem(key, value);
                    const section = document.createElement('div');
                    section.className = 'fv-item';
                    section.innerHTML = `
                        <div class="fv-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
                            <div class="item-header-wrapper" style="width:100%">
                                <div class="item-header">
                                    <span class="toggle-icon">▶</span>
                                    <strong style="color:var(--accent-color)">${key}</strong>
                                </div>
                            </div>
                        </div>
                        <div class="fv-content hidden">${rawItem.html}</div>
                    `;
                    container.appendChild(section);
                });
            }
        }

        let typeChart, freeChart;
        function renderCharts(summary) {
            const typeCtx = document.getElementById('typeChart').getContext('2d');
            if (typeChart) typeChart.destroy();
            
            const labels = Object.keys(summary.space_by_type);
            const values = Object.values(summary.space_by_type);
            
            typeChart = new Chart(typeCtx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#38bdf8', '#818cf8', '#c084fc', '#fb7185', '#fb923c', '#fbbf24', '#4ade80'],
                        borderWidth: 0
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: { 
                        legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 10 } } 
                    } 
                }
            });

            const freeCtx = document.getElementById('freeSpaceChart').getContext('2d');
            if (freeChart) freeChart.destroy();
            freeChart = new Chart(freeCtx, {
                type: 'pie',
                data: {
                    labels: ['Used', 'Free'],
                    datasets: [{
                        data: [summary.used_space, summary.free_space],
                        backgroundColor: ['#38bdf8', '#1e293b'],
                        borderColor: '#334155'
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: { 
                        legend: { position: 'bottom', labels: { color: '#94a3b8' } } 
                    } 
                }
            });
        }

        document.getElementById('toggle-deep').onclick = function() {
            deepAnalysis = !deepAnalysis;
            this.classList.toggle('active');
            renderFile(currentFile);
            
            if (deepAnalysis) {
                // Auto-expand everything for deep analysis
                document.querySelectorAll('.children-container, .fv-content').forEach(el => el.classList.remove('hidden'));
                document.querySelectorAll('.toggle-icon').forEach(el => { 
                    if(el.innerText === '▶') el.innerText = '▼'; 
                });
            }
        };

        const searchInput = document.getElementById('search');
        searchInput.oninput = function(e) {
            const term = e.target.value.toLowerCase().trim();
            
            // If empty, reset everything
            if (!term) {
                document.querySelectorAll('.nested-item, .fv-item').forEach(el => {
                    el.classList.remove('hidden');
                    if (el.classList.contains('nested-item')) {
                        el.querySelector('.children-container').classList.add('hidden');
                        const toggle = el.querySelector('.toggle-icon');
                        if (toggle && toggle.innerText !== '•') toggle.innerText = '▶';
                    } else if (el.classList.contains('fv-item')) {
                        el.querySelector('.fv-content').classList.add('hidden');
                    }
                });
                return;
            }

            // Hide everything first
            document.querySelectorAll('.nested-item, .fv-item').forEach(el => el.classList.add('hidden'));

            // Find matches and expand parents
            const allNested = document.querySelectorAll('.nested-item');
            allNested.forEach(item => {
                const header = item.querySelector('.item-header');
                if (header && header.innerText.toLowerCase().includes(term)) {
                    // Show this item
                    item.classList.remove('hidden');
                    
                    // Reveal all ancestors
                    let parent = item.parentElement.closest('.nested-item');
                    while (parent) {
                        parent.classList.remove('hidden');
                        parent.querySelector('.children-container').classList.remove('hidden');
                        const toggle = parent.querySelector('.toggle-icon');
                        if (toggle && toggle.innerText !== '•') toggle.innerText = '▼';
                        parent = parent.parentElement.closest('.nested-item');
                    }
                    
                    // Reveal parent FV
                    let fvItem = item.closest('.fv-item');
                    if (fvItem) {
                        fvItem.classList.remove('hidden');
                        fvItem.querySelector('.fv-content').classList.remove('hidden');
                    }
                }
            });
        };

        function init() {
            const fileNames = Object.keys(data);
            if (fileNames.length === 0) return;
            const header = document.querySelector('header');
            if (fileNames.length > 1) {
                const select = document.createElement('select');
                select.className = 'filter-btn';
                fileNames.forEach(name => {
                    const opt = document.createElement('option');
                    opt.value = name; opt.text = name; select.appendChild(opt);
                });
                select.onchange = (e) => renderFile(e.target.value);
                header.appendChild(select);
            } else {
                const info = document.getElementById('file-info');
                info.innerText = fileNames[0];
                info.style.color = 'var(--secondary-color)';
            }
            renderFile(fileNames[0]);
        }
        init();
    </script>
</body>
</html>
"""

def generate_report(analysis_data, output_file):
    report_content = HTML_TEMPLATE.replace("{{DATA_JSON}}", json.dumps(analysis_data, ensure_ascii=False))
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    return output_file
