from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Mapping


PAROLA_ALGORITMASI = "pbkdf2_sha256"
VARSAYILAN_TUR_SAYISI = 310_000
VARSAYILAN_OTURUM_SURESI = 3_600
OTURUM_CEREZI_ADI = "syk_runtime_oturum"


class RuntimeOturumYapilandirmaHatasi(ValueError):
    """Eksik veya geçersiz giriş ayarını bildirir."""


def parola_ozeti_uret(
    parola: str,
    *,
    tur_sayisi: int = VARSAYILAN_TUR_SAYISI,
    tuz: bytes | None = None,
) -> str:
    if not parola:
        raise ValueError("Parola boş olamaz.")

    if tur_sayisi < 100_000:
        raise ValueError(
            "PBKDF2 tur sayısı 100000 değerinden küçük olamaz."
        )

    gercek_tuz = tuz or secrets.token_bytes(16)

    ozet = hashlib.pbkdf2_hmac(
        "sha256",
        parola.encode("utf-8"),
        gercek_tuz,
        tur_sayisi,
    )

    return "$".join(
        (
            PAROLA_ALGORITMASI,
            str(tur_sayisi),
            gercek_tuz.hex(),
            ozet.hex(),
        )
    )


def parola_dogrula(
    parola: str,
    kayitli_ozet: str,
) -> bool:
    try:
        algoritma, tur_metni, tuz_hex, ozet_hex = (
            kayitli_ozet.split("$", 3)
        )

        if algoritma != PAROLA_ALGORITMASI:
            return False

        tur_sayisi = int(tur_metni)
        tuz = bytes.fromhex(tuz_hex)
        beklenen = bytes.fromhex(ozet_hex)

        uretilen = hashlib.pbkdf2_hmac(
            "sha256",
            parola.encode("utf-8"),
            tuz,
            tur_sayisi,
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    return hmac.compare_digest(
        uretilen,
        beklenen,
    )


def _base64url_kodla(veri: bytes) -> str:
    return base64.urlsafe_b64encode(
        veri
    ).rstrip(b"=").decode("ascii")


def _base64url_coz(metin: str) -> bytes:
    dolgu = "=" * (-len(metin) % 4)

    return base64.urlsafe_b64decode(
        metin + dolgu
    )


@dataclass(frozen=True)
class RuntimeOturumYoneticisi:
    kullanici_adi: str
    parola_ozeti: str
    oturum_anahtari: bytes
    oturum_suresi_saniye: int = VARSAYILAN_OTURUM_SURESI

    @classmethod
    def ortamdan_olustur(
        cls,
        ortam: Mapping[str, str] | None = None,
    ) -> RuntimeOturumYoneticisi | None:
        kaynak = ortam if ortam is not None else os.environ

        kullanici_adi = kaynak.get(
            "SYK_RUNTIME_KULLANICI",
            "",
        ).strip()

        parola_ozeti = kaynak.get(
            "SYK_RUNTIME_PAROLA_OZETI",
            "",
        ).strip()

        oturum_anahtari = kaynak.get(
            "SYK_RUNTIME_OTURUM_ANAHTARI",
            "",
        ).strip()

        degerler = (
            kullanici_adi,
            parola_ozeti,
            oturum_anahtari,
        )

        if not any(degerler):
            return None

        if not all(degerler):
            raise RuntimeOturumYapilandirmaHatasi(
                "Runtime giriş ayarları eksik. "
                "Kullanıcı, parola özeti ve oturum anahtarı "
                "birlikte tanımlanmalıdır."
            )

        try:
            oturum_suresi = int(
                kaynak.get(
                    "SYK_RUNTIME_OTURUM_SURESI",
                    str(VARSAYILAN_OTURUM_SURESI),
                )
            )
        except ValueError as hata:
            raise RuntimeOturumYapilandirmaHatasi(
                "Oturum süresi tam sayı olmalıdır."
            ) from hata

        if oturum_suresi < 60:
            raise RuntimeOturumYapilandirmaHatasi(
                "Oturum süresi en az 60 saniye olmalıdır."
            )

        if len(oturum_anahtari.encode("utf-8")) < 32:
            raise RuntimeOturumYapilandirmaHatasi(
                "Oturum anahtarı en az 32 bayt olmalıdır."
            )

        if not parola_ozeti.startswith(
            f"{PAROLA_ALGORITMASI}$"
        ):
            raise RuntimeOturumYapilandirmaHatasi(
                "Parola özeti PBKDF2-SHA256 biçiminde olmalıdır."
            )

        return cls(
            kullanici_adi=kullanici_adi,
            parola_ozeti=parola_ozeti,
            oturum_anahtari=oturum_anahtari.encode(
                "utf-8"
            ),
            oturum_suresi_saniye=oturum_suresi,
        )

    def kimlik_dogrula(
        self,
        kullanici_adi: str,
        parola: str,
    ) -> bool:
        kullanici_dogru = hmac.compare_digest(
            kullanici_adi.encode("utf-8"),
            self.kullanici_adi.encode("utf-8"),
        )

        parola_dogru = parola_dogrula(
            parola,
            self.parola_ozeti,
        )

        return kullanici_dogru and parola_dogru

    def oturum_uret(
        self,
        *,
        kullanici_adi: str | None = None,
        hesap_kimligi: int | None = None,
        rol: str | None = None,
        simdi: int | None = None,
    ) -> str:
        an = int(time.time()) if simdi is None else int(simdi)

        kullanici = (
            kullanici_adi
            if kullanici_adi is not None
            else self.kullanici_adi
        ).strip()

        if not kullanici:
            raise ValueError(
                "Oturum kullanici kimligi bos olamaz."
            )

        govde: dict[str, object] = {
            "kullanici": kullanici,
            "son_gecerlilik": (
                an + self.oturum_suresi_saniye
            ),
            "tek_kullanimlik": secrets.token_hex(16),
        }

        if hesap_kimligi is not None:
            govde["hesap_kimligi"] = int(
                hesap_kimligi
            )

        if rol is not None:
            temiz_rol = rol.strip()

            if temiz_rol:
                govde["rol"] = temiz_rol

        govde_metni = json.dumps(
            govde,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        kodlu_govde = _base64url_kodla(
            govde_metni
        )

        imza = hmac.new(
            self.oturum_anahtari,
            kodlu_govde.encode("ascii"),
            hashlib.sha256,
        ).digest()

        return (
            kodlu_govde
            + "."
            + _base64url_kodla(imza)
        )

    def oturum_bilgisi(
        self,
        belirtec: str | None,
        *,
        simdi: int | None = None,
    ) -> dict[str, object] | None:
        if not belirtec:
            return None

        try:
            kodlu_govde, kodlu_imza = belirtec.split(
                ".",
                1,
            )

            if (
                not kodlu_govde
                or not kodlu_imza
                or "." in kodlu_imza
            ):
                return None

            cozulmus_govde = _base64url_coz(
                kodlu_govde
            )
            gelen_imza = _base64url_coz(
                kodlu_imza
            )

            if (
                _base64url_kodla(cozulmus_govde)
                != kodlu_govde
            ):
                return None

            if (
                _base64url_kodla(gelen_imza)
                != kodlu_imza
            ):
                return None

            beklenen_imza = hmac.new(
                self.oturum_anahtari,
                kodlu_govde.encode("ascii"),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(
                beklenen_imza,
                gelen_imza,
            ):
                return None

            govde = json.loads(
                cozulmus_govde.decode("utf-8")
            )

            kullanici = str(
                govde["kullanici"]
            ).strip()

            son_gecerlilik = int(
                govde["son_gecerlilik"]
            )

            tek_kullanimlik = str(
                govde["tek_kullanimlik"]
            ).strip()

            if not kullanici or not tek_kullanimlik:
                return None

            hesap_kimligi = govde.get(
                "hesap_kimligi"
            )

            if hesap_kimligi is not None:
                hesap_kimligi = int(
                    hesap_kimligi
                )

            rol = govde.get("rol")

            if rol is not None:
                rol = str(rol).strip() or None

        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return None

        an = int(time.time()) if simdi is None else int(simdi)

        if son_gecerlilik < an:
            return None

        sonuc: dict[str, object] = {
            "kullanici": kullanici,
            "son_gecerlilik": son_gecerlilik,
            "tek_kullanimlik": tek_kullanimlik,
        }

        if hesap_kimligi is not None:
            sonuc["hesap_kimligi"] = hesap_kimligi

        if rol is not None:
            sonuc["rol"] = rol

        return sonuc

    def oturum_dogrula(
        self,
        belirtec: str | None,
        *,
        simdi: int | None = None,
    ) -> bool:
        return (
            self.oturum_bilgisi(
                belirtec,
                simdi=simdi,
            )
            is not None
        )
