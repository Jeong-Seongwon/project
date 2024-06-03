class State:
    def __init__(self): # 초기화 메서드
        self._observers = [] # 속성 변경을 감지하는 함수나 메서드 저장
        self._project_path = ""
        self._dataset_path = ""
        self._runs_path = ""

    def add_observer(self, observer): # observer 는 속성 변경될 때 호출될 함수나 메서드
        # 옵저버를 받아서 _옵저버 리스트에 추가
        self._observers.append(observer)

    def notify_observers(self): # 속성이 변경될 때 모든 옵저버에게 알림 전달
        # _옵저버 리스트에 있는 모든 옵저버 호출
        for observer in self._observers:
            observer()

    @property # 속성 정의
    def project_path(self):
        return self._project_path

    @project_path.setter # 설정자
    def project_path(self, value): # 새로운 값 설정
        self._project_path = value # 속성값 갱신
        self.notify_observers() # 옵저버들에게 알림

    @property
    def dataset_path(self):
        return self._dataset_path

    @dataset_path.setter
    def dataset_path(self, value):
        self._dataset_path = value
        self.notify_observers()

    @property
    def runs_path(self):
        return self._runs_path

    @runs_path.setter
    def runs_path(self, value):
        self._runs_path = value
        self.notify_observers()
