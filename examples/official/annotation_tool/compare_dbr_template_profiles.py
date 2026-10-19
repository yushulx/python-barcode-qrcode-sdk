from pathlib import Path
import runpy
import sys


def main():
    target = Path(__file__).resolve().parent / "template-optimizer" / "tools" / "compare_dbr_template_profiles.py"
    sys.path.insert(0, str(target.parent))
    original_argv0 = sys.argv[0]
    sys.argv[0] = str(target)
    try:
        runpy.run_path(str(target), run_name="__main__")
    finally:
        sys.argv[0] = original_argv0
        sys.path.pop(0)


if __name__ == "__main__":
    main()