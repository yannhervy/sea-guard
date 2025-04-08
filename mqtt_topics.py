from enum import Enum

class Topics(str, Enum):
    """
    Enum representing MQTT topics used in the Sea Guard project.
    """
    GET_LATEST_PICTURES = "GET_LATEST_PICTURES_N"
    SEND_LATEST_PICTURES = "SEND_LATEST_PICTURES"
    TAKE_PICTURE = "TAKE_PICTURE"
    SEND_MESSAGE = "SEND_MESSAGE"

    PIR_MOTION_DETECTED = "PIR/MOTION_DETECTED"
    PIR_MOTION_ENDED = "PIR/MOTION_ENDED"
    PIR_ARM = "PIR/ARM"
    PIR_DISARM = "PIR/DISARM"