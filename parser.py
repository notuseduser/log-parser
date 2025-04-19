from datetime import datetime
import os
import logging
import multiprocessing
from argparse import ArgumentParser
import re
import glob

""" Constants """
MIN5 = 5 * 60
MIN10 = 10 * 60
FORMAT="%(asctime)s;%(logfile)s;%(levelname)s;%(message)s"

""" Initialize logger """
logging.basicConfig(filename=os.path.join(os.getcwd(), "output"), format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("Parser")
logger.setLevel(logging.INFO)

""" Multiprocess target function """
def process_function(path: str = None, multiprocess: bool = False, lock: multiprocessing.Lock = None):
    Parser(path, multiprocess, lock)

""" Argument parser """
def argument_parser() -> ArgumentParser:
    cwd = os.getcwd()
    parser = ArgumentParser()
    parser.add_argument("-l", "--logs", default=os.path.join(cwd, "logs"), type=str, help="Logs directory path", dest="logs")
    return parser

""" Parser class """
class Parser():
    """
    Parser class:
    :argument path str - mandatory - path of log file to be parsed
    :argument multiprocess bool - whether to use multiprocessing or not
    :argument lock multiprocessing.Lock - lock object to use for multiprocessing
    """
    _path: str
    lock: multiprocessing.Lock
    multiprocess: bool

    def __init__(self, path: str = None, multiprocess: bool = False, lock: multiprocessing.Lock = None):
        try:
            self.path = path
            self.lock = lock
            self.multiprocess = multiprocess
        except FileNotFoundError as e:
            print("File path does not exist or none")
            raise e
        except Exception as e:
            print("Another exception occurred")
            raise e
        self.parse(path, multiprocess, lock)

    @property
    def path(self) -> str:
        return self.path
    @path.setter
    def path(self, path: str) -> None:
        if path is None: raise FileNotFoundError()
        if os.path.exists(path) and os.path.isfile(path): _path = path
        else: raise FileNotFoundError()

    def parse(self, path: str, multiprocess: bool, lock: multiprocessing.Lock) -> None:
        with (open(path, "r") as file):

            status = {}

            for index, line in enumerate(file):
                if line.endswith("\n"): line = line.rstrip("\n")
                if line.endswith("\r"): line = line.rstrip("\r")

                extra = {"logfile": os.path.basename(path)}
                timestamp, description, action, pid= line.split(",")
                if multiprocess: lock.acquire()

                try:
                    if action.lstrip() == "START":
                        if status.get(pid, None) is not None:
                            status[pid] = (timestamp, description, action)
                            raise Exception(f"Duplicate detected: 2 applications running under same PID - {pid}")
                        status[pid] = (timestamp, description, action)
                    elif action.lstrip() == "END":
                        if status.get(pid, None) is None:
                            raise Exception(f"PID ended, but never started - {pid}")
                        time_start = status.get(pid)[0]
                        time_end = timestamp
                        difference_seconds = int((datetime.strptime(time_end, "%H:%M:%S") \
                                        - datetime.strptime(time_start, "%H:%M:%S")).total_seconds())
                        status.pop(pid)
                        if MIN5 <= difference_seconds < MIN10:
                            logger.warning(f"Job with PID - {pid} took longer than 5 minutes", extra=extra)
                        elif difference_seconds >= MIN10:
                            logger.error(f"Job with PID - {pid} took longer than 10 minutes", extra=extra)
                    else:
                        raise Exception(f"Action not START or END")
                except Exception as e:
                    logger.info(f"Exception parsing line with number {index + 1} - {e}", extra=extra)
                finally:
                    if multiprocess: lock.release()

            if len(status):
                for key, value in status.items():
                    if value[2].lstrip() == "START":
                        logger.info(f"PID: {key} - still running", extra=extra)
                    else: logger.info(f"PID: {key} - unknown state", extra=extra)

if __name__ == "__main__":
    ns = argument_parser().parse_args()
    lock = multiprocessing.Lock()
    regex = re.compile(r"^logs-[0-9]+.log$", flags=re.IGNORECASE)
    files = glob.glob(ns.logs + "/**")

    process_list = []

    for file in files:
        match = re.match(regex, os.path.basename(file))
        if match is not None:
            process = multiprocessing.Process(target=process_function, args=(file, True, lock))
            process_list.append(process)
            process.start()

    for process in process_list: process.join()