#!/usr/bin/python3

from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from os import listdir
from os.path import isfile, join
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import argparse
import pickle
import os.path
import ruamel.yaml
import sys

print()
print("Upload at: " + str(datetime.now()))
# os.chdir(r"/home/pcadmin/upload_script/")

# setup cli argparser interface for more flexibility
parser = argparse.ArgumentParser(description=(
    "This python script uploads files into the drive storage of a google account. For this to work, that account must "
    "activate the drive api (under step 1 here: https://developers.google.com/drive/api/v3/quickstart/python). There "
    "we obtain the file credentials.json, which is used to generate the token.pickle file from the browser that will "
    "pop up the first time this script is executed"))

parser.add_argument("-cf", "--config", type=str, help="The path to the config.yaml file")

args = parser.parse_args()

# read the config file passed as argument
yaml = ruamel.yaml.YAML()
with open(args.config) as f:
    config = yaml.load(f)


class Synchronizer:

    def __init__(self):
        self.service = None
        self.auth_run = False

        # Controls what the app is allowed to do in the cloud storage
        # If modifying these scopes, delete the file token.pickle. A new authentication process will be started that
        self.scopes = ['https://www.googleapis.com/auth/drive.file',
                       'https://www.googleapis.com/auth/drive.install']

        # Starts the authentication process of the client-side script
        self.authorize_app()

    def authorize_app(self):
        """
        Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(config["token_path"]):
            with open(config["token_path"], 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                self.auth_run = True
                flow = InstalledAppFlow.from_client_secrets_file(config["credtials_path"], self.scopes)
                creds = flow.run_local_server()

            # Save the credentials for the next run
            with open(config["token_path"], 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def get_folder_id(self, folder_name):
        """
        Returns the id of the given folder that exists in the cloud storage.
        :param folder_name: The name of the folder from which the ID is wanted
        :return:  The ID of the folder
        """
        page_token = None
        folder_id = ""
        while True:
            response = self.service.files().list(q=str("name='" + folder_name + "'"),
                                                 spaces='drive',
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()
            for file in response.get('files', []):
                # Process change
                folder_id = file.get('id')
            page_token = response.get('nextPageToken', None)
            if page_token is None:

                # if the remote folder does not exist
                if not folder_id:
                    print("Creating folder {} in GoogleDrive storage...".format(folder_name))
                    file_metadata = {
                        'name': folder_name,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    file = self.service.files().create(body=file_metadata,
                                                       fields='id').execute()

                    folder_id = file.get('id')
                else:
                    break

        return folder_id

    def get_remote_files(self, contain_query):
        """
        find all files in drive whose names containes the querry
        :param contain_query: the search querry which is checked for each files name
        :return: a list containing the file names of matches
        """
        page_token = None
        files_in_drive = []
        while True:
            print("Searching for files in Cloud storage...")
            # this gives us all files where the name contains .pdf (use this for .sql
            response = self.service.files().list(q="name contains '" + str(contain_query) + "'",
                                                 spaces='drive',
                                                 # fields='nextPageToken, files(id, name)',
                                                 fields='nextPageToken, files(*)',
                                                 pageToken=page_token).execute()

            for file in response.get('files', []):
                # only use file's that are not delete (this is probably only relevant for development)
                if not file["trashed"]:
                    files_in_drive.append(file.get('name'))

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        print("Found {} files in cloud storage containing the querry: {}".format(len(files_in_drive), contain_query))
        return files_in_drive

    @staticmethod
    def get_local_files(local_path, contain_query):
        """
        lists all files in the folder whose name contains the contain_query
        :param local_path: the path of the folder in which to search
        :param contain_query: the querry each files name in the folder must contain
        :return: a list of (full) file paths of the matches
        """
        print("Searching for files in local folder...")
        if os.path.exists(local_path):
            local_files = [join(local_path, f) for f in listdir(local_path) if
                           isfile(join(local_path, f)) and contain_query in f]

            print("Found {} files in {} containing the querry {}".format(len(local_files), local_path, contain_query))
            return local_files

        else:
            raise Exception("Path {0} does not exist".format(local_path))

    def upload_file(self, file, drive_folder=None):
        """
        Uploads a file into a folder on the cloud
        :param file: The file that is uploaded
        :param drive_folder: The target folder into which the file should be upload. If None uploads into root
        """
        if drive_folder is not None:
            # get id for parent folder, to save file in folder in cloud
            parent_id = self.get_folder_id(folder_name=drive_folder)
            file_metadata = {'name': str(os.path.basename(file)), 'parents': [parent_id]}
        else:
            file_metadata = {'name': str(os.path.basename(file))}

        # get file type for metadata and mimetype
        filename, file_extension = os.path.splitext(os.path.basename(file))
        if file_extension == '.sql':
            mimetype = 'application/sql'
        else:
            # default case
            mimetype = 'plain/text'

        media = MediaFileUpload(str(file),
                                mimetype=mimetype)

        file = self.service.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()

        print("File {} has been uploaded into the cloud folder {}".format(file_metadata["name"], drive_folder))


if __name__ == '__main__':
    # init drive api
    Synchronizer = Synchronizer()
    auth_run = Synchronizer.authorize_app()

    # if this was an execution acquiring the token.pickle file, stop further execution
    if Synchronizer.auth_run:
        sys.exit("Token file has been acquired, exiting...")

    # get a list of files that exists in the remote drive folder and contain the query
    remote_sql_files = Synchronizer.get_remote_files(contain_query=config["contain_query"])

    # get a second list of files that exists in the remote folder and contain the query
    local_sql_files = Synchronizer.get_local_files(local_path=config["local_backup_folder"],
                                                   contain_query=config["contain_query"])

    # compare the lists, upload files that exist on local device but not in remote storage
    uploaded_new_file = False
    for local_file in local_sql_files:
        if os.path.basename(local_file) not in remote_sql_files:
            uploaded_new_file = True
            print("Local file {} is not in list of remote files".format(os.path.basename(local_file)))
            Synchronizer.upload_file(file=local_file, drive_folder=config["remote_backup_folder"])

    if not uploaded_new_file:
        print(("No file has been uploaded, because no file was found in the local directory that was not already in "
               "the cloud storage"))
