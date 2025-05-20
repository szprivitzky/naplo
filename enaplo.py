import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import Calendar
from datetime import datetime
import json
from pathlib import Path

DATA_FILE = Path("events.json")


class Event:
    """Egy naptári eseményt reprezentál."""

    def __init__(self, title: str, dt: datetime, description: str = "") -> None:
        self.title = title
        self.dt = dt
        self.description = description

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "dt": self.dt.isoformat(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(
            title=data["title"],
            dt=datetime.fromisoformat(data["dt"]),
            description=data.get("description", ""),
        )

    def __str__(self) -> str:
        return f"{self.dt.strftime('%H:%M')}  {self.title}"


class CalendarModel:
    """Az események tárolásáért és kezeléséért felelős modell."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self.load()

    # ---------- perzisztencia ----------
    def load(self) -> None:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            self._events = [Event.from_dict(e) for e in data]

    def save(self) -> None:
        with open(DATA_FILE, "w", encoding="utf-8") as fp:
            json.dump([e.to_dict() for e in self._events], fp, ensure_ascii=False, indent=2)

    # ---------- CRUD ----------
    def events_on_day(self, date: datetime) -> list[Event]:
        return sorted(
            [e for e in self._events if e.dt.date() == date.date()],
            key=lambda e: e.dt,
        )

    def add_event(self, event: Event) -> None:
        self._events.append(event)
        self.save()

    def delete_event(self, event: Event) -> None:
        self._events.remove(event)
        self.save()


class CalendarApp(tk.Tk):
    """A grafikus felület és esemény‑kezelés."""

    def __init__(self) -> None:
        super().__init__()
        self.title("E‑naptár")
        self.geometry("600x400")
        self.minsize(500, 350)

        self.model = CalendarModel()
        self._create_widgets()
        self._bind_events()
        self._update_event_list()

    # ---------- UI ----------
    def _create_widgets(self) -> None:
        # bal oldalt: dátumválasztó
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=5, pady=5)

        self.cal = Calendar(
            left,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            locale="hu_HU",
            firstweekday="monday",
        )
        self.cal.pack(fill="both", expand=True)

        # jobb oldalt: napi események
        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        topbar = ttk.Frame(right)
        topbar.pack(fill="x")

        self.add_btn = ttk.Button(topbar, text="Esemény hozzáadása", command=self._add_event_dialog)
        self.add_btn.pack(side="left", padx=(0, 5))

        self.del_btn = ttk.Button(topbar, text="Esemény törlése", command=self._delete_selected_event)
        self.del_btn.pack(side="left")

        self.event_list = tk.Listbox(right, activestyle="none")
        self.event_list.pack(fill="both", expand=True, pady=5)

    def _bind_events(self) -> None:
        self.cal.bind("<<CalendarSelected>>", lambda e: self._update_event_list())
        self.event_list.bind("<Double-1>", lambda e: self._show_event_details())

    # ---------- esemény‑kezelők ----------
    def _update_event_list(self) -> None:
        day = datetime.strptime(self.cal.get_date(), "%Y-%m-%d")
        events = self.model.events_on_day(day)

        self.event_list.delete(0, "end")
        for ev in events:
            self.event_list.insert("end", str(ev))

    def _add_event_dialog(self) -> None:
        day = datetime.strptime(self.cal.get_date(), "%Y-%m-%d")

        title = simpledialog.askstring("Esemény címe", "Írd be az esemény címét:", parent=self)
        if not title:
            return

        time_str = simpledialog.askstring(
            "Időpont (ÓÓ:PP)", "Add meg a kezdési időpontot (pl. 14:30):", parent=self
        )
        try:
            hour, minute = map(int, (time_str or "00:00").split(":"))
            dt = day.replace(hour=hour, minute=minute)
        except ValueError:
            messagebox.showerror("Hibás formátum", "Kérlek ÓÓ:PP formátumban add meg az időt.")
            return

        desc = simpledialog.askstring("Leírás", "Rövid leírás (opcionális):", parent=self) or ""

        event = Event(title=title, dt=dt, description=desc)
        self.model.add_event(event)
        self._update_event_list()

    def _delete_selected_event(self) -> None:
        sel = self.event_list.curselection()
        if not sel:
            return
        idx = sel[0]
        day = datetime.strptime(self.cal.get_date(), "%Y-%m-%d")
        events = self.model.events_on_day(day)
        event = events[idx]
        if messagebox.askyesno("Törlés megerősítése", f"Biztosan törölni szeretnéd: {event.title}?"):
            self.model.delete_event(event)
            self._update_event_list()

    def _show_event_details(self) -> None:
        sel = self.event_list.curselection()
        if not sel:
            return
        idx = sel[0]
        day = datetime.strptime(self.cal.get_date(), "%Y-%m-%d")
        event = self.model.events_on_day(day)[idx]
        messagebox.showinfo(
            "Esemény részletei",
            f"Cím: {event.title}\nIdő: {event.dt.strftime('%Y-%m-%d %H:%M')}\n\n{event.description}",
        )


if __name__ == "__main__":
    app = CalendarApp()
    app.mainloop()