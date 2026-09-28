#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(base_dir))
    sys.path.insert(0, str(base_dir / "apps"))

    try:
        from dotenv import load_dotenv
        env_path = base_dir / ".env"
        if not env_path.exists() and (base_dir / ".env.development").exists():
            env_path = base_dir / ".env.development"
        load_dotenv(env_path)
    except ImportError:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
