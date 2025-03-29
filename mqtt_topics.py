from enum import Enum

class Topics(str, Enum):
    """
    Enum representing MQTT topics used in the Sea Guard project.
    """
    GET_LATEST_PICTURES = "GET_LATEST_PICTURES_N"
    SEND_LATEST_PICTURES = "SEND_LATEST_PICTURES"
    PICTURE_TAKEN = "TAKE_PICTURE"  # Updated to match the TAKE_PICTURE topic
    
    PIR_MOTION_DETECTED = "PIR/MOTION_DETECTED"
    PIR_MOTION_ENDED = "PIR/MOTION_ENDED"
    PIR_HEARTBEAT = "PIR/HEARTBEAT"


# from mqtt_topics import GET_LATEST_PICTURES, SEND_LATEST_PICTURES

# client.subscribe(GET_LATEST_PICTURES)
# client.publish(SEND_LATEST_PICTURES, payload)