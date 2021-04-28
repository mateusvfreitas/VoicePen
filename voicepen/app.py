from .src import mic as m
from .src import image as i
from .src import lines as l
from .src import control as c

def run():
    text = m.start()
    path = i.set_image(text)
    l.main(path)

    vp = c.VoicePen()
    vp.draw_from_file("/home/pi/git/VoicePen/voicepen/text.json")