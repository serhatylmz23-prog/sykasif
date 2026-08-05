from pathlib import Path

dosya = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

icerik = dosya.read_text(
    encoding="utf-8-sig"
)

isaret = (
    "# SYK_UGR_DOGRUDAN_ROUTE_BAGLANTISI"
)

if isaret in icerik:
    print(
        "UGR_DOGRUDAN_ROUTE_BAGLANTISI_ZATEN_VAR"
    )
    raise SystemExit(0)

if "syk_ugr_router" not in icerik:
    raise RuntimeError(
        "syk_ugr_router kaynak dosyada bulunamadı."
    )

hedef = (
    "    # SYK_TERMINAL_FINANS_DOGRUDAN_ROUTE_BAGLANTISI\n"
    "    mevcut_yollar = {\n"
    '        getattr(route, "path", None)\n'
    "        for route in uygulama.router.routes\n"
    "    }\n"
    "\n"
    "    for route in syk_terminal_router.routes:\n"
    '        if getattr(route, "path", None) not in mevcut_yollar:\n'
    "            uygulama.router.routes.append(route)\n"
)

eklenecek = hedef + (
    "\n"
    "    # SYK_UGR_DOGRUDAN_ROUTE_BAGLANTISI\n"
    "    mevcut_yollar = {\n"
    '        getattr(route, "path", None)\n'
    "        for route in uygulama.router.routes\n"
    "    }\n"
    "\n"
    "    for route in syk_ugr_router.routes:\n"
    '        if getattr(route, "path", None) not in mevcut_yollar:\n'
    "            uygulama.router.routes.append(route)\n"
)

if hedef not in icerik:
    raise RuntimeError(
        "Terminal doğrudan route bağlantı bloğu bulunamadı."
    )

yeni_icerik = icerik.replace(
    hedef,
    eklenecek,
    1,
)

dosya.write_text(
    yeni_icerik,
    encoding="utf-8",
)

print(
    "UGR_DOGRUDAN_ROUTE_BAGLANTISI_EKLENDI"
)
