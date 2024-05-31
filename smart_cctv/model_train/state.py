class State:
    def __init__(self):
        self._observers = []
        self._project_path = ""
        self._dataset_path = ""
        self._runs_path = ""

    def add_observer(self, observer):
        self._observers.append(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer()

    @property
    def project_path(self):
        return self._project_path

    @project_path.setter
    def project_path(self, value):
        self._project_path = value
        self.notify_observers()

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
