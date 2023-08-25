#!python3

# Before you can use this script, you must install pydub & ffmpeg
# Install pydub with "pip install pydub"
# Installing ffmpeg is a bit harder, see https://phoenixnap.com/kb/ffmpeg-windows

import argparse
import csv
import os
from pydub import AudioSegment

parser = argparse.ArgumentParser(prog="extract_audio.py",
            description="extract audio from source files as specified by a CSV file")
parser.add_argument("CSVFilename", help="CSV file")
args = parser.parse_args()

PreviousSource = None

print("Processing clips specified in {}".format(args.CSVFilename))
if not os.path.isfile(args.CSVFilename):
    print("ERROR: '{}' doesn't exist".format(args.CSVFilename))
else:
    #csvfile = open(args.CSVFilename)
    #csvreader = csv.reader(csvfile)
    csvreader = csv.reader(open(args.CSVFilename))
    for clip in csvreader:
        if len(clip) == 0:
            continue
        SourceFilename, StartTime, EndTime, LevelAdjust, OutputFile = \
            clip[0], float(clip[1]), float(clip[2]), float(clip[3]), clip[4]
        print(SourceFilename, StartTime, EndTime, LevelAdjust, OutputFile)

        if not(PreviousSource == SourceFilename):
            print("Opening {}".format(SourceFilename))
            SourceAudio = AudioSegment.from_file(SourceFilename, "wav")
            PreviousSource = SourceFilename

        AudioClip = SourceAudio[int(1000*StartTime):int(1000*EndTime)]
        #AudioClip = SourceAudio[int(1000*StartTime):int(1000*EndTime)] + LevelAdjust
        AudioClip.export(OutputFile, format="wav")
