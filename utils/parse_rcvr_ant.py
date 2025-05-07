import re

with open('data/rcvr_ant.tab', 'r') as f:
    txt = f.read()

lines = re.findall(
    r'\|\sX{20}\s\|\s{55}\|\n\+-{22}\+-{55}\+\n((?:.|\n)*?)\+\n', txt)

for line in '\n'.join(lines).splitlines():
    item = line[2:22].rstrip(' -')
    if item:
        print(item)
