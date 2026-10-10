import importlib.util
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_release', ROOT / 'packaging/build_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preserves_framework_links_and_executable_mode(tmp_path):
    app = tmp_path / 'Example.app'
    binary = app / 'Versions/A/Example'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b'native executable fixture')
    binary.chmod(0o755)
    (app / 'Versions/Current').symlink_to('A', target_is_directory=True)
    (app / 'Example').symlink_to('Versions/Current/Example')
    archive = tmp_path / 'app.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        module.add_tree(z, app, app.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name, destination in [('Versions/Current', 'A'), ('Example', 'Versions/Current/Example')]:
            item = z.getinfo('Example.app/' + name)
            assert item.create_system == 3
            assert stat.S_ISLNK(item.external_attr >> 16)
            assert z.read(item).decode() == destination
        assert z.getinfo('Example.app/Versions/A/Example').external_attr >> 16 & 0o111
        assert z.read('Example.app/Versions/A/Example') == binary.read_bytes()
