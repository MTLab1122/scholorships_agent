"""YAML utility module to load and dump YAML configuration files.
Uses ruamel.yaml for pure-Python wheel compatibility.
"""

from pathlib import Path
from typing import Any, Union
from ruamel.yaml import YAML

_yaml = YAML(typ="safe")
_yaml.default_flow_style = False


def load_yaml(file_path: Union[str, Path]) -> Any:
    """Loads a YAML file and returns Python dict/list."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    with open(path, "r", encoding="utf-8") as f:
        return _yaml.load(f)


def dump_yaml(data: Any, file_path: Union[str, Path]) -> None:
    """Dumps Python data into a YAML file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        _yaml.dump(data, f)
