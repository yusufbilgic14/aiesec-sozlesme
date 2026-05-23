import os
import subprocess
import sys


def setup():
    fonts_dir = "/usr/share/fonts/truetype/msttcorefonts"
    if os.path.isdir(fonts_dir):
        print("Microsoft fonts already installed.")
        return

    print("Installing Microsoft Core Fonts...")
    try:
        subprocess.run(
            ["bash", os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_fonts.sh")],
            capture_output=True,
            timeout=120,
        )
    except Exception as e:
        print(f"Font installation note: {e}")

    from fill_pdf import FONT_REGULAR, FONT_BOLD
    if FONT_REGULAR:
        print(f"Regular font found: {FONT_REGULAR}")
    else:
        print("WARNING: Regular font not found. PDF text may not match original.")
    if FONT_BOLD:
        print(f"Bold font found: {FONT_BOLD}")
    else:
        print("WARNING: Bold font not found.")


if __name__ == "__main__":
    setup()