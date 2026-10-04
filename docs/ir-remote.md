# Learn an AC remote

The `ir-remote` app records raw infrared envelopes and replays them without
assuming a brand or NEC protocol. Use Mi Remote's working Kenwood profile as
the source for your Kenstar AC. The phone must actually emit IR through its
blaster; a Wi-Fi-only remote app cannot teach the badge.

There is no confirmed model-specific Kenstar/Kenwood database match for this
AC. Learning the signals that already work avoids selecting an unrelated
protocol based on the brand name.

## First command

1. Double-tap RESET and run `uv run --no-project tools/badge.py deploy --app ir-remote`.
   Eject BADGER cleanly, then reset. This installs only the remote app.
2. Open **ir-remote**. Use Up/Down to select a slot, such as **Cool 24C**.
3. Set Mi Remote to the desired mode, temperature, fan, and swing settings.
4. Press A on the badge. Point the phone's IR emitter toward the badge's
   receiver, initially about 10–30 cm apart, and send one command.
5. After silence, the badge saves the signal. Aim the badge's IR transmitter
   toward the AC and press B. Check that the AC responds correctly.
6. Repeat for power off, other temperatures, fan speeds, swing, and the other
   features your working remote supports.

AC remotes often transmit the complete state with each press. A **Cool 24C**
capture can also contain fan speed and swing settings. Replaying **Temp up**
may set the recorded temperature rather than increment the AC's current one.
The app cannot synthesize uncaptured combinations or read the AC's state.
Use custom slots for combinations such as cool 24C, high fan, swing on.

## Controls

| Button | Action |
| --- | --- |
| Up/Down | Select a saved command slot |
| A | Start learning, or cancel an active recording |
| B | Replay the selected slot, or finish an active recording |
| C | Switch between single-command and sequence recording |
| A+C | Ask to delete the selected slot; B confirms, A or C cancels |
| B+C | Change carrier for the next recording: 38, 36, 40, or 56 kHz |
| Rear HOME | Exit and release the IR hardware |

There are 49 slots, including power, cool 16–30C, modes, fan speeds, swing,
turbo, sleep, eco, light, timers, directional keys, and eight custom slots.
Only features emitted by the source remote and understood by the AC will work.

## Sequences and button combinations

Single mode finishes after 180 ms without a received edge. For a command with
longer inter-packet gaps, or multiple button presses, select sequence mode
with C. Press A, send the desired presses in order, then B to finish after the
last signal has ended. The pauses between presses are preserved. Recording is
limited to eight seconds after arming and 4,095 mark/space durations.

To capture a remote button combination, press that combination on the source
remote during recording. The badge captures the resulting IR, not the physical
button identities. Simultaneous badge combinations are reserved for the app
controls above.

## Storage and limitations

Each slot is a JSON file at `/ir-remote/NN.json` on the badge's writable root.
The files contain `carrier` in Hz and an odd-length `timings` list in
microseconds, alternating mark, space, and ending with a mark. Validation and
temporary-file replacement preserve an existing slot if learning fails.
Normal deployment does not overwrite these files. A factory flash erases them,
so take a full backup or copy `/ir-remote/` over serial first.

The demodulating receiver measures the envelope, not the original carrier.
The user's AC trial has not succeeded. The exact emitter location, captured
signal completeness, and physical transmission still need verification. A
"Sent" message confirms software playback, not an AC response or optical output.
38 kHz is the default assumption. If a saved signal does not work, select the
appropriate carrier and relearn it. Range and compatibility require a real AC
test. No Kenstar compatibility claim follows from passing software checks.

Avoid direct sunlight, start nearby, and try another angle if nothing arrives.
If a long signal fails, use sequence mode. An overflowing or incomplete capture
is rejected. The badge uses its firmware-defined `board.IR_RX` and `board.IR_TX`,
verified as GPIO21 and GPIO20 on the tested 2025 device, with PIO state machines
0 and 1. Do not run Quest or another IR consumer at the same time.

## References

### Mi Remote database research

[ysard/mi_remote_database](https://github.com/ysard/mi_remote_database) has a
published `v2.1` dump dated May 21, 2024. Its `3_AC/Kenwood_85.json` contains six
profiles: `kk_3_85_2807`, `kk_3_85_77`, `kk_3_85_11272`, `kk_3_85_11797`,
`kk_3_85_3200`, and `kk_3_85_3203`. No Kenstar brand file appeared in that dump.
The carrier frequencies are 38 kHz, except `11272` at 37.9 kHz.

These profiles contain state templates and field mappings; four also contain
embedded Lua state/checksum rules. They are not simple raw pulse downloads.
The project's README notes that AC patterns are not fully reversed. The
working Mi Remote profile still needs identification before a generated AC
remote can claim support for arbitrary settings.

Download and inspect locally without executing the embedded code:

```sh
gh release download v2.1 --repo ysard/mi_remote_database \
  --pattern database_dump.tar.xz --dir .badge-local
uv run --no-project tools/inspect_mi_remote.py .badge-local/database_dump.tar.xz
```

The upstream project also has a `db_dump` command for querying its API again.
This does not guarantee a newer or complete regional database. No fresh live
API dump has been verified here. The downloaded archive stays local, and the
badge app continues to learn known-working signals.

- [IRremoteESP8266 supported protocols](https://github.com/crankyoldgit/IRremoteESP8266/blob/master/SupportedProtocols.md)
- [AC protocol capture guidance](https://github.com/crankyoldgit/IRremoteESP8266/wiki/Adding-support-for-a-new-AC-protocol)
- [MicroPython PIO reference](https://docs.micropython.org/en/latest/library/rp2.html)

The app is an original implementation using MonaOS's bundled Pimoroni
`aye_arr.pulse.send.PulseSender` for carrier generation. It does not bundle or
port IRremoteESP8266. Offline checks run with
`uv run --no-project tools/test_ir_remote.py`.
