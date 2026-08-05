from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import httpx


HOST = "127.0.0.1"
PORT = 8013
BASE_URL = f"http://{HOST}:{PORT}"

APP_IMPORT = (
    "syk_simulasyon."
    "runtime_ui_sunucusu:app"
)


@dataclass(slots=True)
class DenetimSonucu:
    """Tek canlı HTTP/SSE denetim sonucu."""

    ad: str
    basarili: bool
    sure_ms: float
    durum_kodu: int | None = None
    aciklama: str = ""
    ayrintilar: dict[str, Any] | None = None


def port_acik_mi(
    host: str,
    port: int,
    *,
    timeout: float = 0.25,
) -> bool:
    """TCP portunun dinlemede olup olmadığını denetler."""

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as soket:
        soket.settimeout(timeout)

        return (
            soket.connect_ex(
                (host, port)
            )
            == 0
        )


def bekle_port(
    host: str,
    port: int,
    *,
    sure: float,
    process: subprocess.Popen[str],
) -> None:
    """Sunucu portu açılana kadar kontrollü bekler."""

    son_zaman = (
        time.monotonic()
        + sure
    )

    while time.monotonic() < son_zaman:
        if process.poll() is not None:
            raise RuntimeError(
                "Runtime 8013 işlemi port açılmadan sona erdi. "
                f"CIKIS_KODU={process.returncode}"
            )

        if port_acik_mi(
            host,
            port,
        ):
            return

        time.sleep(0.10)

    raise TimeoutError(
        f"Runtime portu zamanında açılmadı: {host}:{port}"
    )


def islem_durdur(
    process: subprocess.Popen[str],
) -> None:
    """Başlatılan Runtime 8013 işlemini güvenli kapatır."""

    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(
                signal.CTRL_BREAK_EVENT
            )
        else:
            process.send_signal(
                signal.SIGINT
            )

        process.wait(
            timeout=5.0
        )

    except Exception:
        if process.poll() is None:
            process.terminate()

        try:
            process.wait(
                timeout=3.0
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(
                timeout=3.0
            )


def zamanli_denetim(
    ad: str,
    islem: Any,
) -> DenetimSonucu:
    """Denetimi çalıştırır ve süresini kaydeder."""

    baslangic = time.perf_counter()

    try:
        sonuc = islem()

        sure_ms = (
            time.perf_counter()
            - baslangic
        ) * 1000.0

        if isinstance(
            sonuc,
            DenetimSonucu,
        ):
            sonuc.sure_ms = sure_ms
            return sonuc

        return DenetimSonucu(
            ad=ad,
            basarili=True,
            sure_ms=sure_ms,
            aciklama="Denetim geçti.",
            ayrintilar=(
                sonuc
                if isinstance(
                    sonuc,
                    dict,
                )
                else None
            ),
        )

    except Exception as hata:
        sure_ms = (
            time.perf_counter()
            - baslangic
        ) * 1000.0

        return DenetimSonucu(
            ad=ad,
            basarili=False,
            sure_ms=sure_ms,
            aciklama=(
                f"{type(hata).__name__}: {hata}"
            ),
        )


def health_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yanit = client.get(
        "/api/ugr/health"
    )

    veri = yanit.json()

    assert yanit.status_code == 200
    assert veri["durum"] == "saglikli"
    assert veri["runtime_portu"] == 8013
    assert veri["toplam_ikon"] == 215

    return DenetimSonucu(
        ad="HTTP_HEALTH",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "UGR Runtime 8013 sağlık uç noktası başarılı."
        ),
        ayrintilar={
            "runtime_portu": veri[
                "runtime_portu"
            ],
            "toplam_ikon": veri[
                "toplam_ikon"
            ],
            "durum": veri[
                "durum"
            ],
        },
    )


def snapshot_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yanit = client.get(
        "/api/ugr/snapshot"
    )

    veri = yanit.json()

    assert yanit.status_code == 200
    assert veri["olay_turu"] == "snapshot"
    assert veri["veri"]["toplam_ikon"] == 215
    assert len(
        veri["veri"]["ikonlar"]
    ) == 215

    return DenetimSonucu(
        ad="HTTP_SNAPSHOT",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "215 ikonun canlı snapshot çıktısı doğrulandı."
        ),
        ayrintilar={
            "toplam_ikon": veri[
                "veri"
            ][
                "toplam_ikon"
            ],
            "dondurulen_ikon": len(
                veri["veri"]["ikonlar"]
            ),
        },
    )


