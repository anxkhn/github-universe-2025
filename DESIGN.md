# Copilot Minis badge interface

The interface follows Copilot CLI's dark terminal palette, cyan identity,
numbered options, selection cursor, and keyboard hints. OpenCode's terminal
pickers informed rectangular selected rows and persistent footer actions.
The Copilot desktop app's session list maps to the badge's Sessions screen.
All coordinates are logical pixels in a 160x120 framebuffer.

## Layout and typography

`ark.ppf` is 11 pixels high on the tested runtime. One muted context line
begins at y=1, with a divider at y=14. A four-pixel square shows connection
or thread status. There is no permanent brand heading, LIVE label, footer,
or repeated status text. Threads occupy four 25-pixel rows starting at y=18.
Chat content starts at y=19 and shows eight lines with 12-pixel spacing,
60% more lines than the earlier five-line layout. Transient send/error notices
briefly reserve one line. Question summaries use up to three lines, followed
by numbered choices that wrap to two lines. The list scrolls to keep selection
visible. Hold C reveals the button guide only while held.
Content has six-pixel side margins. Width comes from the first element of
`screen.measure_text`, rather than character-count assumptions.

## Colors

| Role | RGB |
| --- | --- |
| Background | 17, 23, 27 |
| Text | 240, 246, 252 |
| Secondary text | 170, 183, 197 |
| Selected row | 33, 48, 56 |
| Identity and selected option | 112, 236, 235 |
| Running | 100, 190, 255 |
| Idle | 90, 215, 135 |
| Permission or question | 255, 195, 70 |
| Error or stopped | 255, 115, 110 |

Status words accompany color. Selected rows have a filled background and a
`>` cursor. Unread rows have a static square marker. Brightness stays at 0.6;
updates never pulse or dim the reading surface. The launcher icon uses the
official Copilot Octicon with a small three-dot chat companion for Minis.
`tools/build_copilot_minis_icon.py` builds it from the pinned SVG. The PNG
contains the upstream source, adaptation description, and MIT license.

## Input and edge states

Up/Down wrap thread or choice selection and scroll chat details. B opens or
submits. A backs out to Sessions, or to options from details. C opens actions
in chat, reads the full selected option and request in options, and opens
connection information from Sessions. C never unexpectedly disconnects.
Pending questions open directly when selecting their session. C's short tap
acts on release; holding it for 500 ms displays help without navigating.
HOME exits
through the launcher. Reject is the first permission option. Commands require
a live connection and the same request ID used when the options opened.
Disconnected, unpaired, empty, changed-request, and laptop-only-answer states
have explicit text. The badge retains readable snapshots while disconnected.

## References and verification

- [Copilot CLI reference image](https://github.com/user-attachments/assets/2e3e84a2-f56b-4852-bbb6-a5e672e2404c), inspected locally.
- [Copilot CLI navigation guidance](https://github.blog/changelog/2025-10-03-github-copilot-cli-enhanced-model-selection-image-support-and-streamlined-ui/).
- [Copilot desktop session navigation](https://github.com/features/ai/github-app).
- OpenCode's `packages/tui/src/ui/dialog-select.tsx`, inspected in the local source reference.

Simulator screenshots checked thread, chat, and numbered-option views. The
physical badge ran the revised app over Wi-Fi and submitted permission and
question replies with injected button states. The updated app was then
checksum-deployed. The brightness regression check asserts constant 0.6
across repeated unread frames.

The compact pass follows [progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
and [deferring secondary mobile content](https://www.nngroup.com/articles/defer-secondary-content-for-mobile/).
Button instructions remain available through hold-C rather than occupying a
permanent reading row. The empty state teaches this shortcut. Hardware tests
cover short-tap navigation, hold-C help, release without accidental navigation,
and live pairing restoration after demo checks.
