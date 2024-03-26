# formation-count

A hacky script to help count formation points in skydive videos

## Install

1. Install `ffmpeg`
2. `poetry install`

## Usage

`poetry run formation-count --help`

Use keybindings to mark points:

| Key | Action |
|-----|--------|
| `s` | Start of a sequence (and a point) |
| `p` | Mark a sequence point |
| `d` | Delete the last point |
| `q` | Quit marking points |

Once the video runs out, or a `q` is received, the program will calculate the highest number of points in the provided timeframe (default is 35 seconds) and extract a new video with the found timeframe
