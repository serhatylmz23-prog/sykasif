from dataclasses import dataclass


@dataclass(frozen=True)
class BrandTitle:
    id: str
    text: str


BRAND_TITLES = {
    "sykasif": BrandTitle("sykasif", "SyKaşif"),
    "syotagi": BrandTitle("syotagi", "SyOtağı"),
    "syfinansotagi": BrandTitle(
        "syfinansotagi",
        "SyFinansOtağı",
    ),
}


class BrandTitleManager:
    def __init__(self):
        self._current = "sykasif"
        self._visible = True

    @property
    def current(self) -> BrandTitle:
        return BRAND_TITLES[self._current]

    @property
    def visible(self) -> bool:
        return self._visible

    def write(self, title_id: str) -> BrandTitle:
        if title_id not in BRAND_TITLES:
            raise KeyError(f"Unknown brand title: {title_id}")

        self._current = title_id
        self._visible = True
        return self.current

    def erase(self) -> None:
        self._visible = False

    def show(self) -> BrandTitle:
        self._visible = True
        return self.current

    def available(self) -> list[BrandTitle]:
        return list(BRAND_TITLES.values())
