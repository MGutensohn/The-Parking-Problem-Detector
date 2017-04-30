# import the necessary packages

import os
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
from uuid import uuid4
import MySQLdb

res_y = 1088
res_x = 1920

#This is where we set up the regions of interest (ROI)
spot_one_ROI = res_x // 4
spot_two_ROI = spot_one_ROI * 2
spot_three_ROI = spot_one_ROI * 3

camera = PiCamera()
camera.resolution = (res_x,res_y)
rawCapture = PiRGBArray(camera)

cars_cascade = cv2.CascadeClassifier('anchor_cascade.xml')

time.sleep(.3)


#Set up table values for this specific CarDetector
level = 'parkinglevel1'
spot_one = 001
spot_one_occupied = 0
spot_two = 002
spot_two_occupied = 0
spot_three = 003
spot_three_occupied = 0
spot_four = 004
spot_four_occupied = 0
pi_id = 0001



def insert_spot_data(spotData):
    '''
    Inserts updated table values into its perspective table in the parking databased
    
    :param spotData: An array of tuples containing table values for each spot entry.
    
    :return: Nothing.
    '''
    query = "INSERT INTO " + level + " (spot_id,spot_avail,pi_id) " \
            "VALUES(%s,%s,%s)" \
            "ON DUPLICATE KEY UPDATE " \
            "spot_avail = VALUES(spot_avail)"

    conn = MySQLdb.connect(host='35.190.143.237',user='root',passwd='rollins',db='tarveltparking')
    cursor = conn.cursor()
    cursor.executemany(query, spotData)
    conn.commit()


    cursor.close()
    conn.close()

def get_car_data(img, spot):
    '''
    captures an image of a car and saves it to the cars/ directory. From there it will be sent to a device specific
    branch of a git repository hosted locally. Once there are enough images collected, a new training file will be
    generate manually and the code will be updated to use the new file, thus ending the "training wheels" phase.
    
    
    :param img: the frame being processed by detect_cars
    :param spot: the spot a car has been detected in.
    :return: nothing, saves in image to the cars/ directory
    '''
    if spot == spot_one:
        data = img[165:570, 415:735]
    elif spot == spot_two:
        data = img[590:570, 840:735]
    elif spot == spot_three:
        data = img[995:570, 1245: 735]
    else:
        data = img[1445:570, 1695:735]

    cv2.imwrite('cars/' + uuid4(), data)

def detect_cars(image_array):
    '''
    detects cars in spots by acknowledging when it can no longer see the detection symbol
    spot occupied values are set to 1 innitially in case the lot is full and there are no detection images found
    
    :param image_array: the frame taken from the piCamera
    :return: Nothing
    '''

    cars = cars_cascade.detectMultiScale(image_array, scaleFactor=1.03,
                                         minNeighbors=0, maxSize=(120, 120))
    spot_one_occupied = 1
    spot_two_occupied = 1
    spot_three_occupied = 1
    spot_four_occupied = 1

    for (x, y, w, h) in cars:

        if x + w < spot_one_ROI:
            spot_one_occupied = 0
        if x >= spot_one_ROI and x + w < spot_two_ROI:
            spot_two_occupied = 0
        if x >= spot_two_ROI and x + w < spot_three_ROI:
            spot_three_occupied = 0
        if x >= spot_three_ROI:
            spot_four_occupied = 0

    if spot_one_occupied == 1:
        get_car_data(image_array, spot_one)
    if spot_two_occupied == 1:
        get_car_data(image_array, spot_two)
    if spot_three_occupied == 1:
        get_car_data(image_array, spot_three)
    if spot_four_occupied == 1:
        get_car_data(image_array, spot_four)

    spotData = [(spot_one, spot_one_occupied, pi_id),
               (spot_two, spot_two_occupied, pi_id),
               (spot_three, spot_three_occupied, pi_id),
               (spot_four, spot_four_occupied, pi_id)]
    insert_spot_data(spotData)



for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True): #captures a frame from the piCam

    image = frame.array #converts frame to numpy array
    detect_cars(image) #checkes numpy array for cars


    key = cv2.waitKey(1) & 0xFF


    time.sleep(54)
    rawCapture.truncate(0)





    if key == ord("q"):
        break
