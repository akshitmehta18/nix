import os
import json

# Constants
NIX_FOLDER = ".nix"
CONFIG_FILE = "config.json"
GITIGNORE_FILE = ".gitignore"
INDEX_FOLDER = "index"
GLOBAL_NIX_DIR = os.path.expanduser("~/.nix")
GLOBAL_CONFIG_FILE = os.path.join(GLOBAL_NIX_DIR, "config.json")

_CURRENT_PROJECT_ROOT = None


def set_project_root(path: str):
    """Set the active project directory."""
    global _CURRENT_PROJECT_ROOT
    if path:
        abs_path = os.path.abspath(os.path.expanduser(path))
        _CURRENT_PROJECT_ROOT = abs_path
        try:
            os.chdir(abs_path)
        except Exception:
            pass


def get_project_root():
    """Get current project directory"""
    global _CURRENT_PROJECT_ROOT
    return _CURRENT_PROJECT_ROOT or os.getcwd()


def get_nix_path():
    """Get full path to .nix folder in current project"""
    return os.path.join(get_project_root(), NIX_FOLDER)


def get_global_nix_path():
    """Get full path to global ~/.nix directory"""
    os.makedirs(GLOBAL_NIX_DIR, exist_ok=True)
    return GLOBAL_NIX_DIR


def get_global_config_path():
    """Get full path to ~/.nix/config.json"""
    return GLOBAL_CONFIG_FILE


def load_global_config():
    """Load global ~/.nix/config.json as dictionary"""
    try:
        path = get_global_config_path()
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_global_config(data: dict):
    """Save dictionary to global ~/.nix/config.json"""
    try:
        get_global_nix_path()
        path = get_global_config_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        return False


def get_config_path():
    """Get full path to config.json"""
    return os.path.join(get_nix_path(), CONFIG_FILE)


def get_index_path():
    """Get full path to index folder"""
    return os.path.join(get_nix_path(), INDEX_FOLDER)


def nix_exists():
    """Check if .nix folder exists"""
    return os.path.exists(get_nix_path())


def create_nix_folder():
    """Create .nix directory and .gitignore"""
    try:
        nix_path = get_nix_path()
        os.makedirs(nix_path, exist_ok=True)

        # Create .gitignore to ignore all contents
        gitignore_path = os.path.join(nix_path, GITIGNORE_FILE)
        with open(gitignore_path, 'w') as f:
            f.write("*\n")

        return True
    except Exception as e:
        raise Exception(f"Failed to create .nix folder: {str(e)}")


def load_config():
    """Load config.json and return as dictionary"""
    try:
        config_path = get_config_path()
        if not os.path.exists(config_path):
            return None

        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def save_config(data):
    """Save dictionary to config.json"""
    try:
        config_path = get_config_path()
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        raise Exception(f"Failed to save config: {str(e)}")


def get_default_config():
    """Return default config structure"""
    return {
        "project_name": os.path.basename(get_project_root()),
        "springboot_version": "",
        "initialized_at": "",
        "total_files": 0,
        "last_checked": ""
    }


def cleanup_nix_folder(silent: bool = True):
    """Delete .nix folder to ensure fresh analysis on next run.

    This is called on exit so that nix always gets the latest
    changes when reinitialized.

    Args:
        silent: If True (default), don't print cleanup message

    Returns:
        True if cleanup was successful or folder didn't exist
    """
    import shutil

    try:
        nix_path = get_nix_path()
        if os.path.exists(nix_path):
            shutil.rmtree(nix_path)
        return True
    except Exception:
        # Silently fail - cleanup is not critical
        return False