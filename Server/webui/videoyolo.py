import cv2
import warnings
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from urllib.parse import urlparse
from ultralytics import YOLO

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=FutureWarning)

def start_yolo_stream_server(stream_urls: list[str], port: int = 8001, model_path: str = 'yolov8n.pt', skip_frames: int = 2) -> list[str]:
    """
    Starts a FastAPI server that streams YOLOv8-annotated video frames for each stream URL.

    Args:
        stream_urls (list[str]): List of input video stream URLs.
        port (int): Port to run the FastAPI server on.
        model_path (str): Path to YOLOv8 model file (e.g., 'yolov8n.pt' or 'best.pt').
        skip_frames (int): Number of frames to skip between detections.

    Returns:
        List[str]: List of processed stream URLs (e.g., http://localhost:8001/laptop)
    """

    app = FastAPI()
    model = YOLO(model_path)

    # TEST
    #results = model("bird.jpg", verbose=False)
    #results[0].show()

    processed_urls = []

    def make_generator(stream_url):
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open stream: {stream_url}")

        frame_count = 0
        last_detections = []

        def generate():
            nonlocal frame_count, last_detections
            while True:
                success, frame = cap.read()
                if not success:
                    continue

                frame_count += 1

                if frame_count % skip_frames == 0:
                    # Optional: convert to RGB if needed
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = model(rgb_frame, verbose=False)[0]
                    last_detections = results.boxes.data.cpu().numpy()
                detections = last_detections

                for det in detections:
                    x1, y1, x2, y2, conf, cls = det[:6]
                    logger.debug(f"Detected {model.names[int(cls)]} with confidence {conf:.2f}")
                    if conf < 0.3:
                        continue
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    label = f"{model.names[int(cls)]} {conf:.2f}"
                    color = confidence_to_color(conf) # color gradient box color based on confidence level
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        return generate

    for stream_url in stream_urls:
        parsed = urlparse(stream_url)
        endpoint_name = parsed.path.strip("/").split("/")[-1] or "stream"
        generator = make_generator(stream_url)

        @app.get(f"/{endpoint_name}")
        def stream_endpoint(gen=generator):
            return StreamingResponse(gen(), media_type='multipart/x-mixed-replace; boundary=frame')

        full_url = f"http://localhost:{port}/{endpoint_name}"
        processed_urls.append(full_url)
        logger.info(f"Registered endpoint /{endpoint_name} for stream: {stream_url}")

    import threading
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port), daemon=True).start()

    return processed_urls

''' Helper Functions '''
def confidence_to_color(conf):
    """
    Maps confidence (0.0 to 1.0) to a BGR color from red to green.
    Red (low) → Orange → Yellow → Green (high)
    """
    conf = max(0.0, min(conf, 1.0))  # Clamp between 0 and 1

    # Interpolate across red → orange → yellow → green
    if conf < 0.33:
        # Red to Orange
        r = 255
        g = int(255 * (conf / 0.33))
        b = 0
    elif conf < 0.66:
        # Orange to Yellow
        r = 255
        g = 255
        b = 0
    else:
        # Yellow to Green
        r = int(255 * (1 - (conf - 0.66) / 0.34))
        g = 255
        b = 0

    return (b, g, r)  # OpenCV uses BGR
