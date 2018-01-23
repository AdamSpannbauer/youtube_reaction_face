
from pytube import YouTube
import re
import tempfile
import glob
import os

def yt_to_mp4(ytURL, dlDir=tempfile.mkdtemp()):
    #find youtube video
    yt = YouTube(ytURL)
    #filter to only mp4 files and take last in list (sorted lowest to highest quality)
    hqMp4 = yt.filter('mp4')[-1]
    #strip quality from video info.. example video info:
    m = re.search("- (\d\d\dp) -", str(hqMp4))
    #save quality capturing group
    quality = m.group(1)
    #get mp4 video with highest quality found
    video = yt.get('mp4', quality)
    #download and save video to specified dir
    video.download(dlDir)
    #return path to video
    mp4_paths = glob.glob("{}/*.mp4".format(dlDir))
    latest_mp4 = max(mp4_paths, key=os.path.getctime)
    return(latest_mp4)

