RAPIDGATOR = 'rapidgator'
MEXASHARE = 'mexashare'
BIGFILE = 'bigfile'
KATFILE = 'katfile'
ROSEFILE = 'rosefile'
DDOWNLOAD = 'ddownload'
FIKPER = 'fikper'


class HostResolver:

    def __init__(self, glv):
        self.glv = glv

    @staticmethod
    def by_url(url):
        if 'rapidgator.net' in url:
            return RAPIDGATOR

        if 'rg.to/' in url:
            return RAPIDGATOR

        if 'mexashare.com' in url:
            return MEXASHARE

        if 'mx-sh.net' in url:
            return MEXASHARE

        if 'mexa.sh' in url:
            return MEXASHARE

        if 'bigfile.to' in url:
            return BIGFILE

        if 'katfile.com' in url:
            return KATFILE

        if 'rosefile.net' in url:
            return ROSEFILE

        if 'ddownload.com' in url:
            return DDOWNLOAD

        if 'fikper.com' in url:
            return FIKPER

        return 'download'
