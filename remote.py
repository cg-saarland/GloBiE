import hashlib
from pathlib import Path
from urlpath import URL

cachedir = Path.cwd() / 'cache'
if not cachedir.exists():
    cachedir.mkdir(parents=True)


class CachedFile(URL):
    def is_file(self):
        return False

    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        return self.filename.open(mode, buffering, encoding, errors, newline)

    def resolve(self, strict=False):
        return self.filename.resolve(strict)

def fetch(url, suffix='.bin', force=False):
    print("FETCHING " + str(url), end="")
    hash = hashlib.sha1(str(url).encode('utf-8')).hexdigest()
    filename = cachedir / (hash + suffix)
    # print()
    # print(filename, end="")

    if not filename.is_file() or force:
        print(' [Loading=', end="")
        with url.get() as response:
            print(str(response.status_code) + ']')
            # info = response.info()
            # print(info.get_content_type())
            if response.status_code == 200:
                filename.write_bytes(response.content)
            else:
                return None
    else:
        print(' [' + hash[:11] + ']')

    cf = CachedFile(url)
    cf.filename = filename
    return cf
