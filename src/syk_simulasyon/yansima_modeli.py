from __future__ import annotations

from dataclasses import dataclass
import math

from .yansima_katsayilari import YansimaKatsayiKaydi
from .yansima_turleri import YansimaTuru
from .yuzey_modeli import YuzeyModeli


@dataclass(frozen=True, slots=True)
class YansimaGirdisi:
    gelen_genlik: float
    frekans_hz: float
    gelis_acisi_derece: float
    yuzey: YuzeyModeli
    katsayi: YansimaKatsayiKaydi

    def dogrula(self) -> None:
        if self.gelen_genlik < 0:
            raise ValueError("gelen_genlik negatif olamaz")
        if not 0.0 <= self.gelis_acisi_derece <= 90.0:
            raise ValueError("gelis_acisi_derece 0 ile 90 arasında olmalıdır")
        self.yuzey.dogrula()
        self.katsayi.dogrula(self.frekans_hz)


@dataclass(frozen=True, slots=True)
class YansimaSonucu:
    yansiyan_genlik: float
    etkin_katsayi: float
    aci_katsayisi: float
    yuzey_katsayisi: float
    varsayimlar: tuple[str, ...]


class YansimaModeli:
    """Kaynaklı bir temel katsayıyı açı ve pürüzlülükle ölçekleyen referans model.

    Gerçek malzeme, mineral veya cihaz yansıma davranışı değildir. Kullanılan
    temel katsayı dışarıdan, kaynağı ve güveniyle birlikte sağlanır.
    """

    def hesapla(self, girdi: YansimaGirdisi) -> YansimaSonucu:
        girdi.dogrula()
        bagil_aci = abs(girdi.gelis_acisi_derece - girdi.yuzey.yonelim_derece)
        bagil_aci = min(90.0, bagil_aci)
        aci_katsayisi = max(0.0, math.cos(math.radians(bagil_aci)))

        p = girdi.yuzey.puruzluluk_0_1
        if girdi.yuzey.yansima_turu is YansimaTuru.DUZGUN:
            yuzey_katsayisi = 1.0 - 0.75 * p
        elif girdi.yuzey.yansima_turu is YansimaTuru.DAGINIK:
            yuzey_katsayisi = 0.25 + 0.75 * p
        else:
            yuzey_katsayisi = 0.5 + 0.25 * (1.0 - p)

        etkin = float(girdi.katsayi.genlik_katsayisi) * aci_katsayisi * yuzey_katsayisi
        etkin = min(1.0, max(0.0, etkin))
        return YansimaSonucu(
            yansiyan_genlik=girdi.gelen_genlik * etkin,
            etkin_katsayi=etkin,
            aci_katsayisi=aci_katsayisi,
            yuzey_katsayisi=yuzey_katsayisi,
            varsayimlar=(
                "tek_yuzey",
                "tek_yansima",
                "kosinus_aci_olceklemesi",
                "basit_puruzluluk_olceklemesi",
            ),
        )
