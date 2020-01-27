import threading
import json

from collections import namedtuple
from time import sleep
from typing import List
from service import startWithDirectArgs
from util import colorprint

BakingJob = namedtuple('BakingJob', ['jobId', 'jobArgs', "state"])


class BakingMan(threading.Thread):
    def __init__(self):
        super().__init__()
        self.isProcessRunning = False
        self.currentId = 0
        self.queue: List[BakingJob] = []
        self.currentJob = None
        self.results: List[BakingJob] = []
        self.running = False

    def addJob(self, args):
        self.getUniqueId()
        newJob = BakingJob(str(self.currentId), args, "pending")
        self.queue.append(newJob)
        return self.currentId

    def stop(self, blocking=True):
        self.running = False
        if blocking:
            self.join()

    def run(self):
        self.running = True
        while self.running:
            if not self.isProcessRunning:
                if len(self.queue) > 0:
                    BakingMan.isProcessRunning = True
                    self.currentJob = self.queue.pop(0)
                    try:
                        self.runJob()
                    except FileNotFoundError as e:
                        BakingMan.isProcessRunning = False
                        colorprint(
                            "File not found for jobId {}".format(
                                self.currentJob.jobId), 31)
                        self.currentJob = None
                        print(e)
                    except json.decoder.JSONDecodeError as e:
                        BakingMan.isProcessRunning = False
                        colorprint(
                            "JSON not valid for jobId {}".format(
                                self.currentJob.jobId), 31)
                        self.currentJob = None
                        print(e)
                    except Exception as e:
                        BakingMan.isProcessRunning = False
                        colorprint(
                            "Exception for jobId {}".format(
                                self.currentJob.jobId), 31)
                        self.currentJob = None
                        print(e)

                else:
                    sleep(0.5)

    def runJob(self):
        colorprint(
            "Starting runJob with jobId {}".format(self.currentJob.jobId), 32)

        self.currentJob = self.currentJob._replace(state="running")
        output = startWithDirectArgs(self.currentJob.jobArgs)

        result = {}
        if "error" in output and output["error"] is not None:
            result = {
                "jobId": self.currentJob.jobId,
                "jobArgs": self.currentJob.jobArgs,
                "state": "error",
                "error": output["error"]
            }
            colorprint("Error in startWithDirectArgs", 31)

        else:
            result = {
                "jobId": self.currentJob.jobId,
                "jobArgs": self.currentJob.jobArgs,
                "urlAoMapImage": output["urlAoMapImage"],
                "urlAoMappingJson": output["urlAoMappingJson"],
                "urlIgxcModified": output["urlIgxcModified"],
                "urlIgxcOriginal": output["urlIgxcOriginal"],
                "transforms": output["transforms"],
                "state": "finished",
                "igxcModified": output["igxcModified"]
            }
            colorprint(
                "Finished runJob with jobId {}".format(self.currentJob.jobId),
                32)

        self.results.append(result)
        self.isProcessRunning = False
        self.currentJob = None
        return result

    def getUniqueId(self) -> str:
        self.currentId += 1
        return str(self.currentId)

    def hasQueuedJob(self, jobId: str) -> bool:
        for entry in self.queue:
            if entry.jobId == jobId:
                return True
        return False

    def isJobFinished(self, jobId: str) -> bool:
        if self.hasJob(jobId):
            for entry in self.results:
                if entry["jobId"] == jobId:
                    return True
        return False

    def hasJob(self, jobId: str) -> bool:
        if self.currentJob != None and self.currentJob.jobId == jobId:
            return True

        for entry in self.results:
            if entry["jobId"] == jobId:
                return True

        for entry in self.queue:
            if entry.jobId == jobId:
                return True
        return False

    def getJob(self, jobId: str) -> BakingJob:
        if self.currentJob != None and self.currentJob.jobId == jobId:
            return self.currentJob._asdict()

        for entry in self.results:
            if entry["jobId"] == jobId:
                return entry

        for entry in self.queue:
            if entry.jobId == jobId:
                return entry._asdict()
        return None

    def getAllJobs(self) -> List[BakingJob]:
        allJobs = self.results[:]
        for entry in self.queue:
            allJobs.append(json.loads(json.dumps(entry._asdict())))
        if self.currentJob != None:
            allJobs.append(json.loads(json.dumps(self.currentJob._asdict())))
        return allJobs
