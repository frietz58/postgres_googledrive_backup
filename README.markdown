# Automatically backup a postgres database table into a remote GoogleDrive folder

Implementing the GoogleDrive API v3, we can easily upload anything we wish into a remote GoogleDrive Folder.
Thus, with an additional shell script and the crontab, the entire backup process can be automated. 

## Before you start
Before you can use the scripts in the repository in a productive setting, two essential step **must be completed 
beforehand**:

1. 
    Enalbing the GoogleDrive API for the Google account whose Drive you wish to use to store the backup files: <br>
    To achieve this, visit [Google's official page](https://developers.google.com/drive/api/v3/quickstart/python) and 
    check step 1 of their guide. This will download the **credentials.json** file, which you will have to feed to the python 
    script so that the next step works...

2. 
    Authorizing the drive_upload.py script to access the Drive storage of that Google account. Problem is, [this 
    authorization can only be done in an interactive manner via a browser](https://stackoverflow.com/questions/28078490/google-drive-oauth2-without-browser).
    After you have obtained the **credentials.json** file, you can authorize the app / script. For that you must first 
    clone this repository, so execute the first two steps of the below installation guide.
    Now, that you have cloned the repository and installed it's requirements, execute the main python script and complete the 
    few authorization steps in the browsrt.


## Installation
1. Clone this repository:
    ```
    git clone https://github.com/MiddyGoesDev/postgres_googledrive_backup.git automatic_backup
    ```
    
2. Create virtualenv:
    ```
    virtualenv -p python3 backup_venv
    source backup_venv/bin/activate
    ```

2. Install the requirements:
    ```
    pip3 install -r automatic_backup/requirements.txt
    ```
    
3. Set the paths to the to the files in the configit ag.yaml files:
    Assuming that you have obtained both the credentials.json and token.pickle file, set their paths in the config.yaml file and make sure the postgres user has read permissions. Also enter the path to the folder where you which to temporary store the local backup files and the name of
    the GoogleDrive Folder into which the backup files should be uploaded.
    
    ```
    vim automatic_backup/config.yaml
    ```
    
    
    
5. Make sure that the postgres user (who is executing the scripts) has ownership and permissions on the scripts and the virtualenv:

    ```
    sudo chown postgres automatic_backup/
    sudo chmod 700 automatic_backup/sud
    sudo chown postgres backup_venv/
    sudo chmod 700 backup_venv/
    ```

6. Set up the crontab of the postgres user. It's important that you use the postgres user's crontab, because only the 
    postgres users has access to the postgres database tables. Simply run the following lines of code and append the 
    content of the crontab.md file to the crontab (changes the paths so that they point to the executables and binaries):

    ```
    sudo su postgres
    crontab -e
    ```
    Don't forget to **adjust the paths in the crontab** to actually point to where you cloned this repository...

7. Make sure that the postgres has permissions to execute and read the scripts and has also to write to the folder 
   where the backups are temporary stored (if yon don't create the folder manually, the script will create the folder
   in which case the postgres user automatically has access to the folder). 

   
