from syk_simulasyon.syk_ui import ImageManager


def test_ui_image_manager_inventory():
    manager = ImageManager()

    assert len(manager.available()) == 11
    assert manager.get("logo").name == "logo.png"
    assert manager.get("syframe").parent.name == "images"
    assert manager.missing_files() == []
    assert manager.is_ready()
