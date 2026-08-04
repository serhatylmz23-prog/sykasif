from pathlib import Path
import ast


path = Path(
    "src/syk_jarmin/text_to_speech.py"
)

text = path.read_text(
    encoding="utf-8",
)

old = """            profile_id=profile.profile_id,
            backend_id=(
"""

new = """            # Çağrıda kullanılan profil adını koru.
            # Eski jarmin_* adları içeride kasif_*
            # profillerine yönlendirilse de dış sözleşme
            # çağrılan adı döndürmeye devam eder.
            profile_id=str(profile_id),
            backend_id=(
"""

if old not in text:
    if "profile_id=str(profile_id)," in text:
        print(
            "SES_PROFILI_AD_UYUMLULUGU_ZATEN_VAR"
        )
    else:
        raise RuntimeError(
            "Ses sonucu profil alanı bulunamadı."
        )
else:
    text = text.replace(
        old,
        new,
        1,
    )

    path.write_text(
        text,
        encoding="utf-8",
    )

ast.parse(
    path.read_text(
        encoding="utf-8",
    )
)

print(
    "SES_PROFILI_AD_UYUMLULUGU_DUZELTILDI"
)
