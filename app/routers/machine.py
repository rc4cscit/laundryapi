from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.auth import validate_api_key
from app.machine import (
    IMachineService,
    Machine,
    MachineFilter,
    MachineStatus,
    MachineType,
    MachineUpdate,
    _field_floor,
    _field_pos,
    _field_status,
    _field_type,
)
from app.redis.machine import get_machine_service

router = APIRouter(prefix="/machine")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    description="Creates a new machine.",
    dependencies=[Depends(validate_api_key)],
)
async def create_machine(
    m: Machine, ms: IMachineService = Depends(get_machine_service)
) -> None:
    ms.create(m.to_machine_x())


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[Machine],
    description="Get a list of machines.",
)
async def get_machines(
    status: Optional[MachineStatus] = Query(
        None, description=_field_status.description
    ),
    floor: Optional[int] = Query(None, description=_field_floor.description),
    pos: Optional[int] = Query(None, description=_field_pos.description),
    type: Optional[MachineType] = Query(None, description=_field_type.description),
    ms: IMachineService = Depends(get_machine_service),
) -> List[Machine]:
    mf = MachineFilter(status=status, floor=floor, pos=pos, type=type)
    return [m.to_machine() for m in ms.find(mf)]


@router.put(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Machine,
    description="Perform partial update of a machine. Use the /start and /stop endpoints instead if setting machine state.",
    dependencies=[Depends(validate_api_key)],
)
async def update_machine(
    mu: MachineUpdate,
    floor: int = Query(..., description=_field_floor.description),
    pos: int = Query(..., description=_field_pos.description),
    ms: IMachineService = Depends(get_machine_service),
) -> Machine:
    return ms.update(floor, pos, mu.to_machine_update_x()).to_machine()


@router.put(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    description="Start this machine.",
    dependencies=[Depends(validate_api_key)],
)
async def start_machine(
    floor: int = Query(..., description=_field_floor.description),
    pos: int = Query(..., description=_field_pos.description),
    ms: IMachineService = Depends(get_machine_service),
):
    return ms.start(floor, pos)


@router.put(
    "/stop",
    status_code=status.HTTP_202_ACCEPTED,
    description="Stop this machine.",
    dependencies=[Depends(validate_api_key)],
)
async def stop_machine(
    floor: int = Query(..., description=_field_floor.description),
    pos: int = Query(..., description=_field_pos.description),
    ms: IMachineService = Depends(get_machine_service),
):
    return ms.stop(floor, pos)
