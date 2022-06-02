from typing import Optional
import re


class Argparser:
    """
    An argument parser that can be used in place of Python's `argparse` module for static typing.
    The parser detects options and flags as strings prefixed by `--` for example `--option`. The value for an
    option is taken as the next value in the arguement list.
    """

    OPT = r"^--(?=\w*)"

    opts: dict[str, str] = {}

    def __init__(self, opts: list[str] = [], flags: list[str] = []) -> None:
        """
        Initialise the parser.

        :param opts: A list of names for the options to register with the parser.
        :param opts: A list of names for the flags to register with the parser.
        """
        for opt in opts:
            self.opts[opt] = None
        for flag in flags:
            self.opts[flag] = str(False)

    def parse(self, args: list[str]) -> None:
        """
        Parse the given argument list.
        
        :param args: The list of arguments to parse.
        """
        i = 0
        while i < len(args):
            name = re.sub(Argparser.OPT, "", args[i])
            if name in self.opts.keys() and self.opts[name] == False:
                self.opts[name] = str(True)
            elif name in self.opts.keys():
                self.opts[name] = args[i + 1]
                i += 1
            i += 1

    def get(self, opt: str) -> Optional[str]:
        """
        Get the value associated with a registered option.

        :param opt: The name of the option.
        """
        return self.opts.get(opt)

    def getf(self, flag: str) -> bool:
        """
        Get a boolean representing the value associated with a registered flag.
        :param flag: The name of the flag.
        """
        return bool(self.opts.get(flag))
