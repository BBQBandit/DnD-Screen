# -*- coding: utf-8 -*-

"""
großer TV : 40 px/square
kleiner tv wohnung 82 px/square

ToDo
check why moving map is so slow
"""

camMoveDistance = 82

import pygame
import math
import time
import numpy as np
import cv2
import re

cap = cv2.VideoCapture(0)
qrDecoder = cv2.QRCodeDetector() # Init

pygame.init()

height = 1080 #ToDo get screen resolution from system
width = 1920

"""
HSV values for detecting gray
"""
gray1 = 67
gray2 = 0.01
gray3 = 68
tolerance_gray = 5

tolerance = 20 #Offset from the border of the screen to prevent false detections at the border
lowerborderx = tolerance
upperborderx = width - tolerance
lowerbordery = tolerance
upperbordery = height - tolerance

corner00 = []
corner11 = []

"""
Load Image for QR Code, map & mask
"""
x0y0 = pygame.image.load('00.png')
x0y0rect = x0y0.get_rect()
picture = pygame.image.load('F:\pathfinder\FortBruchhügel\Eastwing_wohnung.png')
mask = pygame.image.load('F:\pathfinder\FortBruchhügel\Eastwing_wohnung_mask.png')

#picture = pygame.image.load('bridges.png')
#mask = pygame.image.load('bridges_mask.png')

maskrect = mask.get_rect()
#ToDo: Make fancy GUI for the selection

camerax = 0
cameray = 0

cameraCirclex = 0
cameraCircley = 0

win = pygame.display.set_mode((width, height), pygame.FULLSCREEN, pygame.NOFRAME) # Initialize PyGame window

def apply_alpha(texture, mask):
    texture = texture.convert_alpha()
    target = pygame.surfarray.pixels_alpha(texture)
    target[:] = pygame.surfarray.array2d(mask)
    del target
    return texture

def stamp(image, texture, mask):
    lastpic = apply_alpha(texture, mask)
    image.blit(lastpic, (camerax, cameray))


def get_ray_pos(pos, angle): #Check for LOS obstructing elements, starting at pos along a line defined by angle
    n = 0
    m = 0
    hotFlag = False

    while (pos[1] - n) > 0 and (pos[1] - n) < mask.get_height() and (pos[0] - m) > 0 and (pos[0] - m) < mask.get_width():
        try:
            colour = mask.get_at((int(pos[0] - m) ,int(pos[1] - n)))
            if colour == (0,0,0,255) and not hotFlag:
                hotFlag = True
            if colour != (0,0,0,255) and hotFlag:
                break
            else:
                m+= math.cos(angle*math.pi/180)
                n+= math.sin(angle*math.pi/180)
        except:
            pass

    return (pos[0] - m, pos[1]-n)

def  parse_vertix(bb): #Makeshift parser for the QR-reader response for position
    test = str(bb)
    first = test.split(".")
    x = int(re.sub("[^0-9]", "",re.findall(r'\d+', first[0])[0]))
    temp = re.findall(r'\d+', first[1])
    y = int(re.sub("[^0-9]", "", temp[-1]))

    return [x,y]

def transform (pos, top_left_corner, bottom_right_corner):  #Transform coordinates from Cam reference to Screen reference
    top_left_corner = parse_vertix(top_left_corner)
    bottom_right_corner = parse_vertix(bottom_right_corner)
    #tempx = (pos[0] * (width - top_left_corner[0]) / bottom_right_corner[0] - top_left_corner[0]) / 2
    tempx = width * ((pos[0]-top_left_corner[0]) / (bottom_right_corner[0] - top_left_corner[0]))
    #tempy = pos[1] * (height - top_left_corner[1]) / bottom_right_corner[1] - top_left_corner[1] * 2
    tempy = height * ((pos[1]-top_left_corner[1]) / (bottom_right_corner[1] - top_left_corner[1]))
    return (camMoveDistance * math.ceil((tempx - camerax) / camMoveDistance) - camMoveDistance / 2, camMoveDistance * math.ceil((tempy - cameray) / camMoveDistance)  - camMoveDistance / 2)

def isGray (center, radius, feed, contour): #WIP colour detecting to ignore gray minis (monsters in my case)
    center = int(center[0]), int(center[1])
    hsv = cv2.cvtColor(feed, cv2.COLOR_BGR2HSV)
    #h,w,z = feed.shape
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask,contour,-1,255,-1)
    #cv2.circle(mask, center, int(radius), 255, -1)
    mm = cv2.mean(hsv, mask)
    mn = tuple(i/j for i,j in zip(mm, (0.5, 255, 255, 1)))
    print (mn)
    #hist = cv2.calcHist([feed], [0,1,2], mask, [256,256,256], [0,256,0,256,0,256])
    #ma = np.unravel_index(hist.argmax(), hist.shape)
    return mn

centers = []
run = True

