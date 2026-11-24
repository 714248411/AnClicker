"""Verify shared execution guidance reaches providers without granting tools."""
import sys
import threading
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from anclicker.domain.agent_execution_policy import EXECUTION_POLICY, PLANNING_POLICY, INTEGRATION_GUIDE, POLICY_VERSION
from anclicker.domain.agent_protocol import SYSTEM_PROMPT
from models.agent_provider import AgentSettings, ModelClient
from models.agent_small_model import prefix
from models.draft_planner import SYSTEM
from models.tool_api import ToolAPIServer


def main():
    context = SimpleNamespace(stop_requested=False)
    for backend in ('compatible', 'ollama'):
        for mode in ('json', 'native'):
            settings = AgentSettings(backend=backend, mode=mode,
                endpoint='http://127.0.0.1:19999', model='test-model')
            content = '{"type":"message","content":"draft only"}' if mode == 'json' else 'draft only'
            message = {'role': 'assistant', 'content': content}
            response = {'message': message} if backend == 'ollama' else {'choices': [{'message': message}]}
            with patch('models.agent_provider.request_json', return_value=response) as request:
                result = ModelClient(settings).chat([{'role': 'user', 'content': 'test task'}], context)
            messages = request.call_args.args[1]['messages']
            assert EXECUTION_POLICY in messages[0]['content']
            assert messages[-1] == {'role': 'user', 'content': 'test task'}
            assert result['call'] is None
    assert any(EXECUTION_POLICY in m['content'] for m in prefix('auto'))
    assert PLANNING_POLICY in SYSTEM
    doc = Path('docs/大模型执行说明.txt').read_text(encoding='utf-8')
    assert doc == INTEGRATION_GUIDE + '\n\n可直接接入的系统提示词\n' + SYSTEM_PROMPT
    for browser, system in ((False, False), (True, False), (False, True), (True, True)):
        server = ToolAPIServer(('127.0.0.1', 0), 'test-secret', browser, system)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = requests.Session()
        client.trust_env = False
        url = 'http://127.0.0.1:' + str(server.server_port)
        try:
            assert client.get(url + '/v1/guide', timeout=5).status_code == 401
            client.headers['Authorization'] = 'Bearer test-secret'
            response = client.get(url + '/v1/guide', timeout=5)
            assert response.status_code == 200
            guide = response.json()
            assert guide['guide_version'] == POLICY_VERSION
            assert guide['system_prompt'] == SYSTEM_PROMPT
            assert guide['integration_guide'] == INTEGRATION_GUIDE
            assert guide['workflow_scope'] == 'session_drafts'
            assert guide['tools'] == client.get(url + '/v1/tools', timeout=5).json()['tools']
            names = {t['function']['name'] for t in guide['tools']}
            assert ('browser' in names) == browser
            assert ('crawl_page' in names) == browser
            assert ('system_file' in names) == system
            assert ('verify_screen' in names) == system
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    print('PASS: provider guidance, local prefix, draft policy, exported document, authenticated API and permission filtering')


if __name__ == '__main__':
    main()
