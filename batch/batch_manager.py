import subprocess
import sys

from skogkatt.batch.task import Task
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class BatchManager:

    def __init__(self):
        self.tasks = {}

    def add_task(self, task: Task):
        self.tasks[task.name] = task

    def get_task(self, task_name: str) -> Task:
        return self.tasks.get(task_name, None)

    def start_batch(self):
        for task_name, task in self.tasks.items():
            return_code = self.execute_task(task)
            logger.info(f'Task returned : {task.name}, code: {return_code}')

    @staticmethod
    def execute_task(task: Task):
        logger.info(f'Batch task starts: {task.abs_path}')
        proc = subprocess.run(args=[sys.executable, task.abs_path], shell=True)
        return proc.returncode


if '__main__' == __name__:
    manager = BatchManager()
    manager.add_task(Task(name='mock-task', filepath='tests/batch/task_mock.py'))
    manager.start_batch()
