import { readFileSync, writeFileSync } from "node:fs";

const csvPath = "data/workspace/output/assignment-06/weather_top5_2020_2024.csv";
const outputCsvPath = "data/workspace/output/assignment-06/weather_top5_with_rolling_avg.csv";
const outputHtmlPath = "data/workspace/output/assignment-06/temperature_rolling_avg.html";
const outputPrecipCsvPath = "data/workspace/output/assignment-06/weather_top5_with_precip_rolling_avg.csv";
const outputPrecipHtmlPath = "data/workspace/output/assignment-06/precipitation_rolling_avg.html";

const csv = readFileSync(csvPath, "utf-8");
const lines = csv.trim().split("\n");
const header = lines[0].split(",");

const rows: Record<string, string | number>[] = [];
for (let i = 1; i < lines.length; i++) {
  const values = lines[i].split(",");
  const row: Record<string, string | number> = {};
  header.forEach((h, idx) => {
    const val = values[idx];
    if (h === "field_id" || h === "growing_season" || h === "date") {
      row[h] = val;
    } else {
      row[h] = parseFloat(val);
    }
  });
  rows.push(row);
}

const fieldIds = [...new Set(rows.map(r => String(r.field_id)))];
console.log("Fields:", fieldIds);

const WINDOW = 30;
const enrichedRows: Record<string, string | number>[] = [];
const precipEnrichedRows: Record<string, string | number>[] = [];

for (const fieldId of fieldIds) {
  const fieldRows = rows
    .filter(r => r.field_id === fieldId)
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));

  for (let i = 0; i < fieldRows.length; i++) {
    const current = { ...fieldRows[i] };
    const precipCurrent = { ...fieldRows[i] };
    
    if (i >= WINDOW - 1) {
      let t2mSum = 0;
      let precipSum = 0;
      for (let j = i - WINDOW + 1; j <= i; j++) {
        t2mSum += fieldRows[j].T2M as number;
        precipSum += fieldRows[j].PRECTOTCORR as number;
      }
      current.T2M_30d_avg = t2mSum / WINDOW;
      precipCurrent.PRECTOTCORR_30d_avg = precipSum / WINDOW;
    }
    enrichedRows.push(current);
    precipEnrichedRows.push(precipCurrent);
  }
}

enrichedRows.sort((a, b) => String(a.date).localeCompare(String(b.date)));
precipEnrichedRows.sort((a, b) => String(a.date).localeCompare(String(b.date)));

const newHeader = header.concat("T2M_30d_avg").join(",");
const newLines = enrichedRows.map(r => {
  const values = header.map(h => {
    const v = r[h];
    return v === undefined ? "" : v;
  });
  const rollingAvg = r.T2M_30d_avg;
  values.push(rollingAvg === undefined ? "" : rollingAvg.toString());
  return values.join(",");
});

writeFileSync(outputCsvPath, [newHeader, ...newLines].join("\n"));
console.log("Saved CSV with rolling averages to:", outputCsvPath);

const precipHeader = header.concat("PRECTOTCORR_30d_avg").join(",");
const precipLines = precipEnrichedRows.map(r => {
  const values = header.map(h => {
    const v = r[h];
    return v === undefined ? "" : v;
  });
  const rollingAvg = r.PRECTOTCORR_30d_avg;
  values.push(rollingAvg === undefined ? "" : rollingAvg.toString());
  return values.join(",");
});

writeFileSync(outputPrecipCsvPath, [precipHeader, ...precipLines].join("\n"));
console.log("Saved CSV with precipitation rolling averages to:", outputPrecipCsvPath);

const fieldColors: Record<string, string> = {
  "osm-260949778": "#2563eb",
  "osm-813157720": "#dc2626",
  "osm-1153259427": "#16a34a",
  "osm-1305439648": "#9333ea",
  "osm-1386621285": "#ea580c",
};

const dateSet = new Set<string>();
rows.forEach(r => dateSet.add(r.date as string));
const allDates = [...dateSet].sort();

const fieldDataMap = new Map<string, Record<string, { raw: (string | null)[]; rolling: (string | null)[] }>>();
const precipFieldDataMap = new Map<string, Record<string, { raw: (string | null)[]; rolling: (string | null)[] }>>();