def preview_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yanit = client.get(
        "/api/ugr/preview"
    )

    assert yanit.status_code == 200

    icerik_turu = yanit.headers.get(
        "content-type",
        "",
    )

    assert "text/html" in icerik_turu

    assert (
        "SyKaşif UGR"
        in yanit.text
        or "syk-ugr-icon"
        in yanit.text
        or "data-syk-ugr"
        in yanit.text
    )

    return DenetimSonucu(
        ad="HTTP_PREVIEW",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "UGR tarayıcı ön izleme sayfası doğrulandı."
        ),
        ayrintilar={
            "icerik_turu": icerik_turu,
            "boyut": len(
                yanit.content
            ),
        },
    )


def css_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yol = (
        "/api/ugr/assets/"
        "web/static/css/"
        "ugr_dynamic_icons.css"
    )

    yanit = client.get(
        yol
    )

    assert yanit.status_code == 200
    assert ".syk-ugr-icon" in yanit.text

    return DenetimSonucu(
        ad="HTTP_CSS",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "UGR dinamik ikon CSS dosyası canlı erişilebilir."
        ),
        ayrintilar={
            "yol": yol,
            "boyut": len(
                yanit.content
            ),
        },
    )


def javascript_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yol = (
        "/api/ugr/assets/"
        "web/static/js/"
        "ugr_dynamic_icons.js"
    )

    yanit = client.get(
        yol
    )

    assert yanit.status_code == 200

    assert (
        "UgrDynamicIconRuntime"
        in yanit.text
        or "sykUgrRuntime"
        in yanit.text
    )

    return DenetimSonucu(
        ad="HTTP_JAVASCRIPT",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "UGR dinamik ikon JavaScript runtime dosyası doğrulandı."
        ),
        ayrintilar={
            "yol": yol,
            "boyut": len(
                yanit.content
            ),
        },
    )


def ikon_durum_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yanit = client.post(
        "/api/ugr/icons/sys-001/state",
        json={
            "durum": "calisiyor",
            "neden": (
                "SPR-011 Paket-007 "
                "gerçek HTTP doğrulaması."
            ),
            "zorla": True,
        },
    )

    veri = yanit.json()

    assert yanit.status_code == 200
    assert veri["ikon"]["durum"] == "calisiyor"
    assert (
        veri["canli_olay"]["olay_turu"]
        == "ikon_durumu"
    )

    return DenetimSonucu(
        ad="HTTP_IKON_DURUM_DEGISIMI",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "Gerçek HTTP üzerinden ikon durumu değiştirildi."
        ),
        ayrintilar={
            "ikon_kimligi": "sys-001",
            "durum": veri[
                "ikon"
            ][
                "durum"
            ],
            "olay_turu": veri[
                "canli_olay"
            ][
                "olay_turu"
            ],
        },
    )


def toplu_durum_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    yanit = client.post(
        "/api/ugr/icons/bulk/state",
        json={
            "ikon_kimlikleri": [
                "sys-001",
                "sys-002",
                "sys-003",
            ],
            "durum": "uyari",
            "neden": (
                "SPR-011 Paket-007 "
                "canlı toplu durum testi."
            ),
            "zorla": True,
        },
    )

    veri = yanit.json()

    assert yanit.status_code == 200

    assert (
        veri["olay_turu"]
        == "toplu_guncelleme"
    )

    assert (
        veri["veri"][
            "basarili_ikon_sayisi"
        ]
        == 3
    )

    assert (
        veri["veri"][
            "basarisiz_ikon_sayisi"
        ]
        == 0
    )

    return DenetimSonucu(
        ad="HTTP_TOPLU_DURUM",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=yanit.status_code,
        aciklama=(
            "Sabit bulk rotası canlı ağ üzerinden doğrulandı."
        ),
        ayrintilar={
            "basarili_ikon": 3,
            "basarisiz_ikon": 0,
        },
    )


