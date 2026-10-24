
from pystonic.storage.local import LocalStorage

def test_list_files():
    storage = LocalStorage('/tmp')
    storage.write('test_dir/foo.txt', 'foo')
    storage.write('test_dir/bar.txt', b'bar')
    assert len(storage.list_files('test_dir')) == 2
    assert storage.read('test_dir/foo.txt').decode() == 'foo'
    assert storage.read('test_dir/bar.txt').decode() == 'bar'
    assert storage.get_file('test_dir/foo.txt') is not None
    assert storage.get_file('test_dir/bar.txt') is not None

    storage.delete('test_dir')
