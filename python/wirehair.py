#!/usr/bin/env python3

import whirehair as _whirehair


for _name in _whirehair.__all__:
    globals()[_name] = getattr(_whirehair, _name)


if __name__ == "__main__":
    raise SystemExit(_whirehair.main())
