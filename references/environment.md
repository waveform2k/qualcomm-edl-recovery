# Environment and edl gotchas

## Installing edl

bkerler/edl (github.com/bkerler/edl) provides the `edl` command and the
`edlclient` Python package the scripts import.

- pip: `pip install git+https://github.com/bkerler/edl`
- nixpkgs: `edl` is marked unfree, so build it with
  `NIXPKGS_ALLOW_UNFREE=1 nix build --impure --no-link --print-out-paths nixpkgs#edl`.

The scripts import `edlclient` directly. When it sits outside the interpreter's
path, set `EDL_SITE_PACKAGES` to its site-packages directories. For the nixpkgs
wrapper, take the directories and the matching interpreter from the wrapped
entry point:

```sh
W="$(dirname "$(readlink -f "$(command -v edl)")")/.edl-wrapped"
export EDL_SITE_PACKAGES=$(grep -o "\['/nix/store[^]]*\]" "$W" | head -1 | tr -d "[]' " | tr ',' ':')
PY=$(head -1 "$W" | cut -c3-)
$PY -I scripts/edl_guarded.py ...
```

`certs.py` needs the `openssl` command. The other offline scripts need only
Python 3.9+.

## Running

- USB access to the phone needs root: run edl and the edl-driving scripts
  through `pkexec` or `sudo`. Root keeps its own environment, so pass
  `EDL_SITE_PACKAGES` inside the command (`pkexec env EDL_SITE_PACKAGES=... $PY -I ...`).
- Run from an empty directory: `edl memorydump` deletes and recreates
  `./memory`, and edl drops `edl_config.json` and logs where it runs.
- Wrap device commands in `timeout`, and put the timeout *inside* the root
  command: a user-level `timeout` cannot kill a root process.

## edl behaviour worth knowing

| behaviour | consequence |
|---|---|
| a plain `edl` run on a 900e device dumps every memory region | gigabytes of RAM to disk; pass `--partitions=` or use `crashdump_list.py` |
| `memorydump` resets the device after dumping | the phone reboots into its crash loop again |
| a failed sahara handshake makes edl send a reset (`edl.py`, "Error on sahara handshake, resetting.") | a phone in EDL falls out of EDL; `edl_guarded.py` suppresses it |
| a sahara session left open (`crashdump_list.py`, an interrupted run) | the next run waits on "Waiting for the device" until the cable is replugged |
| `edl reset` rejects `--memory` and prints its usage | the phone silently stays in EDL |
| once a firehose loader runs, later edl calls connect straight to it | no re-upload, and the loader guard has nothing to check |
| a loader picked by auto-detection may be "the first loader for this hwid" | always pass `--loader` explicitly, through the guard |

## Untrusted downloads

Put each downloaded package or archive in its own new directory, and run
nothing from inside it. Read it with the scripts in `scripts/`, passing paths
as arguments.
