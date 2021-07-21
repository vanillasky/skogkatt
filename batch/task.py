from skogkatt.conf.app_conf import get_project_path


class Task:
    def __init__(self, name: str, filepath: str, cycle: int = 1, normal_exit_code: int = 0):
        self._abs_path = self.resolve_path(filepath)
        self._script = filepath.split('/')[-1]
        self._name = name
        self._cycle = cycle
        self._filepath = filepath
        self._normal_exit_code = normal_exit_code

    # @staticmethod
    # def from_dict(dic_data: List) -> List:
    #     task_list = []
    #     for i in range(len(dic_data)):
    #         d = dic_data[i]
    #         task = Task(d['name'], d['path'], d['file'], d.get('repeat', 0), d.get('normal_exit_code', 0), d.get('timeout', 0), d.get('cycle', 1))
    #         task_list.append(task)
    #
    #     return task_list

    # @staticmethod
    # def create(dict_data: dict):
    #     task = Task(dict_data['name'],
    #                 dict_data['path'],
    #                 dict_data['file'],
    #                 dict_data.get('repeat', 0),
    #                 dict_data.get('normal_exit_code', 0),
    #                 dict_data.get('timeout', 0),
    #                 dict_data.get('cycle', 1))
    #     return task
    @staticmethod
    def resolve_path(filepath: str):
        root_path = get_project_path()
        file = root_path.absolute() / filepath
        if file.exists():
            return str(file)
        else:
            raise FileNotFoundError(f'File not found: {filepath}')

    @property
    def abs_path(self):
        return self._abs_path

    @property
    def name(self):
        return self._name

    @property
    def filepath(self):
        return self._filepath

    @property
    def cycle(self):
        return self._cycle

    @property
    def normal_exit_code(self):
        return self._normal_exit_code

    @property
    def script(self):
        return self._script
