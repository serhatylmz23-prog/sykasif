from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/syk-ui-screen", response_class=HTMLResponse, include_in_schema=False)
def syk_ui_screen() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SyKaşif Terminal V2</title>
</head>
<body>
    <main id="syk-terminal-v2">
        <h1>SyKaşif Terminal V2</h1>
        <p>UI Runtime aktif.</p>
    </main>
</body>
</html>
        """.strip()
    )
