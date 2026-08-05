from datetime import datetime,UTC
from dataclasses import dataclass,field
from typing import Any

@dataclass(slots=True)
class RuntimeState:
    runtime:str="BOOT"
    connected:bool=False
    tablet:bool=False
    desktop:bool=False
    last_update:datetime=field(default_factory=lambda:datetime.now(UTC))
    payload:dict[str,Any]=field(default_factory=dict)
