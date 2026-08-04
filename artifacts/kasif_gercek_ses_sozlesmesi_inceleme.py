from __future__ import annotations

import ast
from pathlib import Path


dosyalar = [
    Path("src/syk_jarmin/speech_to_text.py"),
    Path("src/syk_jarmin/text_to_speech.py"),
    Path("src/syk_jarmin/wake_word.py"),
    Path("src/syk_jarmin/voice_profiles.py"),
    Path("src/syk_jarmin/audio_router.py"),
    Path("src/syk_jarmin/notification_engine.py"),
    Path("tests/test_speech_to_text.py"),
    Path("tests/test_text_to_speech.py"),
    Path("tests/test_wake_word.py"),
    Path("tests/test_voice_profiles.py"),
    Path("tests/test_audio_router.py"),
    Path("tests/test_notification_engine.py"),
]

eksikler = [
    str(yol)
    for yol in dosyalar
    if not yol.is_file()
]

if eksikler:
    raise FileNotFoundError(
        "Eksik dosyalar:\n"
        + "\n".join(eksikler)
    )


rapor: list[str] = []

for yol in dosyalar:
    metin = yol.read_text(
        encoding="utf-8",
    )

    satirlar = metin.splitlines()

    rapor.extend(
        [
            "",
            "=" * 80,
            yol.as_posix(),
            "=" * 80,
        ]
    )

    if yol.parts[0] == "tests":
        rapor.extend(
            f"{numara:04d}: {satir}"
            for numara, satir in enumerate(
                satirlar,
                start=1,
            )
        )
        continue

    agac = ast.parse(
        metin,
        filename=str(yol),
    )

    bulundu = False

    for dugum in agac.body:
        if isinstance(
            dugum,
            ast.ClassDef,
        ):
            bulundu = True

            rapor.append(
                f"\nSINIF: {dugum.name}"
            )

            for alt in dugum.body:
                if isinstance(
                    alt,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    tur = (
                        "async"
                        if isinstance(
                            alt,
                            ast.AsyncFunctionDef,
                        )
                        else "normal"
                    )

                    argumanlar = [
                        arg.arg
                        for arg in alt.args.args
                    ]

                    rapor.append(
                        f"  METOT: {alt.name}"
                        f" | tür={tur}"
                        f" | giriş={argumanlar}"
                        f" | satır={alt.lineno}-{alt.end_lineno}"
                    )

        elif isinstance(
            dugum,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            bulundu = True

            rapor.append(
                f"\nİŞLEV: {dugum.name}"
                f" | satır={dugum.lineno}-{dugum.end_lineno}"
            )

    if not bulundu:
        rapor.append(
            "\nSINIF_VEYA_İŞLEV_BULUNAMADI"
        )

    rapor.append(
        "\n--- DOSYA İÇERİĞİ ---"
    )

    rapor.extend(
        f"{numara:04d}: {satir}"
        for numara, satir in enumerate(
            satirlar,
            start=1,
        )
    )


rapor_yolu = Path(
    "artifacts/"
    "KASIF_GERCEK_SES_SOZLESMESI.txt"
)

rapor_yolu.write_text(
    "\n".join(rapor),
    encoding="utf-8",
)

print(
    "KASIF_GERCEK_SES_SOZLESMESI_OK"
)

print(
    "RAPOR",
    rapor_yolu,
)

print(
    "INCELENEN_DOSYA_SAYISI",
    len(dosyalar),
)
