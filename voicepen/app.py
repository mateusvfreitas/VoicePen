from .src import listen as l
from .src import image as i

def run():
    text = l.start()
    i.set_image(text)