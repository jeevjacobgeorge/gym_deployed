import os
import dropbox
import requests
from dotenv import load_dotenv
from django.conf import settings

# Load environment variables from .env file
load_dotenv()

# Dropbox API URL for refreshing the access token
TOKEN_URL = 'https://api.dropbox.com/oauth2/token'

# Function to refresh the access token using the refresh token
def refresh_access_token(refresh_token):
    print("Refreshing token")
    """Use the refresh token to get a new access token."""
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': settings.DROPBOX_APP_KEY,
        'client_secret': settings.DROPBOX_APP_SECRET
    }
    
    # Make the API request to refresh the token
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        # Parse the new access token from the response
        print("Got new access token")
        print(response.json())
        tokens = response.json()
        if 'refresh_token' in tokens:
            refresh_token = tokens['refresh_token']
        return tokens['access_token'], refresh_token
    else:
        print(f"Error refreshing token: {response.text}")
        return None, None

# Function to upload a file to Dropbox
def upload_to_dropbox(file_path, dropbox_path):
    # Get the access token and refresh token from environment variables
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    
    if not access_token or not refresh_token:
        raise ValueError("Dropbox access token or refresh token is not set.")
    
    dbx = dropbox.Dropbox(access_token)
    
    try:
        # Try to upload the file
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"File uploaded successfully to {dropbox_path}")
    
    except dropbox.exceptions.AuthError as e:
        # If the access token is expired or invalid, refresh the token and retry
        print(f"Authentication error: {e}")
        
        # Refresh the access token
        new_access_token,refresh_token = refresh_access_token(refresh_token)
        
        if new_access_token:
            # Update the access token (refresh token stays the same)
            access_token = new_access_token
            
            # Optionally save the new access token in environment or settings (e.g., Django settings)
            os.environ["DROPBOX_ACCESS_TOKEN"] = access_token
            settings.DROPBOX_ACCESS_TOKEN = access_token
            
            # Retry the file upload with the new access token
            dbx = dropbox.Dropbox(new_access_token)
            with open(file_path, "rb") as f:
                dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            print(f"File uploaded successfully to {dropbox_path} with new token.")
        else:
            print("Failed to refresh the access token. Please re-authenticate.")
