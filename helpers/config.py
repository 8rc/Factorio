class Auth:
    token: str = "MTIxMDAwNzA1ODIzNDIxMjQzMw.GH4KR9.rRnoqecMxjt9wF9Bma0pzp1EU09eMyvfhYAGRY"  # bot token
    id: int = 1210007058234212433  # bot id
    owners: list = [
        158046167186407424,
        1194157892052455424
    ]
    prefix: str = "$"  # bot default prefix
    #db: str = "postgresql://root:001278870@localhost:5432/factorio"# change this to whatever yo shit is
    logger: str = "<cyan>[</cyan><blue>{time:HH:MM:SS}</blue><cyan>]</cyan> (<magenta>factorio:{function}</magenta>) <yellow>@</yellow> <fg #BBAAEE>{message}</fg #BBAAEE>"


class Colors:
    maincolor = 0x2B2D31
    error = 0x2B2D31
    neutral = 0x2B2D31 #0x2B2D31
    approve = 0x2B2D31 #0xA9E97A
    warn = 0x2B2D31 #0xFFCC00
    deny = 0x2B2D31 #0xFF3636


class Paginatorr:
    previous = "◀️"
    next = "▶"
    stop = "⏹️"
    skip = "🔀"
    first = "⬅️"
    last = "➡️"