#!python3

import irsdk    # iRacing SDK
import time
import re
import os
import sys
import winsound


# Definitions
LANGUAGE = "english"

def play(filename):
    if not os.path.isfile(filename):
        print("Audio file '{}' not found".format(filename))
    else:
        print("Playing '{}'".format(filename))
        winsound.PlaySound(filename, winsound.SND_FILENAME)


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


        # Figure out what files to load
        CornerFile   = LANGUAGE + "/{0}/{0}.txt".format(TrackName)
        TrackWavFile = LANGUAGE + "/{0}/{0}.wav".format(TrackName)
        print("CornerFile is {}".format(CornerFile))
        print("TrackWavFile is {}".format(TrackWavFile))

        if not os.path.isfile(CornerFile) or not os.path.isfile(TrackWavFile):
            # This track is missing Corners.txt or TrackName.wav
            UnsupportedWavFile = LANGUAGE + "/shared/software/UnsupportedTrackOrConfig.wav"
            play(UnsupportedWavFile)
            while iRacing_Active:
                time.sleep(5)
                iRacing_Active = ir.startup()

        else:

            # This track is supported, "let's go Brandon"
            play(TrackWavFile)

            # Read in the list of corners
            Corners = list()
            with open(CornerFile) as f:
                for linenum, line in enumerate(f):
                    comments_removed = re.sub(r'#.*\n?', '', line.strip())
                    if len(comments_removed) == 0:
                        continue
                    Distance = int(comments_removed.split(',')[0].strip())
                    CornerPath = comments_removed.split(',')[1].strip(" \n\'\"")
                    if not os.path.isfile(CornerPath) and not (CornerPath == 'None'):
                        print("Error: cannot find audio file '{}' specified on line {} of '{}'".format(CornerPath, linenum, CornerFile))
                        play(LANGUAGE + "/shared/software/FileNotFound.wav")
                        sys.exit()

                    Corners.append((Distance, CornerPath))

            # Poll iRacing for the current location on track, announce corner name when necessary
            PrevLapDist, LapDist = ir['LapDist'], ir['LapDist']
            while iRacing_Active:
                # Print current LapDist in increments of 10 meters
                if round(LapDist/10.0) > round(PrevLapDist/10.0):
                    print("{:,.2f} meters".format(LapDist))

                # End of lap and reset special cases
                if abs(PrevLapDist - LapDist) > 100.0:
                    print("Lap discontinuity PrevLapDist = {:,.2f}, LapDist = {:,.2f}".format(PrevLapDist, LapDist))
                    # We've jumped back > 100 meters, which means a new lap or a reset
                    PrevLapDist = LapDist - 10.0

                if LapDist > PrevLapDist:
                    # Only speak if moving forward
                    for (Distance, CornerName) in Corners:
                        if (PrevLapDist < Distance <= LapDist):
                            if CornerName != 'None':
                                play(CornerName)
                            break

                PrevLapDist, LapDist = LapDist, ir['LapDist']
                time.sleep(0.25)
                iRacing_Active = ir.startup()

        time.sleep(5)
        ir.shutdown()
        iRacing_Active = ir.startup()
