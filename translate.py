import re
import pyscreenshot
import cv2
import pykakasi
import pyautogui
from googletrans import Translator
from google.cloud import vision
import io
import os

# You can mod this program to translate any language. Just change the screen_translate implementation
# and these variables.
source = "ja"
destination = "en"

# Setting basic, everywhere needed info up.
application_name = "Image translator (press q to quit, press w to refresh, press f to take a full screenshot)"
transImg = "transImg.png"
fullImg = "fullImg.png"

width, height = pyautogui.size()
pyscreenshot.grab(bbox=(0, 0, width - 1, height - 1)).save(fullImg)
kks = pykakasi.kakasi()
translator = Translator()


def detect_text(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    l = []
    for text in texts[1:]:
        l.append(text.description)
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    return ''.join(l)


def screen_translate():
    string = detect_text(transImg)
    result = kks.convert(string)
    # Tweak the loop for wanted results.
    for item in result:
        if re.search(u'[\u4e00-\u9fff]', item['orig']):
            print("{}: '{}': {}".format(item['orig'], item['hira'],
                                        translator.translate(item['orig'], src=source, dest=destination).text))
    translated = translator.translate(string, src=source, dest=destination)
    print(translated.text)


# Code (Modified) from
# https://www.life2coding.com/crop-image-using-mouse-click-movement-python/
cropping = False
croppingImg = False
x_start, y_start, x_end, y_end = 0, 0, 0, 0
x_startPos, y_startPos, x_endPos, y_endPos = 0, 0, width, height
picture = cv2.imread(fullImg)
oriImage = picture.copy()


def write_image(image_name, ref_point):
    if len(ref_point) == 2:  # when two points were found
        roi = oriImage[ref_point[0][1]:ref_point[1][1], ref_point[0][0]:ref_point[1][0]]
        cv2.imwrite(image_name, roi)


def mouse_crop(event, x, y, flags, param):
    # grab references to the global variables
    global x_start, y_start, x_end, y_end, cropping, croppingImg, oriImage, x_startPos, y_startPos, x_endPos, y_endPos
    # if the left mouse button was DOWN, start RECORDING
    # (x, y) coordinates and indicate that cropping is being
    if event == cv2.EVENT_LBUTTONDOWN:
        x_start, y_start, x_end, y_end = x, y, x, y
        cropping = True
    elif event == cv2.EVENT_RBUTTONDOWN:
        x_startPos, y_startPos, x_endPos, y_endPos = x, y, x, y
        croppingImg = True
    # Mouse is Moving
    elif event == cv2.EVENT_MOUSEMOVE:
        if cropping:
            x_end, y_end = x, y
        if croppingImg:
            x_endPos, y_endPos = x, y
    # if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates
        x_end, y_end = x, y
        cropping = False # cropping is finished
        write_image(transImg, [(x_start, y_start), (x_end, y_end)])
        screen_translate()
    elif event == cv2.EVENT_RBUTTONUP:
        # record the ending (x, y) coordinates
        x_endPos, y_endPos = x, y
        croppingImg = False  # cropping is finished
        write_image(fullImg, [(x_startPos, y_startPos), (x_endPos, y_endPos)])


cv2.namedWindow(application_name)
cv2.setMouseCallback(application_name, mouse_crop)

# Run the "GUI" in a while-loop
while True:
    cv2.waitKey(1)
    i = picture.copy()
    if not cropping:
        cv2.imshow(application_name, picture)
    elif cropping:
        cv2.rectangle(i, (x_start, y_start), (x_end, y_end), (255, 0, 0), 2)
        cv2.imshow(application_name, i)
    # If press q quit the application.
    if (cv2.waitKey(1) & 0xFF) == ord("q"):
        cv2.waitKey(1)
        break
    # If press w update the area with new information.
    if (cv2.waitKey(1) & 0xFF) == ord("w"):
        pyscreenshot.grab(bbox=(x_startPos, y_startPos, x_endPos, y_endPos)).save(fullImg)
        cv2.waitKey(50)
        picture = cv2.imread(fullImg)
        oriImage = picture.copy()
    # If press f take a screenshot of the whole desktop.
    if (cv2.waitKey(1) & 0xFF) == ord("f"):
        pyscreenshot.grab().save(fullImg)
        cv2.waitKey(50)
        picture = cv2.imread(fullImg)
        oriImage = picture.copy()

os.remove("fullImg.png")
os.remove("transImg.png")
cv2.destroyAllWindows()
