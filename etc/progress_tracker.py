from dataclasses import dataclass, field
from time import sleep
from enum import Flag


class Progess(Flag):
    STILL = "PROCESSING"
    UPDATED = "NEXT"
    HALT = "HALT"
    DONE = "DONE"


@dataclass
class ProcessProgress:
    tracker_amount: int = field(default=0, compare=False)
    task_list: list[str] = field(default_factory=list)
    status: Progess = Progess.UPDATED

    def json(self) -> dict:
        return f"{{'status':{self.status},'task': {self.task_list}}}"


@dataclass
class ProgressTracker:
    process: dict[int, ProcessProgress] = field(default_factory=dict)

    def new(self) -> int:
        proc_id = len(self.process) + 1
        self.process[proc_id] = ProcessProgress()

        return proc_id

    def get(self, prog_id: int):
        state: ProcessProgress = self.process[prog_id]
        self.process[prog_id].tracker_amount = state.tracker_amount + 1

        while True:
            sleep(1)
            match state.status:
                case Progess.STILL:
                    continue
                case Progess.UPDATED:
                    yield (state.json())
                    self.process[prog_id].status = Progess.STILL
                case Progess.DONE:
                    yield (state.json())
                    break
                case Progess.HALT:
                    yield (state.json())

                    self.kill(prog_id)

                    return
            state = self.process[prog_id]

        self.process[prog_id].tracker_amount = state.tracker_amount - 1

        self.close(prog_id)

    def update(
        self,
        prog_id: int,
        task: str,
    ):
        task_list = self.process[prog_id].task_list
        task_list.append(task)

        self.process[prog_id].task_list = task_list
        self.process[prog_id].status = Progess.UPDATED

    def complete(self, prog_id: int):
        self.process[prog_id].status = Progess.DONE

    def halt(self, prog_id: int):
        self.process[prog_id].status = Progess.HALT

    def kill(self, prog_id: int):
        self.process.pop(prog_id)

    def close(self, prog_id: int):
        prog = self.process[prog_id]

        if prog.tracker_amount == 0:
            self.process.pop(prog_id)
