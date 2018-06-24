#! /usr/bin/python3
#

from PIL import Image
import sys
import statistics

import pyocr
import pyocr.builders

infile = sys.argv[1]
img=Image.open(infile)

textord_min_xheight = 10 # from the docs

tools = pyocr.get_available_tools()
# The tools are returned in the recommended order of usage
tool = tools[1] ## prefer libtesseract over tesseract shell over cuneyform

langs = tool.get_available_languages()
# Note that languages are NOT sorted in any way. Please refer
# to the system locale settings for the default language
# to use.
print(tools)
print(langs)

def avg_dev(data, dev=-1):
  """calculate the value of dev standard-deviations away
     from the arithmetiv mean.
  """
  mu = statistics.mean(data)
  return mu + dev*statistics.pstdev(data, mu)


def word_stats(wordboxdata):
  """compute a represetitive text height and confidence value.
     returns a tuple of (listlen, height, confidence)
     where listlen is the number of usable words in the computation.
     if listlen is 0, the tuple (0, None, None) is returned.
  """
  twords = list(filter(lambda x: len(x.content)>1, wordboxdata))
  if len(twords) < 2:
    twords = list(filter(lambda x: len(x.content) > 0 and x.content != ' ', wordboxdata))
  if len(twords):
    conf_l = list(map(lambda x: x.confidence, twords))
    height_l = list(map(lambda x: x.position[1][1]-x.position[0][1], twords))
    return (avg_dev(conf_l), avg_dev(height_l), len(twords))
  return (None, None, 0)


lang='eng'
# lang='deu'
words = tool.image_to_string(img, lang=lang, builder=pyocr.builders.WordBoxBuilder() )

# tesseract has textord_min_xheight=10  # Min credible pixel xheight
# let us check the boxes that we got,
# if the average height is smaller than 2*textord_min_xheight, scale up.
(a1d_c, a1d_h, tlen) = word_stats(words)
scale = 1
if tlen > 0:
  if a1d_h < 2*textord_min_xheight:
    scale = 2*textord_min_xheight / a1d_h
  # scale up eiher factor 2, 3, or 4 -- nothing else.
  if scale > 1:
    if scale > 2.1:
      if scale > 3.2:
        scale = 4
      else:
        scale = 3
    else:
      scale = 2
else:
  scale = 3       # nothing recognized. try large scale up.
if scale > 1:
  print("avg1d(height)=%g, avg1d(confidence)=%g -> scaling up by %g" % (a1d_h, a1d_c, scale))
  img=img.resize( (int(0.5+img.width*scale), int(0.5+img.height*scale)), Image.BICUBIC)
  words = tool.image_to_string(img, lang=lang, builder=pyocr.builders.WordBoxBuilder() )
  (a1d_c, a1d_h, tlen) = word_stats(words)
  print("improved avg1d(confidence)=%g" % (a1d_c))


print(infile)
for w in words:
  print(w.content, w.position, w.confidence)
