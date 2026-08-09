from terminal_v2_canonical.preview_053005 import app
from terminal_v2_canonical.runtime.map.map_api_053013 import (
    router as real_map_router,
)


existing_paths = {
    getattr(route, "path", None)
    for route in app.routes
}

if "/api/v2/map/state" not in existing_paths:
    app.include_router(real_map_router)
