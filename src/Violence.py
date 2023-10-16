"""
    Abnormal Actions : 
    Violence post-process function
"""

# Import Base Modules
import os

# Import Custom Modules
from TrackingBox import ClassID, TrackingBox

SAMPLE_DIR_PATH = r"../samples/violence_sample_data/"

# 특정 범위 안에 해당 값이 있는지 체크
def is_in_box(box:TrackingBox, mid_points:list) -> bool:
    if box.x < mid_points[0] < box.x + box.w and \
       box.y < mid_points[1] < box.y + box.h:
        return True
    return False

# 폭행 : 객체 ID 탐지 이후 후처리 알고리즘
def check_violence_validation(tracking_boxes_input:list) -> list:
    check_results   = []
    violence_boxes  = []
    person_m_points = []

    # Only works Tracking box type
    tracking_boxes = [ x for x in tracking_boxes_input if isinstance( x, TrackingBox ) ]

    # sort each tracking box prev check validation
    for box in tracking_boxes:
        # if violence class, append itself
        if box.class_id == ClassID.VIOLENCE.value:
            violence_boxes.append( box )

        # if person class, append that mid point
        elif box.class_id == ClassID.PERSON.value:
            person_m_points.append( [ box.x + (box.w / 2), box.y + (box.h / 2) ] )

    # 검출된 사람이 2명 미만, 혹은 폭행이 1개 미만인 경우 => 더 체크하지 않아도 무방
    if len( violence_boxes ) < 1 or len( person_m_points ) < 2:
        return []

    for box in violence_boxes:
        # 각 폭행 클래스마다 해당 클래스 bbox 범위 내 사람 클래스의 중점이 몇 개 포함되어 있는지 체크
        in_person_count = len( list( filter( lambda pt : is_in_box( box, pt ), person_m_points ) ) )

        # 폭행 박스 내 사람 객체가 두 명 이상일 경우
        if in_person_count >= 2:
            check_results.append( box )

    return check_results

# Read File & Get Lines List
def read_file_to_list( file_path:str ) -> list:
    result_list = []
    with open( file_path, 'r' ) as f:
        for eachLine in f:
            eachLine = eachLine.strip('\n')
            result_list.append(eachLine)
    return result_list


# MAIN :: TEST CODE
if __name__ == "__main__":
    for _, _, files in os.walk(SAMPLE_DIR_PATH):
        # 각 1개 파일이 1개 프레임 1회 디텍트 결과들이라 가정
        for file in files:
            # Read File & Get Lines List
            read_lines = read_file_to_list( os.path.join( SAMPLE_DIR_PATH, file ) )

            # Set Buffer for tracking box list
            tracking_boxes = []

            # Convert string to Tracking Box
            for read_line in read_lines:
                tracking_box = TrackingBox().set_value_from_string(read_line)
                tracking_boxes.append( tracking_box )

            # check validation
            valid_violence_list = check_violence_validation( tracking_boxes )

            # print each file results
            print( file, ' : ', valid_violence_list )
