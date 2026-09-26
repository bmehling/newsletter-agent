# Reliable early-morning runs on macOS

Research for [#4](https://github.com/bmehling/newsletter-agent/issues/4), part of the map [#1](https://github.com/bmehling/newsletter-agent/issues/1).
Date: 2026-09-26. Checked on macOS 26.6.2 (Apple M2 Max laptop). Running in the cloud is out of scope.

## Question

How can the agent run at about 5:30 AM on the Operator's Mac so the Episode is in the Feed before the Operator leaves (reference: about 6:30 AM)?

## Short answer

1. launchd does not wake the Mac. A `StartCalendarInterval` job that falls due during sleep runs at the **next wake**, and missed firings are coalesced into one run. If the Mac is off, the run is skipped. So the 5:30 run is only reliable if something makes sure the Mac is awake at 5:30.
2. The only built-in way to wake a sleeping Mac at a set time is `pmset`. Changing the schedule **needs root** (`sudo`), but only once at setup. The schedule persists in a system file. You can have only **one** repeating wake/power-on event.
3. A scheduled wake is not enough on its own. Power-management assertions (what `caffeinate` uses) that stop idle sleep **have no effect during a dark wake**, and on battery they are only suggestions. A laptop with the lid closed and no external display goes back to sleep. Plan for **AC power and lid open** (or closed-display mode with an external display).
4. The simplest reliable setup for a laptop: plugged in overnight, lid open, and "Prevent automatic sleeping on power adapter when the display is off" turned on. The Mac never sleeps, so launchd fires on time. Add a `pmset` wake as a second layer.
5. Do not assume the network is up when the job starts. Retry with backoff. Record the scheduled time, the start time, and the finish time, so the agent can report a late run (launchd ran it at the next wake) or a missed day.

## Findings

### 1. launchd and `StartCalendarInterval` when the Mac sleeps

| Situation at the scheduled time | What launchd does | Source |
|---|---|---|
| Mac awake | Starts the job on time. | [launchd.plist(5)][lp5] |
| Mac asleep | Starts the job "the next time the computer wakes up". | [launchd.plist(5)][lp5], [Scheduling Timed Jobs][stj] |
| Several firings missed during one sleep | "Those events will be coalesced into one event upon wake from sleep." | [launchd.plist(5)][lp5] |
| Mac powered off | Job "does not execute until the next designated time occurs". | [Scheduling Timed Jobs][stj] |
| `StartInterval` (not calendar) during sleep | That interval "will be missed". | [launchd.plist(5)][lp5] |

Key quote from launchd.plist(5): "Unlike cron which skips job invocations when the computer is asleep, launchd will start the job the next time the computer wakes up. If multiple intervals transpire before the computer is woken, those events will be coalesced into one event upon wake from sleep."

What this means for the agent:

- If the Mac sleeps through 5:30 and the Operator opens the lid at 7:00, the Episode is built at 7:00. That is **late**, not missed. The agent must detect this (see section 6).
- If the Mac sleeps from Friday to Monday, the Friday-to-Monday firings coalesce into **one** run. The coverage window in #1 (Newsletters since the previous Episode's cutoff, roll forward) already handles this. The agent must not assume "one run = one day".
- launchd has **no** key that wakes the Mac. Waking is the job of `pmset` (section 2).

Other launchd facts that matter:

- **LaunchAgent needs a logged-in user.** "A user agent ... executes only while that user is logged in" ([Creating Launch Daemons and Agents][cld]). After a restart, the job does not run until the Operator logs in. With FileVault on, "you must log in every time your Mac starts up, and no account is permitted to log in automatically" ([Schedule your Mac to turn on or off in Terminal][sched]). So a scheduled **power-on** does not help a FileVault Mac. Only a **wake** from sleep helps.
- **Default resource limits.** If `ProcessType` is not set, "the system will apply light resource limits to the job, throttling its CPU usage and I/O bandwidth" ([launchd.plist(5)][lp5]). Consider `ProcessType` = `Standard` (same as unset) or `Interactive` if the Episode build runs too slowly. Test before you change it.
- **Timer coalescing** (`LegacyTimers`) is about timers the job creates while it runs, not about when launchd starts the job ([launchd.plist(5)][lp5]). Not relevant here.

### 2. Scheduled wake with `pmset`

From [pmset(1)][pmset] (local man page, macOS 26.6.2):

- `pmset repeat type weekdays time`, where `type` is one of `sleep, wake, poweron, shutdown, wakeorpoweron` and `weekdays` is a subset of `MTWRFSU`.
- "You may only have one pair of repeating events scheduled - a 'power on' event and a 'power off' event." If the Operator already has a repeating wake, the agent's wake replaces it. Check `pmset -g sched` first.
- `pmset schedule wake "MM/dd/yy HH:mm:ss"` adds a one-time event.
- "pmset must be run as root in order to modify any settings." Apple's own example uses `sudo pmset repeat wake M 8:00:00` ([Schedule your Mac to turn on or off in Terminal][sched]).
- Scheduled events are stored in `/Library/Preferences/SystemConfiguration/com.apple.AutoWake.plist` ([pmset(1)][pmset]). They are per-system, not per-user, and survive a restart.
- Reading the schedule (`pmset -g sched`) does not need root.

**Permissions.** A repeating event needs `sudo` only once, at setup. For example:

```sh
pmset -g sched                                  # check for an existing repeat event
sudo pmset repeat wake MTWRF 05:25:00           # wake 5 min before the job
```

Use `wake`, not `wakeorpoweron`, on a FileVault Mac (power-on stops at the login window, so the LaunchAgent cannot run). If Episode days change, setup must re-run `sudo pmset repeat ...`. Do **not** give the agent passwordless `sudo` for `pmset` to schedule one-time wakes each night. That adds a privilege path for little gain.

Schedule the wake a few minutes **before** the launchd time. The launchd job then fires while the Mac is already awake, not at an uncertain moment during the wake.

### 3. Dark wake, Power Nap, and why a scheduled wake may not hold

Power Nap "lets some Mac computers stay up to date even while they're sleeping". On battery it checks Mail, Calendar, and iCloud. On a power adapter it also downloads software updates and runs Time Machine backups ([What is Power Nap on Mac?][pn]). Apple lists only its own tasks. Apple does not document that Power Nap runs third-party launchd jobs, so the agent cannot count on Power Nap.

The system's own wake log shows how short these wakes are. On the test Mac (battery, lid closed) `pmset -g log` shows `DarkWake` entries lasting 2 to 45 seconds, then `Entering Sleep state due to 'Maintenance Sleep'`. An Episode build (LLM calls plus TTS) takes minutes, so a dark wake is too short.

Assertions do not keep a dark wake alive. From the IOKit header `IOPMLib.h` ([IOKit IOPMLib][iopm]):

- `kIOPMAssertPreventUserIdleSystemSleep` (what `caffeinate -i` takes): "This assertion has no effect if the system is in Dark Wake." It also says "The system may still sleep for lid close, Apple menu, low battery, or other sleep reasons."
- `kIOPMAssertNetworkClientActive`: "keeps the system awake in dark or full wake, as long as the system is on AC power. On battery, this assertion can prevent system from going into idle sleep. IOKit power assertions are suggestions and OS X may not honor them under battery, thermal, or user circumstances."
- `kIOPMAssertionTypePreventSystemSleep` is deprecated and "not supported in any OS X releases".

From [caffeinate(8)][caff]:

- `-s` "prevent the system from sleeping. This assertion is valid only when system is running on AC power."
- `-u` "declare that user is active. If the display is off, this option turns the display on". This maps to `IOPMAssertionDeclareUserActivity`, which "causes the display to power on" and needs no special privileges ([IOPMAssertionDeclareUserActivity][iopmdua]).

What this means:

- At the start of `run_agent.sh`, call `caffeinate -u -t 5` to promote the wake to a full (display-on) wake. Then run the agent under `caffeinate -i -s` so it holds the Mac awake for the length of the run. `-s` only works on AC.
- **Unverified:** whether a `pmset` scheduled wake on an Apple silicon laptop is a full wake or a dark wake, and whether it stays up with the lid closed. Apple does not document this. Community reports say a closed-lid MacBook goes back to sleep unless something holds it (for example, an external display) ([Apple Community thread][ac1]). Treat the lid-closed case as **not supported** until tested (see "Test plan").

### 4. Battery vs AC, and the lid

| Setup | Expected result | Why |
|---|---|---|
| AC, lid open, "Prevent automatic sleeping on power adapter when the display is off" on | **Reliable.** Mac does not sleep; job fires on time. | Setting is in System Settings > Battery > Options ([Set sleep and wake settings][sw]). Same as `pmset -c sleep 0` ([pmset(1)][pmset]). |
| AC, lid open, Mac sleeps, `pmset` wake at 5:25 | Likely reliable. `caffeinate -u` gives a full wake; `-s` holds it on AC. | [caffeinate(8)][caff], [IOPMLib][iopm] |
| AC, lid closed, external display + keyboard/mouse (closed-display mode) | Likely reliable; behaves like a desktop. | Apple says you can close the lid and keep using the Mac with a connected display and accessories ([Connect an external display to MacBook Pro][ext]). |
| AC, lid closed, no external display | **Not reliable.** Closing the lid is a sleep reason that assertions do not override. | [IOPMLib][iopm] |
| Battery, any lid state | **Not reliable.** Assertions are "suggestions" on battery; `-s` does not apply; Low Power Mode may be on. | [IOPMLib][iopm], [caffeinate(8)][caff] |
| Mac shut down | **Missed.** launchd skips it. | [Scheduling Timed Jobs][stj] |

Note: on the test Mac, `pmset -g custom` already shows `sleep 0` on AC (never idle-sleep) and `lowpowermode 1` on battery. Each Operator's settings differ, so setup should check and report them.

### 5. Network after wake

Apple: "If your daemon depends on the network being available, this cannot be handled with dependencies because network interfaces can come and go at any time in OS X. To solve this problem, you should use the network reachability functionality or the dynamic store functionality in the System Configuration framework" ([Creating Launch Daemons and Agents][cld]).

Practical steps for a shell/Python job:

- Before the first API call, wait for reachability. `scutil -r <host>` reports "Reachable" or "Not Reachable" from the current network configuration ([scutil(8)][scutil]). Reachable means a route exists, not that the request will succeed.
- So also retry the first real request (Gmail API) with backoff, for example up to 5 minutes. Wi-Fi can take several seconds to join after a wake.
- In Swift, the modern API is [`NWPathMonitor`][nwpm]. Not needed for this Python agent.

### 6. Detect and report a missed or late run

launchd gives little help. `launchctl print gui/<uid>/<label>` shows the service's state and "last exit status" ([launchctl(1)][lctl]). It does not record whether a firing was late or coalesced. The agent must record this itself.

Proposed approach:

1. **Run record.** At start and finish, the agent writes the scheduled time, the actual start time, the finish time, the power source (`pmset -g batt`), and the result to a small state file (or Notion). Compare start time to the scheduled time. If the start is more than N minutes late, or the finish is after the leave time, mark the Episode **late**.
2. **Gap check.** On every run, compare the last successful Episode date with the expected Episode days. Any expected day with no Episode is **missed** (Mac off, or asleep all day). Coalescing means the next run sees the gap.
3. **Report.** Put late or missed status where the Operator will see it: in the Episode show notes or the Notion daily page, plus a macOS notification (`osascript -e 'display notification ...'`) or an email through the existing Gmail client. Which channel is a config choice (see #1 "Config surface").
4. **Diagnostics.** When a run is late, save the relevant part of `pmset -g log` (wake and sleep lines, wake reason) to the log. This shows whether the scheduled wake fired, and whether the Mac was on battery or had the lid closed.
5. **Preflight check (setup and each run).** Warn if `pmset -g sched` has no matching wake, if on battery at run time, or if AC `sleep` is not 0 and no wake is scheduled.

## Recommendation

1. Move `StartCalendarInterval` to 5:30 on the Episode days (setting-driven).
2. Setup script: show the current `pmset -g sched`, then run `sudo pmset repeat wake <days> 05:25:00` with Operator consent. Warn that this replaces any existing repeating wake.
3. Tell the Operator the supported setup: **plugged in, lid open** (or closed-display mode), and "Prevent automatic sleeping on power adapter when the display is off" on.
4. `run_agent.sh`: `caffeinate -u -t 5`, then `caffeinate -i -s <python> main.py`. Add a network wait-and-retry step before the first API call.
5. Add the run record, gap check, and late/missed report from section 6.

## Test plan (open question: lid-closed and dark-wake behavior)

Apple does not document these. Test on the Operator's Mac before you promise them:

1. Schedule a one-time wake 3 minutes ahead: `sudo pmset schedule wake "MM/dd/yy HH:mm:ss"` and a launchd job 1 minute after it.
2. Sleep the Mac (`pmset sleepnow`) in each state: AC lid open, AC lid closed, battery lid open, battery lid closed.
3. Afterwards, check `pmset -g log | grep -E "Wake|DarkWake|Sleep"` and the job's run record. Did the wake fire? Full or dark? Did the job finish before the Mac slept again?
4. Remove leftovers: `sudo pmset schedule cancelall`.

## Sources

- [lp5]: launchd.plist(5), local man page, macOS 26.6.2 (`man launchd.plist`). Web copy: https://keith.github.io/xcode-man-pages/launchd.plist.5.html
- [pmset]: pmset(1), local man page (`man pmset`). Web copy: https://keith.github.io/xcode-man-pages/pmset.1.html
- [caff]: caffeinate(8), local man page (`man caffeinate`). Web copy: https://keith.github.io/xcode-man-pages/caffeinate.8.html
- [scutil]: scutil(8), local man page (`man scutil`). Web copy: https://keith.github.io/xcode-man-pages/scutil.8.html
- [lctl]: launchctl(1), local man page (`man launchctl`). Web copy: https://keith.github.io/xcode-man-pages/launchctl.1.html
- [iopm]: IOKit `IOPMLib.h`, macOS SDK (`/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/IOKit.framework/Headers/pwr_mgt/IOPMLib.h`). Apple docs: https://developer.apple.com/documentation/iokit/iopmlib_h
- [iopmdua]: IOPMAssertionDeclareUserActivity: https://developer.apple.com/documentation/iokit/1557127-iopmassertiondeclareuseractivity
- [stj]: Apple, Daemons and Services Programming Guide, "Scheduling Timed Jobs": https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html
- [cld]: Apple, "Creating Launch Daemons and Agents": https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
- [sched]: Apple Support, "Schedule your Mac to turn on or off in Terminal": https://support.apple.com/guide/mac-help/schedule-your-mac-to-turn-on-or-off-mchl40376151/mac
- [sw]: Apple Support, "Set sleep and wake settings for your Mac": https://support.apple.com/guide/mac-help/set-sleep-and-wake-settings-mchle41a6ccd/26/mac/26
- [pn]: Apple Support, "What is Power Nap on Mac?": https://support.apple.com/en-gb/guide/mac-help/mh40773/14.0/mac/14.0
- [ext]: Apple Support, "Connect an external display to MacBook Pro": https://support.apple.com/guide/macbook-pro/connect-an-external-display-apd8cdd74f57/mac
- [nwpm]: Apple, NWPathMonitor: https://developer.apple.com/documentation/network/nwpathmonitor
- [ac1]: Apple Community (secondary, user reports only), "MacBook Pro waking while lid is closed": https://discussions.apple.com/thread/254563510

[lp5]: https://keith.github.io/xcode-man-pages/launchd.plist.5.html
[pmset]: https://keith.github.io/xcode-man-pages/pmset.1.html
[caff]: https://keith.github.io/xcode-man-pages/caffeinate.8.html
[scutil]: https://keith.github.io/xcode-man-pages/scutil.8.html
[lctl]: https://keith.github.io/xcode-man-pages/launchctl.1.html
[iopm]: https://developer.apple.com/documentation/iokit/iopmlib_h
[iopmdua]: https://developer.apple.com/documentation/iokit/1557127-iopmassertiondeclareuseractivity
[stj]: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html
[cld]: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
[sched]: https://support.apple.com/guide/mac-help/schedule-your-mac-to-turn-on-or-off-mchl40376151/mac
[sw]: https://support.apple.com/guide/mac-help/set-sleep-and-wake-settings-mchle41a6ccd/26/mac/26
[pn]: https://support.apple.com/en-gb/guide/mac-help/mh40773/14.0/mac/14.0
[ext]: https://support.apple.com/guide/macbook-pro/connect-an-external-display-apd8cdd74f57/mac
[nwpm]: https://developer.apple.com/documentation/network/nwpathmonitor
[ac1]: https://discussions.apple.com/thread/254563510
