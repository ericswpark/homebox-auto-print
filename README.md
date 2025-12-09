# homebox-auto-print

Small script to automatically print labels downloaded into the specified directory
(usually `~/Downloads/`)


## Requirements

- Imagemagick
- ptouch-print

## Installation

```
pacman -S imagemagick
yay -S ptouch-print

virtualenv .venv
. .venv/bin/activate
pip install -r requirements.txt
```


## Usage

```
python main.py ~/Downloads
```

All flags:

```
python main.py ~/Downloads --recursive --font "Noto-Sans-Bold" --remove
```
