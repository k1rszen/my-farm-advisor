import pandas as pd
import json

DATA_FILE = '/workspaces/my-farm-advisor/data/workspace/output/assignment-06/weather_top5_2020_2024.csv'
OUTPUT_DIR = '/workspaces/my-farm-advisor/data/workspace/output/assignment-06'

def celsius_to_fahrenheit(c):
    """Convert Celsius to Fahrenheit"""
    return (c * 9/5) + 32

def load_and_process_data():
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    
    fields = sorted(df['field_id'].unique())
    years = sorted([int(y) for y in df['year'].unique()])
    
    data_by_field = {}
    
    for field in fields:
        data_by_field[field] = {}
        
        for year in years:
            year_data = df[(df['field_id'] == field) & (df['year'] == year)].sort_values('date')
            
            # Calculate cumulative precipitation
            year_data = year_data.copy()
            year_data['cumul_precip'] = year_data['PRECTOTCORR'].cumsum()
            
            # Calculate GDD cumulative within year
            year_data['gdd_cumul'] = year_data['gdd'].cumsum()
            
            data_by_field[field][year] = []
            
            for _, row in year_data.iterrows():
                data_by_field[field][year].append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'doy': int(row['doy']),
                    'month': int(row['month']),
                    'temp': round(celsius_to_fahrenheit(float(row['T2M']))),  # Convert to F
                    'temp_max': round(celsius_to_fahrenheit(float(row['T2M_MAX']))),
                    'temp_min': round(celsius_to_fahrenheit(float(row['T2M_MIN']))),
                    'precip': round(float(row['PRECTOTCORR']), 1),
                    'cumul_precip': round(float(row['cumul_precip']), 1),
                    'gdd': round(float(row['gdd']), 1),
                    'gdd_cumul': round(float(row['gdd_cumul']), 1),
                    'solar': round(float(row['ALLSKY_SFC_SW_DWN']), 1)
                })
    
    return data_by_field, fields, years

