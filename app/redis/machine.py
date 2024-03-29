import logging
from datetime import datetime
from typing import List

from fastapi import Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from redis import Redis
from redis.commands.json import JSON as RedisJSON
from redis.commands.search import Search as RediSearch
from redis.commands.search.document import Document
from redis.commands.search.query import Query

from app.machine import (
    IMachineService,
    MachineFilter,
    MachineStatus,
    MachineUpdateX,
    MachineX,
)

from . import get_redis

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MachineService(IMachineService):
    """
    Service class implementing the IMachineService interface, with Redis as
    the datastore.
    """

    root_path: str = "."

    def __init__(self, redis: Redis):
        self.redis: Redis = redis
        self.rj: RedisJSON = redis.json()
        self.rs: RediSearch = redis.ft(index_name="machineIdx")

    def create(self, m: MachineX) -> None:
        """Creates a machine. Fails silently if a machine at the same floor
        and position already exists."""
        res = self.rj.set(m.create_key(), self.root_path, jsonable_encoder(m), nx=True)
        if res is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Machine at floor {m.floor} position {m.pos} already exists.",
            )

    def find(self, mf: MachineFilter) -> List[MachineX]:
        """Queries Redis for machines, based on the filter provided."""
        q = self.build_query(mf)
        logger.info(f"executing RediSearch query; query={q.query_string()}")
        res = self.rs.search(q)
        return [self.from_document(doc) for doc in res.docs]

    def update(self, floor: int, pos: int, mu: MachineUpdateX) -> MachineX:
        key = MachineX._create_key(floor, pos)
        res = self.rj.get(key)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine at floor {floor} and position {pos} was not found.",
            )
        old = MachineX(**res)
        new = old.copy(update=mu.dict(exclude_unset=True, exclude_none=True))
        self.rj.set(key, self.root_path, jsonable_encoder(new))
        return new

    def start(self, floor: int, pos: int) -> None:
        self.update(
            floor,
            pos,
            MachineUpdateX(
                status=MachineStatus.in_use, last_started_at=datetime.utcnow()
            ),
        )

    def stop(self, floor: int, pos: int) -> None:
        self.update(floor, pos, MachineUpdateX(status=MachineStatus.idle))

    def delete(self, floor: int, pos: int) -> MachineX:
        raise NotImplementedError()

    @staticmethod
    def from_document(doc: Document) -> MachineX:
        return MachineX.from_json(doc.__dict__["json"])

    @staticmethod
    def build_query(mf: MachineFilter) -> Query:
        """Builds a RediSearch query string based on a MachineFilter
        instance."""

        def floor(v):
            return f"@floor:[{v} {v}]"

        def pos(v):
            return f"@pos:[{v} {v}]"

        def type(v):
            return f"@type:{v}"

        def status(v):
            return f"@status:{v}"

        q_mapping = {"floor": floor, "pos": pos, "type": type, "status": status}

        mf_dict = mf.dict(exclude_unset=True, exclude_none=True)

        if not mf_dict:
            q = Query("*")
        else:
            q = Query(" ".join([q_mapping[k](v) for k, v in mf_dict.items()]))
        q.paging(0, 20)
        return q


def get_machine_service(redis: Redis = Depends(get_redis)):
    """Fastapi dependency for getting a MachineService instance."""
    return MachineService(redis)
