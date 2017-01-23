#!/usr/bin/env python

import os
import re
import cv2
import sys
import ast
import glob
import json
import time
import httplib
import random
import getopt
import shutil
import tempfile
import requests
import operator
import numpy as np
import pandas as pd
from pytube import YouTube
from collections import defaultdict
from dplython import (DplyFrame, X, select, arrange, mutate, group_by, ungroup, summarize, sift)

api_file = open('api_keys')
api_str = api_file.read()
api_keys = json.loads(api_str)

ms_key1 = api_keys['ms_key1'][0]

emotions = ["neutral", "anger", "disgust", "fear", "happy", "sadness", "surprise"]
#emotions = ["anger", "disgust", "fear", "happy", "sadness", "surprise"]
#ytURL    = "http://www.youtube.com/watch?v=-nQGBZQrtT0" #SNL debate skit
#ytURL    = "https://www.youtube.com/watch?v=kNZenoPC3Hs" #CNN: Trump and Clinton battle over presidential temperament
#ytURL    = "https://www.youtube.com/watch?v=yvlgt-7efdw" #the many faces of donald trump
#ytURL    = "https://www.youtube.com/watch?v=r9SvUJmLwOk" #costa on innovation
#ytURL = "https://www.youtube.com/watch?v=BsO3ZqO9yJ8" #fantastic 4cast

def downloadYtMp4(ytURL, dlDir=os.getcwd()):
    #find youtube video
    yt = YouTube(ytURL)
    #
    #filter to only mp4 files and take last in list (sorted lowest to highest quality)
    hqMp4 = yt.filter('mp4')[-1]
    #strip quality from video info.. example video info:
    m = re.search("- (\d\d\dp) -", str(hqMp4))
    #save quality capturing group
    quality = m.group(1)
    #
    #get mp4 video with highest quality found
    video = yt.get('mp4', quality)
    #download and save video to specified dir
    video.download(dlDir)

def mp4Frames(ytURL, picDir, maxCount):
    dirpath = tempfile.mkdtemp()
    print("downloading yt video to tmp dir: %s" % dirpath)
    downloadYtMp4(ytURL, dirpath)
    mp4File = glob.glob("%s/*.mp4" % dirpath)[0]
    #
    vidcap = cv2.VideoCapture(mp4File)
    success = True
    count = 0
    framesRead = 0
    while success:
        success, image = vidcap.read()
        if framesRead == maxCount:
            success = False
        if count%30 == 0:
            framesRead += 1
            #print 'Read a new frame: ', success
            if success:
                cv2.imwrite("%s/frame%d.jpg" % (picDir, count), image)     # save frame as JPEG file
        count += 1
    shutil.rmtree(dirpath)

def getNewInstances(ytURL, faceDet, faceDet2, faceDet3, faceDet4, maxCount):
    framepath = tempfile.mkdtemp()
    #
    mp4Frames(ytURL, framepath, maxCount)
    #
    files = glob.glob("%s/*" %framepath) #Get list of all images with emotion
    #
    prediction_data   = []
    predictDataSrcImg = []
    predictFaceDims   = []
    fileInd = 0
    for f in files:
        fileInd += 1
        print("detecting faces in frame: %d of %d" %(fileInd, files.__len__()))
        if f[-9:] != "Thumbs.db": #f windows
            #
            frame = cv2.imread(f) #Open image as grayscale
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #Convert image to grayscale
            #
            #Detect face using 4 different classifiers
            face = faceDet.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5), flags=cv2.CASCADE_SCALE_IMAGE)
            face2 = faceDet2.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5), flags=cv2.CASCADE_SCALE_IMAGE)
            face3 = faceDet3.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5), flags=cv2.CASCADE_SCALE_IMAGE)
            face4 = faceDet4.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5), flags=cv2.CASCADE_SCALE_IMAGE)
            #
            #Go over detected faces, stop at first detected face, return empty if no face.
            if len(face) == 1:
                facefeatures = face
            elif len(face2) == 1:
                facefeatures = face2
            elif len(face3) == 1:
                facefeatures = face3
            elif len(face4) == 1:
                facefeatures = face4
            else:
                facefeatures = None
            #
            if facefeatures is not None:
                #Cut and save face
                for (x, y, w, h) in facefeatures: #get coordinates and size of rectangle containing face
                    #print "\tface found in file: %s" %f
                    gray = gray[y:y+h, x:x+w] #Cut the frame to size
                    #
                    try:
                        out = cv2.resize(gray, (350, 350)) #Resize face so all images have same size
                        prediction_data.append(out)
                        predictDataSrcImg.append(frame)
                        predictFaceDims.append([x, y, w, h])
                    except:
                       pass #If error, pass file
                       #
    shutil.rmtree(framepath)
    return prediction_data, predictDataSrcImg, predictFaceDims

