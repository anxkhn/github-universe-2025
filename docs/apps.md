# App catalog and sources

The 2025 bundle has 33 user apps. `menu` and `startup` are system apps and do
not count toward that total. Deploy the complete `badge25/` tree using the
[tinkering guide](2025-guide.md).

## Existing upstream 2025 apps

Badge, Commits, Copilot Loop, Crypto, Files, Flappy, Gallery, Gitris, Hello,
Invaders, JezzBall, Life, Monapet, Quest, Sketch, Snake, Stocks, Weather,
Wi-Fi, and WLED come from upstream `badge25/` at commit `26f4f14`.

Network apps require configuration. WLED also needs your own WLED controller.
Quest uses infrared beacons, and the guide includes optional unlock/reset
commands. External APIs and services can change independently of the firmware.

## Community additions

These were open pull requests when imported on October 4, 2026. They are included
in this fork and tested here, not described as merged upstream releases.

| App | Source and pinned commit | Controls and notes |
| --- | --- | --- |
| 2048 | [PR 99](https://github.com/badger/home/pull/99), `2045c58ac9f744e5300cae7398a17d6747a18f8d` | A left, B right, Up/Down vertical. A restarts after game over. State saves on exit |
| Fireplace | [PR 101](https://github.com/badger/home/pull/101), `5d3ab3c295caede9f757d5db6dae4dc317853bec` | Up faster, Down slower, A/B/C reset animation speed |
| System | [PR 97](https://github.com/badger/home/pull/97), `2d6327cebc1da58f00d16024ce995d1a6f97c816` | A sync, Up/Down UTC offset. Defaults to UTC in this fork |
| Pokedex | [PR 93](https://github.com/badger/home/pull/93), `4caaf9808089e8d64cf0b41ce431ad2643cf7f69` | A previous, C next, B random, Up shiny. Local sprites live inside the app directory |
| Wordclock | [PR 81](https://github.com/badger/home/pull/81), `460e7e6a4d4d76839ad278acb4ead558f2c071dc` | Wi-Fi/NTP word clock. Shares System's saved timezone, default UTC |
| Clock | [PR 61](https://github.com/badger/home/pull/61), `f326046c3caf7ee65803aaea58440920be0ca158` | NTP clock with IP-based timezone detection, A reconnect, B sync when connected |
| Christmas | [PR 47](https://github.com/badger/home/pull/47), `1258040d559db6fd509b872c55f88fdd49c5cd65` | Christmas countdown with snow and Wi-Fi/NTP |
| Jungle | [PR 45](https://github.com/badger/home/pull/45), `823ae10643630d6a929c1afad012a2775201253f` | Up jump, Down duck, A retry |

Source imports retain their existing attribution. Wordclock has its SPDX and
author header. Pokedex sprites are downloaded locally from PokeAPI through
wsrv.nl; they are not distributed in this Git repository. Failed downloads
must succeed before claiming a complete offline sprite set.

## Additional native apps

These use native MonaOS implementations and the badge's physical controls.

| App | Controls | Adaptation |
| --- | --- | --- |
| Hydrate | B +250 ml, A -250 ml, C reset, Up/Down goal | Saved water-intake counter and pie chart. Replaces touch menu and newer graphics methods |
| Tomato | B start/pause, A reset, C switch focus/break | 25-minute focus, 10-minute short break, 30-minute long break after four tasks. Uses monotonic ticks and a screen alert |
| Tennis | B start, Up/Down paddle | CPU opponent, first to six. Uses 160x120 rendering and elapsed-time movement |
| IR remote | Up/Down slot, A learn, B replay, C sequence | Original raw IR learner for unknown-model remotes. See [setup and limitations](ir-remote.md). Uses bundled Pimoroni carrier generation |
| Minesweeper | A release/C left/right, Up/Down vertical, B reveal, hold A then B flag, A+C new | Original 9x7 board with 10 mines, pixel-art tiles, and safe first reveal. See [controls, rules, and artwork](minesweeper.md) |

Every app in this bundle targets the physical buttons and graphics API of the
badge. New apps need individual hardware and gameplay verification before
joining the bundle.

## Verification record

The eleven additions passed real-device import, initialization, and three-frame
render checks. 2048's `[2,2,2,2]` merge produced `[4,4,0,0]`, and move commit/render
passed. Tennis entered gameplay. Pokedex had all 302 normal/shiny PNGs installed.
Launcher page icons loaded successfully. These checks do not certify every
game level, network API, or service-specific setup.

IR remote passed on-device PIO assembly/start/stop, all 49 slot renders,
control text widths, and writable-root JSON replacement checks. Actual phone
capture, infrared replay accuracy, and Kenstar AC response need a physical test.

Run the repeatable test with `uv run --no-project tools/badge.py smoke`.

Minesweeper passed offline first-click safety across all 63 cells, flood fill,
flagging, win/loss, and correct/incorrect chord checks. Installed-device tests
covered startup, gameplay, win/loss rendering, icon loading, and launcher
discovery. Run logic checks with `uv run --no-project tools/test_minesweeper.py`.
