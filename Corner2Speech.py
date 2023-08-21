#!python3

import sys
import time
import re
import os
import winsound


# Before importing irsdk, check if the Python yaml library is installed
try:
    import yaml
    from yaml.reader import Reader as YamlReader
except ModuleNotFoundError:
    #  Install the Python yaml library if it is missing
    print("ERROR: Python yaml library was not installed... installing")
    import subprocess
    #subprocess.check_output([sys.executable, "-m", "pip", "install", "pyyaml"])
    print(subprocess.check_output([sys.executable, "-m", "pip", "install", "pyyaml"]))
    print()
    print("Please restart this application")
    while True:
        time.sleep(1)


import irsdk    # iRacing SDK

# Determine the location of this script so that we can refer to relative paths
PATH = os.path.dirname(os.path.abspath(__file__)) + "/"

# Utility functions
def announce(FileName):
    if not os.path.isfile(FileName):
        print("Audio file '{}' not found".format(FileName))
    else:
        print("Announcing '{}'".format(FileName))
        winsound.PlaySound(FileName, winsound.SND_FILENAME)

def play(Distance, FileName):
    # We checked all of the audio files at load time, so we're
    # not going to check if the file exists here, just play it
    if not os.path.isfile(FileName):
        print("{:7,.1f} meters: Audio file '{}' not found".format(Distance, FileName))
    else:
        print("{:7,.1f} meters: playing '{}'".format(Distance, FileName))
    winsound.PlaySound(FileName, winsound.SND_FILENAME | winsound.SND_ASYNC)

def parse_corner_file(Corners, filename):
    with open(filename) as f:
        for linenum, line in enumerate(f):
            comments_removed = re.sub(r'#.*\n?', '', line.strip())
            if len(comments_removed) == 0:
                continue
            Distance = int(comments_removed.split(',')[0].strip())
            AudioFilePath = PATH + comments_removed.split(',')[1].strip(" \n\'\"")
            if not os.path.isfile(AudioFilePath) and not (AudioFilePath == 'None'):
                print("Error: cannot find audio file '{}' specified on line {} of '{}'".format(AudioFilePath, linenum, filename))
                announce(PATH + "shared/software/File Not Found.wav")
                while True:
                    time.sleep(1)

            Corners[Distance] = AudioFilePath


def read_corners(ir):
    # Get track, driver & car info from the iRacing session
    TrackID = ir['WeekendInfo']['TrackID']
    TrackName = ir['WeekendInfo']['TrackName']
    TrackDisplayName = ir['WeekendInfo']['TrackDisplayName']
    TrackConfigName = ir['WeekendInfo']['TrackConfigName']
    print("TrackID: {}, TrackName: '{}', TrackDisplayName: '{}', TrackConfigName: '{}'".format(TrackID, TrackName, TrackDisplayName, TrackConfigName))

    DriverID = int(ir['DriverInfo']['DriverUserID'])
    DriverIdx = int(ir['DriverInfo']['DriverCarIdx'])
    DriverUserName = ir['DriverInfo']['Drivers'][DriverIdx]['UserName']
    Debug = (DriverID == 603475)
    if Debug:
        print("DriverID: {}, DriverUserName: '{}' => Debug mode enabled".format(DriverID, DriverUserName))
    else:
        print("DriverID: {}, DriverUserName: '{}'".format(DriverID, DriverUserName))

    CarID = ir['DriverInfo']['Drivers'][DriverIdx]['CarID']
    CarPath = ir['DriverInfo']['Drivers'][DriverIdx]['CarPath']
    CarDisplayName = ir['DriverInfo']['Drivers'][DriverIdx]['CarScreenName']
    print("CarID: {}, CarPath: '{}', CarDisplayName: '{}''".format(CarID, CarPath, CarDisplayName))

    # Read in the list of corners
    Corners = dict()
    TrackSupported = False
    CornerFile = PATH + "tracks/{0}/{0}.txt".format(TrackName)
    if os.path.isfile(CornerFile):
        print("Reading track information from '{}'".format(CornerFile))
        TrackSupported = True
        parse_corner_file(Corners, CornerFile)
    else:
        print("Warning: No track information, which would have been in file '{}'".format(CornerFile))

    CornerCarFile = PATH + "userfiles/{0} {1}.txt".format(TrackName, CarPath)
    if os.path.isfile(CornerCarFile):
        print("Reading track+car information from '{}'".format(CornerCarFile))
        TrackSupported = True
        parse_corner_file(Corners, CornerCarFile)
    else:
        print("Warning: No track+car information, which would have been in file '{}'".format(CornerCarFile))

    return Debug, TrackSupported, Corners


# Announce Corner2Speech startup
announce(PATH + "shared/software/Corner2Speech Is Started.wav")


# Initiate the iRacing SDK
ir = irsdk.IRSDK()

while True:
    iRacing_Active = ir.startup()
    if not iRacing_Active:
        # Wait until iRacing is running
        announce(PATH + "shared/software/Waiting For iRacing.wav")
        while not iRacing_Active:
            print("Waiting for iRacing to start... retry in 5 seconds")
            time.sleep(5)
            iRacing_Active = ir.startup()

    else:
        # iRacing is running
        announce(PATH + "shared/software/iRacing Is Started.wav")
        Debug, TrackSupported, Corners = read_corners(ir)

        if not TrackSupported:
            # This track is missing corner information
            announce(PATH + "shared/software/Unsupported Track Or Config.wav")

            # Wait until iRacing shuts down
            while iRacing_Active:
                time.sleep(5)
                iRacing_Active = ir.startup()

        else:
            # This track is supported, "let's go Brandon"
            announce(PATH + "shared/software/Corner Information Loaded.wav")

            # Play the track name if available
            TrackName = ir['WeekendInfo']['TrackName']
            TrackWavFile = PATH + "/{0}/{0}.wav".format(TrackName)
            if os.path.isfile(TrackWavFile):
                announce(TrackWavFile)

            # Poll iRacing for the current location on track, announce corner name when necessary
            PrevLapDist, LapDist = ir['LapDist'], ir['LapDist']
            while iRacing_Active:
                if Debug:
                    # Print current LapDist in increments of 5 meters
                    if round(LapDist/5.0) > round(PrevLapDist/5.0):
                        print("{:7,.1f} meters".format(LapDist))

                # End of lap and reset special cases
                if abs(PrevLapDist - LapDist) > 100.0:
                    print("Lap discontinuity PrevLapDist = {:,.2f}, LapDist = {:,.2f}".format(PrevLapDist, LapDist))
                    # We've jumped back > 100 meters, which means a new lap or a reset
                    PrevLapDist = LapDist - 10.0

                    # For debug purposes, every time we cross the start finish line we reload the corner files
                    if Debug:
                        Debug, TrackSupported, Corners = read_corners(ir)

                # Normal announce corner name
                if LapDist > PrevLapDist:
                    # Only speak if moving forward
                    for Distance in Corners:
                        if (PrevLapDist < Distance <= LapDist):
                            if Corners[Distance] != 'None':
                                play(LapDist, Corners[Distance])

                PrevLapDist, LapDist = LapDist, ir['LapDist']
                time.sleep(0.05)
                iRacing_Active = ir.startup()

        time.sleep(5)
        ir.shutdown()