for (const fieldId of fieldIds) {
  const fieldRows = rows.filter(r => r.field_id === fieldId);
  const enrichedFieldRows = enrichedRows.filter(r => r.field_id === fieldId);
  const precipEnrichedFieldRows = precipEnrichedRows.filter(r => r.field_id === fieldId);
  
  const rawMap = new Map<string, number>();
  const rollingMap = new Map<string, number | null>();
  const precipRawMap = new Map<string, number>();
  const precipRollingMap = new Map<string, number | null>();
  
  fieldRows.forEach(r => rawMap.set(r.date as string, r.T2M as number));
  enrichedFieldRows.forEach(r => rollingMap.set(r.date as string, r.T2M_30d_avg as number | null));
  fieldRows.forEach(r => precipRawMap.set(r.date as string, r.PRECTOTCORR as number));
  precipEnrichedFieldRows.forEach(r => precipRollingMap.set(r.date as string, r.PRECTOTCORR_30d_avg as number | null));
  
  const data: { raw: (string | null)[]; rolling: (string | null)[] } = { raw: [], rolling: [] };
  const precipData: { raw: (string | null)[]; rolling: (string | null)[] } = { raw: [], rolling: [] };
  for (const d of allDates) {
    data.raw.push(rawMap.has(d) ? (rawMap.get(d) as number).toFixed(2) : null);
    data.rolling.push(rollingMap.has(d) ? (rollingMap.get(d) as number)?.toFixed(2) ?? null : null);
    precipData.raw.push(precipRawMap.has(d) ? (precipRawMap.get(d) as number).toFixed(2) : null);
    precipData.rolling.push(precipRollingMap.has(d) ? (precipRollingMap.get(d) as number)?.toFixed(2) ?? null : null);
  }
  fieldDataMap.set(fieldId, data);
  precipFieldDataMap.set(fieldId, precipData);
}

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Temperature Rolling Average - 5 Fields</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
  <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.2.0"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f5; }
    .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    h1 { font-size: 24px; margin-bottom: 8px; color: #1f2937; }
    .subtitle { color: #6b7280; margin-bottom: 24px; }
    .chart-container { position: relative; height: 500px; }
    .legend-custom { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 16px; justify-content: center; }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; }
    .legend-swatch { width: 24px; height: 3px; border-radius: 2px; }
    .legend-swatch.raw { height: 1px; opacity: 0.6; }
    .legend-swatch.rolling { height: 3px; }
    .controls { margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    .controls-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
    .controls-label { font-size: 13px; font-weight: 500; }
    .field-toggles { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }
    .field-toggle { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
    .field-toggle input { cursor: pointer; }
    .color-dot { width: 12px; height: 12px; border-radius: 50%; }
    button { padding: 8px 16px; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer; font-size: 13px; }
    button:hover { background: #f3f4f6; }
    button.active { background: #2563eb; color: white; border-color: #2563eb; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Temperature Time Series with 30-Day Rolling Average</h1>
    <p class="subtitle">Daily temperature (T2M) and 30-day rolling average for 5 fields (2020-2024)</p>
    
    <div class="controls">
      <button id="btnZoomReset" onclick="resetZoom()">Reset Zoom</button>
    </div>
    
    <div class="controls-row">
      <span class="controls-label">Show Fields:</span>
      <div class="field-toggles" id="fieldToggles"></div>
      <div style="margin-left: auto; display: flex; gap: 8px;">
        <button onclick="selectAll()">Select All</button>
        <button onclick="clearAll()">Clear All</button>
      </div>
    </div>
    
    <div class="chart-container">
      <canvas id="tempChart"></canvas>
    </div>
    
    <div class="legend-custom" id="legendCustom"></div>
  </div>

  <script>
    const fieldIds = ${JSON.stringify(fieldIds)};
    const allDates = ${JSON.stringify(allDates)};
    const colors = ${JSON.stringify(fieldColors)};
    const fieldData = ${JSON.stringify(Object.fromEntries(fieldDataMap))};
    
    const dateObjects = allDates.map(d => new Date(d));
    const timestamps = dateObjects.map(d => d.getTime());
    
    const datasets = [];
    const legendCustom = document.getElementById('legendCustom');
    const fieldToggles = document.getElementById('fieldToggles');
    const fieldDatasetIndices = {};
    
    fieldIds.forEach((fieldId, fieldIdx) => {
      const color = colors[fieldId] || '#666';
      const dataObj = fieldData[fieldId];
      const rawIdx = datasets.length;
      const rollingIdx = datasets.length + 1;
      fieldDatasetIndices[fieldIdx] = { raw: rawIdx, rolling: rollingIdx };
      
      datasets.push({
        label: fieldId + ' (daily)',
        data: dataObj.raw.map((y, i) => y === null ? null : parseFloat(y)).map((y, i) => y === null ? null : { x: timestamps[i], y }),
        borderColor: color,
        borderWidth: 1,
        pointRadius: 0,
        tension: 0,
        fill: false,
        order: 2,
        spanGaps: false
      });
      
      datasets.push({
        label: fieldId + ' (30d avg)',
        data: dataObj.rolling.map((y, i) => y === null ? null : parseFloat(y)).map((y, i) => y === null ? null : { x: timestamps[i], y }),
        borderColor: color,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.1,
        fill: false,
        order: 1,
        spanGaps: false
      });
      
      const toggle = document.createElement('label');
      toggle.className = 'field-toggle';
      toggle.innerHTML = '<input type="checkbox" checked data-field-idx="' + fieldIdx + '"><span class="color-dot" style="background:' + color + '"></span><span>' + fieldId + '</span>';
      fieldToggles.appendChild(toggle);
      
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = '<span class="legend-swatch raw" style="background:' + color + '"></span><span class="legend-swatch rolling" style="background:' + color + '"></span><span>' + fieldId + '</span>';
      legendCustom.appendChild(item);
    });
    
    document.querySelectorAll('.field-toggle input').forEach(cb => {
      cb.addEventListener('change', (e) => {
        const fieldIdx = parseInt(e.target.dataset.fieldIdx);
        const indices = fieldDatasetIndices[fieldIdx];
        chart.setDatasetVisibility(indices.raw, e.target.checked);
        chart.setDatasetVisibility(indices.rolling, e.target.checked);
        chart.update();
      });
    });
    
    const config = {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'nearest', axis: 'x', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => new Date(items[0].parsed.x).toLocaleDateString(),
              label: (ctx) => ctx.dataset.label + ': ' + (ctx.parsed.y?.toFixed(1) ?? 'N/A') + ' °C'
            }
          },
          zoom: {
            pan: { enabled: true, mode: 'x' },
            zoom: {
              wheel: { enabled: true },
              pinch: { enabled: true },
              mode: 'x'
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: { unit: 'month', displayFormats: { month: 'MMM yyyy' } },
            title: { display: true, text: 'Date' },
            grid: { color: '#f3f4f6' }
          },
          y: {
            title: { display: true, text: 'Temperature (°C)' },
            grid: { color: '#f3f4f6' }
          }
        }
      }
    };
    
    const chart = new Chart(document.getElementById('tempChart'), config);
    
    function resetZoom() {
      chart.resetZoom();
    }
    
    function selectAll() {
      document.querySelectorAll('.field-toggle input').forEach((cb, i) => {
        cb.checked = true;
        const indices = fieldDatasetIndices[i];
        chart.setDatasetVisibility(indices.raw, true);
        chart.setDatasetVisibility(indices.rolling, true);
      });
      chart.update();
    }
    
    function clearAll() {
      document.querySelectorAll('.field-toggle input').forEach((cb, i) => {
        cb.checked = false;
        const indices = fieldDatasetIndices[i];
        chart.setDatasetVisibility(indices.raw, false);
        chart.setDatasetVisibility(indices.rolling, false);
      });
      chart.update();
    }
  </script>
</body>
</html>`;

writeFileSync(outputHtmlPath, html);
console.log("Saved HTML chart to:", outputHtmlPath);

const precipHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Precipitation Rolling Average - 5 Fields</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
  <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.2.0"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f5; }
    .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    h1 { font-size: 24px; margin-bottom: 8px; color: #1f2937; }
    .subtitle { color: #6b7280; margin-bottom: 24px; }
    .chart-container { position: relative; height: 500px; }
    .legend-custom { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 16px; justify-content: center; }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; }
    .legend-swatch { width: 24px; height: 3px; border-radius: 2px; }
    .legend-swatch.raw { height: 1px; opacity: 0.6; }
    .legend-swatch.rolling { height: 3px; }
    .controls { margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    .controls-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
    .controls-label { font-size: 13px; font-weight: 500; }
    .field-toggles { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }
    .field-toggle { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
    .field-toggle input { cursor: pointer; }
    .color-dot { width: 12px; height: 12px; border-radius: 50%; }
    button { padding: 8px 16px; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer; font-size: 13px; }
    button:hover { background: #f3f4f6; }
    button.active { background: #2563eb; color: white; border-color: #2563eb; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Precipitation Time Series with 30-Day Rolling Average</h1>
    <p class="subtitle">Daily precipitation (PRECTOTCORR) and 30-day rolling average for 5 fields (2020-2024)</p>
    
    <div class="controls">
      <button id="btnZoomReset" onclick="resetZoom()">Reset Zoom</button>
    </div>
    
    <div class="controls-row">
      <span class="controls-label">Show Fields:</span>
      <div class="field-toggles" id="fieldToggles"></div>
      <div style="margin-left: auto; display: flex; gap: 8px;">
        <button onclick="selectAll()">Select All</button>
        <button onclick="clearAll()">Clear All</button>
      </div>
    </div>
    
    <div class="chart-container">
      <canvas id="precipChart"></canvas>
    </div>
    
    <div class="legend-custom" id="legendCustom"></div>
  </div>

  <script>
    const fieldIds = ${JSON.stringify(fieldIds)};
    const allDates = ${JSON.stringify(allDates)};
    const colors = ${JSON.stringify(fieldColors)};
    const fieldData = ${JSON.stringify(Object.fromEntries(precipFieldDataMap))};
    
    const dateObjects = allDates.map(d => new Date(d));
    const timestamps = dateObjects.map(d => d.getTime());
    
    const datasets = [];
    const legendCustom = document.getElementById('legendCustom');
    const fieldToggles = document.getElementById('fieldToggles');
    const fieldDatasetIndices = {};
    
    fieldIds.forEach((fieldId, fieldIdx) => {
      const color = colors[fieldId] || '#666';
      const dataObj = fieldData[fieldId];
      const rawIdx = datasets.length;
      const rollingIdx = datasets.length + 1;
      fieldDatasetIndices[fieldIdx] = { raw: rawIdx, rolling: rollingIdx };
      
      datasets.push({
        label: fieldId + ' (daily)',
        data: dataObj.raw.map((y, i) => y === null ? null : parseFloat(y)).map((y, i) => y === null ? null : { x: timestamps[i], y }),
        borderColor: color,
        borderWidth: 1,
        pointRadius: 0,
        tension: 0,
        fill: false,
        order: 2,
        spanGaps: false
      });
      
      datasets.push({
        label: fieldId + ' (30d avg)',
        data: dataObj.rolling.map((y, i) => y === null ? null : parseFloat(y)).map((y, i) => y === null ? null : { x: timestamps[i], y }),
        borderColor: color,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.1,
        fill: false,
        order: 1,
        spanGaps: false
      });
      
      const toggle = document.createElement('label');
      toggle.className = 'field-toggle';
      toggle.innerHTML = '<input type="checkbox" checked data-field-idx="' + fieldIdx + '"><span class="color-dot" style="background:' + color + '"></span><span>' + fieldId + '</span>';
      fieldToggles.appendChild(toggle);
      
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = '<span class="legend-swatch raw" style="background:' + color + '"></span><span class="legend-swatch rolling" style="background:' + color + '"></span><span>' + fieldId + '</span>';
      legendCustom.appendChild(item);
    });
    
    document.querySelectorAll('.field-toggle input').forEach(cb => {
      cb.addEventListener('change', (e) => {
        const fieldIdx = parseInt(e.target.dataset.fieldIdx);
        const indices = fieldDatasetIndices[fieldIdx];
        chart.setDatasetVisibility(indices.raw, e.target.checked);
        chart.setDatasetVisibility(indices.rolling, e.target.checked);
        chart.update();
      });
    });
    
    const config = {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'nearest', axis: 'x', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => new Date(items[0].parsed.x).toLocaleDateString(),
              label: (ctx) => ctx.dataset.label + ': ' + (ctx.parsed.y?.toFixed(1) ?? 'N/A') + ' mm'
            }
          },
          zoom: {
            pan: { enabled: true, mode: 'x' },
            zoom: {
              wheel: { enabled: true },
              pinch: { enabled: true },
              mode: 'x'
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: { unit: 'month', displayFormats: { month: 'MMM yyyy' } },
            title: { display: true, text: 'Date' },
            grid: { color: '#f3f4f6' }
          },
          y: {
            title: { display: true, text: 'Precipitation (mm/day)' },
            grid: { color: '#f3f4f6' }
          }
        }
      }
    };
    
    const chart = new Chart(document.getElementById('precipChart'), config);
    
    function resetZoom() {
      chart.resetZoom();
    }
    
    function selectAll() {
      document.querySelectorAll('.field-toggle input').forEach((cb, i) => {
        cb.checked = true;
        const indices = fieldDatasetIndices[i];
        chart.setDatasetVisibility(indices.raw, true);
        chart.setDatasetVisibility(indices.rolling, true);
      });
      chart.update();
    }
    
    function clearAll() {
      document.querySelectorAll('.field-toggle input').forEach((cb, i) => {
        cb.checked = false;
        const indices = fieldDatasetIndices[i];
        chart.setDatasetVisibility(indices.raw, false);
        chart.setDatasetVisibility(indices.rolling, false);
      });
      chart.update();
    }
  </script>
</body>
</html>`;

writeFileSync(outputPrecipHtmlPath, precipHtml);
console.log("Saved HTML chart to:", outputPrecipHtmlPath);