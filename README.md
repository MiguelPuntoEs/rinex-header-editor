# RINEX Header Editor

Minimalistic drag-and-drop Python-based app to view and edit RINEX 3.0x and RINEX 4.0x headers.

Format descriptions:

- RINEX 2:
  - [RINEX 2](https://files.igs.org/pub/data/format/rinex2.txt)
  - [RINEX 2.10](https://files.igs.org/pub/data/format/rinex210.txt)
  - [RINEX 2.11](https://files.igs.org/pub/data/format/rinex211.txt)
- RINEX 3:
  - [RINEX 3.00](https://files.igs.org/pub/data/format/rinex300.pdf)
  - [RINEX 3.01](https://files.igs.org/pub/data/format/rinex301.pdf)
  - [RINEX 3.02](https://files.igs.org/pub/data/format/rinex302.pdf)
  - [RINEX 3.03](https://files.igs.org/pub/data/format/rinex303.pdf)
  - [RINEX 3.04](https://files.igs.org/pub/data/format/rinex304.pdf)
  - [RINEX 3.05](https://files.igs.org/pub/data/format/rinex305.pdf)
- RINEX 4:
  - [RINEX 4.00](https://files.igs.org/pub/data/format/rinex_4.00.pdf)
  - [RINEX 4.01](https://files.igs.org/pub/data/format/rinex_4.01.pdf)
  - [RINEX 4.02](https://files.igs.org/pub/data/format/rinex_4.02.pdf)

## Usage

In order to use the app, first install all necessary Python libraries with:

```console
pip install -r requirements.txt
```

Then, execute:

```console
python3 app.pyw
```

To view and edit a RINEX file headers, just drag and drop the file into the app window. To save changes into the file, just press "Write".

## Settings

All app settings are configured in the `settings.json` file using JSON format.

This file contains most commercial GNSS antennas and receivers.

In order to add new "favorite" coordinates, just edit the corresponding section of the `settings.json` file (ECEF coordinates):

```json
"coordinates": {
    "SMPL": [4198945, 174747, 4781887]
  }
```

## Antenna and receiver information source

- Antenna information is extracted from NOAA Antenna Calibrations, [NGS20 Absolute](https://geodesy.noaa.gov/ANTCAL/).
- Receiver information is extracted from [IGS rcvr_ant.tab](https://files.igs.org/pub/station/general/rcvr_ant.tab).

If you want to add your own list of antennas and receivers, you can use following code to extract receivers from the `rcvr_ant.tab`file:

```python
import re

with open('data/rcvr_ant.tab', 'r') as f:
  txt = f.read()

  lines = re.findall(
  r'\|\sX{20}\s\|\s{55}\|\n\+-{22}\+-{55}\+\n((?:.|\n)*?)\+\n', txt)

  for line in '\n'.join(lines).splitlines():
    item = line[2:22].rstrip(' -')
    if item:
      print(item)

  f.close()
```
