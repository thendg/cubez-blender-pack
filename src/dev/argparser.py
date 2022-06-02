from typing import Optional
import re


class Argparser:
    """
    An argument parse that can be used in place of Python's `argparse` module for static typing
    """

    OPT = r"^--(?=\w*)"

    opts: dict[str, str | bool] = {}

    def __init__(self, opts: list[str] = [], flags: list[str] = []) -> None:
        for opt in opts:
            self.opts[opt] = None
        for flag in flags:
            self.opts[flag] = False

    def parse(self, args: list[str]) -> None:
        i = 0
        while i < len(args):
            name = re.sub(Argparser.OPT, "", args[i])
            if name in self.opts.keys() and self.opts[name] == False:
                self.opts[name] = True
            elif name in self.opts.keys():
                self.opts[name] = args[i + 1]
                i += 1
            i += 1

    def get(self, opt: str) -> Optional[str | bool]:
        return self.opts.get(opt)
