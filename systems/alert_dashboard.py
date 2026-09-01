from flask import Flask, jsonify, render_template_string
import glob
import json
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>IDS Alert Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        async function fetchAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const alerts = await response.json();
                const container = document.getElementById('alerts-container');
                container.innerHTML = '';
                
                if (alerts.length === 0) {
                    container.innerHTML = '<p class="text-gray-500 text-center py-8">🟢 System is secure. No attacks detected yet.</p>';
                    return;
                }

                alerts.forEach(alert => {
                    // Determine colors based on severity
                    let color = 'bg-yellow-100 border-yellow-500 text-yellow-800'; // Default Medium
                    if (alert.severity === 'HIGH' || (alert.alert_type && alert.alert_type.includes('BRUTEFORCE'))) {
                        color = 'bg-red-100 border-red-500 text-red-800'; // High Severity
                    } else if (alert.severity === 'LOW') {
                        color = 'bg-blue-100 border-blue-500 text-blue-800'; // Low Severity
                    }
                    
                    const div = document.createElement('div');
                    div.className = `border-l-4 p-4 mb-4 rounded shadow-sm flex flex-col gap-1 ${color}`;
                    
                    div.innerHTML = `
                        <div class="flex justify-between items-center">
                            <h2 class="font-bold text-lg">⚠️ ${alert.alert_type || 'SECURITY ALERT'}</h2>
                            <span class="text-xs font-semibold px-2 py-1 rounded uppercase tracking-wide bg-white bg-opacity-50">
                                ${alert.severity || 'HIGH'}
                            </span>
                        </div>
                        <p class="font-medium">${alert.message || JSON.stringify(alert)}</p>
                        
                        <div class="text-sm mt-2 flex gap-4 opacity-80">
                            <span><b>Attacker:</b> ${alert.attacker_ip || 'Unknown'}</span>
                            <span><b>Target:</b> ${alert.host_compromised || 'Unknown'}</span>
                        </div>
                        <p class="text-xs mt-2 opacity-60 text-right">${alert.timestamp || new Date().toISOString()}</p>
                    `;
                    container.appendChild(div);
                });
            } catch (error) {
                console.error("Error fetching alerts", error);
            }
        }
        
        // Auto-refresh the dashboard every 3 seconds
        setInterval(fetchAlerts, 3000);
        window.onload = fetchAlerts;
    </script>
</head>
<body class="bg-gray-100 min-h-screen p-8 font-sans">
    <div class="max-w-4xl mx-auto">
        <!-- Header -->
        <div class="bg-gray-800 text-white rounded-t-lg p-6 shadow-md flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-bold tracking-wider">🛡️ IDS SECURITY DASHBOARD</h1>
                <p class="text-gray-400 mt-1 text-sm">Real-time Machine Learning Threat Detection</p>
            </div>
            <div class="flex items-center gap-2">
                <span class="relative flex h-3 w-3">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span class="text-sm text-gray-300">Live</span>
            </div>
        </div>

        <!-- Alerts Container -->
        <div class="bg-white rounded-b-lg shadow-md p-6 min-h-[500px]">
            <div id="alerts-container">
                <p class="text-gray-500 text-center py-8 animate-pulse">Loading alerts...</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/alerts')
def get_alerts():
    alerts = []
    # Read all JSON files from ML/alerts directory
    alert_files = glob.glob('ML/alerts/*.json')
    for f in alert_files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    alerts.extend(data)
                else:
                    alerts.append(data)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            pass
    
    # Sort alerts so the newest is at the top
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify(alerts)

if __name__ == '__main__':
    print("="*50)
    print(" starting IDS UI DASHBOARD ")
    print(" Open http://localhost:5000 in your web browser")
    print("="*50)
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
