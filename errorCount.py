#!/usr/bin/env python3
import re, os
from collections import Counter

logpath = os.path.expanduser('/Users/raymond/Downloads/Terminal Saved Output.txt')
patterns = {
    'appledouble': re.compile(r'/\._'),
    'spotlight':   re.compile(r'\.Spotlight-V100'),
    'other':       re.compile(r'.*'),
}
counts = Counter()
others = set()

with open(logpath, 'r', errors='ignore') as f:
    for line in f:
        if 'Operation not permitted' not in line:
            continue
        for name, patt in patterns.items():
            if patt.search(line):
                counts[name] += 1
                if name == 'other':
                    # extract the filename between quotes
                    m = re.search(r'"([^"]+)"', line)
                    if m:
                        others.add(m.group(1))
                break

print("Other rsync failures:")
for path in sorted(others):
    print(" ", path)