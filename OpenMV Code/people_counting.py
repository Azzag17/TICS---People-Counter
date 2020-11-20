# People Counting - By: pi - Thu. Oct. 15
# Aaron Gilbert  100600264

import sensor, image, time, os, tf, pyb

class CountObject:
    def __init__(self, px, py, p_px, p_py, Id, isCounted, direction, prev_dir):
        self.px = px
        self.py = py
        self.p_px = p_px
        self.p_py = p_py
        self.Id = Id
        self.isCounted = isCounted
        self.direction = direction
        self.prev_dir = prev_dir



sensor.reset()                         # Reset and initialize the sensor.
sensor.set_pixformat(sensor.GRAYSCALE) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)      # Set frame size to QVGA (320x240)
sensor.set_windowing((240, 240))       # Set 240x240 window.
sensor.skip_frames(time=2000)          # Let the camera adjust.

clock = time.clock()

print("Loading model")
person_cascade = image.HaarCascade("/PeopleCounting/people_counting_cascade.cascade", stages=25)


height = None
width = None
count = 0

direction = 0
isCounted = False
i = 1
j = 1


b_boxes = []

vid = image.ImageReader("/PeopleCounting/walking.bin")


while(True):
    clock.tick()
    #img = image.Image("/PeopleCounting/person.bmp", copy_to_fb = True)
    img = vid.next_frame(copy_to_fb = True)

    if not img:
        print("video end")
        break

    height = img.height()
    width = img.width()

    line_x1 = width//2    #0
    line_y1 = 0           #height//2
    line_x2 = width//2    #width
    line_y2 = height      #height//2

    img.draw_line(line_x1, line_y1, line_x2, line_y2, (0,0,255))

    objects = img.find_features(person_cascade, threshold=1, scale_factor=1.5)

    #for obj in objects:
    if objects:
        obj = objects[0]

        img.draw_rectangle(obj) #draw rectangle around detected object

        (x,y,w,h) = obj  #obtain x,y,width and height of object

        x2 = x+w  #calculate x,y of bottom right rectangle
        y2 = y+h

        #determine the coords of the centre point and draw circle
        cx = ((x2+x)//2)
        cy = ((y2+y)//2)

        prev_cx = 0
        prev_cy = 0

        objId = i

        isNew = True

        #if bounding box list doesn't exist, then create it with newly detected object
        if not b_boxes:
            b_boxes.append(CountObject(cx, cy, prev_cx, prev_cy, i, isCounted, direction, 0))
            i = i+1
            print("New Object made")
            print("No bounding boxes list")
        else:
            #Check if detected object is close to another object, meaning potentially same object
            for ob in b_boxes:
                if (abs((cx-ob.px)) < 130) and (abs((cy-ob.py)) < 130):
                    ob.px = cx
                    ob.py = cy
                    prev_cx = ob.p_px
                    prev_cy = ob.p_py
                    objId = ob.Id
                    print("Current object found")

                    isNew = False

                    continue

            #if new object is detected, then track it on bounding box list
            if isNew:
                    b_boxes.append(CountObject(cx, cy, prev_cx, prev_cy, i, isCounted, direction, 0))
                    i = i+1
                    print("New Object made")

            #for each object in list, draw ID and circles at current and previous position
            for obj in b_boxes:
                img.draw_circle(obj.px, obj.py, 5, (255,0,0), 1, True)
                img.draw_string(obj.px-20, obj.py-25, "ID = %d"%obj.Id, (0,255,0), 2, mono_space = False)
                img.draw_circle(obj.p_px, obj.p_py, 5, (255,255,0), 1, True)


                #determine which direction the object is moving, 1 = right, -1 = left on frame
                if (obj.p_px != 0)and(obj.p_py != 0):
                    if (obj.p_px < obj.px):
                        obj.prev_dir = obj.direction
                        obj.direction = 1
                    elif (prev_cx > cx):
                        obj.prev_dir = obj.direction
                        obj.direction = -1
                    else:
                        obj.direction = 0

            #Iterate through list and obtain current object, check position to determine if entered/exited store
            for obj in b_boxes:
                if(obj.Id == objId):
                    if (obj.px > line_x1)and(obj.p_px <= line_x1)and(obj.direction == 1):
                        print("Object entered store")
                        if not obj.isCounted:
                            count = count+1
                            obj.isCounted = True
                    elif (obj.px < line_x1)and(obj.p_px >= line_x1)and(obj.direction == -1):
                        print("Object exited store")
                        if not obj.isCounted:
                            count = count-1
                            obj.isCounted = True
                    else:
                        print("Object did not move")

                    #update previous position is to be current position
                    obj.p_px = cx
                    obj.p_py = cy




            #Check if same object has changed directions and re-entered/exited store
            for obj in b_boxes:
                if (obj.isCounted):
                    if (obj.direction == 1) and (obj.prev_dir == -1):
                        obj.isCounted = False
                    if (obj.direction == -1) and (obj.prev_dir == 1):
                        obj.isCounted = False

            pyb.delay(30)

            isCounted = False



    img.draw_string(5, height-20, "Count = %d" % count, (0,255,0), 2, mono_space = False)

sensor.flush()
