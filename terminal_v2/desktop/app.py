from __future__ import annotations

import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Any

from terminal_v2.desktop.runtime_client import RuntimeClient
from terminal_v2.desktop.module_views import modul_gorunumu_getir


DURUM_RENKLERI = {
    "BEKLIYOR": "#f5c451",
    "CALISIYOR": "#55e6c1",
    "TARIYOR": "#55c9ff",
    "DOGRULANIYOR": "#9a8cff",
    "TAMAMLANDI": "#69e27d",
    "DURDU": "#b5bdc9",
    "CEVRIMDISI": "#7d8795",
    "HATA": "#ff6b6b",
}


class TerminalRuntimeProcess:
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        if self.process is not None:
            return

        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "terminal_v2.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8013",
                "--log-level",
                "warning",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

    def stop(self) -> None:
        if self.process is None:
            return

        if self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.process.kill()

        self.process = None


class SyKasifDesktopApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SyKaşif Terminal V2")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.root.configure(bg="#08111d")

        self.client = RuntimeClient()
        self.runtime_process = TerminalRuntimeProcess()
        self.runtime_started_here = False
        self.closed = False

        self.status_text = tk.StringVar(
            value="Çalışma alanına bağlanılıyor..."
        )
        self.revision_text = tk.StringVar(
            value="Sürüm: 0"
        )
        self.active_module_text = tk.StringVar(
            value="Aktif modül: Ana Çalışma Alanı"
        )
        self.module_view_title = tk.StringVar(
            value="Ana ?al??ma Alan?"
        )
        self.module_view_description = tk.StringVar(
            value=(
                "Sistem durumu, ba?l? cihazlar ve aktif g?revler "
                "bu ?al??ma alan?nda g?sterilecek."
            )
        )
        self.module_view_details = tk.StringVar(
            value=(
                "? Runtime ba?lant? durumunu izle\n"
                "? Ba?l? cihazlar? g?r?nt?le\n"
                "? Aktif g?revleri takip et\n"
                "? Son bildirimleri incele"
            )
        )

        self.cards_frame: ttk.Frame
        self.card_widgets: dict[str, dict[str, tk.Widget]] = {}

        self._configure_styles()
        self._build_ui()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._close,
        )

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Root.TFrame",
            background="#08111d",
        )
        style.configure(
            "Panel.TFrame",
            background="#101d2c",
        )
        style.configure(
            "Title.TLabel",
            background="#08111d",
            foreground="#f5f7fa",
            font=("Segoe UI Semibold", 24),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#08111d",
            foreground="#9cabbd",
            font=("Segoe UI", 11),
        )
        style.configure(
            "Status.TLabel",
            background="#101d2c",
            foreground="#55e6c1",
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Info.TLabel",
            background="#101d2c",
            foreground="#c7d1dc",
            font=("Segoe UI", 10),
        )

    def _build_ui(self) -> None:
        ana_kapsayici = ttk.Frame(
            self.root,
            style="Root.TFrame",
        )
        ana_kapsayici.pack(
            fill="both",
            expand=True,
        )

        self.scroll_canvas = tk.Canvas(
            ana_kapsayici,
            bg="#08111d",
            highlightthickness=0,
            borderwidth=0,
        )

        self.scrollbar = ttk.Scrollbar(
            ana_kapsayici,
            orient="vertical",
            command=self.scroll_canvas.yview,
        )

        self.scroll_canvas.configure(
            yscrollcommand=self.scrollbar.set,
        )

        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.scroll_canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        root_frame = ttk.Frame(
            self.scroll_canvas,
            style="Root.TFrame",
            padding=28,
        )

        self.scroll_window = (
            self.scroll_canvas.create_window(
                (0, 0),
                window=root_frame,
                anchor="nw",
            )
        )

        root_frame.bind(
            "<Configure>",
            lambda _event: self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox("all")
            ),
        )

        self.scroll_canvas.bind(
            "<Configure>",
            lambda event: self.scroll_canvas.itemconfigure(
                self.scroll_window,
                width=event.width,
            ),
        )

        self.scroll_canvas.bind(
            "<Enter>",
            lambda _event: self.scroll_canvas.bind_all(
                "<MouseWheel>",
                self._on_mousewheel,
            ),
        )

        self.scroll_canvas.bind(
            "<Leave>",
            lambda _event: self.scroll_canvas.unbind_all(
                "<MouseWheel>"
            ),
        )

        header = ttk.Frame(
            root_frame,
            style="Root.TFrame",
        )
        header.pack(
            fill="x",
            pady=(0, 22),
        )

        ttk.Label(
            header,
            text="SYKAŞİF TERMINAL V2",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Windows Masaüstü Çalışma Alanı",
            style="Title.TLabel",
        ).pack(
            anchor="w",
            pady=(4, 2),
        )

        ttk.Label(
            header,
            text=(
                "Masaüstü, Samsung tablet ve telefon aynı "
                "canlı çalışma durumunu kullanır."
            ),
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        status_panel = ttk.Frame(
            root_frame,
            style="Panel.TFrame",
            padding=18,
        )
        status_panel.pack(
            fill="x",
            pady=(0, 18),
        )

        ttk.Label(
            status_panel,
            textvariable=self.status_text,
            style="Status.TLabel",
        ).pack(side="left")

        ttk.Label(
            status_panel,
            textvariable=self.active_module_text,
            style="Info.TLabel",
        ).pack(
            side="left",
            padx=28,
        )

        ttk.Label(
            status_panel,
            textvariable=self.revision_text,
            style="Info.TLabel",
        ).pack(side="right")

        ttk.Label(
            root_frame,
            text="Canlı Modüller",
            style="Title.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 12),
        )

        workspace = tk.Frame(
            root_frame,
            bg="#101d2c",
            highlightthickness=1,
            highlightbackground="#26384c",
            padx=20,
            pady=18,
        )
        workspace.pack(
            fill="x",
            pady=(0, 20),
        )

        tk.Label(
            workspace,
            textvariable=self.module_view_title,
            bg="#101d2c",
            fg="#f5f7fa",
            font=("Segoe UI Semibold", 18),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            workspace,
            textvariable=self.module_view_description,
            bg="#101d2c",
            fg="#9cabbd",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=1000,
        ).pack(
            fill="x",
            pady=(8, 0),
        )

        tk.Label(
            workspace,
            textvariable=self.module_view_details,
            bg="#101d2c",
            fg="#c8d2df",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=1000,
        ).pack(
            fill="x",
            pady=(14, 0),
        )

        self.module_action_frame = tk.Frame(
            workspace,
            bg="#101d2c",
        )
        self.module_action_frame.pack(
            fill="x",
            pady=(16, 0),
        )


        self.cards_frame = ttk.Frame(
            root_frame,
            style="Root.TFrame",
        )
        self.cards_frame.pack(
            fill="both",
            expand=True,
        )

        self.bottom_safe_area = tk.Frame(
            root_frame,
            bg="#08111d",
            height=120,
        )
        self.bottom_safe_area.pack(
            fill="x",
            side="bottom",
        )
        self.bottom_safe_area.pack_propagate(
            False
        )

    def _on_mousewheel(
        self,
        event,
    ) -> None:
        if not hasattr(self, "scroll_canvas"):
            return

        adim = int(-event.delta / 120)

        if adim == 0:
            adim = -1 if event.delta > 0 else 1

        self.scroll_canvas.yview_scroll(
            adim,
            "units",
        )

    def _kaydirma_konumunu_geri_yukle(
        self,
        konum: float,
    ) -> None:
        if not hasattr(self, "scroll_canvas"):
            return

        self.scroll_canvas.update_idletasks()

        bbox = self.scroll_canvas.bbox(
            "all"
        )

        if bbox is None:
            return

        self.scroll_canvas.configure(
            scrollregion=bbox,
        )

        self.scroll_canvas.yview_moveto(
            max(0.0, min(1.0, konum))
        )

    def _render_module_actions(
        self,
        islemler,
    ) -> None:
        if not hasattr(
            self,
            "module_action_frame",
        ):
            return

        for widget in (
            self.module_action_frame.winfo_children()
        ):
            widget.destroy()

        for index, islem in enumerate(
            islemler,
            start=1,
        ):
            button = tk.Button(
                self.module_action_frame,
                text=islem,
                command=lambda secilen=islem: (
                    self._module_action_selected(
                        secilen
                    )
                ),
                bg="#17283a",
                fg="#f5f7fa",
                activebackground="#1d354b",
                activeforeground="#55e6c1",
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                font=("Segoe UI Semibold", 10),
                anchor="w",
                padx=14,
                pady=10,
            )

            button.grid(
                row=(index - 1) // 2,
                column=(index - 1) % 2,
                sticky="ew",
                padx=(
                    0
                    if index % 2 == 1
                    else 6
                ),
                pady=4,
            )

        self.module_action_frame.grid_columnconfigure(
            0,
            weight=1,
        )
        self.module_action_frame.grid_columnconfigure(
            1,
            weight=1,
        )

    def _module_action_selected(
        self,
        islem: str,
    ) -> None:
        mesaj = "\u0130\u015flem se\u00e7ildi: "
        self.status_text.set(
            mesaj + islem
        )

    def _render_cards(
        self,
        cards: list[dict[str, Any]],
    ) -> None:
        kart_imzasi = tuple(
            (
                str(card.get("kod", "")),
                str(card.get("ad", "")),
                str(card.get("durum_kodu", "")),
                str(card.get("durum_metni", "")),
                bool(card.get("aktif", False)),
            )
            for card in cards
        )

        if getattr(
            self,
            "_son_kart_imzasi",
            None,
        ) == kart_imzasi:
            return

        self._son_kart_imzasi = kart_imzasi

        kaydirma_konumu = 0.0

        if hasattr(self, "scroll_canvas"):
            gorunen_aralik = self.scroll_canvas.yview()

            if gorunen_aralik:
                kaydirma_konumu = gorunen_aralik[0]

        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        self.card_widgets.clear()
        columns = 3

        for index, card in enumerate(cards):
            row = index // columns
            column = index % columns
            modul_kodu = str(card.get("kod", "dashboard"))

            durum_kodu = str(
                card.get("durum_kodu", "BEKLIYOR")
            )
            accent = DURUM_RENKLERI.get(
                durum_kodu,
                "#7d8795",
            )

            frame = tk.Frame(
                self.cards_frame,
                bg="#101d2c",
                highlightthickness=2 if card.get("aktif") else 1,
                highlightbackground=(
                    accent
                    if card.get("aktif")
                    else "#26384c"
                ),
                padx=18,
                pady=16,
                cursor="hand2",
            )
            frame.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=7,
                pady=7,
            )

            self.cards_frame.grid_columnconfigure(
                column,
                weight=1,
            )

            title = tk.Label(
                frame,
                text=str(card.get("ad", "Modül")),
                bg="#101d2c",
                fg="#f5f7fa",
                font=("Segoe UI Semibold", 14),
                anchor="w",
                cursor="hand2",
            )
            title.pack(fill="x")

            status = tk.Label(
                frame,
                text=str(
                    card.get(
                        "durum_metni",
                        "Bekliyor",
                    )
                ),
                bg="#101d2c",
                fg=accent,
                font=("Segoe UI Semibold", 11),
                anchor="w",
                cursor="hand2",
            )
            status.pack(
                fill="x",
                pady=(10, 0),
            )

            detail = tk.Label(
                frame,
                text=(
                    "Aktif çalışma modülü"
                    if card.get("aktif")
                    else "Açmak için tıklayın"
                ),
                bg="#101d2c",
                fg="#9cabbd",
                font=("Segoe UI", 9),
                anchor="w",
                cursor="hand2",
            )
            detail.pack(
                fill="x",
                pady=(4, 0),
            )

            callback = (
                lambda _event, kod=modul_kodu:
                self._activate_module(kod)
            )

            frame.bind("<Button-1>", callback)
            title.bind("<Button-1>", callback)
            status.bind("<Button-1>", callback)
            detail.bind("<Button-1>", callback)

            self.card_widgets[modul_kodu] = {
                "frame": frame,
                "title": title,
                "status": status,
                "detail": detail,
            }


        if hasattr(self, "scroll_canvas"):
            self.scroll_canvas.update_idletasks()
            self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox(
                    "all"
                )
            )
            self.root.after_idle(
                self._kaydirma_konumunu_geri_yukle,
                kaydirma_konumu,
            )

    def _activate_module(
        self,
        modul_kodu: str,
    ) -> None:
        self.status_text.set(
            "Modül açılıyor..."
        )

        threading.Thread(
            target=self._activate_module_worker,
            args=(modul_kodu,),
            daemon=True,
        ).start()

    def _activate_module_worker(
        self,
        modul_kodu: str,
    ) -> None:
        result = self.client.aktif_modulu_degistir(
            modul_kodu
        )

        if not result.basarili:
            self._schedule_ui(
                self._show_connection_error,
                result.hata,
            )
            return

        self.client.modul_durumunu_degistir(
            modul_kodu,
            "CALISIYOR",
        )

        self._load_data()

    def _load_data(self) -> None:
        runtime = self.client.runtime_durumu()

        if not runtime.basarili:
            if not self.runtime_started_here:
                self.runtime_process.start()
                self.runtime_started_here = True
                time.sleep(1.2)

            runtime = self.client.runtime_durumu()

        if not runtime.basarili:
            self._schedule_ui(
                self._show_connection_error,
                runtime.hata,
            )
            return

        self.client.masaustunu_bagla()

        cards = self.client.modul_kartlari()

        if not cards.basarili:
            self._schedule_ui(
                self._show_connection_error,
                cards.hata,
            )
            return

        self._schedule_ui(
            self._apply_data,
            runtime.veri,
            cards.veri,
        )

    def _apply_data(
        self,
        runtime_data: dict[str, Any],
        card_data: dict[str, Any],
    ) -> None:
        revision = runtime_data.get("revision", 0)
        durum = runtime_data.get("durum", {})
        sistem = durum.get("sistem", {})

        self.status_text.set(
            sistem.get(
                "mesaj",
                "Çalışma alanı hazır.",
            )
        )
        self.revision_text.set(
            f"Sürüm: {revision}"
        )
        self.active_module_text.set(
            "Aktif modül: "
            + str(
                card_data.get(
                    "aktif_modul",
                    "dashboard",
                )
            )
        )

        aktif_modul = str(
            card_data.get(
                "aktif_modul",
                "dashboard",
            )
        )

        gorunum = modul_gorunumu_getir(
            aktif_modul
        )

        self.module_view_title.set(
            gorunum.baslik
        )
        self.module_view_description.set(
            gorunum.aciklama
        )
        self.module_view_details.set(
            gorunum.islem_metni
        )
        self._render_module_actions(
            gorunum.islemler
        )
        self.status_text.set(
            gorunum.durum
        )

        self._render_cards(
            card_data.get("kartlar", [])
        )

    def _show_connection_error(
        self,
        message: str,
    ) -> None:
        self.status_text.set(
            message or "Bağlantı kurulamadı."
        )

    def _schedule_ui(
        self,
        callback,
        *args,
    ) -> None:
        if self.closed:
            return

        self.root.after(
            0,
            callback,
            *args,
        )

    def _poll(self) -> None:
        if self.closed:
            return

        threading.Thread(
            target=self._load_data,
            daemon=True,
        ).start()

        self.root.after(
            2000,
            self._poll,
        )

    def _close(self) -> None:
        self.closed = True

        if hasattr(self, "scroll_canvas"):
            self.scroll_canvas.unbind_all(
                "<MouseWheel>"
            )

        if self.runtime_started_here:
            self.runtime_process.stop()

        self.root.destroy()

    def run(self) -> None:
        self._poll()
        self.root.mainloop()


def main() -> None:
    SyKasifDesktopApp().run()


if __name__ == "__main__":
    main()
