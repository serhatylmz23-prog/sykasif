import pytest

from syk_simulasyon.syk_ui import BrandTitleManager


def test_ui_brand_title_write_erase_cycle():
    manager = BrandTitleManager()

    assert manager.current.text == "SyKa\u015fif"
    assert manager.visible

    assert manager.write("syotagi").text == "SyOta\u011f\u0131"
    assert manager.visible

    manager.erase()
    assert not manager.visible

    assert manager.show().text == "SyOta\u011f\u0131"
    assert manager.visible

    assert manager.write(
        "syfinansotagi"
    ).text == "SyFinansOta\u011f\u0131"

    assert len(manager.available()) == 3

    with pytest.raises(KeyError):
        manager.write("unknown")