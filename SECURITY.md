# Security Policy

## Supported Versions

LiteVTT is a personal macOS tool under active development. Only the latest
commit on `main` is supported.

## Scope

LiteVTT processes all audio and text **entirely on-device** using a local
Whisper model. It makes no network connections and stores no data outside
`~/Documents/LiteVTT/` (or a path you configure). There are no servers,
accounts, or credentials involved.

The practical attack surface is therefore small: local file handling,
subprocess calls to macOS system utilities (`pbcopy`, `pbpaste`, `osascript`,
`ffmpeg`), and Python dependency vulnerabilities.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Use GitHub's built-in private reporting instead:

1. Go to the **Security** tab of this repository.
2. Click **"Report a vulnerability"**.
3. Fill in the details — what you found, how to reproduce it, and what impact
   you believe it has.

You can expect an acknowledgement within **7 days** and a fix or assessment
within **30 days** for confirmed issues.

## What to Report

Good candidates:

- A Python dependency with a published CVE that affects this codebase.
- A subprocess call that can be exploited via a crafted file path or
  filename to execute arbitrary code.
- A way for a malicious audio file to escape the temp-file sandbox during
  transcription.

Out of scope:

- Attacks that require physical access to the machine where the app is running.
- Theoretical vulnerabilities with no practical impact on a single-user
  desktop tool.
- Issues in the Whisper model weights themselves (report those upstream to
  [whisper.cpp](https://github.com/ggerganov/whisper.cpp)).