def sse_denetle(
    client: httpx.Client,
) -> DenetimSonucu:
    """SSE bağlantısını açar ve gerçek ikon olayını yakalar."""

    hazir = threading.Event()
    tamamlandi = threading.Event()

    sonuclar: dict[
        str,
        Any
    ] = {
        "olay_turu": None,
        "veri": None,
        "hata": None,
    }

    def sse_okuyucu() -> None:
        try:
            with client.stream(
                "GET",
                "/api/ugr/events",
                params={
                    "kalp_atisi_suresi": 1.0,
                },
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=8.0,
                    write=5.0,
                    pool=5.0,
                ),
            ) as yanit:
                assert yanit.status_code == 200

                icerik_turu = (
                    yanit.headers.get(
                        "content-type",
                        "",
                    )
                )

                assert (
                    "text/event-stream"
                    in icerik_turu
                )

                hazir.set()

                mevcut_olay = None

                for satir in yanit.iter_lines():
                    if satir.startswith(
                        "event:"
                    ):
                        mevcut_olay = (
                            satir.split(
                                ":",
                                1,
                            )[1].strip()
                        )

                    elif satir.startswith(
                        "data:"
                    ):
                        ham_veri = (
                            satir.split(
                                ":",
                                1,
                            )[1].strip()
                        )

                        veri = json.loads(
                            ham_veri
                        )

                        if (
                            mevcut_olay
                            == "ikon_durumu"
                        ):
                            sonuclar[
                                "olay_turu"
                            ] = mevcut_olay

                            sonuclar[
                                "veri"
                            ] = veri

                            tamamlandi.set()
                            return

                    if tamamlandi.is_set():
                        return

        except Exception as hata:
            sonuclar["hata"] = (
                f"{type(hata).__name__}: {hata}"
            )

            hazir.set()
            tamamlandi.set()

    thread = threading.Thread(
        target=sse_okuyucu,
        name="sykasif-ugr-sse-test",
        daemon=True,
    )

    thread.start()

    if not hazir.wait(
        timeout=5.0
    ):
        raise TimeoutError(
            "SSE istemcisi zamanında hazırlanamadı."
        )

    if sonuclar["hata"]:
        raise RuntimeError(
            sonuclar["hata"]
        )

    tetikleme = client.post(
        "/api/ugr/icons/sys-004/state",
        json={
            "durum": "yeni_veri",
            "neden": (
                "SPR-011 Paket-007 "
                "SSE canlı olay tetiklemesi."
            ),
            "zorla": True,
        },
    )

    assert tetikleme.status_code == 200

    if not tamamlandi.wait(
        timeout=8.0
    ):
        raise TimeoutError(
            "SSE üzerinden ikon_durumu olayı alınamadı."
        )

    if sonuclar["hata"]:
        raise RuntimeError(
            sonuclar["hata"]
        )

    olay = sonuclar["veri"]

    assert olay is not None
    assert olay["olay_turu"] == "ikon_durumu"
    assert olay["ikon_kimligi"] == "sys-004"

    thread.join(
        timeout=1.0
    )

    return DenetimSonucu(
        ad="SSE_CANLI_IKON_OLAYI",
        basarili=True,
        sure_ms=0.0,
        durum_kodu=200,
        aciklama=(
            "SSE kanalı gerçek ikon durum olayını iletti."
        ),
        ayrintilar={
            "olay_turu": olay[
                "olay_turu"
            ],
            "ikon_kimligi": olay[
                "ikon_kimligi"
            ],
            "durum": olay[
                "veri"
            ][
                "durum"
            ],
        },
    )


