import os
import sys
import re
import json
import base64
import urllib.request
from urllib.error import HTTPError, URLError
from datetime import datetime
import random

# ==========================================
# CONFIGURATION
# ==========================================
# If running in Docker (from previous setup), the file is in /app/data/
# If running locally, adjust the path as needed.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MARKDOWN_PATH = os.path.join(SCRIPT_DIR, 'data', 'Time Logging.md') 
ENV_FILE = os.path.join(SCRIPT_DIR, '.jira-env')

# Fallback to local directory if 'data' dir doesn't exist (useful for testing outside Docker)
if not os.path.exists(MARKDOWN_PATH):
    MARKDOWN_PATH = os.path.join(SCRIPT_DIR, 'Time Logging.md')

# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================
if not os.path.isfile(ENV_FILE):
    print(f"❌ Error: Jira environment file '{ENV_FILE}' not found!\n")
    print("Create the file with the following content:")
    print("JIRA_DOMAIN=https://your-company.atlassian.net")
    print("JIRA_EMAIL=your-email@example.com")
    print("JIRA_API_TOKEN=your-api-token")
    sys.exit(1)

# Parse simple .env file manually to avoid needing python-dotenv library
with open(ENV_FILE, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

# ==========================================
# VALIDATE JIRA CONFIGURATION
# ==========================================
jira_domain = os.environ.get('JIRA_DOMAIN', '').strip()
jira_email = os.environ.get('JIRA_EMAIL', '').strip()
jira_api_token = os.environ.get('JIRA_API_TOKEN', '').strip()

if not jira_domain:
    print("❌ Error: JIRA_DOMAIN is not configured.")
    sys.exit(1)
if not jira_email:
    print("❌ Error: JIRA_EMAIL is not configured.")
    sys.exit(1)
if not jira_api_token:
    print("❌ Error: JIRA_API_TOKEN is not configured.")
    sys.exit(1)

# Remove trailing slash from Jira domain
jira_domain = jira_domain.rstrip("/")

# ==========================================
# CHECK MARKDOWN FILE
# ==========================================
if not os.path.isfile(MARKDOWN_PATH):
    print(f"❌ Error: Markdown file not found at '{MARKDOWN_PATH}'!")
    sys.exit(1)

# ==========================================
# READ WORKLOG DATE
# ==========================================
with open(MARKDOWN_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

if not lines:
    print("❌ Error: Markdown file is empty.")
    sys.exit(1)

first_line = lines[0].strip()
date_match = re.match(r'^([0-9]{4}-[0-9]{2}-[0-9]{2})$', first_line)

if date_match:
    worklog_date = date_match.group(1)
    try:
        # Parse date and add 01:00:00 time
        dt = datetime.strptime(f"{worklog_date} 01:00:00", "%Y-%m-%d %H:%M:%S")
        
        # Get local timezone offset formatted as +HHMM or -HHMM
        local_tz = datetime.now().astimezone().tzinfo
        dt = dt.replace(tzinfo=local_tz)
        
        # Jira format: YYYY-MM-DDTHH:mm:ss.000+HHMM
        started = dt.strftime("%Y-%m-%dT%H:%M:%S.000%z")
        
        # If timezone offset is empty (e.g., UTC on some systems), default to +0000
        if not dt.strftime("%z"):
            started = dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")

        print(f"Using worklog date: {started}")
    except ValueError:
        print(f"❌ Error: Invalid date '{worklog_date}'.")
        sys.exit(1)
else:
    print("❌ First line must contain a date in format YYYY-MM-DD")
    sys.exit(1)

# ==========================================
# CREATE AUTHENTICATION HEADER
# ==========================================
auth_string = f"{jira_email}:{jira_api_token}"
auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Basic {auth_base64}"
}

# ==========================================
# READ FILE LINE BY LINE
# ==========================================
has_errors = False  # <--- ADD THIS FLAG

# Skip the first line (date)
for line in lines[1:]:
    line = line.strip()
    if not line:
        continue

    match = re.match(r'^#*\s*\[([A-Z]+-[0-9]+)\]\s*-\s*([0-9]+[mhd](?:\s*[0-9]+[mhd])*)\s*-\s*(.*)$', line)
    
    if line.startswith('---'):
        print("Reached notes section. Stopping ticket parsing.")
        break
    
    if match:
        ticket = match.group(1)
        time_spent = match.group(2)
        comment = match.group(3)

        print(f"\nLogging {time_spent} to {ticket}: '{comment}'...")

        payload = {
            "timeSpent": time_spent,
            "started": started,
            "comment": comment
        }
        payload_data = json.dumps(payload).encode('utf-8')

        jira_url = f"{jira_domain}/rest/api/2/issue/{ticket}/worklog"
        req = urllib.request.Request(jira_url, data=payload_data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 201:
                    print(f"✅ Successfully logged work for {ticket}.")
                else:
                    print(f"❌ Failed to log work for {ticket}. HTTP Status: {response.getcode()}")
                    has_errors = True
        except HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ Failed to log work for {ticket}. HTTP Status: {e.code}")
            print(f"   Jira Error: {error_body}")
            has_errors = True
        except Exception as e:
            print(f"❌ Failed to log work for {ticket}. Error: {str(e)}")
            has_errors = True

    else:
        print(f"⚠️ Skipping line (Regex mismatch): '{line}'")

# ==========================================
# FINISH
# ==========================================
if has_errors:
    print("\nCompleted with errors.")
    sys.exit(1)
else:
    print("\nDone. All successful!")
    sys.exit(0)