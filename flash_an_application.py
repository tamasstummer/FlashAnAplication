#TODO logo

import os
import zipfile
import argparse
import sys
import glob
import subprocess

#----------------------------------------------------------
# Set this path yourself first
commander = "C:/SiliconLabs/studio/rel_1361/SimplicityStudio_v5/developer/adapter_packs/commander/commander.exe"
#----------------------------------------------------------

default_application = "SwitchOnOff"
default_board = "brd4205b"
default_frquency = "US"
default_build = "lastsuccessful"
default_branch = "develop%252F22q2" # develop/22q2
default_build = "lastSuccessfulBuild"

#Apps and board definitions
#-----------------------------------------------------------------------------------------------
Apps = ['SwitchOnOff', 'PowerStrip', 'SensorPIR', 'DoorLockKeyPad', 'WallController', 'LEDBulb', 'SerialAPI', 'ZnifferPTI']
NonCertifiableApps = ['MultilevelSensor']

SERIES1_BOARDS= {
  "brd4200a": "ZGM130S",
  "brd4201a": "EFR32ZG14",
  "brd4202a": "ZGM130S",
  "brd4207a": "ZGM130S",
  "brd4208a": "EFR32ZG14",
  "brd4209a": "EFR32RZ13",
}
SERIES2_BOARDS= {
  "brd4204a" : "EFR32ZG23",
  "brd4204b" : "EFR32ZG23",
  "brd4204c" : "EFR32ZG23",
  "brd4204d" : "EFR32ZG23",
  "brd4205a" : "ZGM230S",
  "brd4205b" : "ZGM230S",
  "brd4210a" : "EFR32ZG23",
  "brd2603a" : "ZGM230S",
}

frequencies= {
  "REGION_EU" : "0x00",
  "REGION_US" : "0x01",
  "REGION_US_LR" : "0x09",
}

#-----------------------------------------------------------------------------------------------
# Parse the inputs first
parser = argparse.ArgumentParser(description="Flash any sample application on any board")
parser.add_argument('--serialno',          type=str, help="JLink serial nmber of the board",                   nargs='?') #Mandatory parameter
parser.add_argument('--name',              type=str, help="Name of the application, you want to flash.",       nargs='?', default = default_application)
parser.add_argument('--freq',              type=str, help="Frequency of the binary",                           nargs='?', default = default_frquency)
parser.add_argument('--board',             type=str, help="Target board.",                                     nargs='?', default = default_board)
parser.add_argument('--branch',            type=str, help="Name of a specific jenkins branch.",                nargs='?', default = default_branch)
parser.add_argument('--build',             type=str, help="Specifies the number of the build on jenkins",      nargs='?', default = default_build)

args = parser.parse_args()

# ---------------------------------------------------------------------------------------------
def download_application_binary(branch_name, build_name, app_name, board_name, region_name) -> None:
    print("----------------------------------------------")
    print("Download app binary...")
    #ZW_SerialAPI_Controller_7.18.0_238_ZGM230S_brd2603a_REGION_US
    branch_name = branch_name.replace("/", "%252F")  # Jenkins needs this

    #Check every possible error at the begining
    app_chategory = give_back_application_cathegory(app_name)
    board_name = check_if_board_existing(board_name)
    region_name = check_region(region_name)
    extra_path_element = ""  # in case of the SerialAPI, we need a "Controller" element in the path
    if(app_name == "SerialAPI"):
        extra_path_element = "Controller/"
    global name_of_zip
    name_of_zip = app_name + ".zip"
    url = "https://zwave-jenkins.silabs.com/job/zw-zwave/job/" + branch_name + "/" + build_name + "/artifact/" + app_chategory + "/" + app_name + "/out/" + extra_path_element + board_name + "_" + region_name + "/build/release/*zip*/" + name_of_zip
    print("This URL is the source of your hex file: " + url)

    os.system('wget ' + url)
    #https://zwave-jenkins.silabs.com/job/zw-zwave/job/develop%252F22q2/lastSuccessfulBuild/artifact/Apps/SwitchOnOff/out/brd2603a_REGION_US/build/release/
    print("Done")

def give_back_application_cathegory(application_name) -> str:
    if(application_name in Apps):
        return "Apps"
    elif(application_name in NonCertifiableApps):
        return "NonCertifiableApps"
    else:
        print('The given application chategory is invalid')
        sys.exit(-1)
    return
def check_if_board_existing(board_name) -> str:
    if(board_name in SERIES1_BOARDS or board_name in SERIES2_BOARDS):
        return board_name
    else:
        print('The given board name is invalid')
        sys.exit(-1)
        return

def check_region(region_name) -> str:
    region_name = "REGION_" + region_name
    if(region_name in frequencies):
        return region_name
    else:
        print('The given frequency name is invalid')
        sys.exit(-1)
        return

def unzip_downloaded_binary() -> None:
    print("----------------------------------------------")
    print("Unzip downloaded stuff...")
    with zipfile.ZipFile(name_of_zip, 'r') as zip_ref:
        zip_ref.extractall(os.getcwd())
    return
    print("Done")

#def delete_frequency_mfg_token() -> None:

    #...
def flash_application_binary(serialno, board_name) -> None:
    print("----------------------------------------------")
    print("Flash the hex files")

    hex_file_name = ""
    os.chdir("./release")
    for file in glob.glob("*.hex"):
        print("Found hex file will be flashed: " + file)
        hex_file_name = file
        hex_file_path = "./release/" + file
        os.chdir("./..")
    if hex_file_name:
        #Reset device
        os.system(commander + " device masserase -s " + str(serialno) + " -d " + SERIES2_BOARDS.get(board_name))
        os.system(commander + " device reset -s " + str(serialno) + " -d " + SERIES2_BOARDS.get(board_name))

        # Reset the mfg token
        os.system(commander + " flash --tokengroup znet --token MFG_ZWAVE_COUNTRY_FREQ:0x01 -s " + str(serialno) + " -d " + SERIES2_BOARDS.get(board_name))

        #Flash the downloaded hex file
        os.system(commander + " flash " + hex_file_path + " -s " + str(serialno) + " -d " + SERIES2_BOARDS.get(board_name))

        #Get the region mfg token's value just for sure
        os.system(commander + " tokendump --tokengroup znet --token MFG_ZWAVE_COUNTRY_FREQ -s " + str(serialno) + " -d " + SERIES2_BOARDS.get(board_name))
        print("Done")

def delete_downloaded_shit() -> None:
    os.system("rm -rf release")
    os.system("rm -rf " + name_of_zip)

def main() -> None:
    print("Flash any sample application on any board")
    download_application_binary(args.branch, args.build, args.name, args.board, args.freq)
    unzip_downloaded_binary()
    flash_application_binary(args.serialno, args.board)
    delete_downloaded_shit()

if __name__ == "__main__":
  main()