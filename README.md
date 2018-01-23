# YouTube Reaction Face Finder

<p align="center"><img src="readme/pres_header.png" height="125"/></p>

This repo has code to extract 'reaction' faces from a given YouTube video.  Huge thanks to [Adrian](https://twitter.com/PyImageSearch) at [PyImageSearch](https://www.pyimagesearch.com/) for his book, [Deep Learning for Computer Vision with Python](https://www.pyimagesearch.com/deep-learning-computer-vision-python-book/).  Adrian and the book gave me all the tools needed for building the emotion model.

The code requires `opencv` & `keras` (model trained with TensorFlow backend).

## Example Output

Output from video: [Donald Trump funny faces at the CNN GOP Debate](https://www.youtube.com/watch?v=tVb0g0-JCfk).

<table width="500" border="0" cellpadding="5">

<tr>

<td align="center" valign="center">
<img src="output/angry.jpg" height=100 />
<br />
Angry
</td>

<td align="center" valign="center">
<img src="output/neutral.jpg" height=100 />
<br />
Neutral
</td>

<td align="center" valign="center">
<img src="output/happy.jpg" height=100 />
<br />
Happy
</td>

</tr>

</table>

## Usage

`youtube_react_face.py -y YOUTUBEURL -o OUTPUT [-m MAXFRAMES]`

#### Required Arguments:

    -y YOUTUBEURL, --youtubeURL YOUTUBEURL
                        url for youtube video to find reaction faces in
    -o OUTPUT, --output OUTPUT
                        dir to output reactions to
                        
#### Optional Arguments:

    -m MAXFRAMES, --maxFrames MAXFRAMES
                        stop processing video frames after this many (default 5000)
                        
#### Example command (run in repo dir)

`python youtube_react_face.py --youtubeURL https://www.youtube.com/watch?v=tVb0g0-JCfk --output output`
