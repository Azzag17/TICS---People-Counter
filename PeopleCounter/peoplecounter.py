from pyimagesearch.centroidtracker import CentroidTracker
from pyimagesearch.trackableobject import TrackableObject
from imutils.video import FPS
from datetime import datetime

import numpy as np
import imutils
import dlib
import cv2
import serial
import time
import firebaseaccess


# main function to run all the code
def main():
    classes = [
        "background", "aeroplane", "bicycle", "bird", "boat",
        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
        "sofa", "train", "tvmonitor"
    ]

    # MobileNet Variables
    proto_file = "mobilenet_ssd/MobileNetSSD_deploy.prototxt"
    model_file = "mobilenet_ssd/MobileNetSSD_deploy.caffemodel"

    # load the model
    print("Loading the Caffe model")
    net = cv2.dnn.readNetFromCaffe(proto_file, model_file)

    # connect to firestore database
    print("Connecting to firestore database")
    database = firebaseaccess.connDb()

    # connect to arduino
    print("Connecting to Arduino")
    arduino = serial.Serial("COM3", baudrate=9600)
    arduino.flushInput()

    # load video file
    print("Opening video")
    vid = cv2.VideoCapture("videos/aaron_vid.mp4")

    #if arduino was successfully connected to, send 'Accept' code
    if arduino:
        arduino.write("A".encode())


    # initialise variables
    threshold = firebaseaccess.getThreshold(database) # get latest threshold val from database
    time_now = datetime.now() # get current time to enter into database
    device_name = firebaseaccess.getDeviceName(database) # get device name
    width = None
    height = None
    total_frames = 0
    count = 0

    #different colours to use
    YELLOW = (0, 255, 255)
    CYAN = (255, 255, 0)
    RED = (0, 0, 255)
    BLUE = (255, 0, 0)
    GREEN = (0, 255, 0)


    #Initialise centroidtracker and a list of trackers
    cenTrack = CentroidTracker(maxDisappeared=40, maxDistance=50)
    trackers = []
    trackObjs = {}

    #start fps to keep track of fps
    fps = FPS().start()

    while 1:
        #read the video and save a frame as 'img'
        img = vid.read()
        img = img[1]

        #if img is none then it is most likely the end of the frame, or there was an error
        if img is None:
            print("End of video, loop ending")
            break

        #resize the image to fit the blob function
        img = imutils.resize(img, width=500)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        #set the height and width of the image
        height = img.shape[0]
        width = img.shape[1]

        #create list of bounding boxes
        b_boxes = []

        #every 20 frames perform object detection
        if total_frames % 30 == 0:
            trackers = []
            blob = cv2.dnn.blobFromImage(img, 0.007843, (width, height), 127.5)
            net.setInput(blob)
            detects = net.forward()


            for i in np.arange(0, detects.shape[2]):
                conf = detects[0, 0, i, 2]
                if conf > 0.3:
                    idx = int(detects[0, 0, i, 1])

                    if classes[idx] != "person":
                        continue

                    box = detects[0, 0, i, 3:7] * np.array([width, height, width, height])
                    (x1, y1, x2, y2) = box.astype("int")

                    tracker = dlib.correlation_tracker()
                    tracker.start_track(img, dlib.rectangle(x1, y1, x2, y2))

                    trackers.append(tracker)
        else:
            for tracker in trackers:
                tracker.update(img_rgb)

                position = tracker.get_position()

                x1 = int(position.left())
                y1 = int(position.top())
                x2 = int(position.right())
                y2 = int(position.bottom())

                b_boxes.append((x1, y1, x2, y2))

        #detection line coordinates (from x1,y1 to x2,y2)
        line_x1 = 0
        line_y1 = (height//2)
        line_x2 = width
        line_y2 = (height//2)

        #draw line across the screen at halfway
        #cv2.line(image, start_point, end_point, colour, thickness)
        cv2.line(img, (line_x1, line_y1), (line_x2, line_y2), RED, 1)

        objects = cenTrack.update(b_boxes)

        #iterate through the objects that are being tracked
        for (objectID, centroid) in objects.items():
            track_obj = trackObjs.get(objectID, None)

            #obtain objs current x,y coord from centroid array
            curr_x_pos = centroid[0]
            curr_y_pos = centroid[1]

            #if there is no current object being tracked then create a new one
            if track_obj is None:
                track_obj = TrackableObject(objectID, centroid)

            #iterate through the tracked objects
            else:
                y = [c[1] for c in track_obj.centroids]

                #direction is calculated by subtracting current centroid position from previous positions
                direction = curr_y_pos - np.mean(y)
                track_obj.centroids.append(centroid)

                #if the object hasn't already been counted
                if not track_obj.counted:
                    #if direction is moving up, and the object is above the line, then decrement
                    if direction < 0 and curr_y_pos < line_y1:
                        new_count = -1
                        track_obj.counted = True

                        #confirm that person was detected and update count accordingly
                        count = updateArduino(arduino, new_count, count, threshold, time_now, device_name, database)


                    ##if direction is moving down, and the object is below the line, then increment
                    elif direction > 0 and curr_y_pos > line_y1:
                        new_count = 1
                        track_obj.counted = True

                        #confirm that person was detected and update count
                        count = updateArduino(arduino, new_count, count, threshold, time_now, device_name, database)


            trackObjs[objectID] = track_obj

            #draw circle at centroid
            cv2.circle(img, (curr_x_pos, curr_y_pos), 4, YELLOW, -1)

        text = "Total Count: " + str(count)

        #cv2.putText(img, text, (X,Y), font, fontScale, colour, thickness)
        cv2.putText(img, text, (10, height - 20), cv2.FONT_HERSHEY_TRIPLEX, 0.6, YELLOW, 2)

        cv2.imshow("People Counting Device", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        total_frames = total_frames + 1
        fps.update()

    fps.stop()

    vid.release()

    cv2.destroyAllWindows()


#If person has been detected, confirm with US sensor from arduino
def updateArduino(ard, upd_count, curr_count, th, curr_time, device, db):
    #send serial command to Arduino 'C' arduino.send...
    errCount = 0
    count = 0
    cmd = 'C'
    ard.write(cmd.encode())
    time.sleep(0.1)

    while ard.in_waiting:
        errCount += errCount
        data = ard.readline()
        decoded_data = int(data[0:len(data)-2].decode("utf-8"))

        if errCount > 100:
            print("problem")
        else:
            if data:
                if decoded_data == 1:
                    count = curr_count + upd_count
                    print("updated count: " + str(count))

                    # add entry into firestore
                    curr_threshold = firebaseaccess.getLatestThreshold(db)

                    if curr_threshold == -1:
                        curr_threshold = th

                    new_db_id = firebaseaccess.getLatestFirestoreId(db)
                    firebaseaccess.addCount(new_db_id, count, curr_threshold, curr_time, device, db)

                    updateLEDs(ard, curr_threshold, count)

                elif decoded_data == 0:
                    count = curr_count
                    print("No confirmation. Did not change count. Count: " + str(count))

    return count

#update LEDs
def updateLEDs(ard, threshold, count):
    print("Updating LEDs on Arduino")

    if count >= int(threshold):
        #send serial command to Arduino 'S' (stop) arduino.send...
        cmd = 'S'
        ard.write(cmd.encode())
        print("LEDs turning red")

    else:
        #send serial command to Arduino 'G' (go) arduino.send...
        cmd = 'G'
        ard.write(cmd.encode())
        print("LEDs turning green")

#call main to run program
if __name__ == '__main__':
    main()


