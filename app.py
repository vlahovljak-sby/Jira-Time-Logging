from flask import Flask, request, jsonify, send_file
import os
import subprocess

app = Flask(__name__)

DATA_DIR = '/app/data'
SCRIPT_PATH = '/app/upload_script.py' # You can change this to a .sh script if you prefer

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    date = data.get('date')
    entries = data.get('entries', [])

    if not date or not entries:
        return jsonify({"error": "Missing data"}), 400

    os.makedirs(DATA_DIR, exist_ok=True)

    # Format the Markdown content
    content = f"{date}\n\n"
    for entry in entries:
        content += f"[{entry['ticket']}] - {entry['duration']} - {entry['desc']}\n"

    # Define paths
    time_logging_path = os.path.join(DATA_DIR, 'Time Logging.md')
    date_logging_path = os.path.join(DATA_DIR, 'previous_logs', f'{date}.md')

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