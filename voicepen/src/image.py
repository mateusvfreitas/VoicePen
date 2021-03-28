from PIL import Image, ImageDraw, ImageFont
import textwrap

''' ---- GLOBALS ---- '''
# A5 paper size
# create Image object with the input image
image = Image.new("RGB", (1748, 2480), color = "white")
color = "rgb(0, 0, 0)" # black color
text_start_height = 150
text_start_width = 150
text = ["I went to the market and bought some apples and some milk", "I need to call the doctor's office, can you do it for me?"] # local tests only
 
# initialise the drawing context with the image object as background
draw = ImageDraw.Draw(image)

# create font object with the font file and specify
# desired size
font = ImageFont.truetype('Arial_Bold.ttf', size=70)
''' ---- GLOBALS ---- ''' 

def draw_multiple_lines_text(image, text, text_start_height):
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=40)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text), 
                  line, font=font, fill=color)
        y_text += line_height
    return y_text
    
def set_image(text):
    lh = text_start_height
    for item in text:
        next_line = draw_multiple_lines_text(image, item, lh)
        lh = next_line + 150
    # generates bmp file on apropriate folder
    image.save("voicepen/images/text.bmp")

# TODO: use line below if testing file alone
set_image(text)