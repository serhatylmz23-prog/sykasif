from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ProjectRecord:
    project_id: str
    name: str
    research_area: str
    description: str
    status: str
    active: bool
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._projects: dict[str, ProjectRecord] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def reset(self) -> None:
        with self._lock:
            self._projects.clear()

    def create(
        self,
        *,
        name: str,
        research_area: str,
        description: str = "",
    ) -> ProjectRecord:
        clean_name = name.strip()
        clean_area = research_area.strip()

        if not clean_name:
            raise ValueError("Proje adı boş bırakılamaz.")

        if not clean_area:
            raise ValueError("Araştırma alanı boş bırakılamaz.")

        now = self._now()

        project = ProjectRecord(
            project_id=str(uuid4()),
            name=clean_name,
            research_area=clean_area,
            description=description.strip(),
            status="ready",
            active=False,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._projects[project.project_id] = project

        return project

    def list(self) -> list[ProjectRecord]:
        with self._lock:
            return sorted(
                self._projects.values(),
                key=lambda item: item.created_at,
            )

    def get(self, project_id: str) -> ProjectRecord | None:
        with self._lock:
            return self._projects.get(project_id)

    def activate(self, project_id: str) -> ProjectRecord | None:
        with self._lock:
            selected = self._projects.get(project_id)

            if selected is None:
                return None

            now = self._now()

            for project in self._projects.values():
                project.active = project.project_id == project_id

                if project.active:
                    project.status = "active"

                elif project.status == "active":
                    project.status = "ready"

                project.updated_at = now

            return selected

    def archive(self, project_id: str) -> ProjectRecord | None:
        with self._lock:
            project = self._projects.get(project_id)

            if project is None:
                return None

            project.active = False
            project.status = "archived"
            project.updated_at = self._now()

            return project


project_repository = ProjectRepository()