#from .src import mic as m
from .src import image as i
from .src import lines as l

def run():
#    text = m.start()
    # for debugging: 
    #text = ["get more", "tonic"]
    text = ["call", "gabriel", "and", "laugh"]
    i.set_image(text)
    path = "voicepen/images/text.png"
    l.main(path)