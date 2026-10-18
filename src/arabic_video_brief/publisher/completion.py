"""Mark an episode folder after publication while keeping its local paths usable."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def mark_episode_done(published_folder: Path) -> dict[str, Any]:
    folder = published_folder.resolve(strict=True)
    episode = folder.parent if folder.name.lower() in {"v2", "v3"} else folder
    parent = episode.parent.resolve(strict=True)
    if episode == parent or episode.name.lower() in {"outputs", "work"}:
        raise ValueError("Expected one episode folder, not an output root")
    if episode.name.lower().startswith("done-"):
        return {"status": "already_marked", "episode_folder": str(episode), "folder": str(folder)}
    destination = parent / ("Done-" + episode.name)
    # Both targets are resolved and checked before moving this one episode.
    if destination.resolve().parent != parent or episode.parent != parent:
        raise ValueError("Episode rename must stay inside its original parent")
    if destination.exists():
        raise FileExistsError(f"Cannot mark episode: destination already exists: {destination}")

    def rebase(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: rebase(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rebase(item) for item in value]
        if isinstance(value, str):
            for old, new in ((str(episode), str(destination)), (episode.as_posix(), destination.as_posix())):
                if value == old or value.startswith(old + "/") or value.startswith(old + "\\"):
                    return new + value[len(old):]
        return value

    updates = []
    warnings = []
    for path in episode.rglob("*.json"):
        if not path.resolve().is_relative_to(episode):
            continue
        try:
            before = json.loads(path.read_text(encoding="utf-8-sig"))
            after = rebase(before)
            if before != after:
                updates.append((path.relative_to(episode), after))
        except (OSError, ValueError) as error:
            warnings.append(f"Could not inspect {path.name}: {error}")
    episode.rename(destination)
    for relative, data in updates:
        try:
            path = destination / relative
            temporary = path.with_name(path.name + ".pending")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(path)
        except OSError as error:
            warnings.append(f"Could not update {relative}: {error}")
    return {"status": "renamed", "episode_folder": str(destination),
            "folder": str(destination / folder.relative_to(episode)), "warnings": warnings}
