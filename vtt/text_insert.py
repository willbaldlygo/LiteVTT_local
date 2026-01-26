"""Text insertion module for VTT Local.

Inserts transcribed text at the current cursor position
in any application using clipboard and paste.
"""

import subprocess
import time


def insert_text(text: str) -> bool:
    """Insert text at the current cursor position.
    
    Uses clipboard + paste approach for maximum compatibility.
    
    Args:
        text: The text to insert
    
    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False
    
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
        
        return True
        
    except Exception as e:
        print(f"Error inserting text: {e}")
        return False


def insert_text_direct(text: str) -> bool:
    """Insert text by simulating keystrokes (alternative method).
    
    This types the text character by character, which is slower
    but doesn't affect the clipboard.
    
    Args:
        text: The text to insert
    
    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False
    
    try:
        # Escape special characters for AppleScript
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        
        script = f'''
        tell application "System Events"
            keystroke "{escaped}"
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error inserting text: {e}")
        return False
