import numpy as np
import cv2
from PIL import Image
import math
import json


def main(image):
    # contours = sortlines(get_contours(image))
    lines = get_contours(image)
    
    f = open("voicepen/images/text.svg", 'w')
    f.write(makesvg(lines))
    f.close()

    lines_to_json_file(lines, "text.json")

    return lines

def get_contours(image):
    print("getting contours...")
    image = find_edges(image)
    img = image.copy()
    img_pixels = get_pixels(img)

    return img_pixels

def find_edges(image):
    print("finding edges...")
    img = cv2.imread(image)
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (thresh, b_w) = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV)

    borders = np.zeros(b_w.shape, np.uint8)
    contours = cv2.findContours(b_w, cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[0][:]
    cv2.drawContours(borders, list(contours), -1, 255, 1)

    image = Image.fromarray(borders)
    return image

def get_pixels(img):
    print("getting pixels...")
    matrix = img.load()
    pixels = []

    width, height = img.size

    for row in range(height-1):
        coord = []
        for col in range(1,width):
            if(matrix[col, row] == 255):
                if((matrix[col+1, row] == 255 and matrix[col-1, row] == 0) or (matrix[col+1,row] == 0 and matrix[col-1,row] == 255)):
                    coord.append(col, row)
            else:
                if(len(coord) > 0):
                    pixels.append(coord)
                    coord = []

    for col in range(1,width):
        coord = []
        for row in range(height-1):
            if(matrix[col, row] == 255):
                if((matrix[col, row+1] == 255 and matrix[col, row-1] == 0) or (matrix[col,row+1] == 0 and matrix[col,row-1] == 255)):
                    coord.append(col, row)
            else:
                if(len(coord) > 0):
                    pixels.append(coord)
                    coord = []

    return pixels

def lines_to_json_file(lines, filename):
    with open(filename, "w") as file_to_save:
        json.dump(lines, file_to_save, indent=4)


''' BLOCK OF CODE TO TEST FUNCTIONS '''
def makesvg(lines):
    print("generating svg file...")
    width = math.ceil(max([max([p[0]*0.5 for p in l]) for l in lines]))
    height = math.ceil(max([max([p[1]*0.5 for p in l]) for l in lines]))
    out = '<svg xmlns="http://www.w3.org/2000/svg" height="%spx" width="%spx" version="1.1">' % (height, width)

    for l in lines:
        l = ",".join([str(p[0]*0.5)+","+str(p[1]*0.5) for p in l])
        out += '<polyline points="'+l+'" stroke="black" stroke-width="1" fill="none" />\n'
    out += '</svg>'
    return out
    
image = "voicepen/images/text3.png"
main(image)