def create_html(data_by_field, fields, years):
    data_json = json.dumps(data_by_field)
    fields_json = json.dumps(fields)
    years_json = json.dumps(years)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Weather Trends Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 15px;
            background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%);
            min-height: 100vh;
        }}
        
        .container {{ max-width: 950px; margin: 0 auto; }}
        
        header {{ text-align: center; margin-bottom: 15px; }}
        
        h1 {{ color: white; font-size: 1.6rem; margin-bottom: 4px; }}
        
        .subtitle {{ color: rgba(255,255,255,0.8); font-size: 0.9rem; }}
        
        .controls {{
            display: flex; justify-content: center; gap: 15px;
            margin-bottom: 15px; flex-wrap: wrap;
        }}
        
        .control-group {{
            display: flex; align-items: center; gap: 8px;
        }}
        
        .control-group label {{
            color: white; font-weight: 600; font-size: 0.85rem;
        }}
        
        select {{
            padding: 8px 12px;
            font-size: 0.85rem;
            border: none;
            border-radius: 5px;
            background: white;
            color: #333;
            cursor: pointer;
            min-width: 160px;
        }}
        
        .data-note {{
            background: #fff3cd;
            padding: 8px 12px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 0 auto 15px;
            max-width: 600px;
            font-size: 0.8rem;
            color: #856404;
        }}
        
        .chart-panel {{
            display: none;
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        }}
        
        .chart-panel.active {{ display: block; }}
        
        .chart-row {{
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        .chart-row:last-child {{
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }}
        
        .chart-header {{
            display: flex; justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .chart-title {{
            font-size: 1rem; color: #333; font-weight: 600;
        }}
        
        .chart-subtitle {{
            font-size: 0.75rem; color: #666;
        }}
        
        .chart-container {{
            position: relative;
            height: 150px;
            padding: 0 45px 0 55px;
        }}
        
        .x-axis {{
            position: absolute;
            bottom: 0;
            left: 55px;
            right: 45px;
            height: 20px;
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: #666;
        }}
        
        .y-axis {{
            position: absolute;
            left: 0;
            top: 0;
            bottom: 20px;
            width: 50px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            font-size: 9px;
            color: #000;
            text-align: right;
            padding-right: 5px;
        }}
        
        .chart-area {{
            position: relative;
            z-index: 2;
            height: 100%;
        }}
        
        canvas {{
            width: 100%; height: 100%;
        }}
        
        .legend {{
            display: flex; justify-content: center; gap: 15px;
            margin-top: 8px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex; align-items: center; gap: 5px;
            font-size: 0.75rem;
        }}
        
        .legend-color {{
            width: 15px; height: 3px;
            border-radius: 2px;
        }}
        
        .tooltip {{
            position: fixed;
            background: #2c3e50;
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 11px;
            pointer-events: none;
            z-index: 1000;
            display: none;
            white-space: nowrap;
        }}
        
        .tooltip.visible {{ display: block; }}
        
        .note {{
            background: #e8f4f8;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
            margin-top: 15px;
            color: #2c5c72;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Weather Trends Dashboard</h1>
            <p class="subtitle">Daily weather indicators by field and year</p>
        </header>
        
        <div class="data-note">
            <strong>Note:</strong> osm-1305439648 and osm-1386621285 have identical weather data. These fields are located very close to each other (~8km apart), resulting in the same weather observations from NASA POWER.
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label>Field:</label>
                <select id="fieldSelect" onchange="showData()">
'''
    
    for f in fields:
        html += f'\n                    <option value="{f}">{f}</option>'
    
    html += f'''
                </select>
            </div>
            
            <div class="control-group">
                <label>Year:</label>
                <select id="yearSelect" onchange="showData()">
'''
    
    for y in years:
        html += f'\n                    <option value="{y}">{y}</option>'
    
    html += f'''
                </select>
            </div>
        </div>
'''
    
    # Create panels for each field/year combination
    for f in fields:
        for y in years:
            panel_id = f"{f}-{y}"
            html += f'''
        <div id="panel-{panel_id}" class="chart-panel">
            <div class="chart-header">
                <div>
                    <div class="chart-title">{f}</div>
                    <div class="chart-subtitle">{y} Weather Data</div>
                </div>
            </div>
            
            <!-- Temperature Row -->
            <div class="chart-row">
                <div class="chart-header">
                    <div class="chart-title">Temperature (°F)</div>
                </div>
                <div class="chart-container">
                    <div class="y-axis" id="y-temp-{panel_id}"></div>
                    <div class="chart-area">
                        <canvas id="canvas-temp-{panel_id}"></canvas>
                    </div>
                    <div class="x-axis">
                        <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
                    </div>
                </div>
            </div>
            
            <!-- Daily Precipitation Row -->
            <div class="chart-row">
                <div class="chart-header">
                    <div class="chart-title">Daily Precipitation (mm)</div>
                </div>
                <div class="chart-container">
                    <div class="y-axis" id="y-precip-{panel_id}"></div>
                    <div class="chart-area">
                        <canvas id="canvas-precip-{panel_id}"></canvas>
                    </div>
                    <div class="x-axis">
                        <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
                    </div>
                </div>
            </div>
            
            <!-- Cumulative Precipitation Row -->
            <div class="chart-row">
                <div class="chart-header">
                    <div class="chart-title">Cumulative Precipitation (mm)</div>
                </div>
                <div class="chart-container">
                    <div class="y-axis" id="y-cumul-{panel_id}"></div>
                    <div class="chart-area">
                        <canvas id="canvas-cumul-{panel_id}"></canvas>
                    </div>
                    <div class="x-axis">
                        <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
                    </div>
                </div>
            </div>
            
            <!-- GDD Row -->
            <div class="chart-row">
                <div class="chart-header">
                    <div class="chart-title">Growing Degree Days (GDD) - Cumulative</div>
                </div>
                <div class="chart-container">
                    <div class="y-axis" id="y-gdd-{panel_id}"></div>
                    <div class="chart-area">
                        <canvas id="canvas-gdd-{panel_id}"></canvas>
                    </div>
                    <div class="x-axis">
                        <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
                    </div>
                </div>
            </div>
            
            <!-- Solar Row -->
            <div class="chart-row">
                <div class="chart-header">
                    <div class="chart-title">Solar Radiation (W/m²)</div>
                </div>
                <div class="chart-container">
                    <div class="y-axis" id="y-solar-{panel_id}"></div>
                    <div class="chart-area">
                        <canvas id="canvas-solar-{panel_id}"></canvas>
                    </div>
                    <div class="x-axis">
                        <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
                    </div>
                </div>
            </div>
            
            <div class="note">
                <strong>Note:</strong> Hover over charts to see daily values. Use dropdowns to select field and year.
            </div>
        </div>'''
    
    html += f'''
    </div>
    
    <div id="tooltip" class="tooltip"></div>
    
    <script>
        const weatherData = {data_json};
        const fields = {fields_json};
        const years = {years_json};
        const tooltip = document.getElementById('tooltip');
        
        // Global scales for axes
        const globalScales = {{}};
        
        // First pass: calculate year-specific max for GDD
        fields.forEach(f => {{
            globalScales[f] = {{}};
            years.forEach(y => {{
                if (weatherData[f] && weatherData[f][y]) {{
                    const data = weatherData[f][y];
                    const maxGdd = Math.max(...data.map(d => d.gdd_cumul));
                    globalScales[f][y] = {{ maxGdd }};
                }}
            }});
        }});
        
        // Global max values for other metrics
        const allTemps = [], allPrecip = [], allCumulPrecip = [], allSolar = [];
        
        fields.forEach(f => {{
            years.forEach(y => {{
                if (weatherData[f] && weatherData[f][y]) {{
                    weatherData[f][y].forEach(d => {{
                        allTemps.push(d.temp);
                        allPrecip.push(d.precip);
                        allCumulPrecip.push(d.cumul_precip);
                        allSolar.push(d.solar);
                    }});
                }}
            }});
        }});
        
        const maxTemp = Math.max(...allTemps);
        const maxPrecip = Math.max(...allPrecip);
        const maxCumulPrecip = Math.max(...allCumulPrecip);
        const maxSolar = Math.max(...allSolar);
        
        function showData() {{
            const field = document.getElementById('fieldSelect').value;
            const year = document.getElementById('yearSelect').value;
            const panelId = field + '-' + year;
            
            document.querySelectorAll('.chart-panel').forEach(p => p.classList.remove('active'));
            document.getElementById('panel-' + panelId).classList.add('active');
            
            drawChart(field, year, panelId);
        }}
        
        function drawChart(field, year, panelId) {{
            const data = weatherData[field][year];
            if (!data) return;
            
            const dayCount = data.length;
            
            // Temperature (Fahrenheit)
            drawLineChart('canvas-temp-' + panelId, data, 'temp', maxTemp + 32, '#e74c3c', 'y-temp-' + panelId, '°F');
            
            // Daily Precipitation
            drawBarChart('canvas-precip-' + panelId, data, 'precip', maxPrecip, 'y-precip-' + panelId, 'mm');
            
            // Cumulative Precipitation
            drawLineChart('canvas-cumul-' + panelId, data, 'cumul_precip', maxCumulPrecip, '#27ae60', 'y-cumul-' + panelId, 'mm');
            
            // GDD - use year-specific max
            const yearMaxGdd = globalScales[field][year] ? globalScales[field][year].maxGdd : maxCumulPrecip;
            drawLineChart('canvas-gdd-' + panelId, data, 'gdd_cumul', yearMaxGdd, '#27ae60', 'y-gdd-' + panelId, '');
            
            // Solar
            drawLineChart('canvas-solar-' + panelId, data, 'solar', maxSolar, '#f39c12', 'y-solar-' + panelId, ' W/m²');
        }}
        
        function drawLineChart(canvasId, data, dataKey, maxVal, color, yAxisId, unit) {{
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext('2d');
            
            const rect = canvas.parentElement.getBoundingClientRect();
            canvas.width = rect.width * 2;
            canvas.height = rect.height * 2;
            ctx.scale(2, 2);
            
            const width = rect.width;
            const height = rect.height;
            const chartHeight = height - 20;
            const chartWidth = width;
            
            // Update y-axis
            if (yAxisId) {{
                const yAxis = document.getElementById(yAxisId);
                const topVal = formatNum(maxVal) + unit;
                const midVal = formatNum(maxVal/2) + unit;
                yAxis.innerHTML = '<span>' + topVal + '</span><span>' + midVal + '</span><span>0' + unit + '</span>';
            }}
            
            ctx.clearRect(0, 0, width, height);
            
            // Draw grid
            ctx.strokeStyle = '#eee';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 4; i++) {{
                const y = chartHeight * i / 4;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }}
            
            // Draw line
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            data.forEach((d, i) => {{
                const x = (i / data.length) * chartWidth;
                const y = chartHeight - (d[dataKey] / maxVal) * chartHeight;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }});
            ctx.stroke();
            
            canvas.chartData = data;
            canvas.dataKey = dataKey;
        }}
        
        function drawBarChart(canvasId, data, dataKey, maxVal, yAxisId, unit) {{
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext('2d');
            
            const rect = canvas.parentElement.getBoundingClientRect();
            canvas.width = rect.width * 2;
            canvas.height = rect.height * 2;
            ctx.scale(2, 2);
            
            const width = rect.width;
            const height = rect.height;
            const chartHeight = height - 20;
            const chartWidth = width;
            
            // Update y-axis
            if (yAxisId) {{
                const yAxis = document.getElementById(yAxisId);
                const topVal = formatNum(maxVal) + unit;
                const midVal = formatNum(maxVal/2) + unit;
                yAxis.innerHTML = '<span>' + topVal + '</span><span>' + midVal + '</span><span>0' + unit + '</span>';
            }}
            
            ctx.clearRect(0, 0, width, height);
            
            // Draw grid
            ctx.strokeStyle = '#eee';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 4; i++) {{
                const y = chartHeight * i / 4;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }}
            
            // Draw bars (blue)
            ctx.fillStyle = 'rgba(52, 152, 219, 0.6)';
            data.forEach((d, i) => {{
                const x = (i / data.length) * chartWidth;
                const barWidth = chartWidth / data.length * 0.8;
                const barHeight = (d[dataKey] / maxVal) * chartHeight;
                ctx.fillRect(x - barWidth/2, chartHeight - barHeight, barWidth, barHeight);
            }});
            
            canvas.chartData = data;
            canvas.dataKey = dataKey;
        }}
        
        function formatNum(n) {{
            return Math.round(n).toLocaleString();
        }}
        
        // Initial show
        showData();
        
        // Add hover tracking
        document.querySelectorAll('canvas').forEach(canvas => {{
            canvas.addEventListener('mousemove', (e) => {{
                if (!canvas.chartData) return;
                
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const idx = Math.floor((x / rect.width) * canvas.chartData.length);
                const d = canvas.chartData[idx];
                
                if (d) {{
                    tooltip.innerHTML = '<strong>' + d.date + '</strong><br>' +
                        'Temp: ' + d.temp + '°F<br>' +
                        'Precip: ' + d.precip + 'mm<br>' +
                        'Cumul Precip: ' + d.cumul_precip + 'mm<br>' +
                        'GDD: ' + d.gdd_cumul + '<br>' +
                        'Solar: ' + d.solar + ' W/m²';
                    tooltip.style.left = (e.clientX + 15) + 'px';
                    tooltip.style.top = (e.clientY + 15) + 'px';
                    tooltip.classList.add('visible');
                }}
            }});
            
            canvas.addEventListener('mouseleave', () => {{
                tooltip.classList.remove('visible');
            }});
        }});
    </script>
</body>
</html>'''
    
    return html

def main():
    print("Loading weather data...")
    print("Processing data...")
    data_by_field, fields, years = load_and_process_data()
    
    print(f"Found {len(fields)} fields, {len(years)} years")
    
    print("Creating HTML...")
    html = create_html(data_by_field, fields, years)
    
    with open(f'{OUTPUT_DIR}/weather_trends.html', 'w') as f:
        f.write(html)
    
    print(f"\\nDone! Created: {OUTPUT_DIR}/weather_trends.html")

if __name__ == '__main__':
    main()