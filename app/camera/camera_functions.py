from picamera2 import Picamera2
import pprint

# Initialize the camera object
try:
    picam2 = Picamera2()
    
    # Get the camera controls dictionary
    controls = picam2.camera_controls
    
    # Use pprint for a more readable output of the dictionary
    pprint.pprint(controls)
    
except Exception as e:
    print(f"Error accessing camera controls: {e}")
finally:
    # Always remember to stop and close the camera
    if 'picam2' in locals() and picam2.started:
        picam2.stop()
    if 'picam2' in locals():
        picam2.close()