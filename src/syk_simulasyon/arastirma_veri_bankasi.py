from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import secrets
import sqlite3
from pathlib import Path
from typing import Any


def _kod(on_ek: str, uzunluk: int = 12) -> str:
    return f"{on_ek}-" + secrets.token_hex(uzunluk // 2).upper()


def arastirma_kimligi_uret() -> str:
    return _kod("AK", 16)


def deney_numarasi_uret() -> str:
    return _kod("DN", 14)


@dataclass(frozen=True)
class GeriAlmaTalebi:
    talep_kimligi: str
    arastirma_kimligi: str
    hedef_karar_kimligi: str
    gerekce: str
    bilge_kaan_onayi: bool = False
    kurucu_kaan_onayi: bool = False

    @property
    def uygulanabilir(self) -> bool:
        return self.bilge_kaan_onayi and self.kurucu_kaan_onayi


class ArastirmaVeriBankasi:
    def __init__(self, yol: str | Path = ":memory:") -> None:
        self.db = sqlite3.connect(str(yol))
        self.db.row_factory = sqlite3.Row
        self._kur()

    def _kur(self) -> None:
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS arastirma (
          kimlik TEXT PRIMARY KEY,
          kod_adi TEXT NOT NULL,
          amac_kodu TEXT NOT NULL,
          durum TEXT NOT NULL,
          olusturma_zamani TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deney (
          numara TEXT PRIMARY KEY,
          arastirma_kimligi TEXT NOT NULL REFERENCES arastirma(kimlik),
          senaryo_sha256 TEXT NOT NULL,
          durum TEXT NOT NULL,
          olusturma_zamani TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS karar_defteri (
          sira INTEGER PRIMARY KEY AUTOINCREMENT,
          karar_kimligi TEXT UNIQUE NOT NULL,
          arastirma_kimligi TEXT NOT NULL,
          karar_kodu TEXT NOT NULL,
          gerekce TEXT NOT NULL,
          onceki_hash TEXT NOT NULL,
          kayit_hash TEXT NOT NULL,
          bilge_kaan_onayi INTEGER NOT NULL,
          kurucu_kaan_onayi INTEGER NOT NULL,
          zaman TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS geri_alma_gecmisi (
          sira INTEGER PRIMARY KEY AUTOINCREMENT,
          talep_kimligi TEXT UNIQUE NOT NULL,
          arastirma_kimligi TEXT NOT NULL,
          hedef_karar_kimligi TEXT NOT NULL,
          geri_alma_karar_kimligi TEXT NOT NULL,
          gerekce TEXT NOT NULL,
          bilge_kaan_onayi INTEGER NOT NULL,
          kurucu_kaan_onayi INTEGER NOT NULL,
          zaman TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS politika_kaydi (
          politika_id TEXT PRIMARY KEY,
          surum INTEGER NOT NULL,
          durum TEXT NOT NULL,
          veri_json TEXT NOT NULL,
          veri_sha256 TEXT NOT NULL,
          zaman TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS hedef_evrimi (
          sira INTEGER PRIMARY KEY AUTOINCREMENT,
          hedef_kimligi TEXT NOT NULL,
          surum INTEGER NOT NULL,
          degisim_kodu TEXT NOT NULL,
          veri_json TEXT NOT NULL,
          veri_sha256 TEXT NOT NULL,
          zaman TEXT NOT NULL,
          UNIQUE(hedef_kimligi, surum)
        );
        """)
        self.db.commit()

    def arastirma_ac(self, kod_adi: str, amac_kodu: str) -> str:
        kimlik = arastirma_kimligi_uret()
        self.db.execute("INSERT INTO arastirma VALUES (?,?,?,?,?)", (kimlik, kod_adi, amac_kodu, "ACIK", datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return kimlik

    def deney_ekle(self, arastirma_kimligi: str, senaryo: dict[str, Any]) -> str:
        numara = deney_numarasi_uret()
        ham = json.dumps(senaryo, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        self.db.execute("INSERT INTO deney VALUES (?,?,?,?,?)", (numara, arastirma_kimligi, hashlib.sha256(ham).hexdigest(), "PLANLANDI", datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return numara

    def karar_ekle(self, arastirma_kimligi: str, karar_kodu: str, gerekce: str,
                   bilge_kaan_onayi: bool, kurucu_kaan_onayi: bool) -> str:
        karar_kimligi = _kod("KD", 16)
        son = self.db.execute("SELECT kayit_hash FROM karar_defteri ORDER BY sira DESC LIMIT 1").fetchone()
        onceki = son[0] if son else "0" * 64
        zaman = datetime.now(timezone.utc).isoformat()
        ham = "|".join([karar_kimligi, arastirma_kimligi, karar_kodu, gerekce, onceki, str(int(bilge_kaan_onayi)), str(int(kurucu_kaan_onayi)), zaman])
        kayit_hash = hashlib.sha256(ham.encode()).hexdigest()
        self.db.execute("INSERT INTO karar_defteri (karar_kimligi,arastirma_kimligi,karar_kodu,gerekce,onceki_hash,kayit_hash,bilge_kaan_onayi,kurucu_kaan_onayi,zaman) VALUES (?,?,?,?,?,?,?,?,?)",
                        (karar_kimligi, arastirma_kimligi, karar_kodu, gerekce, onceki, kayit_hash, int(bilge_kaan_onayi), int(kurucu_kaan_onayi), zaman))
        self.db.commit()
        return karar_kimligi

    def karar_zincirini_dogrula(self) -> bool:
        onceki = "0" * 64
        for r in self.db.execute("SELECT * FROM karar_defteri ORDER BY sira"):
            ham = "|".join([r["karar_kimligi"], r["arastirma_kimligi"], r["karar_kodu"], r["gerekce"], onceki,
                            str(r["bilge_kaan_onayi"]), str(r["kurucu_kaan_onayi"]), r["zaman"]])
            if r["onceki_hash"] != onceki or hashlib.sha256(ham.encode()).hexdigest() != r["kayit_hash"]:
                return False
            onceki = r["kayit_hash"]
        return True

    def geri_al(self, talep: GeriAlmaTalebi) -> str:
        if not talep.uygulanabilir:
            raise PermissionError("geri alma için Bilge Kaan ve Kurucu Kaan onayı zorunludur")
        hedef = self.db.execute("SELECT karar_kimligi FROM karar_defteri WHERE karar_kimligi=?", (talep.hedef_karar_kimligi,)).fetchone()
        if hedef is None:
            raise KeyError("Geri alınacak karar bulunamadı")
        karar_kimligi = self.karar_ekle(talep.arastirma_kimligi, "GERI_ALMA", talep.gerekce, True, True)
        self.db.execute(
            "INSERT INTO geri_alma_gecmisi (talep_kimligi,arastirma_kimligi,hedef_karar_kimligi,geri_alma_karar_kimligi,gerekce,bilge_kaan_onayi,kurucu_kaan_onayi,zaman) VALUES (?,?,?,?,?,?,?,?)",
            (talep.talep_kimligi, talep.arastirma_kimligi, talep.hedef_karar_kimligi, karar_kimligi, talep.gerekce, 1, 1, datetime.now(timezone.utc).isoformat()),
        )
        self.db.commit()
        return karar_kimligi

    def geri_alma_gecmisi(self, arastirma_kimligi: str) -> tuple[dict[str, Any], ...]:
        satirlar = self.db.execute("SELECT * FROM geri_alma_gecmisi WHERE arastirma_kimligi=? ORDER BY sira", (arastirma_kimligi,)).fetchall()
        return tuple(dict(r) for r in satirlar)

    def politika_kaydet(self, politika_id: str, surum: int, durum: str, veri: dict[str, Any]) -> str:
        if surum < 1:
            raise ValueError("Politika sürümü en az 1 olmalıdır")
        veri_json = json.dumps(veri, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        veri_sha = hashlib.sha256(veri_json.encode()).hexdigest()
        self.db.execute(
            "INSERT INTO politika_kaydi (politika_id,surum,durum,veri_json,veri_sha256,zaman) VALUES (?,?,?,?,?,?)",
            (politika_id, surum, durum, veri_json, veri_sha, datetime.now(timezone.utc).isoformat()),
        )
        self.db.commit()
        return veri_sha

    def politika_butunlugunu_dogrula(self, politika_id: str) -> bool:
        r = self.db.execute("SELECT veri_json,veri_sha256 FROM politika_kaydi WHERE politika_id=?", (politika_id,)).fetchone()
        return bool(r and hashlib.sha256(r["veri_json"].encode()).hexdigest() == r["veri_sha256"])

    def yedekle(self, hedef_yol: str | Path) -> Path:
        hedef = Path(hedef_yol)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        yedek = sqlite3.connect(str(hedef))
        try:
            self.db.backup(yedek)
        finally:
            yedek.close()
        return hedef

    def butunluk_kontrolu(self) -> bool:
        sonuc = self.db.execute("PRAGMA integrity_check").fetchone()[0]
        return sonuc == "ok" and self.karar_zincirini_dogrula()

    def hedef_surumu_ekle(self, hedef_kimligi: str, degisim_kodu: str, veri: dict[str, Any]) -> int:
        son = self.db.execute("SELECT MAX(surum) FROM hedef_evrimi WHERE hedef_kimligi=?", (hedef_kimligi,)).fetchone()[0]
        surum = 1 if son is None else int(son) + 1
        veri_json = json.dumps(veri, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        sha = hashlib.sha256(veri_json.encode()).hexdigest()
        self.db.execute("INSERT INTO hedef_evrimi (hedef_kimligi,surum,degisim_kodu,veri_json,veri_sha256,zaman) VALUES (?,?,?,?,?,?)",
                        (hedef_kimligi, surum, degisim_kodu, veri_json, sha, datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return surum
