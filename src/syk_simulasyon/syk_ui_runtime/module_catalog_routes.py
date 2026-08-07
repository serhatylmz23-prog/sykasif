from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v2/runtime-modules", tags=["runtime-modules"])

_MODULES = {
    "harita": {
        "id": "harita",
        "ad": "Harita",
        "durum": "hazir",
    },
    "kanit": {
        "id": "kanit",
        "ad": "Kanıt",
        "durum": "hazir",
    },
    "analiz": {
        "id": "analiz",
        "ad": "Analiz",
        "durum": "hazir",
    },
    "rapor": {
        "id": "rapor",
        "ad": "Rapor",
        "durum": "hazir",
    },
}


@router.get("")
def modul_katalogu():
    return {
        "durum": "ok",
        "moduller": list(_MODULES.values()),
        "toplam": len(_MODULES),
    }


@router.get("/{module_id}")
def modul_detayi(module_id: str):
    module = _MODULES.get(module_id)

    if module is None:
        raise HTTPException(
            status_code=404,
            detail="MODULE_NOT_FOUND",
        )

    return {
        "durum": "ok",
        "modul": module,
    }
