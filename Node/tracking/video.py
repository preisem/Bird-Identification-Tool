import logging
import time
import cv2
from flask import Flask, Response

logger = logging.getLogger(__name__)

def look_for_birds(camera_int: int, node_name: str):
    logger.info(f"Starting Bird Video Stream: {str(camera_int)} to port :5000/" + node_name)
    
    app = Flask(__name__)

    video_source = camera_int 
    camera = cv2.VideoCapture(video_source)

    def generate_frames():
        while True:
            # Capture frame-by-frame
            success, frame = camera.read()
            if not success:
                break
            else:
                # Encode the frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                # Yield the frame as part of an HTTP response
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @app.route('/' + node_name)
    def video_feed():
        # Stream the video frames to the browser
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    # run flask server with video stream on port 5000
    app.run(host='0.0.0.0', port=5000)
