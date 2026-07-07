import os
import sys
import gzip
import shutil
import hashlib
import json
import argparse
import urllib.request
from urllib.error import URLError, HTTPError

# Try to import dotenv to load local env variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Load credentials from environment
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_BUCKET_ID = os.getenv("B2_BUCKET_ID")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "procureiq")
CONTAINER_NAME = os.getenv("DB_CONTAINER_NAME", "procureiq-alloydb-local")

BACKUP_DIR = "./deploy/alloydb/local/backups"
FILENAME = "latest_db_backup.sql.gz"
FILEPATH = os.path.join(BACKUP_DIR, FILENAME)

def check_b2_credentials():
    if not all([B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_ID, B2_BUCKET_NAME]):
        print("Error: Backblaze B2 credentials (B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_ID, B2_BUCKET_NAME) are missing in environment/env files!")
        sys.exit(1)

def b2_authorize():
    url = "https://api.backblazeb2.com/b2api/v2/b2_authorize_account"
    req = urllib.request.Request(url)
    
    import base64
    auth_str = f"{B2_KEY_ID}:{B2_APPLICATION_KEY}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    req.add_header("Authorization", f"Basic {auth_b64}")
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data["apiUrl"], data["authorizationToken"], data["downloadUrl"]
    except Exception as e:
        print(f"B2 Authorization failed: {e}")
        sys.exit(1)

def get_upload_url(api_url, auth_token):
    url = f"{api_url}/b2api/v2/b2_get_upload_url"
    payload = json.dumps({"bucketId": B2_BUCKET_ID}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", auth_token)
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data["uploadUrl"], data["authorizationToken"]
    except Exception as e:
        print(f"Failed to get B2 upload URL: {e}")
        sys.exit(1)

def do_backup():
    import subprocess
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    sql_filename = "latest_db_backup.sql"
    sql_filepath = os.path.join(BACKUP_DIR, sql_filename)
    
    print(f"Dumping database from container '{CONTAINER_NAME}'...")
    
    # Check if container is running
    status_cmd = f"docker inspect -f '{{{{.State.Running}}}}' {CONTAINER_NAME}"
    try:
        res = subprocess.check_output(status_cmd, shell=True, stderr=subprocess.DEVNULL)
        if b"true" not in res:
            raise Exception("not running")
    except Exception:
        print(f"Error: Docker container '{CONTAINER_NAME}' is not running!")
        sys.exit(1)
        
    # Run pg_dump via docker exec
    dump_cmd = f"docker exec -t {CONTAINER_NAME} pg_dump -U {DB_USER} -d {DB_NAME}"
    try:
        with open(sql_filepath, "wb") as f_out:
            subprocess.check_call(dump_cmd, shell=True, stdout=f_out)
    except Exception as e:
        print(f"Database dump failed: {e}")
        if os.path.exists(sql_filepath):
            os.remove(sql_filepath)
        sys.exit(1)
        
    print(f"Compressing dump file...")
    with open(sql_filepath, "rb") as f_in:
        with gzip.open(FILEPATH, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    os.remove(sql_filepath)
    size = os.path.getsize(FILEPATH) / 1024 / 1024
    print(f"Backup completed: {FILEPATH} ({size:.2f} MB)")
    return FILEPATH

def do_upload():
    check_b2_credentials()
    
    if not os.path.exists(FILEPATH):
        print("No local backup file found. Creating one now...")
        do_backup()
            
    api_url, auth_token, _ = b2_authorize()
    upload_url, upload_auth_token = get_upload_url(api_url, auth_token)
    
    # Calculate SHA1
    sha1 = hashlib.sha1()
    with open(FILEPATH, "rb") as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    sha1_hex = sha1.hexdigest()
    
    with open(FILEPATH, "rb") as f:
        file_data = f.read()
        
    print(f"Uploading {FILENAME} (updating/overwriting) to Backblaze B2 bucket '{B2_BUCKET_NAME}'...")
    req = urllib.request.Request(upload_url, data=file_data, method="POST")
    req.add_header("Authorization", upload_auth_token)
    req.add_header("X-Bz-File-Name", FILENAME)
    req.add_header("Content-Type", "application/octet-stream")
    req.add_header("X-Bz-Content-Sha1", sha1_hex)
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if "fileId" in result:
                print(f"Successfully uploaded/updated: {FILENAME} (File ID: {result['fileId']})")
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

def do_download():
    check_b2_credentials()
    api_url, auth_token, download_url = b2_authorize()
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    download_file_url = f"{download_url}/file/{B2_BUCKET_NAME}/{FILENAME}"
    print(f"Downloading latest backup '{FILENAME}' from Backblaze B2...")
    
    req = urllib.request.Request(download_file_url)
    req.add_header("Authorization", auth_token)
    
    try:
        with urllib.request.urlopen(req) as response, open(FILEPATH, "wb") as f_out:
            shutil.copyfileobj(response, f_out)
        print(f"Download complete: {FILEPATH}")
        return FILEPATH
    except Exception as e:
        print(f"Download failed: {e}")
        if os.path.exists(FILEPATH):
            os.remove(FILEPATH)
        sys.exit(1)

def do_restore():
    import subprocess
    
    if not os.path.exists(FILEPATH):
        print(f"Error: Local backup file {FILEPATH} not found. Please run download first.")
        sys.exit(1)

    print(f"Restoring database from: {FILENAME}...")
    
    # Check if container is running
    status_cmd = f"docker inspect -f '{{{{.State.Running}}}}' {CONTAINER_NAME}"
    try:
        res = subprocess.check_output(status_cmd, shell=True, stderr=subprocess.DEVNULL)
        if b"true" not in res:
            raise Exception("not running")
    except Exception:
        print(f"Error: Docker container '{CONTAINER_NAME}' is not running!")
        sys.exit(1)
        
    # Recreate public schema to ensure clean slate
    clean_cmd = f"docker exec -i {CONTAINER_NAME} psql -U {DB_USER} -d {DB_NAME} -c 'DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;'"
    subprocess.call(clean_cmd, shell=True, stdout=subprocess.DEVNULL)
    
    # Decompress and stream to psql
    restore_cmd = f"docker exec -i {CONTAINER_NAME} psql -U {DB_USER} -d {DB_NAME}"
    try:
        with gzip.open(FILEPATH, 'rb') as f_in:
            proc = subprocess.Popen(restore_cmd, shell=True, stdin=subprocess.PIPE)
            shutil.copyfileobj(f_in, proc.stdin)
            proc.stdin.close()
            proc.wait()
            if proc.returncode != 0:
                raise Exception("psql returned non-zero code")
        print("Database restore completed successfully!")
    except Exception as e:
        print(f"Restore failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="ProcureIQ Database & Backblaze B2 Manager Tool")
    parser.add_argument("command", choices=["backup", "upload", "download", "restore"], 
                        help="Action to perform")
    
    args = parser.parse_args()
    
    if args.command == "backup":
        do_backup()
    elif args.command == "upload":
        do_upload()
    elif args.command == "download":
        do_download()
    elif args.command == "restore":
        do_restore()

if __name__ == "__main__":
    main()
