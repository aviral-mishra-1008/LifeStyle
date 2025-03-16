import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import datetime
import sqlite3

class GoogleDriveBackup:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, db_path):
        self.db_path = db_path
        self.creds = None
        self.token_path = 'token.pickle'
        self.credentials_path = 'credentials.json'

    def authenticate(self):
        # The file token.pickle stores the user's credentials
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

    def backup_database(self):
        try:
            # Authenticate
            self.authenticate()

            # Create Drive service
            service = build('drive', 'v3', credentials=self.creds)

            # Prepare backup file name
            backup_filename = f'lifestyle_tracker_backup_{datetime.datetime.now().strftime("%Y%m%d")}.db'

            # Prepare file metadata
            file_metadata = {
                'name': backup_filename,
                'parents': ['root']  # Uploads to root directory
            }
            media = MediaFileUpload(self.db_path, resumable=True)

            # Create the file in Google Drive
            file = service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id'
            ).execute()

            return True, f"Backup successful. File ID: {file.get('id')}"
        
        except Exception as e:
            return False, f"Backup failed: {str(e)}"

def check_and_backup(db_path):
    # Check last backup date
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create backup_info table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_info (
            last_backup_date TEXT
        )
    ''')
    
    # Get last backup date
    cursor.execute('SELECT last_backup_date FROM backup_info')
    result = cursor.fetchone()
    
    current_date = datetime.datetime.now()
    
    if not result:
        # No previous backup
        perform_backup = True
    else:
        last_backup_date = datetime.datetime.strptime(result[0], '%Y-%m-%d')
        days_since_last_backup = (current_date - last_backup_date).days
        perform_backup = days_since_last_backup >= 7
    
    if perform_backup:
        backup = GoogleDriveBackup(db_path)
        success, message = backup.backup_database()
        
        if success:
            # Update last backup date
            cursor.execute('DELETE FROM backup_info')
            cursor.execute('INSERT INTO backup_info (last_backup_date) VALUES (?)', 
                           (current_date.strftime('%Y-%m-%d'),))
        
        conn.commit()
        conn.close()
        
        return success, message
    
    conn.close()
    return False, "Backup not needed"