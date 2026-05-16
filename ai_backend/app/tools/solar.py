import cv2
import numpy as np

def analyze_brightness(image_bytes):
    """
    Analyzes the image to find the brightest region (potential sunlight).
    Returns coordinates (x, y) relative to the center (-1.0 to 1.0).
    """
    if image_bytes is None:
        return None
    
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
    
    # Find the brightest spot
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blurred)
    
    h, w = img.shape[:2]
    # Calculate relative coordinates from -1.0 to 1.0
    rel_x = (maxLoc[0] - w/2) / (w/2)
    rel_y = (maxLoc[1] - h/2) / (h/2)
    
    return {
        "x": round(rel_x, 2),
        "y": round(rel_y, 2),
        "intensity": round(maxVal / 255.0, 2)
    }
