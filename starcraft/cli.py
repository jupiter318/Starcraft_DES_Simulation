from __future__ import annotations

import argparse

from .simulation import find_best_order


def main() -> None:
    parser = argparse.ArgumentParser(description="Starcraft build order search")
    parser.add_argument('marines', type=int, help='number of marines to produce')
    args = parser.parse_args()
    find_best_order(args.marines)


if __name__ == '__main__':
    main()
