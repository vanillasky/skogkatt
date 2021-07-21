import subprocess
import sys
from datetime import datetime

import psutil

from threading import Timer

from skogkatt.batch import batch_lookup, BatchStatus
from skogkatt.batch.monitor import BatchMonitor
from skogkatt.batch.task import Task
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def start(task: Task, timeout: int):
    status = BatchStatus(task.name, datetime.now())
    monitor = BatchMonitor()
    monitor.start(status)

    ret = execute_task(task, timeout)
    while True:
        if ret == 7:
            logger.info("Daily chart updated successfully.")
            status.end = datetime.now()
            status.elapsed = status.end - status.start
            status.status = 0
            monitor.end(status)
            break
        else:
            ret = execute_task(task, timeout)


def execute_task(task: Task, timeout: int):
    set_timer_to_kill_process(task.script, timeout)

    collector_proc = subprocess.run(args=[sys.executable, task.abs_path], shell=True)
    ret = collector_proc.returncode
    return ret


def set_timer_to_kill_process(name, timeout: int):
    timer = Timer(timeout, kill_process, [name])
    timer.start()


def kill_process(name):
    logger.info(f"find & kill process {name}")
    # print(f"find & kill process {name}")
    proc = find("python.exe", name)
    if proc is not None:
        # print(proc.cmdline())
        proc.kill()
    else:
        logger.debug(f"process not found: {name}")


def find(name, script_name):
    # proc_list = []
    for proc in psutil.process_iter():
        try:
            if name.lower() in proc.name().lower():
                if proc.cmdline()[1].endswith(script_name):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as err:
            pass

    return None


if __name__ == '__main__':
    chart_task = Task(name=batch_lookup.COLLECT_CHART['name'], filepath='api/kiwoom/collector.py')
    start(chart_task, timeout=240)
