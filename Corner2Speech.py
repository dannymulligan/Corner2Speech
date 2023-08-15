#!python3

import irsdk    # iRacing SDK
import time
import re
import os
import sys
import winsound


# Definitions
LANGUAGE = "english"

# Utility functions
def play(filename):
    if not os.path.isfile(filename):
        print("Audio file '{}' not found".format(filename))
    else:
        print("Playing '{}'".format(filename))
        winsound.PlaySound(filename, winsound.SND_FILENAME)

def parse_corner_file(Corners, filename):
    with open(filename) as f:
        for linenum, line in enumerate(f):
            comments_removed = re.sub(r'#.*\n?', '', line.strip())
            if len(comments_removed) == 0:
                continue
            Distance = int(comments_removed.split(',')[0].strip())
            AudioFilePath = comments_removed.split(',')[1].strip(" \n\'\"")
            if not os.path.isfile(AudioFilePath) and not (AudioFilePath == 'None'):
                print("Error: cannot find audio file '{}' specified on line {} of '{}'".format(AudioFilePath, linenum, filename))
                play(LANGUAGE + "/shared/software/FileNotFound.wav")
                sys.exit()

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
    print("DriverID: {}, DriverUserName: '{}'".format(DriverID, DriverUserName))

    CarID = ir['DriverInfo']['Drivers'][DriverIdx]['CarID']
    CarPath = ir['DriverInfo']['Drivers'][DriverIdx]['CarPath']
    CarDisplayName = ir['DriverInfo']['Drivers'][DriverIdx]['CarScreenName']
    print("CarID: {}, CarPath: '{}', CarDisplayName: '{}''".format(CarID, CarPath, CarDisplayName))

    # Read in the list of corners
    Corners = dict()
    TrackSupported = False
    CornerFile = LANGUAGE + "/{0}/{0}.txt".format(TrackName)
    if os.path.isfile(CornerFile):
        print("Reading corner information from '{}'".format(CornerFile))
        TrackSupported = True
        parse_corner_file(Corners, CornerFile)

    CornerCarFile = LANGUAGE + "/{0}/{0} {1}.txt".format(TrackName, CarPath)
    if os.path.isfile(CornerCarFile):
        print("Reading corner information from '{}'".format(CornerCarFile))
        TrackSupported = True
        parse_corner_file(Corners, CornerCarFile)

    return TrackSupported, Corners


# Announce Corner2Speech startup
play(LANGUAGE + "/shared/software/Corner2SpeechIsStarted.wav")


# Initiate the iRacing SDK
ir = irsdk.IRSDK()
iRacing_Active = ir.startup()



while True:
    if not iRacing_Active:
        # Wait until iRacing is running
        play(LANGUAGE + "/shared/software/WaitingForiRacing.wav")
        while not iRacing_Active:
            print("Waiting for iRacing to start... retry in 5 seconds")
            time.sleep(5)
            iRacing_Active = ir.startup()

    else:
        # Iracing is running
        play(LANGUAGE + "/shared/software/iRacingIsStarted.wav")
        TrackSupported, Corners = read_corners(ir)

        if not TrackSupported:
            # This track is missing corner information
            play(LANGUAGE + "/shared/software/UnsupportedTrackOrConfig.wav")

            # Wait until iRacing shuts down
            while iRacing_Active:
                time.sleep(5)
                iRacing_Active = ir.startup()

        else:
            # This track is supported, "let's go Brandon"
            play(LANGUAGE + "/shared/software/CornerInformationLoaded.wav")

            # Play the track name if available
            TrackName = ir['WeekendInfo']['TrackName']
            TrackWavFile = LANGUAGE + "/{0}/{0}.wav".format(TrackName)
            if os.path.isfile(TrackWavFile):
                play(TrackWavFile)

            # Poll iRacing for the current location on track, announce corner name when necessary
            PrevLapDist, LapDist = ir['LapDist'], ir['LapDist']
            while iRacing_Active:
                # Print current LapDist in increments of 10 meters
                if round(LapDist/5.0) > round(PrevLapDist/5.0):
                    print("{:,.1f} meters".format(LapDist))

                # End of lap and reset special cases
                if abs(PrevLapDist - LapDist) > 100.0:
                    print("Lap discontinuity PrevLapDist = {:,.2f}, LapDist = {:,.2f}".format(PrevLapDist, LapDist))
                    # We've jumped back > 100 meters, which means a new lap or a reset
                    PrevLapDist = LapDist - 10.0
                    # For debug purposes, every time we cross the start finish line we reload the corner files
                    TrackSupported, Corners = read_corners(ir)
                    play(LANGUAGE + "/shared/software/Reload.wav")

                if LapDist > PrevLapDist:
                    # Only speak if moving forward
                    for Distance in Corners:
                        if (PrevLapDist < Distance <= LapDist):
                            if Corners[Distance] != 'None':
                                play(Corners[Distance])

                PrevLapDist, LapDist = LapDist, ir['LapDist']
                time.sleep(0.05)
                iRacing_Active = ir.startup()

        time.sleep(5)
        ir.shutdown()
        iRacing_Active = ir.startup()
