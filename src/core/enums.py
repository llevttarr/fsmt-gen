from enum import Enum
class CameraState(Enum):
    DEFAULT = 60.0
    ZOOM = 30.0

class Region(Enum):
    STEPPE = 1
    FOREST = 2
    SNOW_PLAINS = 3

class RotationAxis(Enum):
    X=1
    Y=2
    Z=3
class ObjectViewType(Enum):
    # This might or might not be implemented
    DEFAULT = 1
    TOPOGRAPHY = 2
    OUTLINE_ONLY = 3

class WindowState(Enum):
    '''
    Current state of the app window
    '''
    MAIN_MENU = 1
    # this state occurs right before the world generation
    GENERATOR_CONFIG = 2
    GENERATOR_VIEW = 3
    INFO_PAGE = 4
