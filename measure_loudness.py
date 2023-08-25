#!python3

# You may need to run "pip install pyloudnorm" before you can run this code
# You may need to run "pip install pysoundfile" before you can run this code

import os
import argparse
import soundfile
import pyloudnorm

parser = argparse.ArgumentParser(prog="measure_loudness.py",
            description="measure and report the loudness of an audio file")
parser.add_argument("filenames", help="audio file", nargs="*")
args = parser.parse_args()

for FileName in args.filenames:
    if not os.path.isfile(FileName):
        print("Warning: '{}' not found".format(FileName))
    else:
        data, rate = soundfile.read(FileName)
        meter = pyloudnorm.Meter(rate)
        loudness = meter.integrated_loudness(data)
        print("rate = {:,}Hz, loudness = {:4.1f}dB: '{}'".format(rate, loudness, FileName))
