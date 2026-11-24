"""Read only stable releases from the configured public repository."""
import re
from urllib.parse import urlsplit, quote
import requests
from info import VERSION, Github_WEBSITE


def check_latest():
    repository = urlsplit(Github_WEBSITE)
    if repository.scheme != 'https' or repository.netloc != 'github.com':
        raise ValueError('GitHub 更新地址无效')
    parts = repository.path.strip('/').split('/')
    if len(parts) != 2 or not all(re.fullmatch(r'[A-Za-z0-9_.-]+', p) for p in parts):
        raise ValueError('GitHub 仓库地址无效')
    with requests.get('https://api.github.com/repos/' + '/'.join(parts) + '/releases/latest',
                      headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'AnClicker-update'},
                      timeout=(3, 5)) as response:
        response.raise_for_status()
        release = response.json()
    tag = str(release.get('tag_name', ''))
    if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'v?\d+\.\d+\.\d+', tag):
        raise ValueError('GitHub 未返回有效正式版本')
    version = tag.removeprefix('v')
    if tuple(map(int, version.split('.'))) <= tuple(map(int, VERSION.split('.'))):
        return None
    return {'external_release': True, 'Version': version,
            'NotesMarkdown': str(release.get('body') or '')[:12000],
            'ReleaseUrl': Github_WEBSITE.rstrip('/') + '/releases/tag/' + quote(tag, safe='')}
