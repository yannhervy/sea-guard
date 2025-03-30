from enum import Enum

class Topics(str, Enum):
    """
    Enum representing MQTT topics used in the Sea Guard project.
    """
    GET_LATEST_PICTURES = "GET_LATEST_PICTURES_N"
    SEND_LATEST_PICTURES = "SEND_LATEST_PICTURES"
    PICTURE_TAKEN = "PICTURE_TAKEN"  # Updated to match the TAKE_PICTURE topic
    TAKE_PICTURE = "TAKE_PICTURE"

    PIR_MOTION_DETECTED = "PIR/MOTION_DETECTED"
    PIR_MOTION_ENDED = "PIR/MOTION_ENDED"
    PIR_HEARTBEAT = "PIR/HEARTBEAT"
    PIR_ARM = "PIR/ARM"  # Topic to arm the PIR sensor
    PIR_DISARM = "PIR/DISARM"  # Topic to disarm the PIR sensor


# from mqtt_topics import GET_LATEST_PICTURES, SEND_LATEST_PICTURES

# client.subscribe(GET_LATEST_PICTURES)
# client.publish(SEND_LATEST_PICTURES, payload)