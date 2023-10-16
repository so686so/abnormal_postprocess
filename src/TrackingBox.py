"""
    TrackingBox Class(Structure) for Abnormal Event Algorithm
"""

# Import
from enum import Enum, unique

# Enum class : Class ID
@unique
class ClassID(Enum):
    NONE     = 999
    PERSON   = 0
    VIOLENCE = 6
    TRASH    = 8
    DUMPING  = 22

# Structure : TrackingBox
class TrackingBox:
    def __init__( self, 
                  class_id = ClassID.NONE.value, 
                  track_id = 0,
                  x = 0., 
                  y = 0., 
                  w = 0., 
                  h = 0. ) -> None:
        # Initialize
        self.class_id = class_id
        self.track_id = track_id
        self.x        = x
        self.y        = y
        self.w        = w
        self.h        = h

    def set_value_from_string(self, string_line:str) -> bool:
        params = string_line.split()

        if len( params ) != 6:
            return False
        
        self.class_id = int  ( params[0] )
        self.track_id = int  ( params[1] )
        self.x        = float( params[2] )
        self.y        = float( params[3] )
        self.w        = float( params[4] )
        self.h        = float( params[5] )

        return True