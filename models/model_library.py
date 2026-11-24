"""Local GGUF library. Files and active selection stay under models."""
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4
from models.agent_local import _manager,LocalModelManager

class ModelLibrary:
    def __init__(self,manager=None):
        self.manager=manager or _manager
        self.root=Path(self.manager.root).resolve()
    def active(self):
        try:return json.loads((self.root/'active_model.json').read_text(encoding='utf8')).get('file')
        except (OSError,ValueError,AttributeError):return None
    def dual_config(self):
        try:return json.loads((self.root/'dual_model.json').read_text(encoding='utf8'))
        except (OSError,ValueError):return {}
    def recommended_dual(self):
        candidates=[]
        try:
            recommended=json.loads((self.root/'recommended_dual_model.json').read_text(encoding='utf8'))
            if isinstance(recommended,dict) and recommended.get('verified') is True:candidates.append(recommended)
        except (OSError,ValueError):pass
        candidates.append(self.dual_config())
        candidates.append({'splitter':'anclicker-v6-splitter-q4_0.gguf','converter':'anclicker-v6-converter-q4_0.gguf'})
        for candidate in candidates:
            try:
                config={'enabled':True,**{role:candidate[role] for role in ('splitter','converter')}}
                for role in ('splitter','converter'):self.path(config[role])
                mode=candidate.get('splitter_mode','whole')
                if mode not in ('whole','pairwise','boundary_batch'):raise ValueError('未知拆句协议')
                config['splitter_mode']=mode
                for key,default in (('serial_models',True),('embedding_enabled',False),('correction_memory_enabled',True)):
                    value=candidate.get(key,default)
                    if type(value) is not bool:raise ValueError('双模型配置开关必须是布尔值')
                    config[key]=value
                return config
            except (ValueError,TypeError,KeyError):continue
        return None
    def _stop_roles(self):
        for role in ('splitter','converter'):
            state=self.root/'.dual-runtime'/role
            if state.is_dir():LocalModelManager(state,runtime_dir=self.root).stop()
    def _write_dual(self,config):
        temp=self.root/(uuid4().hex+'.tmp')
        try:
            temp.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8');os.replace(temp,self.root/'dual_model.json')
        finally:temp.unlink(missing_ok=True)
    def path(self,name):
        path=(self.root/name).resolve()
        if path.parent!=self.root or path.suffix.lower()!='.gguf' or not path.is_file():raise ValueError('模型文件不存在或不在本机模型目录中')
        return path
    def list(self):
        active=self.active()
        return [{'file':p.name,'bytes':p.stat().st_size,'active':p.name==active} for p in sorted(self.root.glob('*.gguf')) if p.is_file() and p.resolve().parent==self.root]
    def _select(self,name):
        data={'file':name,'name':Path(name).stem if name else '未选择本机模型'}
        temp=self.root/('selection-'+uuid4().hex+'.tmp')
        try:
            temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
            os.replace(temp,self.root/'active_model.json')
        finally:temp.unlink(missing_ok=True)
    def apply(self,action,value):
        self.root.mkdir(parents=True,exist_ok=True)
        with self.manager._exclusive(blocking=False) as acquired:
            if not acquired:raise RuntimeError('模型正在使用，请先结束当前请求')
            if action=='add':
                source=Path(value).resolve()
                if source.suffix.lower()!='.gguf':raise ValueError('请选择 GGUF 模型文件')
                with source.open('rb') as stream:header=stream.read(8)
                if header[:4]!=b'GGUF' or int.from_bytes(header[4:8],'little') not in (2,3):raise ValueError('文件不是支持的 GGUF 模型')
                target=self.root/source.name
                if target.exists():raise ValueError('同名模型已存在，请重命名后添加')
                temp=self.root/(uuid4().hex+'.importing')
                try:
                    shutil.copyfile(source,temp)
                    temp.rename(target)
                finally:temp.unlink(missing_ok=True)
                return {'message':'已添加 '+target.name,'activate':False}
            if action=='dual':
                config=self.recommended_dual()
                if not config:raise ValueError('没有可用的双模型，请先准备已验收的模型文件')
                for role in ('splitter','converter'):self.path(config[role])
                self.manager.stop();self._stop_roles();self._write_dual(config)
                return {'message':'已选择双模型：'+config['splitter']+' + '+config['converter'],'activate':True}
            path=self.path(value)
            if action=='select':
                self.manager.stop();self._stop_roles();self._select(path.name)
                config=self.dual_config()
                if config.get('enabled'):self._write_dual(dict(config,enabled=False))
                return {'message':'已选择 '+path.name,'activate':True}
            if action=='delete':
                config=self.dual_config()
                if config.get('enabled') and path.name in (config.get('splitter'),config.get('converter')):raise ValueError('请先切换为单模型，再删除双模型所使用的文件')
                if self.active()==path.name:
                    raise ValueError('请先切换到其他模型，再删除当前模型')
                # Recoverable deletion; only the explicitly selected file is moved.
                self.manager.stop()
                trash=self.root/'.trash';trash.mkdir(exist_ok=True)
                target=trash/(uuid4().hex+'-'+path.name)
                if target.resolve().parent!=trash.resolve():raise ValueError('删除目标路径无效')
                path.rename(target)
                return {'message':'已删除 '+path.name+'（文件保留在 models/.trash）','activate':False}
            raise ValueError('未知模型操作')
