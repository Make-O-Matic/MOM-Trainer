#!/usr/bin/env python
import sys
import subprocess

if __name__== '__main__':

    #execute command:
    #ffmpeg -i input.wmv -ss 00:00:30.0 -c copy -t 00:00:10.0 output.wmv
    #ffmpeg -i input.wmv -ss 30 -c copy -t 10 output.wmv
    #source: http://superuser.com/questions/138331/using-ffmpeg-to-cut-up-video

    #slice in many Segments at once
    #source: http://stackoverflow.com/questions/5651654/ffmpeg-how-to-split-video-efficiently

    sliceAt = 30 #Begin: Seconds
    sliceUntil = 10 #Duration: Seconds
    inputFile = "videos/rotated.mp4"
    outputFile1 = "videos/sliced-1.mp4"
    outputFile2 = "videos/sliced-2.mp4"

    subprocess.call(['ffmpeg', '-i', inputFile, '-ss', str(sliceAt), '-c', 'copy', '-t', str(sliceUntil), outputFile1])
    subprocess.call(['ffmpeg', '-i', inputFile, '-ss', str(sliceAt+sliceUntil), '-c', 'copy', '-t', str(sliceAt*3), outputFile2])
