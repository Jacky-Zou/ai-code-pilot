from pathlib import Path, PureWindowsPath

from app.core.config import PROJECT_ROOT, Settings, get_settings
from app.core.exceptions import ToolError


def normalize_project_path(project_path: str, settings: Settings | None = None) -> str:
    """Resolve a user-provided project path into a path visible to the backend.

    In local Python mode the user can pass an ordinary OS path. In Docker mode,
    Windows paths such as `D:/code/my_projects/demo` are not directly visible
    inside the Linux container. When PROJECTS_HOST_ROOT and
    PROJECTS_CONTAINER_ROOT are configured, this function maps the host path
    prefix to the mounted container prefix before existence checks.
    """

    resolved_settings = settings or get_settings()
    raw_path = project_path.strip()
    if not raw_path:
        raise ToolError("Project path cannot be empty")

    direct_path = Path(raw_path).expanduser()
    if not direct_path.is_absolute():
        direct_path = PROJECT_ROOT / direct_path
    if direct_path.exists():
        return str(direct_path.resolve())

    mapped_path = _map_host_path_to_container(raw_path, resolved_settings)
    if mapped_path is not None and mapped_path.exists():
        return str(mapped_path.resolve())

    hint = ""
    if resolved_settings.projects_host_root and resolved_settings.projects_container_root:
        hint = (
            f" The configured Docker project mapping is "
            f"{resolved_settings.projects_host_root} -> {resolved_settings.projects_container_root}."
        )
    raise ToolError(
        "Project path is not accessible from the backend: "
        f"{project_path}.{hint} If you run with Docker, mount the host project directory and use its container path."
    )


def _map_host_path_to_container(raw_path: str, settings: Settings) -> Path | None:
    if not settings.projects_host_root or not settings.projects_container_root:
        return None

    normalized_raw = raw_path.replace("\\", "/")
    normalized_host_root = settings.projects_host_root.replace("\\", "/").rstrip("/")
    if not normalized_host_root:
        return None

    raw_lower = normalized_raw.lower()
    host_lower = normalized_host_root.lower()
    if raw_lower == host_lower:
        relative = ""
    elif raw_lower.startswith(host_lower + "/"):
        relative = normalized_raw[len(normalized_host_root) :].lstrip("/")
    else:
        return None

    # PureWindowsPath keeps drive-letter parsing predictable even when this
    # code runs inside a Linux container.
    safe_relative = PureWindowsPath(relative).as_posix().lstrip("/")
    return Path(settings.projects_container_root).joinpath(safe_relative)
