from flask import Flask, request, jsonify, send_file
import os
import subprocess
import re

app = Flask(__name__)

DATA_DIR = '/app/data'
SCRIPT_PATH = '/app/upload_script.py' # You can change this to a .sh script if you prefer

@app.route('/')
def index():
    return send_file('index.html')
    
@app.route('/favicon.svg')
def favicon():
    return send_file('favicon.svg', mimetype='image/svg+xml')
    
@app.route('/history', methods=['GET'])
def history():
    search_date = request.args.get('date')
    previous_logs_dir = os.path.join(DATA_DIR, 'previous_logs')
    
    if not os.path.exists(previous_logs_dir):
        return jsonify([])

    files = [f for f in os.listdir(previous_logs_dir) if f.endswith('.md')]
    files.sort(reverse=True)

    results = []
    
    # Helper to calculate total time from markdown text
    def calculate_total(content):
        total_minutes = 0
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('---'):  # Stop when we hit notes
                break
            
            # Extract time portion between the first two hyphens
            match = re.match(r'^#*\s*\[.*?\]\s*-\s*(.*?)\s*-', line)
            if match:
                time_str = match.group(1).lower()
                h_match = re.search(r'(\d+)h', time_str)
                m_match = re.search(r'(\d+)m', time_str)
                
                if h_match: total_minutes += int(h_match.group(1)) * 60
                if m_match: total_minutes += int(m_match.group(1))
                
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        time_parts = []
        if hours > 0: time_parts.append(f"{hours}h")
        if minutes > 0 or hours == 0: time_parts.append(f"{minutes}m")
        return " ".join(time_parts)

    if search_date:
        target_file = f"{search_date}.md"
        if target_file in files:
            with open(os.path.join(previous_logs_dir, target_file), 'r') as f:
                content = f.read()
                results.append({"date": search_date, "total": calculate_total(content), "content": content})
    else:
        for f_name in files[:10]:
            date_str = f_name.replace('.md', '')
            with open(os.path.join(previous_logs_dir, f_name), 'r') as f:
                content = f.read()
                results.append({"date": date_str, "total": calculate_total(content), "content": content})
                
    return jsonify(results)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    date = data.get('date')
    entries = data.get('entries', [])
    notes = data.get('notes', '').strip()

    if not date or not entries:
        return jsonify({"error": "Missing data"}), 400

    os.makedirs(DATA_DIR, exist_ok=True)

    # Format the Markdown content
    content = f"{date}\n\n"
    for entry in entries:
        content += f"[{entry['ticket']}] - {entry['duration']} - {entry['desc']}\n"
        
    if notes:
        content += f"\n---\n\n{notes}\n"

    # Define paths
    time_logging_path = os.path.join(DATA_DIR, 'Time Logging.md')
    date_logging_path = os.path.join(DATA_DIR, 'previous_logs', f'{date}.md')
    
    if os.path.exists(date_logging_path):
        return jsonify({
            "status": "error",
            "output": f"❌ Error: A log for {date} already exists.\n\nTo submit again, you must delete {date}.md from the previous_logs folder."
        })

    # Write / Overwrite files
    with open(time_logging_path, 'w') as f:
        f.write(content)
        
    with open(date_logging_path, 'w') as f:
        f.write(content)
        
    script_output = "Script not found."
    script_success = False

    # Trigger external script and WAIT for it to finish
    if os.path.exists(SCRIPT_PATH):
        # run() waits for the process to finish
        result = subprocess.run(['python', SCRIPT_PATH], capture_output=True, text=True)
        # Combine stdout (prints) and stderr (errors)
        script_output = result.stdout + result.stderr
        script_success = result.returncode == 0

    return jsonify({
        "status": "success" if script_success else "error", 
        "output": script_output
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)