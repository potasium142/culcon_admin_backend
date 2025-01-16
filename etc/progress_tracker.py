from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from time import sleep
from enum import Enum


class Status(str, Enum):
    STALL = "STALL"
    UPDATED = "UPDATED"
    HALT = "HALT"
    DONE = "DONE"


class SubTask(BaseModel):
    status: Status
    description: str
    progress: int


class ProcessProgress(BaseModel):
    tracker_amount: int = Field(
        default=0,
        exclude=True,
    )
    subtask: dict[int, SubTask] = dict()
    status: Status = Status.UPDATED


@dataclass
class ProgressTracker:
    process: dict[int, ProcessProgress] = field(default_factory=dict)

    def new(
        self,
    ) -> int:
        proc_id = len(self.process) + 1

        pp = ProcessProgress()

        self.process[proc_id] = pp
        return proc_id

    def get(self, prog_id: int):
        state: ProcessProgress = self.process[prog_id]
        self.process[prog_id].tracker_amount = state.tracker_amount + 1

        while True:
            sleep(0.7)
            match state.status:
                case Status.STALL:
                    continue
                case Status.UPDATED:
                    yield state.model_dump_json()
                    self.process[prog_id].status = Status.STALL
                case Status.DONE:
                    yield state.model_dump_json()

                    break
                case Status.HALT:
                    yield state.model_dump_json()
                    self.kill(prog_id)
                    return
            state = self.process[prog_id]

        self.process[prog_id].tracker_amount = state.tracker_amount - 1

        self.close(prog_id)

    def new_subtask(
        self,
        prog_id: int,
        description: str,
        status: Status = Status.UPDATED,
        progress: int = 0,
    ) -> int:
        id: int = len(self.process[prog_id].subtask)

        self.process[prog_id].subtask[id] = SubTask(
            status=status,
            description=description,
            progress=progress,
        )

        return id

    def update_subtask(
        self,
        prog_id: int,
        subtask_id: int,
        progress: int | None = None,
        status: None | Status = None,
    ):
        subtask = self.process[prog_id].subtask[subtask_id]

        if progress:
            subtask.progress = progress
        if status:
            subtask.status = status

        self.process[prog_id].subtask[subtask_id] = subtask
        self.process[prog_id].status = Status.UPDATED

    def close_subtask(self, prog_id: int, subtask_id: int):
        subtask = self.process[prog_id].subtask[subtask_id]

        subtask.status = Status.DONE

        self.process[prog_id].subtask[subtask_id] = subtask
        self.process[prog_id].status = Status.UPDATED

    def complete(
        self,
        prog_id: int,
    ):
        self.process[prog_id].status = Status.DONE

    def halt(
        self,
        prog_id: int,
        msg: str,
    ):
        id: int = len(self.process[prog_id].subtask)

        self.process[prog_id].subtask[id] = SubTask(
            status=Status.HALT,
            description=msg,
            progress=-1,
        )

        self.process[prog_id].status = Status.HALT

    def kill(self, prog_id: int):
        del self.process[prog_id]

    def close(self, prog_id: int):
        prog = self.process[prog_id]

        if prog.tracker_amount == 0:
            del self.process[prog_id]


pp = ProgressTracker()
