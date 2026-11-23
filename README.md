# Ember — a MustardOS theme

A grid-first theme for MustardOS (muOS) on 640×480 handhelds such as the Anbernic RG40XXV and RG40XXH.

- **Main menu:** OneTwo-style layout, with Explore, Collections and History as large tiles on top and Apps, Info, Settings, Restart and Shutdown along the bottom.
- **Games, collections and history:** a 3×2 grid of square box art cards. The selected game's title is shown in the header.
- **Apps:** a 4×3 grid with line-art icons for the bundled apps plus Scrappy and Artie.
- **Accent colours:** Amber (default), Tangerine, Rose, Lavender, Sky, Teal, Mint and Lime, selectable under *Customisation → Alternative Theme*.

## Install

Download `Ember.muxthm` from the latest release (or from the build artifact of any CI run), copy it to `ARCHIVE` on the SD card, install it with Archive Manager, then select it in the theme picker.

Box art should be **184×184** (fit inside, keep aspect ratio).

## Build

```sh
pip install -r requirements.txt
python build_theme.py      # writes dist/Ember.muxthm
```

CI builds the package on every push and pull request. Pushing a tag such as `v1.0.0` publishes a GitHub release with the package attached.

## Layout

| Path | What it is |
|---|---|
| `build_theme.py` | Palette, scheme settings, main-menu tiles, accent alternatives and packaging |
| `app_icons.py` | Drawn app icons (file name = the app's `# ICON:` value) |
| `assets/catalogue/` | Console/folder artwork, collection art and extra app icons copied into the theme |
| `assets/image/` | Full-screen images copied into `640x480/image/`: `shutdown.png`, `reboot.png`, `bootlogo.png`, `charge.png`, `load.png` (optionally in a language subfolder such as `English/`). Each is centred over the theme background colour. |
| `fonts/` | Poppins (SIL Open Font License 1.1) |

To change the palette, edit the constants at the top of `build_theme.py`. To add an accent, add it to `ACCENTS`.

## Credits

Main menu layout inspired by OneTwo by bulkh. Font: Poppins by Indian Type Foundry, SIL Open Font License 1.1 (`fonts/OFL.txt`).
