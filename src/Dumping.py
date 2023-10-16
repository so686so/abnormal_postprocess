"""
    Abnormal Actions : 
    Dumping Algorithm Class
"""

# Import Base Modules
from collections import defaultdict
# Import Custom Modules
from TrackingBox import ClassID, TrackingBox

# algorithm threshold const value
DUMPING_THRESHOLD = 200

# count about release history
RELEASE_THRESHOLD = 10

def calculate_distance(x, y):
    return ( ( (x[0] + x[2] / 2) - (y[0] + y[2] / 2) ) ** 2 \
           + ( (x[1] + x[3] / 2) - (y[1] + y[3] / 2) ) ** 2 ) ** 0.5

def calculate_iou(boxA:TrackingBox, boxB:TrackingBox):
    # 겹치는 영역 계산
    xInf = max(boxA.x, boxB.x)
    yInf = max(boxA.y, boxB.y)
    xSup = min(boxA.x + boxA.w, boxB.x + boxB.w)
    ySup = min(boxA.y + boxA.h, boxB.y + boxB.h)

    # 겹치는 영역의 너비와 높이 계산
    intersection_area = max(0, xSup - xInf + 1) * max(0, ySup - yInf + 1)

    # 각 박스의 영역 계산
    areaA = ( boxA.w + 1 ) * ( boxA.h + 1 )
    areaB = ( boxB.w + 1 ) * ( boxB.h + 1 )

    # IOU
    iou = intersection_area / float( areaA + areaB - intersection_area )
    return iou


"""
- History Class는 생명 주기(RELEASE_THRESHOLD) 만큼 해당 객체에 저장된 데이터를 보존함.
- Data는 key:value 형태의 Dict로 관리됨.
- 만약 같은 key 값으로 데이터가 update 될 경우, data 값은 덮어씌워짐.
- update 시 생명 주기 카운트가 초기화되어, 다시 RELEASE_THRESHOLD 만큼 보존됨.
- RELEASE_THRESHOLD 횟수동안 update 되지 않은 데이터는 다음 update() 에서 자동 소멸됨.
"""
class History:
    # Initialize
    def __init__(self) -> None:
        self._history_dict = {} # { TrackID : HistoryElement }

    # Inner Class
    class HistoryElement:
        def __init__(self, value = None) -> None:
            self._count = 0
            self._value = value

        @property
        def value(self):
            return self._value

        def increase(self):
            self._count += 1

        def is_expired(self):
            if self._count >= RELEASE_THRESHOLD: return True
            return False

    # dict[key] 값 형태의 return override
    def __getitem__(self, track_id:int):
        return self._history_dict[track_id].value
    
    # 생명주기 만료된 데이터 삭제 함수
    def release_history(self):
        keys_to_delete = [ k for k, v in self._history_dict.items() if v.is_expired() ]
        for k in keys_to_delete:
            del self._history_dict[k]

    # 신규 데이터로 업데이트 하는 함수 : 해당 함수에서 생명주기 관리까지 동시 진행
    def update(self, current_history:dict):
        # 기존 데이터들 AGE + 1
        for elem in self._history_dict.values():
            elem.increase()

        # when updated, increased count reset
        for k, v in current_history.items():
            self._history_dict[k] = self.HistoryElement(v)
        
        # release expired history 
        self.release_history()

    def hist_keys(self):
        return [ k for k in self._history_dict.keys() ]
    
    def hist_items(self):
        return [ (k, v.value) for k, v in self._history_dict.items() ]
    
    def hist_values(self):
        return [ v.value for v in self._history_dict.values() ]


class Dumping:
    def __init__(self) -> None:
        self.trash_history    = History()
        self.person_history   = History()
        self.relation_history = History()

    def Request(self, tracking_boxes_input:list) -> list:
        # Only works TrackingBox type
        tracking_boxes = [ x for x in tracking_boxes_input if isinstance( x, TrackingBox ) ]

        if not tracking_boxes:
            return []
        
        current_trash_dict    = {}
        current_person_dict   = {}
        current_relation_dict = defaultdict(lambda : [])

        # Sort Input by CLASS ID
        # ==========================================================================================================
        for box in tracking_boxes:
            if box.class_id == ClassID.PERSON.value:
                current_person_dict[box.track_id] = box
            elif box.class_id == ClassID.TRASH.value:
                current_trash_dict[box.track_id] = box

        # Trash Box IOU 보정
        # ==========================================================================================================
        for prev_track_id, prev_box in self.trash_history.hist_items():
            for curr_track_id, curr_box in current_trash_dict.items():
                # 만약 기존 히스토리에 있던 특정 쓰레기 box 와 현재 쓰레기 목록 중 어떤 box 가 90% 이상 영역이 일치하다면
                if calculate_iou( prev_box, curr_box ) > 0.9:
                    # 현재 쓰레기 TrackID를 지우고
                    del current_trash_dict[curr_track_id]
                    # 영역이 거의 겹치는 기존 TrackID로 대체시키기
                    current_trash_dict[prev_track_id] = curr_box

        # Make Relation
        # ==========================================================================================================
        for trash_track_id, trash_box in current_trash_dict.items():

            # 해당 쓰레기 TrackID의 쓰레기 박스와 일정 거리 안에 있는 사람들의 TrackID 리스트 생성
            in_range_persons = list( filter( lambda t_id : calculate_distance(current_person_dict[t_id], trash_box) < DUMPING_THRESHOLD, current_person_dict.keys() ) )

            # 새롭게 발견된 쓰레기 TrackID 라면
            if trash_track_id not in self.trash_history.hist_keys():
                # 해당 사람들 TrackID : [ 관계 있는 쓰레기 TrackID List ] 추가
                for person_track_id in in_range_persons:
                    current_relation_dict[person_track_id].append(trash_track_id)

            # 이전에 존재하던 쓰레기 TrackID 라면
            else:
                for person_track_id in in_range_persons:
                    # 해당 Person Track ID 와 기존에 관계가 없던 Trash Track ID 라면 그대로 continue
                    if trash_track_id not in self.relation_history[person_track_id]:
                        continue
                    # 이미 관계가 있던 Trash Track ID 만 새로 갱신
                    current_relation_dict[person_track_id].append(trash_track_id)

        # Find Dumping Event For Algorithm
        # ==========================================================================================================
        results_list = []

        # 관계가 있었다가 사라진 Person Track ID 색출
        for prev_person_track_id, prev_trash_track_ids in self.relation_history.hist_items():
            # 여전히 Person Track ID 존재하는데 / Relation 갯수가 줄었다 => 해당 Person이 Trash와의 관계맺음이 깨졌다 => 쓰레기 버리고 지나갔다
            if prev_person_track_id in current_person_dict.keys() and len( current_relation_dict[person_track_id] ) < len( prev_trash_track_ids ):
                # 해당 Person 객체 Event Class ID 로 변경해서 결과 리스트에 append
                _, track_id, x, y, w, h = current_person_dict[prev_person_track_id]
                results_list.append( TrackingBox( ClassID.DUMPING.value, track_id, x, y, w, h ) )

        # History Update
        # ==========================================================================================================
        self.relation_history.update( current_relation_dict )
        self.person_history.update( current_person_dict )
        self.trash_history.update( current_trash_dict )

        return results_list
