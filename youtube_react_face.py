# USAGE
# python youtube_react_face.py --youtubeURL https://www.youtube.com/watch?v=tVb0g0-JCfk --output output

# import the necessary packages
from keras.preprocessing.image import img_to_array
from keras.models import load_model
import numpy as np
import argparse
import imutils
import cv2
import utils
from progress.bar import IncrementalBar

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-y", "--youtubeURL", required=True,
	help="url for youtube video to find reaction faces in")
ap.add_argument("-o", "--output", required=True,
	help="dir to output reactions to")
ap.add_argument("-m", "--maxFrames", default=5000, type=int,
	help="stop processing video frames after this many (default 5000)")
args = vars(ap.parse_args())

# load the face detector cascade, emotion detection CNN, then define
# the list of emotion labels
detector = cv2.CascadeClassifier('haarcascade/haarcascade_frontalface_default.xml')
model = load_model('model/keras_emotion_mod.hdf5')
EMOTIONS = ["angry", "scared", "happy", "sad", "surprised", "neutral"]

#store values of most representative face of each emotion
react_vals = {"angry": 0.5,
			  "scared": 0.5,
			  "happy": 0.5,
			  "sad": 0.5,
			  "surprised": 0.5,
			  "neutral": 0.5}

#download youtube video
video_path = utils.yt_to_mp4(args['youtubeURL'])

#start vid cap
camera = cv2.VideoCapture(video_path)
# get vid frame count
vid_frame_count = int(camera.get(cv2.CAP_PROP_FRAME_COUNT))

#set max frames
if args['maxFrames'] > 0:
	max_frames = min(args['maxFrames'], vid_frame_count-1)
else:
	max_frames = vid_frame_count-1


bar = IncrementalBar('Processing', max=max_frames)
counter = 0
# keep looping
while True:
	counter += 1
	if counter > max_frames:
		break
	bar.next()
	# grab the current frame
	(grabbed, frame) = camera.read()

	# if we are viewing a video and we did not grab a
	# frame, then we have reached the end of the video
	if not grabbed:
		break

	# resize the frame and convert it to grayscale
	frame = imutils.resize(frame, width=300)
	# cv2.imshow('frame', frame)
	# cv2.waitKey(5)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# detect faces in the input frame, then clone the frame so that
	# we can draw on it
	rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
		minNeighbors=5, minSize=(30, 30),
		flags=cv2.CASCADE_SCALE_IMAGE)

	# ensure at least one face was found before continuing
	if len(rects) > 0:
		# get top 3 biggest faces
		rects = sorted(rects, reverse=True,
			key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[:3]
		for rect in rects:
			(fX, fY, fW, fH) = rect

			# extract the face ROI from the image, then pre-process
			# it for the network
			roi = gray[fY:fY + fH, fX:fX + fW]
			roi = cv2.resize(roi, (48, 48))
			roi = roi.astype("float") / 255.0
			roi = img_to_array(roi)
			roi = np.expand_dims(roi, axis=0)

			# make a prediction on the ROI
			preds = model.predict(roi)[0]
			# get val of most confident class
			max_pred = preds[preds.argmax()]
			# lookup the class label
			label    = EMOTIONS[preds.argmax()]

			#if new pred more confident than current largest
			#save new max confidence and most representative face
			if max_pred > react_vals[label]:
				react_vals[label] = max_pred
				out_file = "{out}/{lab}.jpg".format(out=args['output'],lab= label, pred= max_pred, prec=2)
				cv2.imwrite(out_file, frame[fY:fY + fH, fX:fX + fW])

bar.finish()

