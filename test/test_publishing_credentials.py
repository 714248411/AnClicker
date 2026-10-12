from pathlib import Path
import importlib.util
import pytest
from info import UPDATE_CONFIG
spec=importlib.util.spec_from_file_location('publishing_credentials',Path(__file__).resolve().parents[1]/'tools/publishing_credentials.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def config_file(tmp_path, **changes):
    values={UPDATE_CONFIG[k+'_env']: UPDATE_CONFIG[k] for k in ('bucket','region','key_prefix','public_base_url')}
    values.update(QINIU_ACCESS_KEY='fake-access-for-test',QINIU_SECRET_KEY='fake-secret-for-test')
    values.update(changes)
    path=tmp_path/'credentials.txt'
    path.write_text('\n'.join("'%s' = '%s'" % pair for pair in values.items())+'\nthrow \'must never execute\'\n',encoding='utf-8-sig')
    return path

def test_credentials_are_child_only_and_formal_url_is_preserved(tmp_path):
    base={'UNCHANGED':'yes'}
    env=module.publishing_environment(config_file(tmp_path,QINIU_PUBLIC_BASE_URL='https://legacy.invalid'),base,UPDATE_CONFIG)
    assert env['QINIU_ACCESS_KEY']=='fake-access-for-test'
    assert env['QINIU_PUBLIC_BASE_URL']==UPDATE_CONFIG['public_base_url']
    assert base=={'UNCHANGED':'yes'}

@pytest.mark.parametrize('changes',[{'QINIU_BUCKET':'wrong-bucket'},{'QINIU_SECRET_KEY':''}])
def test_invalid_publishing_configuration_rejected(tmp_path,changes):
    with pytest.raises(ValueError):module.publishing_environment(config_file(tmp_path,**changes),{},UPDATE_CONFIG)
