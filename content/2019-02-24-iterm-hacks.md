---
layout: post
title: iTerm Profiles
date: 2019-02-24
comments: true
---
## Hacking on iTerm 2

I wanted a small weekend project to hack on today, so I decided to hack a little on iTerm. First, I wanted to make it easier to switch between light and dark profiles. Switching profiles in iTerm requires a bunch of clicks, and I hate using my mouse.

<!-- more -->

So, I set out to build a few features:
- A bash function to switch between light and dark profiles
- Automatically select a specific profile when I connect to a remote server
- Randomly select a profile when opening a new tab (to more visual context for different mental context)

Granted - this isn't for everyone. Many people find backgrounds in their terminal to be distracting, and use their prompt to make these distinctions. But, I love having background images and the more visual cues, the better.


## Control iTerm Profiles from bash

iTerm has a special escape sequence it can catch to switch profiles:

```
echo -e "\033]50;SetProfile=MyAwesomeProfile\a"
```

iTerm also sets an environmental variable, `ITERM_PROFILE`, but running the above doesn't update it. So here is a simple bash function to change the current iTerm session's profile:

```
function iterm-profile() {
  echo -e "\033]50;SetProfile=$1\a"
  ITERM_PROFILE=$1
}
```

## Switching between light and dark

iTerm doesn't have an easy way to change settings of a profile, so to accomplish this I just created a light and dark version of all my profiles, i.e. `Dark-1` and `Light-1`. Assuming that the current profile has a respective opposite version, here's a function to switch between the two:

```
function flip-iterm-profile() {
  iterm-profile $(
  python -c '
import sys
dl, profile = sys.argv[1].split("-")
dl = {"Dark": "Light", "Light": "Dark"}[dl]
print(dl+"-"+profile)
  ' $ITERM_PROFILE)
}
```

## Change Profile for remote connection

I use [Eternal Terminal](https://mistertea.github.io/EternalTerminal/) for my remote connections. It keeps your connection alive, between network changes (similar to [Mosh](https://mosh.org/)), but also allows for port forwarding, which I use with sshx in my emacs session. One downside of Eternal Terminal, though, is that it won't read `LocalForward` settings from your ssh config. I also have it connect directly to my already running tmux session on my remote session. This ends up in a fairly complicated connection command, which I had aliased:

```
alias up='et -c="tmux a" -x -t="10022:22" devserver'
```

To add in the profile changing, I created two profiles, `Dark-Devserver` and `Light-Devserver`, and I changed the alias to a function:

```
function up() {
  PREVIOUS_PROFILE=$ITERM_PROFILE
  iterm-profile $(
  python -c '
import sys
dl, profile = sys.argv[1].split("-")
print(dl+"-Devserver")
  ' $ITERM_PROFILE)
  et -c="tmux a" -x -t="10022:22" devserver.et:8080
  iterm-profile $PREVIOUS_PROFILE
}
```

The `et` command could easily be swapped for a `ssh` or `mosh` command. The only extra piece here is that I maintain the dark/light setting from the existing profile.

This can also be accomplished with [Automatic Profile Switching](https://iterm2.com/documentation-automatic-profile-switching.html) in iTerm, but it wouldn't maintain the light/dark setting. You could also include similar code in your bash profile on the server, but that was complicated by my connecting directly to a running tmux session.

## Random Profile on Launch

This one only works because I created six pairs of profiles named `Light-<n>` and `Dark-<n>`. I then (somewhat arbitrarily) decided to set the profile to `Light` between 6am and 3pm, and `Dark` otherwise. Additionally, a random choice doesn't guarantee a unique profile, but it's simple enough to call the function again if you're unsatisfied.

```
function random-iterm-profile() {
  # pick random profile (of the 6)
  # Light between 6am and 3pm, otherwise Dark
  iterm-profile $(
  python -c '
import random
from datetime import datetime
dl = "Light" if 6 < datetime.now().hour < 15 else "Dark"
profile = str(random.randint(1,6))
print(dl+"-"+profile)')
}
```

Here's what it looks like calling it a few times:

<video width="100%" height="100%" loop autoplay muted>
<source src="/images/iterm.mp4" type="video/mp4; codecs=&quot;avc1.42E01E, mp4a.40.2&quot;">
</video>

## Wrap it all up

If you want to copy and paste directly in your bash profile, here you go. You'll need the following iTerm profiles defined:

- Light-1
- Light-2
- Light-3
- Light-4
- Light-5
- Light-6
- Light-Devserver
- Dark-1
- Dark-2
- Dark-3
- Dark-4
- Dark-5
- Dark-6
- Dark-Devserver

and you'll need to change the `et` command to something that makes sense for you.

```
function up() {
  PREVIOUS_PROFILE=$ITERM_PROFILE
  iterm-profile $(
  python -c '
import sys
dl, profile = sys.argv[1].split("-")
print(dl+"-Devserver")
  ' $ITERM_PROFILE)
  et -c="tmux a" -x -t="10022:22" devserver
  iterm-profile $PREVIOUS_PROFILE
}

function iterm-profile() {
  echo -e "\033]50;SetProfile=$1\a"
  ITERM_PROFILE=$1
}

function flip-iterm-profile() {
  iterm-profile $(
  python -c '
import sys
dl, profile = sys.argv[1].split("-")
dl = {"Dark": "Light", "Light": "Dark"}[dl]
print(dl+"-"+profile)
  ' $ITERM_PROFILE)
}

function random-iterm-profile() {
  # pick random profile (of the 6)
  # Light between 6am and 3pm, otherwise Dark
  iterm-profile $(
  python -c '
import random
from datetime import datetime
dl = "Light" if 6 < datetime.now().hour < 15 else "Dark"
profile = str(random.randint(1,6))
print(dl+"-"+profile)')
}

random-iterm-profile
```
