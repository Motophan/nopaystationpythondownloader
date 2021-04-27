import os
import requests
import csv
import re
from subprocess import Popen, PIPE

# need to change this to the folder with all the tsv
# I recomend only keeping the NPS tsv files in this folder
TSV_location = r'/media/sf_Z_DRIVE/Emulation/Games/Sony/PlayStation 3/Tools/Scripts/NPS'

# need to change this to the folder where you want the pkg files downloaded
PKG_Download_Location = r'/home/user/Downloads/PKG'

#  need to change this to the folder where PSN_get_pkg_info.py is located 
# you can get this tool from https://github.com/windsurfer1122/PSN_get_pkg_info
pkg_info_script_location = r'/home/user/Downloads/PSN_get_pkg_info-2019.06.30.post1'

# set = to 1 if you want to validate the files if the pkg already exists
# you may want to set to 1 if you stop it mid download.
# only does a small request for the head of the file to get file size
ValidateFiles = 0

# wherever you have this script is where it will put the failed pkg link text file
cwd = os.getcwd()

def Get_PKG_Name(PKG_Link):
    try:
        NPS_Type = '[UNKNOWN]'
        PKG_title = '[UNKNOWN]'
        PKG_content_id = '[UNKNOWN]'
        arg = PKG_Link
        arg2 = '-f 0'
        arg3 = '--unclean'
        proc = Popen(['python3', pkg_info_script_location + os.sep + 'PSN_get_pkg_info.py', arg, arg2, arg3], stdin=PIPE, stdout=PIPE)
        lines = proc.communicate()[0].decode("utf-8").split('\n')
        for line in lines:
            hold = line.split(':')
            if hold[0] == 'NPS Type':
                NPS_Type = hold[1].strip()
            elif hold[0] == 'Title':
                PKG_title = hold[1].strip()
            elif hold[0] == 'Content ID':
                PKG_content_id = hold[1].strip()
        return NPS_Type + os.sep + PKG_title + '\t' + PKG_content_id
    except Exception as e:
        print('Get_PKG_Name Broke. Here is the error:\n' + e + '\nDon\'t worry just gonna skip this one.')
        # just incase garbage data got in them
        # '[UNKNOWN]' will cause the download to be skipped
        PKG_title = '[UNKNOWN]'
        PKG_content_id = '[UNKNOWN]'
        return PKG_title + '\t' + PKG_content_id     

# This function will request the head of the pkg link so it can get the correct file size
def File_Check(PKG_link, final_path, PKG_CONTENT_ID):
    print("Checking File Integrity!")
    file_location = final_path + os.sep + PKG_CONTENT_ID + '.pkg'
    if os.path.exists(file_location):
        head = requests.head(PKG_link)
        size = head.headers['Content-Length']
        file_size = os.path.getsize(file_location)
        if int(size) == int(file_size):
            return True
        else:
            os.remove(file_location)
            print("File size from server didn't match file size downloaded")
            return False
    else:
        print("Why am I checking for a file that doesn't exist?")
        print(file_location)
        return False

# function will downmload pkg and check that it was downloaded properly. 
# it will only try to re download the file once before giving up
def Downloader(PKG_link, ValidateFiles, Retry=0):
    try:
        head = requests.head(PKG_link)
        if head.status_code == 200:
            # Get pkg name and content id
            temp = Get_PKG_Name(PKG_link)
            temp_slipt = temp.split('\t')
            PKG_NAME = temp_slipt[0] + ' - (' + temp_slipt[1] + ')'
            PKG_CONTENT_ID = temp_slipt[1]
            if PKG_NAME == '[UNKNOWN]' or PKG_CONTENT_ID == '[UNKNOWN]':
                print("There was a problem getting pkg name and content id from pkg link: " + PKG_link)
                return False
            # set file path
            final_path = PKG_Download_Location + os.sep + PKG_NAME
            if not os.path.exists(final_path + os.sep + PKG_CONTENT_ID):
                # check if folder og pkg name exists 
                # realistically it shouldn't exist beofre this
                if not os.path.exists(final_path):
                    # if not make it
                    os.makedirs(final_path)
                r = requests.get(PKG_link)
                # downloading of file
                with open(final_path + os.sep + PKG_CONTENT_ID + '.pkg', 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                # checking that file was downloaded correctly
                if File_Check(PKG_link, final_path, PKG_CONTENT_ID):
                    return True
                else:
                    if Retry == 1:
                        print("There was a problem trying to re-downloading the file.\nURL: " + PKG_link)
                        return False
                    print("Trying to re-download file.")
                    return Downloader(PKG_link, 0, 1)
            else:
                print("PKG Already Downloaded")
                if ValidateFiles == 1:
                    if File_Check(PKG_link, final_path, PKG_CONTENT_ID):
                        return True
                    else:
                        if Retry == 1:
                            print("There was a problem trying to re-downloading the file.\nURL: " + PKG_link)
                            return False
                        print("Trying to re-download file.")
                        return Downloader(PKG_link, 0, 1)
                else:
                    return True
        else:
            print("Failed to load site: " + PKG_link)
            return False
    except Exception as e:
        print("Something Really broke!\nSkipping Download.")
        print(e)
        return False        

# get the name of all files in folder
with os.scandir(TSV_location) as NPS_tsvs:
    # loop over all files in folder
    for NPS_tvs in NPS_tsvs:
        # makes sure only .tsv files are run though this
        r = re.search(r'.tsv',NPS_tvs.name)
        if r:
            # open tsv and read data
            with open(TSV_location + os.sep + NPS_tvs.name) as file:
                file_data = csv.reader(file,delimiter='\t')
                # transpose data to make easier to search though
                file_data_transposed = list(map(list, zip(*file_data)))
            # the list at index 3 are the pkg links [1:] is to skip the title of row
            pkg_link_list = file_data_transposed[3][1:]
            for PKG_link in pkg_link_list:
                if 'http' in PKG_link:
                    if Downloader(PKG_link, ValidateFiles):
                        print("Successfully Downloaded: " + PKG_link)
                    else:
                        print("FAILED to Download: " + PKG_link)
                        with open(cwd + os.sep + 'Failed_PKG_Link.txt','a') as file:
                            file.writelines(PKG_link + '\n')
                    
