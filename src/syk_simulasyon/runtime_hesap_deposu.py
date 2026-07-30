from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Protocol

from .runtime_oturum import parola_dogrula, parola_ozeti_uret


VARSAYILAN_GUVENLIK_DIZINI = (
    Path(
        os.getenv(
            "LOCALAPPDATA",
            Path.home(),
        )
    )
    / "SyKasif"
    / "guvenlik"
)

VARSAYILAN_HESAP_VERITABANI = (
    VARSAYILAN_GUVENLIK_DIZINI
    / "hesaplar.db"
)


class HesapDeposuHatasi(RuntimeError):
    """Kalici hesap deposu islemlerindeki hatalari bildirir."""


class CihazAnahtariKoruyucusu(Protocol):
    def koru(self, veri: bytes) -> bytes:
        ...

    def ac(self, veri: bytes) -> bytes:
        ...


class _DataBlob(ctypes.Structure):
    _fields_ = (
        ("cbData", wintypes.DWORD),
        (
            "pbData",
            ctypes.POINTER(ctypes.c_ubyte),
        ),
    )


class WindowsDpapiKoruyucusu:
    """Veriyi mevcut Windows kullanicisi kapsaminda korur."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError(
                "Windows DPAPI yalniz Windows ortaminda kullanilabilir."
            )

        self._crypt32 = ctypes.windll.crypt32
        self._kernel32 = ctypes.windll.kernel32

    @staticmethod
    def _blob_olustur(
        veri: bytes,
    ) -> tuple[_DataBlob, ctypes.Array]:
        tampon = ctypes.create_string_buffer(veri)

        blob = _DataBlob(
            len(veri),
            ctypes.cast(
                tampon,
                ctypes.POINTER(ctypes.c_ubyte),
            ),
        )

        return blob, tampon

    def koru(self, veri: bytes) -> bytes:
        giris, _tampon = self._blob_olustur(veri)
        cikis = _DataBlob()

        basarili = self._crypt32.CryptProtectData(
            ctypes.byref(giris),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(cikis),
        )

        if not basarili:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(
                cikis.pbData,
                cikis.cbData,
            )
        finally:
            self._kernel32.LocalFree(
                cikis.pbData
            )

    def ac(self, veri: bytes) -> bytes:
        giris, _tampon = self._blob_olustur(veri)
        cikis = _DataBlob()

        basarili = self._crypt32.CryptUnprotectData(
            ctypes.byref(giris),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(cikis),
        )

        if not basarili:
            raise ctypes.WinError()

        try:
            return ctypes.string_at(
                cikis.pbData,
                cikis.cbData,
            )
        finally:
            self._kernel32.LocalFree(
                cikis.pbData
            )


@dataclass(frozen=True)
class RuntimeHesabi:
    hesap_kimligi: int
    kullanici_adi: str
    eposta: str | None
    telefon: str | None
    rol: str
    hizli_giris_etkin: bool
    etkin: bool


@dataclass(frozen=True)
class TaninmisCihaz:
    hesap_kimligi: int
    cihaz_kimligi: str
    cihaz_anahtari: bytes
    etkin: bool


class RuntimeHesapDeposu:
    def __init__(
        self,
        yol: str | Path = VARSAYILAN_HESAP_VERITABANI,
        *,
        koruyucu: CihazAnahtariKoruyucusu | None = None,
    ) -> None:
        self._yol = Path(yol)
        self._yol.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._koruyucu = (
            koruyucu
            if koruyucu is not None
            else WindowsDpapiKoruyucusu()
        )

        self._veritabani_hazirla()

    @property
    def yol(self) -> Path:
        return self._yol

    def _baglan(self) -> sqlite3.Connection:
        baglanti = sqlite3.connect(
            str(self._yol)
        )
        baglanti.row_factory = sqlite3.Row
        baglanti.execute(
            "PRAGMA foreign_keys = ON"
        )
        return baglanti

    def _veritabani_hazirla(self) -> None:
        with self._baglan() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS hesaplar (
                    hesap_kimligi INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT NOT NULL UNIQUE,
                    eposta TEXT UNIQUE,
                    telefon TEXT UNIQUE,
                    parola_ozeti TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    hizli_giris_etkin INTEGER NOT NULL DEFAULT 0,
                    etkin INTEGER NOT NULL DEFAULT 1,
                    olusturulma_zamani TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS taninmis_cihazlar (
                    cihaz_kimligi TEXT PRIMARY KEY,
                    hesap_kimligi INTEGER NOT NULL,
                    korumali_anahtar BLOB NOT NULL,
                    etkin INTEGER NOT NULL DEFAULT 1,
                    olusturulma_zamani TEXT NOT NULL,
                    FOREIGN KEY (hesap_kimligi)
                        REFERENCES hesaplar(hesap_kimligi)
                        ON DELETE CASCADE
                );
                """
            )

    def hesap_var_mi(self) -> bool:
        with self._baglan() as db:
            satir = db.execute(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM hesaplar
                    WHERE etkin = 1
                ) AS var_mi
                """
            ).fetchone()

        return bool(satir["var_mi"])

    def hesap_olustur(
        self,
        *,
        kullanici_adi: str,
        parola: str,
        eposta: str | None = None,
        telefon: str | None = None,
        rol: str = "kurucu",
        hizli_giris_etkin: bool = False,
        tur_sayisi: int = 310_000,
    ) -> RuntimeHesabi:
        kimlik = kullanici_adi.strip()
        temiz_eposta = (
            eposta.strip().lower()
            if eposta and eposta.strip()
            else None
        )
        temiz_telefon = (
            telefon.strip()
            if telefon and telefon.strip()
            else None
        )

        if not kimlik:
            raise ValueError(
                "Kullanici adi bos olamaz."
            )

        parola_ozeti = parola_ozeti_uret(
            parola,
            tur_sayisi=tur_sayisi,
        )

        zaman = datetime.now(
            UTC
        ).isoformat()

        try:
            with self._baglan() as db:
                imlec = db.execute(
                    """
                    INSERT INTO hesaplar (
                        kullanici_adi,
                        eposta,
                        telefon,
                        parola_ozeti,
                        rol,
                        hizli_giris_etkin,
                        etkin,
                        olusturulma_zamani
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        kimlik,
                        temiz_eposta,
                        temiz_telefon,
                        parola_ozeti,
                        rol,
                        int(hizli_giris_etkin),
                        zaman,
                    ),
                )
                hesap_kimligi = int(
                    imlec.lastrowid
                )
        except sqlite3.IntegrityError as hata:
            raise HesapDeposuHatasi(
                "Kullanici adi, e-posta veya telefon zaten kayitli."
            ) from hata

        hesap = self.hesap_getir(
            hesap_kimligi
        )

        if hesap is None:
            raise HesapDeposuHatasi(
                "Olusturulan hesap okunamadi."
            )

        return hesap

    def hesap_getir(
        self,
        hesap_kimligi: int,
    ) -> RuntimeHesabi | None:
        with self._baglan() as db:
            satir = db.execute(
                """
                SELECT
                    hesap_kimligi,
                    kullanici_adi,
                    eposta,
                    telefon,
                    rol,
                    hizli_giris_etkin,
                    etkin
                FROM hesaplar
                WHERE hesap_kimligi = ?
                """,
                (hesap_kimligi,),
            ).fetchone()

        return (
            self._satirdan_hesap(satir)
            if satir is not None
            else None
        )

    def kimlikle_hesap_bul(
        self,
        kimlik: str,
    ) -> RuntimeHesabi | None:
        aranan = kimlik.strip()

        with self._baglan() as db:
            satir = db.execute(
                """
                SELECT
                    hesap_kimligi,
                    kullanici_adi,
                    eposta,
                    telefon,
                    rol,
                    hizli_giris_etkin,
                    etkin
                FROM hesaplar
                WHERE etkin = 1
                  AND (
                    kullanici_adi = ?
                    OR lower(eposta) = lower(?)
                    OR telefon = ?
                  )
                LIMIT 1
                """,
                (
                    aranan,
                    aranan,
                    aranan,
                ),
            ).fetchone()

        return (
            self._satirdan_hesap(satir)
            if satir is not None
            else None
        )

    def kimlik_dogrula(
        self,
        kimlik: str,
        parola: str,
    ) -> RuntimeHesabi | None:
        hesap = self.kimlikle_hesap_bul(
            kimlik
        )

        if hesap is None:
            parola_dogrula(
                parola,
                parola_ozeti_uret(
                    "sabit-gecikme",
                    tur_sayisi=100_000,
                    tuz=b"0123456789abcdef",
                ),
            )
            return None

        with self._baglan() as db:
            satir = db.execute(
                """
                SELECT parola_ozeti
                FROM hesaplar
                WHERE hesap_kimligi = ?
                  AND etkin = 1
                """,
                (hesap.hesap_kimligi,),
            ).fetchone()

        if (
            satir is None
            or not parola_dogrula(
                parola,
                satir["parola_ozeti"],
            )
        ):
            return None

        return hesap

    def hizli_giris_ayarla(
        self,
        hesap_kimligi: int,
        etkin: bool,
    ) -> None:
        with self._baglan() as db:
            sonuc = db.execute(
                """
                UPDATE hesaplar
                SET hizli_giris_etkin = ?
                WHERE hesap_kimligi = ?
                """,
                (
                    int(etkin),
                    hesap_kimligi,
                ),
            )

        if sonuc.rowcount != 1:
            raise HesapDeposuHatasi(
                "Hesap bulunamadi."
            )

    def cihaz_tanit(
        self,
        *,
        hesap_kimligi: int,
        cihaz_kimligi: str | None = None,
        cihaz_anahtari: bytes | None = None,
    ) -> TaninmisCihaz:
        gercek_cihaz_kimligi = (
            cihaz_kimligi
            or secrets.token_hex(16)
        )
        gercek_anahtar = (
            cihaz_anahtari
            or secrets.token_bytes(32)
        )

        korumali = self._koruyucu.koru(
            gercek_anahtar
        )

        zaman = datetime.now(
            UTC
        ).isoformat()

        try:
            with self._baglan() as db:
                db.execute(
                    """
                    INSERT INTO taninmis_cihazlar (
                        cihaz_kimligi,
                        hesap_kimligi,
                        korumali_anahtar,
                        etkin,
                        olusturulma_zamani
                    )
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (
                        gercek_cihaz_kimligi,
                        hesap_kimligi,
                        korumali,
                        zaman,
                    ),
                )
        except sqlite3.IntegrityError as hata:
            raise HesapDeposuHatasi(
                "Cihaz kaydi olusturulamadi."
            ) from hata

        return TaninmisCihaz(
            hesap_kimligi=hesap_kimligi,
            cihaz_kimligi=gercek_cihaz_kimligi,
            cihaz_anahtari=gercek_anahtar,
            etkin=True,
        )

    def cihaz_dogrula(
        self,
        *,
        hesap_kimligi: int,
        cihaz_kimligi: str,
        cihaz_anahtari: bytes,
    ) -> bool:
        with self._baglan() as db:
            satir = db.execute(
                """
                SELECT korumali_anahtar
                FROM taninmis_cihazlar
                WHERE hesap_kimligi = ?
                  AND cihaz_kimligi = ?
                  AND etkin = 1
                """,
                (
                    hesap_kimligi,
                    cihaz_kimligi,
                ),
            ).fetchone()

        if satir is None:
            return False

        try:
            kayitli_anahtar = self._koruyucu.ac(
                bytes(satir["korumali_anahtar"])
            )
        except Exception:
            return False

        return secrets.compare_digest(
            kayitli_anahtar,
            cihaz_anahtari,
        )

    def cihaz_iptal_et(
        self,
        cihaz_kimligi: str,
    ) -> None:
        with self._baglan() as db:
            db.execute(
                """
                UPDATE taninmis_cihazlar
                SET etkin = 0
                WHERE cihaz_kimligi = ?
                """,
                (cihaz_kimligi,),
            )

    @staticmethod
    def _satirdan_hesap(
        satir: sqlite3.Row,
    ) -> RuntimeHesabi:
        return RuntimeHesabi(
            hesap_kimligi=int(
                satir["hesap_kimligi"]
            ),
            kullanici_adi=str(
                satir["kullanici_adi"]
            ),
            eposta=satir["eposta"],
            telefon=satir["telefon"],
            rol=str(satir["rol"]),
            hizli_giris_etkin=bool(
                satir["hizli_giris_etkin"]
            ),
            etkin=bool(
                satir["etkin"]
            ),
        )
