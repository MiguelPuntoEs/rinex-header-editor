from dataclasses import dataclass
import parse


@dataclass
class RINEX_Header:
    marker_name: str = ''
    marker_type: str = ''
    receiver_sn: str = ''
    receiver_type: str = ''
    receiver_version: str = ''
    antenna_sn: str = ''
    antenna_type: str = ''
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0


def format_approx_position(x: float, y: float, z: float) -> str:
    return f'{x:14.4f}{y:14.4f}{z:14.4f}                  APPROX POSITION XYZ\n'


def get_antenna_IGS_code(antenna: str) -> str:
    antenna = ' '.join(antenna.split())
    parts = antenna.split(' ')
    if len(parts) == 1:
        antenna_type = f'{parts[0]:20}'
    else:
        antenna_type = parts[0] + \
            (' ' * (20 - len(parts[0]) - len(parts[1]))) + parts[1]
    return antenna_type


def parse_header(header: list[str]) -> RINEX_Header:
    rinex_header = RINEX_Header()
    for line in header:
        if line[60:] == 'REC # / TYPE / VERS\n':
            fmt = '{:20}{:20}{:20}REC # / TYPE / VERS\n'
            receiver_sn, receiver_type, receiver_version = parse.parse(
                fmt, line)

            rinex_header.receiver_sn = receiver_sn.rstrip()
            rinex_header.receiver_type = receiver_type.rstrip()
            rinex_header.receiver_version = receiver_version.rstrip()
        elif line[60:] == 'ANT # / TYPE\n':
            fmt = '{:20}{:20}                    ANT # / TYPE\n'
            antenna_sn, antenna_type = parse.parse(fmt, line)

            rinex_header.antenna_sn = antenna_sn.rstrip()
            rinex_header.antenna_type = antenna_type.rstrip()
        elif line[60:] == 'APPROX POSITION XYZ\n':
            fmt = '{:14.4f}{:14.4f}{:14.4f}                  APPROX POSITION XYZ\n'
            rinex_header.position_x, rinex_header.position_y, rinex_header.position_z = parse.parse(
                fmt, line)
        elif line[60:] == 'MARKER NAME\n':
            fmt = '{:60}MARKER NAME\n'
            marker_name, *_ = parse.parse(fmt, line)
            rinex_header.marker_name = marker_name.rstrip()
        elif line[60:] == 'MARKER TYPE\n':
            fmt = '{:60}MARKER TYPE\n'
            marker_type, *_ = parse.parse(fmt, line)
            rinex_header.marker_type = marker_type.rstrip()

    return rinex_header


def parse_RINEX(lines: list[str]) -> tuple[list[str], list[str]]:
    header_complete: bool = False
    header: list[str] = []
    body: list[str] = []

    for line in lines:
        line = line.rstrip() + '\n'

        if not header_complete:
            header.append(line)
            if line[60:] == 'END OF HEADER\n':
                header_complete = True
        else:
            body.append(line)

    return header, body


def modify_header(header: list[str], rinex_header: RINEX_Header):
    for idx, line in enumerate(header):
        if line[60:] == 'REC # / TYPE / VERS\n':
            header[idx] = f'{rinex_header.receiver_sn:20}{rinex_header.receiver_type:20}' \
                f'{rinex_header.receiver_version:20}REC # / TYPE / VERS\n'
        elif line[60:] == 'ANT # / TYPE\n':
            antenna_type = get_antenna_IGS_code(rinex_header.antenna_type)

            header[idx] = f'{rinex_header.antenna_sn:<20}{antenna_type:20}                    ANT # / ' \
                f'TYPE\n'
        elif line[60:] == 'APPROX POSITION XYZ\n':
            header[idx] = f'{rinex_header.position_x:14.4f}{rinex_header.position_y:14.4f}' \
                f'{rinex_header.position_z:14.4f}                  APPROX POSITION XYZ\n'
        # elif line[60:] == 'RINEX VERSION / TYPE\n':
        #     header_[idx] = '     3.02           OBSERVATION DATA    M: MIXED            RINEX VERSION / TYPE\n'
        elif line[60:] == 'MARKER NAME\n':
            header[idx] = f'{rinex_header.marker_name:60}MARKER NAME\n'
        elif line[60:] == 'MARKER TYPE\n':
            header[idx] = f'{rinex_header.marker_type:60}MARKER TYPE\n'
        elif line[60:] == 'PRN / # OF OBS\n':
            header[idx] = ''
        elif line[60:] == '# OF SATELLITES\n' in line:
            header[idx] = ''
