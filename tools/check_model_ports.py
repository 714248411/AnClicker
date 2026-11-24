import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager
from models.agent_local import LocalModelManager
from models.agent_provider import ModelClient, AgentSettings
with tempfile.TemporaryDirectory() as directory:
    manager=LocalModelManager(directory)
    with socket.socket() as listener:
        try:listener.bind(('127.0.0.1',8766));listener.listen()
        except OSError:pass
        manager._select_endpoint()
        assert manager.endpoint!='http://127.0.0.1:8766'
    with patch.object(manager,'_owns_listener',return_value=False),patch.object(manager,'health',return_value=200) as health:
        try:manager.ensure()
        except RuntimeError as error:assert '未检测到模型' in str(error)
        else:raise AssertionError('foreign service adopted')
        health.assert_not_called()
@contextmanager
def lease(*args):yield 'http://127.0.0.1:54321/v1'
context=SimpleNamespace(stop_requested=False)
settings=AgentSettings(mode='native')
with patch('models.agent_local.local_model_lease',lease),patch('models.agent_provider.request_json') as request:
    request.return_value={'choices':[{'message':{'content':'ok'}}]}
    assert ModelClient(settings).chat([],context)['text']=='ok'
    assert request.call_args.args[0]=='http://127.0.0.1:54321/v1/chat/completions'
    request.return_value={'data':[{'id':'anclicker-small'}]}
    assert ModelClient(settings).models(context)==['anclicker-small']
    assert request.call_args.args[0]=='http://127.0.0.1:54321/v1/models'
print('PASS occupied port fallback, foreign service rejection, chat and model discovery routing')
