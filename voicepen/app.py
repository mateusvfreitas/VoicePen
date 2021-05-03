from .src import mic
from .src import image
from .src import lines
from .src import control
import importlib

def run():
    m = importlib.reload(mic)
    i = importlib.reload(image)
    l = importlib.reload(lines)
    c = importlib.reload(control)

    text = m.start()
    path = i.set_image(text)
    l.main(path)

    vp = c.VoicePen()
    vp.draw_from_file("/home/pi/git/VoicePen/voicepen/text.json")

while True:
    run()
