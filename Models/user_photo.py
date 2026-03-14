from dataclasses import dataclass


@dataclass
class UserPhoto:
    employee_id: int
    webview_link: str
    local_path: str | None = ""
