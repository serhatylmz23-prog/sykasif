import pytest

from syk_ui import BrandTitleManager


def test_ui_brand_title_write_erase_cycle():
    manager = BrandTitleManager()

    assert manager.current.text == "SyKaşif"
    assert manager.visible

    assert manager.write("syotagi").text == "SyOtağı"
    assert manager.visible

    manager.erase()
    assert not manager.visible

    assert manager.show().text == "SyOtağı"
    assert manager.visible

    assert manager.write(
        "syfinansotagi"
    ).text == "SyFinansOtağı"

    assert len(manager.available()) == 3

    with pytest.raises(KeyError):
        manager.write("unknown")
