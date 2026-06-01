from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import ToolError
from app.core.project_paths import normalize_project_path


def test_normalize_project_path_accepts_existing_path(tmp_path: Path) -> None:
    assert normalize_project_path(str(tmp_path), settings=Settings(_env_file=None)) == str(tmp_path.resolve())


def test_normalize_project_path_maps_configured_host_root(tmp_path: Path) -> None:
    host_root = "D:/code/projects"
    container_root = tmp_path / "workspace"
    mapped_project = container_root / "demo"
    mapped_project.mkdir(parents=True)
    settings = Settings(
        PROJECTS_HOST_ROOT=host_root,
        PROJECTS_CONTAINER_ROOT=str(container_root),
        _env_file=None,
    )

    assert normalize_project_path("D:/code/projects/demo", settings=settings) == str(mapped_project.resolve())


def test_normalize_project_path_reports_docker_mapping_hint(tmp_path: Path) -> None:
    settings = Settings(
        PROJECTS_HOST_ROOT="D:/code/projects",
        PROJECTS_CONTAINER_ROOT=str(tmp_path / "workspace"),
        _env_file=None,
    )

    with pytest.raises(ToolError, match="not accessible from the backend"):
        normalize_project_path("D:/other/demo", settings=settings)
