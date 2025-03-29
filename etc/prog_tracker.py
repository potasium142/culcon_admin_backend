from enum import Enum
import time

from pydantic import BaseModel, Field


class Status(str, Enum):
    PROCESS = "PROCESS"
    HALT = "HALT"
    DONE = "DONE"


class ProdCrtStg(str, Enum):
    PREPARE = "PREPARE"
    CREATE_PRODUCT = "CREATE_PRODUCT"
    EMBED_DATA = "EMBED_DATA"
    CREATE_DOC = "CREATE_DOC"
    UPLOAD_IMAGE = "UPLOAD_IMAGE"
    SAVING_INGREDIENT = "SAVING_INGREDIENT"


class StageProgress(BaseModel):
    total_stage: int = Field(
        exclude=True,
    )
    complete_stage: int = Field(
        default=0,
        exclude=True,
    )
    progress: float = 0.0

    def update_state(self, stage: int):
        self.complete_stage = stage
        self.progress = self.complete_stage / self.total_stage


class ProgressTracker(BaseModel):
    total_stage: int = Field(
        exclude=True,
    )
    complete_stage: int = Field(
        default=0,
        exclude=True,
    )
    progress: float = 0.0

    status: Status = Status.PROCESS
    error_msg: str = ""
    stage_progress: dict[ProdCrtStg, StageProgress]


class ProgressTrackerManager:
    def __init__(
        self,
        image_amount: int,
        ingredient_amount: int = 0,
    ) -> None:
        self.updated = True
        self.complete = False
        self.tracker = self.create_mealkti_create_progress(
            image_amount, ingredient_amount
        )

    def create_mealkti_create_progress(
        self, image_amount: int, ingredient_amount: int
    ) -> ProgressTracker:
        prog_trckr = ProgressTracker(
            total_stage=6,
            stage_progress={
                ProdCrtStg.PREPARE: StageProgress(total_stage=1),
                ProdCrtStg.CREATE_PRODUCT: StageProgress(total_stage=1),
                ProdCrtStg.EMBED_DATA: StageProgress(total_stage=3),
                ProdCrtStg.CREATE_DOC: StageProgress(total_stage=1),
                ProdCrtStg.SAVING_INGREDIENT: StageProgress(
                    total_stage=ingredient_amount
                ),
                ProdCrtStg.UPLOAD_IMAGE: StageProgress(total_stage=image_amount),
            },
        )

        return prog_trckr

    def halt(self, msg: str):
        self.updated = True
        self.complete = True
        self.tracker.status = Status.HALT
        self.tracker.error_msg = msg

    def done(self):
        self.updated = True
        self.complete = True
        self.tracker.status = Status.DONE

    def removable(self):
        return self.tracker.status == Status.DONE

    def update(self, stage_name: ProdCrtStg, stage_prog: int):
        self.updated = True
        self.tracker.stage_progress[stage_name].update_state(stage_prog)

        if self.tracker.stage_progress[stage_name].total_stage == stage_prog:
            self.tracker.complete_stage += 1

        self.tracker.progress = self.tracker.complete_stage / self.tracker.total_stage

    def stream(self):
        while True:
            time.sleep(1)
            if not self.updated:
                continue

            yield self.tracker.model_dump_json()

            if self.complete:
                return


prod_creation_tracker: dict[str, ProgressTrackerManager] = dict()


def get_prog_tracker():
    yield prod_creation_tracker