def rapor_metni(
    rapor: dict[str, Any],
) -> str:
    satirlar = [
        "SPR-011 PAKET-007",
        "UGR RUNTIME 8013 CANLI DOGRULAMA RAPORU",
        "",
        f"HOST={rapor['host']}",
        f"PORT={rapor['port']}",
        f"BASE_URL={rapor['base_url']}",
        f"APP_IMPORT={rapor['app_import']}",
        (
            "TOPLAM_DENETIM="
            f"{rapor['toplam_denetim']}"
        ),
        (
            "BASARILI_DENETIM="
            f"{rapor['basarili_denetim']}"
        ),
        (
            "BASARISIZ_DENETIM="
            f"{rapor['basarisiz_denetim']}"
        ),
        (
            "GENEL_DURUM="
            f"{rapor['genel_durum']}"
        ),
        "",
        "DENETIMLER:",
    ]

    for sonuc in rapor["sonuclar"]:
        satirlar.extend(
            [
                "-" * 72,
                f"AD={sonuc['ad']}",
                (
                    "BASARILI="
                    f"{sonuc['basarili']}"
                ),
                (
                    "SURE_MS="
                    f"{sonuc['sure_ms']:.3f}"
                ),
                (
                    "DURUM_KODU="
                    f"{sonuc['durum_kodu']}"
                ),
                (
                    "ACIKLAMA="
                    f"{sonuc['aciklama']}"
                ),
                (
                    "AYRINTILAR="
                    + json.dumps(
                        sonuc["ayrintilar"],
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                ),
            ]
        )

    satirlar.extend(
        [
            "",
            (
                "RUNTIME_ISLEMI="
                "DOGRULAMA_SONUNDA_DURDURULDU"
            ),
            (
                "GERCEK_HTTP_DOGRULAMASI="
                "TAMAMLANDI"
            ),
            (
                "SSE_CANLI_DOGRULAMA="
                "TAMAMLANDI"
            ),
            "",
        ]
    )

    return "\n".join(
        satirlar
    )


def parser_uret() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-json",
        required=True,
    )

    parser.add_argument(
        "--output-text",
        required=True,
    )

    parser.add_argument(
        "--stdout",
        required=True,
    )

    parser.add_argument(
        "--stderr",
        required=True,
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parser_uret().parse_args(
        argv
    )

    output_json = Path(
        args.output_json
    )

    output_text = Path(
        args.output_text
    )

    stdout_path = Path(
        args.stdout
    )

    stderr_path = Path(
        args.stderr
    )

    for path in (
        output_json,
        output_text,
        stdout_path,
        stderr_path,
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    if port_acik_mi(
        HOST,
        PORT,
    ):
        raise RuntimeError(
            "8013 portu doğrulama öncesinde kullanımda. "
            "Mevcut süreç otomatik kapatılmadı."
        )

    creation_flags = 0

    if os.name == "nt":
        creation_flags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
        )

    stdout_handle = stdout_path.open(
        "w",
        encoding="utf-8",
    )

    stderr_handle = stderr_path.open(
        "w",
        encoding="utf-8",
    )

    process: subprocess.Popen[str] | None = None

    try:
        command = [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "uvicorn",
            APP_IMPORT,
            "--host",
            HOST,
            "--port",
            str(PORT),
            "--log-level",
            "info",
            "--no-access-log",
        ]

        process = subprocess.Popen(
            command,
            cwd=Path.cwd(),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            creationflags=creation_flags,
        )

        bekle_port(
            HOST,
            PORT,
            sure=15.0,
            process=process,
        )

        with httpx.Client(
            base_url=BASE_URL,
            timeout=httpx.Timeout(
                connect=5.0,
                read=15.0,
                write=10.0,
                pool=5.0,
            ),
            follow_redirects=True,
        ) as client:
            denetimler = [
                zamanli_denetim(
                    "HTTP_HEALTH",
                    lambda: health_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "HTTP_SNAPSHOT",
                    lambda: snapshot_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "HTTP_PREVIEW",
                    lambda: preview_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "HTTP_CSS",
                    lambda: css_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "HTTP_JAVASCRIPT",
                    lambda: javascript_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "HTTP_IKON_DURUM_DEGISIMI",
                    lambda: ikon_durum_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "HTTP_TOPLU_DURUM",
                    lambda: toplu_durum_denetle(
                        client
                    ),
                ),
                zamanli_denetim(
                    "SSE_CANLI_IKON_OLAYI",
                    lambda: sse_denetle(
                        client
                    ),
                ),
            ]

        basarili = sum(
            sonuc.basarili
            for sonuc in denetimler
        )

        basarisiz = (
            len(denetimler)
            - basarili
        )

        rapor = {
            "sema": (
                "sykasif.ugr."
                "runtime-8013-live-validation.v1"
            ),
            "host": HOST,
            "port": PORT,
            "base_url": BASE_URL,
            "app_import": APP_IMPORT,
            "toplam_denetim": len(
                denetimler
            ),
            "basarili_denetim": basarili,
            "basarisiz_denetim": basarisiz,
            "genel_durum": (
                "basarili"
                if basarisiz == 0
                else "basarisiz"
            ),
            "sonuclar": [
                asdict(sonuc)
                for sonuc in denetimler
            ],
        }

        output_json.write_text(
            json.dumps(
                rapor,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        output_text.write_text(
            rapor_metni(
                rapor
            ),
            encoding="utf-8",
        )

        print(
            json.dumps(
                {
                    "toplam_denetim": len(
                        denetimler
                    ),
                    "basarili_denetim": basarili,
                    "basarisiz_denetim": basarisiz,
                    "genel_durum": rapor[
                        "genel_durum"
                    ],
                    "port": PORT,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        for sonuc in denetimler:
            durum = (
                "PASSED"
                if sonuc.basarili
                else "FAILED"
            )

            print(
                f"{sonuc.ad}={durum} "
                f"SURE_MS={sonuc.sure_ms:.3f}"
            )

            if not sonuc.basarili:
                print(
                    f"HATA={sonuc.aciklama}"
                )

        if basarisiz:
            print(
                "UGR_RUNTIME_8013_CANLI_DOGRULAMA_BASARISIZ"
            )

            return 1

        print(
            "UGR_RUNTIME_8013_CANLI_DOGRULAMA_TAMAMLANDI"
        )

        return 0

    finally:
        if process is not None:
            islem_durdur(
                process
            )

        stdout_handle.close()
        stderr_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
