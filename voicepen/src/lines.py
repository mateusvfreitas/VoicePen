import numpy as np
import cv2

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

    cv2.imshow("teste", borders)
    cv2.waitKey()

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
            if(PX[col, row] == 255):
                if((PX[col+1, row] == 255 and PX[col-1, row] == 0) or (PX[col+1,row] == 0 and PX[col-1,row] == 255)):
                    coord.append((col, row))
            else:
                if(len(coord) > 0):
                    pixels.append(coord)
                    coord = []

    for col in range(1,width):
        coord = []
        for row in range(height-1):
            if(PX[col, row] == 255):
                if((PX[col, row+1] == 255 and PX[col, row-1] == 0) or (PX[col,row+1] == 0 and PX[col,row-1] == 255)):
                    coord.append((col, row))
            else:
                if(len(coord) > 0):
                    pixels.append(coord)
                    coord = []

    return pixels


''' BLOCK OF CODE TO TEST FUNCTIONS '''
image = "images/text.png"
find_edges(image)