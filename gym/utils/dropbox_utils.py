import dropbox
import os
from django.conf import settings

def upload_to_dropbox(local_path, dropbox_path):
    access_token = settings.DROPBOX_ACCESS_TOKEN  # Store your token in Django settings
    print(f"Access Token: {access_token}")
    dbx = dropbox.Dropbox(access_token)
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
    print(f"Uploaded {local_path} to {dropbox_path}")
