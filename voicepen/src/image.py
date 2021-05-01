from PIL import Image, ImageDraw, ImageFont
import textwrap

''' ---- GLOBALS ---- '''
# A5 paper size
# create Image object with the input image
image = Image.new("RGB", (1748, 2480), color = "white")
color = "rgb(0, 0, 0)" # black color
text_start_height = 150
text_start_width = 150

# initialise the drawing context with the image object as background
draw = ImageDraw.Draw(image)

# font type and size
font = ImageFont.truetype('/home/pi/git/VoicePen/voicepen/fonts/forced_square/thin.ttf', size=12)
''' ---- GLOBALS ---- ''' 

def draw_multiple_lines_text(image, text, text_start_height):
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=30)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text), 
                  line.upper(), font=font, fill=color)
        y_text += line_height + 2
    return y_text
    
def set_image(text):
    lh = text_start_height
    for item in text:
        next_line = draw_multiple_lines_text(image, item, lh)
        lh = next_line + 2
    # generates .png file on apropriate folder
    path = "/home/pi/git/VoicePen/voicepen/images/text.png"
    image.save(path)

    return path