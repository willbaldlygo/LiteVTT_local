# LiteVTT Project Log

## Session: April 17, 2026

**Context:** Full codebase review, cleanup, security hardening, and fresh-machine install testing. All work carried out collaboratively between Will Baldlygo and Claude (Sonnet 4.6) via Claude Code.

---

## Phase 1: Codebase Audit and Cleanup

### Bug Fixes

**Missing `json` import in `vtt/app.py`**
`_load_config()` called `json.load()` but `json` was never imported. Config had silently never loaded since the app was first written, meaning `default_model`, `use_small_en`, and the trigger string were always falling back to hardcoded defaults.

**Hardcoded status string in `vtt/app.py`**
Line 222 had `"Ready - Hold Fn+Ctrl"` hardcoded. Changed to read from the config-backed `self._trigger` instance variable, consistent with how the rest of the status messages work.

**`env=` replacing entire subprocess environment in `vtt/text_insert.py`**
`subprocess.Popen(['pbcopy'], env={'LANG': 'en_US.UTF-8'})` was replacing the full environment rather than adding to it, stripping `PATH`, `HOME`, `USER` etc. from the pbcopy process. Changed to `env={**os.environ, 'LANG': 'en_US.UTF-8'}`.

### Storage Path Simplification

Removed the network drive discovery logic from `vtt/recorder.py`. The original code globbed `/Volumes/array_main*` looking for a NAS, with a local fallback. Replaced with a clean default of `~/Documents/LiteVTT/` with an optional override via `config.json` `storage.path`. Updated `config.json` accordingly:

```json
"storage": { "path": "" }
```

Empty string means use the default. Any value overrides it.

**Decision:** The network drive logic was personal infrastructure that had no place in a distributed tool. All users now get a sensible, predictable default.

### Dead Code and File Removal

- Deleted `run.py` — identical duplicate of `litetype.py`
- Deleted `download_model.command` — superseded by `download_models.py`
- Removed `pynput` from `requirements.txt` — never imported anywhere
- Removed `scipy` from `requirements.txt` — see scipy section below
- Removed module-level singleton `_recorder` and three convenience functions from `vtt/audio.py`
- Removed module-level `_transcriber`, `get_transcriber()`, and `transcribe()` from `vtt/transcriber.py`
- Removed `insert_text_direct()` from `vtt/text_insert.py` — never called
- Removed `trim_silence()` from `vtt/recorder.py` — no-op placeholder
- Removed unused `threading` and `glob` imports from `vtt/recorder.py`

### scipy Removal and ffmpeg Fix

`litescribe.py` was importing scipy to resample audio to 16kHz, but `convert_to_wav()` already passed `-ar 16000` to ffmpeg — so the audio was already 16kHz before scipy touched it. Removed the scipy resampling branch entirely.

Changed `convert_to_wav()` to always run ffmpeg for all input formats (previously it skipped WAV files). This guarantees 16kHz mono output regardless of input, so soundfile just reads the result.

### Function Rename

Renamed `create_option_s_handler` to `create_hotkey_handler` in `vtt/hotkeys.py`. The original name was a stale relic from an earlier implementation. Updated the call site in `vtt/app.py` and removed the "Kept name for compatibility" comment.

### Model Selection Fix

`vtt/app.py` `_load_model()` ignored `config.json` entirely and always tried the same hardcoded priority list. Updated to read `default_model` and `use_small_en` from config and build the candidate list accordingly. Applied the same fix to `litescribe.py`.

### Clipboard Save/Restore

`insert_text()` previously overwrote the clipboard and never restored it. Updated to:
1. Save clipboard contents with `pbpaste` before writing
2. Restore after the paste keystroke completes
3. Handle empty clipboard (restore `b''`)
4. Handle `pbpaste` failure or non-text content gracefully — skip restore rather than crash
5. Handle restore failure without propagating the exception

### Bare Except Cleanup

Replaced `except: pass` with `except Exception as e: print(f"Warning: {e}")` in `vtt/app.py` (`_load_config`, `_update_status`) and `vtt/recorder.py` (`_load_config`, `start`).

### README Rewrite

Rewrote `README.md` to reflect the cleaned-up codebase: removed network drive mention, fixed model descriptions (Base is faster, Small English is more accurate — they were swapped), removed false claim that hotkeys are configurable, documented `Setup.command` as the recommended setup path, noted storage default and clipboard behaviour.

---

## Phase 2: Unit Test Suite

Added `tests/` with 36 tests covering the pure-logic modules (no macOS hardware required):

- `test_storage.py` — `LiteRecorder._find_storage_path()`: default path, custom path, tilde expansion, directory creation, subdirectory creation, transcript content and filename
- `test_config.py` — `_load_config()`: valid JSON, missing file, malformed JSON, IO error
- `test_model_selection.py` — `get_model_path()`: candidate priority, `use_small_en` flag, fallback behaviour, deduplication
- `test_text_insert.py` — `insert_text()`: empty input, pbcopy failure, osascript failure, clipboard saved and restored, empty clipboard restored, no restore when pbpaste fails or raises, restore on paste failure, restore failure doesn't crash

`tests/conftest.py` mocks `numpy`, `sounddevice`, `soundfile`, `rumps`, `AppKit`, `Quartz`, and `pywhispercpp` so the suite runs on any platform including Linux CI.

---

