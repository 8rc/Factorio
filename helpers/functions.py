from xxhash import xxh64_hexdigest
from discord.ext.commands import (CommandError, Converter, Context)
import re, datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, Sequence

def human_join(seq: Sequence[str], delim: str = ", ", final: str = "or") -> str:
    size = len(seq)
    if size == 0:
        return ""

    if size == 1:
        return seq[0]

    if size == 2:
        return f"{seq[0]} {final} {seq[1]}"

    return delim.join(seq[:-1]) + f" {final} {seq[-1]}"

def duration(duration: int, ms: bool = True):
    if ms:
        seconds = int((duration / 1000) % 60)
        minutes = int((duration / (1000 * 60)) % 60)
        hours = int((duration / (1000 * 60 * 60)) % 24)
    else:
        seconds = int(duration % 60)
        minutes = int((duration / 60) % 60)
        hours = int((duration / (60 * 60)) % 24)

    if any((hours, minutes, seconds)):
        result = ""
        if hours:
            result += f"{hours:02d}:"
        result += f"{minutes:02d}:"
        result += f"{seconds:02d}"
        return result
    else:
        return "00:00"
    
class plural:
    def __init__(self, value: int, bold: bool = False, code: bool = False):
        self.value: int = value
        self.bold: bool = bold
        self.code: bool = code

    def __format__(self, format_spec: str) -> str:
        v = self.value
        if isinstance(v, list):
            v = len(v)
        if self.bold:
            value = f"**{v:,}**"
        elif self.code:
            value = f"`{v:,}`"
        else:
            value = f"{v:,}"

        singular, sep, plural = format_spec.partition("|")
        plural = plural or f"{singular}s"

        if abs(v) != 1:
            return f"{value} {plural}"

        return f"{value} {singular}"

def hash(text: str):
    return xxh64_hexdigest(str(text))

def shorten(value: str, length: int = 20):
    if len(value) > length:
        value = value[: length - 2] + (".." if len(value) > length else "").strip()
    return value



PERCENTAGE = re.compile(r"(?P<percentage>\d+)%")

HH_MM_SS = re.compile(r"(?P<h>\d{1,2}):(?P<m>\d{1,2}):(?P<s>\d{1,2})")
MM_SS = re.compile(r"(?P<m>\d{1,2}):(?P<s>\d{1,2})")
HUMAN = re.compile(r"(?:(?P<m>\d+)\s*m\s*)?(?P<s>\d+)\s*[sm]")
OFFSET = re.compile(r"(?P<s>(?:\-|\+)\d+)\s*s")

class Percentage(Converter):
    async def convert(self, ctx: Context, argument: str) -> int:
        if argument.isdigit():
            argument = int(argument)

        elif match := PERCENTAGE.match(argument):
            argument = int(match.group(1))

        else:
            argument = 0

        if argument < 0 or argument > 100:
            raise CommandError("Please **specify** a valid percentage")

        return argument
    
class Position(Converter):
    async def convert(self, ctx: Context, argument: str) -> int:
        argument = argument.lower()
        player = ctx.voice_client
        ms: int = 0

        if ctx.invoked_with == "ff" and not argument.startswith("+"):
            argument = f"+{argument}"

        elif ctx.invoked_with == "rw" and not argument.startswith("-"):
            argument = f"-{argument}"

        if match := HH_MM_SS.fullmatch(argument):
            ms += (
                int(match.group("h")) * 3600000
                + int(match.group("m")) * 60000
                + int(match.group("s")) * 1000
            )

        elif match := MM_SS.fullmatch(argument):
            ms += int(match.group("m")) * 60000 + int(match.group("s")) * 1000

        elif (match := OFFSET.fullmatch(argument)) and player:
            ms += player.position + int(match.group("s")) * 1000

        elif match := HUMAN.fullmatch(argument):
            if m := match.group("m"):
                if match.group("s") and argument.endswith("m"):
                    raise CommandError(f"Position `{argument}` is not valid")

                ms += int(m) * 60000

            elif s := match.group("s"):
                if argument.endswith("m"):
                    ms += int(s) * 60000
                else:
                    ms += int(s) * 1000

        else:
            raise CommandError(f"Position `{argument}` is not valid")

        return ms
    

def human_timedelta(
    dt: datetime.datetime,
    *,
    source: Optional[datetime.datetime] = None,
    accuracy: Optional[int] = 3,
    brief: bool = False,
    suffix: bool = True,
) -> str:
    if isinstance(dt, datetime.timedelta):
        dt = datetime.datetime.utcfromtimestamp(dt.total_seconds())

    now = source or datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)

    now = now.replace(microsecond=0)
    dt = dt.replace(microsecond=0)

    if dt > now:
        delta = relativedelta(dt, now)
        output_suffix = ""
    else:
        delta = relativedelta(now, dt)
        output_suffix = " ago" if suffix else ""

    attrs = [
        ("year", "y"),
        ("month", "mo"),
        ("day", "d"),
        ("hour", "h"),
        ("minute", "m"),
        ("second", "s"),
    ]

    output = []
    for attr, brief_attr in attrs:
        elem = getattr(delta, attr + "s")
        if not elem:
            continue

        if attr == "day":
            weeks = delta.weeks
            if weeks:
                elem -= weeks * 7
                if not brief:
                    output.append(format(plural(weeks), "week"))
                else:
                    output.append(f"{weeks}w")

        if elem <= 0:
            continue

        if brief:
            output.append(f"{elem}{brief_attr}")
        else:
            output.append(format(plural(elem), attr))

    if accuracy is not None:
        output = output[:accuracy]

    if len(output) == 0:
        return "now"
    else:
        if not brief:
            return human_join(output, final="and") + output_suffix
        else:
            return "".join(output) + output_suffix

def hash(text: str):
    return xxh64_hexdigest(str(text))