while run: # Main PyGame loop

    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, th3 = cv2.threshold(gray,75,255,cv2.THRESH_BINARY)
    cv2.imshow('frame',th3)



    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_w:
                cameray -= camMoveDistance
                cameraCircley -= camMoveDistance
                print(cameray)
            if event.key == pygame.K_s:
                cameray += camMoveDistance
                cameraCircley += camMoveDistance
                print(cameray)
            if event.key == pygame.K_a:
                camerax -= camMoveDistance
                cameraCirclex -= camMoveDistance
                print(camerax)
            if event.key == pygame.K_d:
                camerax += camMoveDistance
                cameraCirclex += camMoveDistance
                print(camerax)

            if event.key == pygame.K_ESCAPE:
                """
                necessary if you displayed the webcam feed
                """
                cv2.destroyAllWindows()

                pygame.quit()
            if event.key == pygame.K_c: # "c" key for "calibrating" - reading the QR Codes

                """
                Read the top-left QR code
                """
                read = True
                while read:
                    pygame.event.get()
                    win.fill((255,255,255))
                    win.blit(x0y0, [0,0])
                    pygame.display.flip()
                    ret, frame = cap.read()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    ret, th3 = cv2.threshold(gray,75,255,cv2.THRESH_BINARY)
                    #th3 = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,21,10)
                    """
                    un-comment this below to show a window of the webcam-feed (for setting up)
                    """
                    cv2.imshow('frame',th3)
                    try:
                        data,bbox,rectifiedImage = qrDecoder.detectAndDecode(th3)
                    except Exception:
                        pass #QR-Code module occasionally throws exceptions ¯\_(ツ)_/¯
                    if data == '00':
                        read = False
                        corner00 = bbox[0]
                        break
                    print('no QR found')
                """
                Fill the screen
                check the pygame docs for further info
                """
                win.fill((255,255,255))
                win.blit(x0y0, [width-x0y0rect.width,height-x0y0rect.height])
                pygame.display.flip()

                time.sleep(2)   #Delay for the screen to update & webcam to adjust


                #reading the second QR code - should have defined a function
                read = True
                while read:
                    pygame.event.get()
                    win.fill((255,255,255))
                    win.blit(x0y0, [width-x0y0rect.width,height-x0y0rect.height])
                    pygame.display.flip()
                    ret, frame = cap.read()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    ret, th3 = cv2.threshold(gray,75,255,cv2.THRESH_BINARY)
                    #th3 = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,15,8)
                    cv2.imshow('frame',th3)
                    try:
                        data,bbox,rectifiedImage = qrDecoder.detectAndDecode(th3)
                    except Exception:
                        pass #QR-Code module occasionally throws exceptions ¯\_(ツ)_/¯
                    if data == '00':
                        read = False
                        corner11 = bbox[2]
                        break
                    print('no QR found')

                """
                necessary if you displayed the webcam feed
                """
                #cv2.destroyAllWindows()

                win.fill((255,255,255))
                pygame.display.flip()
                time.sleep(2)


            if event.key == pygame.K_SPACE: #Press space to run the LOS programm (after calibrating)

                cameraCirclex = 0
                cameraCircley = 0
                centers = []

                win.fill((255,255,255))
                #pygame.draw.circle(win, (255,0,0), (int(corner00[0]), int(corner00[1])), 50) #Draw detected top left corner on screen
                #pygame.draw.circle(win, (255,0,0), (int(corner11[0]), int(corner11[1])), 50) #Draw detected bottom right corner on screen
                pygame.display.flip()
                time.sleep(2)

                for abc in range(20):   #having some dummy readings seems to help with detection
                    ret, frame = cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  #Create grayscale image
                ret, th3 = cv2.threshold(gray,75,255,cv2.THRESH_BINARY) #Apply Treshhold to pixel values (grayscale -> Black & white only)
                #th3 = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,15,8)
                #cv2.imshow('frame',th3)

                contours,hie = cv2.findContours(th3,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)    #This is where all "contours" are detected


                if contours != []:
                    for contour in contours:
                        center, radius = cv2.minEnclosingCircle(contour)
                        """
                        Huge if statement,
                        filters out contours that are too small/large to be a proper detection
                        filters out contours that are too close to the border
                        (had some issues with false positives at the edge of the screen)
                        """
                        if radius > 15 and radius < 100 and center[0] > lowerborderx and center[0] < upperborderx and center[1] > lowerbordery and center[1] < upperbordery:
                            """
                            First attempts at colour detection
                            """
                            g1, g2, g3,g4 = isGray(center, radius, frame, contour)
                            if g2 > gray2:
                                cv2.circle(th3, (int(center[0]), int(center[1])), int(radius), (0, 255, 0), 3)
                                centers.append(transform(center, corner00, corner11)) # centers define the points where minis were detected

                cv2.waitKey(1)
                print("done")

            win.fill((0,0,0))

            for center in centers:
                corners = []
                for i in range(1,360, 5): # 360° FoV in 5° increments, decrease this angle for more accurate LoS
                    x = get_ray_pos(center,i)
                    corners.append(x)   # corners define the points of the polygon that defines the visible area for a contour/mini

                """
                "stamp" out the LoS polygon from the map-picture
                """
                #mask_calc = pygame.Surface((width,height), depth=8)
                mask_calc = pygame.Surface(picture.get_size(), depth=8)
                poly = pygame.draw.polygon(mask_calc, 255, corners, 0)
                stamp(win, picture,mask_calc)

            for center in centers:
                """
                draw a red circle where a mini was detected
                ToDo: make the colour of the circle the actual colour of the mini
                """
                pygame.draw.circle(win, (255,0,0), (int(center[0] + camerax), int(center[1] + cameray)), 50)

            pygame.display.flip()


pygame.quit()