## Phase 3: Security Hardening

### Security Review Findings

- **No `SECURITY.md`** — no vulnerability disclosure channel
- **No CI** — tests existed but nothing ran them automatically
- **No Dependabot** — no automated dependency vulnerability alerts
- **`env=` bug** — subprocess environment replacement (fixed in Phase 1)
- **Unpinned dependencies** — `>=` floors only; acceptable risk for a personal tool

### Actions Taken

- Added `SECURITY.md` with private vulnerability reporting instructions, 7-day acknowledgement / 30-day resolution SLA, scope definition
- Added `.github/workflows/tests.yml` — runs `pytest tests/ -v` on push and PR to `main` using `ubuntu-latest` + Python 3.11
- Added `.github/dependabot.yml` — weekly checks for pip and GitHub Actions dependencies
- Enabled Private Vulnerability Reporting, Dependency graph, Dependabot alerts, Dependabot security updates, and Grouped security updates in GitHub repo settings
- Enabled branch protection on `main` requiring CI to pass before merge

**Decision on `.command` files:** These are unsigned bash scripts requiring a Gatekeeper bypass. This is standard and acceptable for a developer tool distributed via GitHub to a supervised audience. For unsupported consumer distribution, a signed and notarised `.app` bundle would be required — a significant engineering effort not appropriate for this tool's scope.

---

## Phase 4: Fresh-Machine Install Testing

Tested installation on a second MacBook where the tool had never been installed. Multiple failures were discovered and fixed iteratively.

### Failure 1: `python` command not found
macOS provides `python3`, not `python`. All manual commands in the README used `python`. Fixed: updated all references to `python3`.

### Failure 2: README ordering — clone step missing from Option A
Option A said "Double-click Setup.command" before any mention of cloning the repository. A new user following Option A had no instructions for getting the code. Fixed: added explicit `git clone` and `cd` commands as step 1 of Option A.

### Failure 3: Gatekeeper blocking Setup.command
macOS blocked `Setup.command` on first run with "cannot be executed because you do not have appropriate access privileges." Fixed: README now documents right-click → Open and explains why. A Troubleshooting section was added covering this and three other common first-run failures.

### Failure 4: Stale venv from previous attempt
A failed install left a `venv` directory pointing to a Python binary that no longer existed. `pip` subsequently failed with "bad interpreter". Fixed: documented in Troubleshooting (`rm -rf venv` and start again).

### Failure 5: `.command` files not executable after cloning
Git stored all three `.command` files as `100644` (no execute bit). macOS blocked them. Fixed: `git update-index --chmod=+x` applied to all three files. The execute permission is now stored in the git index and restored on every clone.

### Failure 6: SSL certificate error when downloading models
`download_models.py` used `urllib.request.urlretrieve` which failed with `CERTIFICATE_VERIFY_FAILED` on a fresh macOS Python install. Root cause: Python on macOS does not use the system certificate store by default. Fixed: added `certifi` to `requirements.txt` and updated `download_models.py` to build a custom SSL context using `certifi.where()` before the download runs.

**Note on PR workflow:** During this phase, fixes were pushed to the feature branch and PRs were created incrementally. Several fixes arrived on the branch after a PR had already been merged, requiring additional PRs. Going forward, fixes should be batched on the branch before raising a PR.

---

## Phase 5: Post-Install Improvements

### Terminal window stays open after exit
Both `LiteType.command` and `LiteScribe.command` left the Terminal window open after the Python process exited — after voice shutdown (LiteType) or selecting Quit (LiteScribe). Fixed: both launchers now run `osascript -e 'tell application "Terminal" to close front window'` after the Python process returns.

### LiteScribe Quit option
The user reported no obvious way to quit LiteScribe. The "3. Quit" option already existed in the menu — the issue was that selecting it ended the Python process but left the Terminal open. Resolved by the terminal close fix above.

---

## Final State of main Branch

All changes described above are merged to `main`. PR #6 (terminal close + README Option A clone step) is open at time of writing.

### Files changed from original codebase

| File | Change |
|---|---|
| `vtt/app.py` | json import, bare excepts, status string, trigger var, hotkey rename, model config |
| `vtt/recorder.py` | Storage path simplified, bare excepts, removed threading/glob/trim_silence |
| `vtt/audio.py` | Removed module-level singleton and convenience functions |
| `vtt/transcriber.py` | Removed module-level instance and convenience functions |
| `vtt/text_insert.py` | Clipboard save/restore, removed insert_text_direct, env= fix |
| `vtt/hotkeys.py` | Renamed create_option_s_handler → create_hotkey_handler |
| `litescribe.py` | Removed scipy, ffmpeg handles all formats, model config, Volumes check removed |
| `config.json` | Storage block simplified to `{"path": ""}` |
| `requirements.txt` | Removed pynput, scipy; added certifi |
| `download_models.py` | certifi SSL fix |
| `README.md` | Full rewrite; clone step in Option A; Troubleshooting section |
| `Setup.command` | Per-step output; uses venv python |
| `LiteType.command` | Closes terminal on exit |
| `LiteScribe.command` | Closes terminal on exit |
| `SECURITY.md` | New file |
| `.github/workflows/tests.yml` | New file |
| `.github/dependabot.yml` | New file |
| `tests/` | New directory — 36 unit tests |

### Files deleted

- `run.py`
- `download_model.command`
