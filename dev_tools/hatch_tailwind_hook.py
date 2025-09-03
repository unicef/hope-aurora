import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class TailwindBuildHook(BuildHookInterface):
    PLUGIN_NAME = "tailwind"

    def _run(self, *cmds: str) -> None:
        theme = Path(__file__).parent.parent / "src/aurora/web/theme/"
        src = theme / "static_src"
        try:
            process = subprocess.run(cmds, cwd=src, check=True, capture_output=True)  # noqa: S603
            if process.stderr:
                if process.returncode != 0:
                    self.app.display_error(f"Tailwind build STDERR:\n{process.stderr}")
                else:
                    self.app.display_info(f"Tailwind build STDERR:\n{process.stderr}")

        except Exception:
            self.app.display_error("Error executing Tailwind command")
            raise

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        theme = Path(__file__).parent.parent / "src/aurora/web/theme/"
        node_modules = theme / "static_src/node_modules"
        if node_modules.exists():
            self.app.display_info("Compiling Tailwind CSS...")
            self._run("npm", "run", "build")
            self._run("git", "add", "../static")
        else:
            self.app.display_info(f"Skip Tailwind compilation: '{node_modules}' does not esists")
