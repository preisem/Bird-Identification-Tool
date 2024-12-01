import logging
import time
import cv2

logger = logging.getLogger(__name__)

def look_for_birds(camera: int):
    logger.info(f"Starting Bird Video Watcher with Camera: {str(camera)}")
    
    cap=cv2.VideoCapture(int(camera)) #// if you have second camera you can set first parameter as 1
    if not (cap.isOpened()):
        print("Could not open video device")
    while True: 
        ret,frame= cap.read()
        cv2.imshow("Live",frame)
        cv2.waitKey(1)
    cv2.destroyAllWindows()
    
    return