def processRequest(image, headers):
    #
    tempDir = tempfile.mkdtemp()
    #
    ms_api = 'https:://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'
    #
    imagePath = "%s/singleFrame.jpg" % tempDir
    cv2.imwrite(imagePath, image)
    #
    with open(imagePath, 'rb') as f:
        data = f.read()
    #
    shutil.rmtree(tempDir)
    #
    json = None
    params = None
    retries = 0
    result = None
    #
    while True:
        try:
            conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
            conn.request("POST", "/emotion/v1.0/recognize", data, headers)
            response = conn.getresponse()
            response_data = response.read()
            conn.close()
            result = ast.literal_eval(response_data)
            break
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
            if retries <= 5:
                time.sleep(1)
                retries += 1
                continue
            else:
                print( 'Error: failed after retrying!' )
                result = None
                break
    #
    return result

def main(argv):
    ytURL = None
    outdir = None
    maxFrames = 500
    try:
        opts, args = getopt.getopt(argv,"hy:o:m:",["yturl=","odir=","maxframes="])
    except getopt.GetoptError:
        print 'Error: shellScript.py -y <yturl> -o <odir> -m <maxframes>'
        sys.exit(2)
    #print opts
    for opt, arg in opts:
        if opt == '-h':
            print 'help: shellScript.py -y <yturl> -o <odir> -m <maxframes>'
            sys.exit()
        elif opt in ("-y", "--yturl"):
            print("--yturl={}".format(arg))
            ytURL = arg
        elif opt in ("-o", "--odir"):
            print("--odir={}".format(arg))
            outdir = arg
        elif opt in ("-m", "--maxframes"):
            print("--maxframes={}".format(arg))
            maxFrames = int(arg)
    #
    if ytURL is None:
        print 'bad yt: shellScript.py -y <yturl> -o <odir> -m <maxframes>'
        sys.exit()
    #
    if outdir is None:
        print 'bad outdir: shellScript.py -y <yturl> -o <odir> -m <maxframes>'
        sys.exit()
    #
    if False == isinstance(maxFrames, (int, long)):
        print 'bad maxFrames: shellScript.py -y <yturl> -o <odir> -m <maxframes>'
        sys.exit()
    #
    #
    faceDet  = cv2.CascadeClassifier("haarcascade/haarcascade_frontalface_default.xml")
    faceDet2 = cv2.CascadeClassifier("haarcascade/haarcascade_frontalface_alt2.xml")
    faceDet3 = cv2.CascadeClassifier("haarcascade/haarcascade_frontalface_alt.xml")
    faceDet4 = cv2.CascadeClassifier("haarcascade/haarcascade_frontalface_alt_tree.xml")
    #
    pdata, pframes, pfacedims = getNewInstances(ytURL, faceDet, faceDet2, faceDet3, faceDet4, maxCount=maxFrames)
    #
    headers = dict()
    headers['Ocp-Apim-Subscription-Key'] = ms_key1
    headers['Content-Type'] = 'application/octet-stream'
    #
    resultsDf = pd.DataFrame()
    frameId = 0
    for image in pframes:
        print ("posting frame %d of %d" %(frameId,len(pframes)))
        resultMS = processRequest(image, headers)
        #
        if isinstance(resultMS, list):
            for result in resultMS:
                if isinstance(result, dict):
                    resFrameList = []
                    for res in result['scores'].items():
                        resFrameList.append((frameId,res[0],res[1],
                                             result["faceRectangle"]['left'],
                                             result["faceRectangle"]['top'],
                                             result["faceRectangle"]['width'],
                                             result["faceRectangle"]['height']))
                        appendDf = pd.DataFrame(resFrameList, columns=["frameId", "emotionLabel", "conf", "faceleft","facetop","faceW","faceH"])
                        resultsDf = resultsDf.append(appendDf)
        time.sleep(2)
        frameId += 1
    #
    dfFaces = DplyFrame(resultsDf)
    #
    topFaces = (dfFaces >>
                   group_by(X.emotionLabel) >>
                   sift(X.conf == X.conf.max()) >>
                   sift(X.frameId == X.frameId.min()) >>
                   ungroup() >>
                   group_by(X.frameId) >>
                   sift(X.conf == X.conf.max()) >>
                   ungroup() >>
                   arrange(X.emotionLabel))

    topFaces = topFaces.drop_duplicates()
    #print(topFaces)
    #
    i = 0
    for index, row in topFaces.iterrows():
        print ("saving emotion frame %d of %d" %(i,len(topFaces.index)))
        #
        emotion = row["emotionLabel"]
        confid  = int(row["conf"]*100)
        image   = pframes[int(row["frameId"])]
        faceL = row["faceleft"]
        faceT = row["facetop"]
        faceW = row["faceW"]
        faceH = row["faceH"]
        #
        #save cropped face
        imageW = image[faceT:faceT+faceH, faceL:faceL+faceW]
        cv2.imwrite(os.path.expanduser("%s/Cropped_%s.jpg" % (outdir, emotion)), imageW)
        #
        cv2.rectangle( image,(faceL,faceT),
                      (faceL+faceW, faceT + faceH),
                       color = (255,0,0), thickness = 5 )
        cv2.putText( image, emotion, (faceL,faceT-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1 )
        #
        cv2.imwrite(os.path.expanduser("%s/box%s.jpg" % (outdir, emotion)), image)
        i += 1

if __name__ == "__main__":
   main(sys.argv[1:])
