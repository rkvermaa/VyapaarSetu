from dynaconf import Dynaconf
import os

_settings_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")

settings = Dynaconf(
    envvar_prefix="VYAPAARSETU",
    settings_files=[
        os.path.join(_settings_dir, "settings.toml"),
        os.path.join(_settings_dir, ".secrets.toml"),
    ],
    environments=True,
    load_dotenv=False,
    env_switcher="VYAPAARSETU_ENV",
    merge_enabled=True,
)
