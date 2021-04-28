from .src import mic as m
from .src import image as i
from .src import lines as l

def run():
    text = m.start()
    path = i.set_image(text)
    l.main(path)