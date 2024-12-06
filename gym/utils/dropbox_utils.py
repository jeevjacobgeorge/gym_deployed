import dropbox
import os
from django.conf import settings
def upload_to_dropbox(file_path, dropbox_path):
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not access_token:
        access_token = settings.DROPBOX_ACCESS_TOKEN
        if not access_token:
            raise ValueError("Dropbox access token is not set.")
    dbx = dropbox.Dropbox(access_token)
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
