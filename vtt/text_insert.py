"""Text insertion module for VTT Local.

Inserts transcribed text at the current cursor position
in any application using clipboard and paste.
"""

import subprocess
import time


def insert_text(text: str) -> bool:
    """Insert text at the current cursor position.

    Saves and restores the clipboard around the paste operation.

    Args:
        text: The text to insert

    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False

    # Save existing clipboard contents before overwriting
    original_clipboard = None
    try:
        result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            original_clipboard = result.stdout
    except Exception as e:
        print(f"Warning: Could not save clipboard: {e}")

    try:
        # Copy text to clipboard using pbcopy
        process = subprocess.Popen(
            ['pbcopy'],
            stdin=subprocess.PIPE,
            env={'LANG': 'en_US.UTF-8'}
        )
        process.communicate(text.encode('utf-8'))

        if process.returncode != 0:
            print("Failed to copy to clipboard")
            return False

        # Small delay to ensure clipboard is updated and app is ready
        time.sleep(0.2)

        # Paste using AppleScript and System Events
        script = '''
        tell application "System Events"
            keystroke "v" using command down
        end tell
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Failed to paste: {result.stderr}")
            return False

        # Small delay to let the paste complete before restoring
        time.sleep(0.1)

        return True

    except Exception as e:
        print(f"Error inserting text: {e}")
        return False

    finally:
        # Restore the original clipboard contents
        if original_clipboard is not None:
            try:
                restore = subprocess.Popen(
                    ['pbcopy'],
                    stdin=subprocess.PIPE
                )
                restore.communicate(original_clipboard)
            except Exception as e:
                print(f"Warning: Could not restore clipboard: {e}")
