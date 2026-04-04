#!/usr/bin/env python3
import sys

def main():
    current_key = None
    current_count = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        key, value = line.split("\t")
        value = int(value)

        if current_key == key:
            current_count += value
        else:
            if current_key is not None:
                print(f"{current_key}\t{current_count}")
            current_key = key
            current_count = value

    if current_key is not None:
        print(f"{current_key}\t{current_count}")

if __name__ == "__main__":
    main()