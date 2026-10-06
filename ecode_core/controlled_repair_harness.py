"""Run a frozen controlled-repair plan with isolated subjects and preserved evidence.

This harness is opt-in: without ``--execute`` it only validates the input bundle.
It never changes ECode's production mutation, dispatch, or evaluation behavior.
"""
import argparse
from pathlib import Path
import re
import ast
import datetime
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import traceback
import types
from dataclasses import asdict
from unittest.mock import patch
from urllib.parse import urlparse

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

def snapshot_drift(identity,root):
 try:
  branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
  if identity.get('branch') and branch!=identity['branch']:return 'BRANCH_IDENTITY_MISMATCH'
  if identity.get('base_head') and head!=identity['base_head']:return 'HEAD_IDENTITY_MISMATCH'
  for relative,digest in identity['file_sha256'].items():
   path=root/relative
   if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:return 'TRACKED_SOURCE_SNAPSHOT_DRIFT'
  tracked_diff=subprocess.check_output(['git','diff','--binary'],cwd=root)
  if hashlib.sha256(tracked_diff).hexdigest()!=identity['tracked_diff_sha256']:return 'TRACKED_DIFF_SNAPSHOT_DRIFT'
  if 'untracked_sha256' in identity:
   raw=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=root)
   paths=sorted(path.decode() for path in raw.split(b'\0') if path)
   actual={path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in paths}
   if actual!=identity['untracked_sha256']:return 'UNTRACKED_SOURCE_SNAPSHOT_DRIFT'
 except (OSError,KeyError,subprocess.CalledProcessError):return 'SNAPSHOT_IDENTITY_UNVERIFIABLE'
 return None

def parse_args():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source-dir',type=Path,required=True,help='Frozen plan, identity, cases, and verifier inputs.')
 parser.add_argument('--output-dir',type=Path,required=True,help='New evidence directory under <repo>/.provenance/.')
 parser.add_argument('--execute',action='store_true',help='Run the real-model protocol. Omit for a read-only bundle preflight.')
 args=parser.parse_args()
 source=args.source_dir.resolve();output=args.output_dir.resolve();provenance=(REPOSITORY_ROOT/'.provenance').resolve()
 if not source.is_dir(): parser.error(f'source directory does not exist: {source}')
 if not output.is_relative_to(provenance) or output == provenance:
  parser.error(f'output directory must be a child of {provenance}')
 if output.exists(): parser.error(f'refusing to overwrite existing evidence directory: {output}')
 required=('run-plan.json','snapshot-identity.json','carried-cases.json','frozen-observer.py')
 missing=[name for name in required if not (source/name).is_file()]
 if missing: parser.error('source bundle is incomplete: '+', '.join(missing))
 plan=json.loads((source/'run-plan.json').read_text())
 identity=json.loads((source/'snapshot-identity.json').read_text())
 if not plan.get('cases') or not isinstance(plan.get('attempt_limit'),int) or plan['attempt_limit']<1:
  parser.error('run plan must declare cases and a positive attempt_limit')
 if not identity.get('file_sha256') or not identity.get('tracked_diff_sha256'):
  parser.error('snapshot identity is incomplete')
 if not plan.get('runtime_context_api_base_url'):
  parser.error('run plan must explicitly declare runtime_context_api_base_url')
 model_identity=plan.get('model_identity')
 if not isinstance(model_identity,dict) or not model_identity.get('name') or not model_identity.get('digest'):
  parser.error('run plan must pin an exact model_identity name and digest')
 if model_identity['name']!=plan.get('model'):
  parser.error('pinned model_identity name must exactly match the run plan model')
 if not plan.get('helper_image_id'):
  parser.error('run plan must pin the cached Docker helper image ID')
 completion=urlparse(plan.get('endpoint',''));context=urlparse(plan['runtime_context_api_base_url'])
 if (completion.scheme,completion.netloc)!=(context.scheme,context.netloc) or context.path not in ('','/') or context.username or context.password or context.query or context.fragment:
  parser.error('runtime context API must use the same origin as the frozen completion endpoint')
 drift=snapshot_drift(identity,REPOSITORY_ROOT)
 if drift: parser.error(f'frozen source identity check failed: {drift}')
 for entry in plan['cases']:
  case_id=entry.get('id','')
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',case_id):
   parser.error(f'invalid case id: {case_id!r}')
  case_dir=source/case_id
  if not (case_dir/'case.json').is_file() or not (case_dir/'verifier.py').is_file() or not (case_dir/'broken').is_dir():
   parser.error(f"case bundle is incomplete: {case_id}")
  if not set(entry.get('allowed',())).issubset(entry.get('broken_sha256',{})):
   parser.error(f"case allowed paths lack frozen hashes: {case_id}")
  for relative,digest in entry.get('broken_sha256',{}).items():
   subject=Path(relative)
   if subject.is_absolute() or '..' in subject.parts or not (case_dir/'broken'/subject).is_file():
    parser.error(f"invalid or missing frozen subject file: {case_id}/{relative}")
   actual=hashlib.sha256((case_dir/'broken'/subject).read_bytes()).hexdigest()
   if actual!=digest: parser.error(f"frozen subject hash mismatch: {case_id}/{relative}")
 if not args.execute:
  print(json.dumps({'classification':'PREFLIGHT_ONLY','source_dir':str(source),'output_dir':str(output),
   'model':plan.get('model'),'endpoint':plan.get('endpoint'),'runtime_context_api_base_url':plan['runtime_context_api_base_url'],'attempt_limit':plan['attempt_limit'],
   'model_identity':model_identity,
   'case_ids':[entry['id'] for entry in plan['cases']],'snapshot_sha256':identity['snapshot_sha256'],
   'branch':identity.get('branch'),'head':identity.get('base_head'),'snapshot_validation':'PASS','model_calls':0,'docker_calls':0},indent=2))
  raise SystemExit(0)
 return source,output,plan,identity

SOURCE,OUT,PLAN,IDENTITY=parse_args()
R=REPOSITORY_ROOT
MODEL_TIMEOUT_SECONDS=180
VERIFIER_TIMEOUT_SECONDS=30
RANDOM_SEED=17
# Load runtime dependencies only after the read-only preflight has completed.
import docker  # noqa: E402
from docker.models.containers import ExecResult  # noqa: E402
from ecode_core.adapters.ecode_mutation import ECodeMutationRunner  # noqa: E402
from ecode_core.adapters.ecode_evaluator import ECodeEvaluator  # noqa: E402
from ecode_core.archive import Archive,KeepAll  # noqa: E402
from ecode_core.contracts import AgentVersion,ArtifactRef,EvaluationContext  # noqa: E402
from ecode_core.selectors import BestScoreParentSelector  # noqa: E402
from ecode_core.engine import EvolutionEngine  # noqa: E402
from ecode_core.telemetry import JsonlTelemetry  # noqa: E402
MODEL=PLAN['model'];ENDPOINT=PLAN['endpoint'];client=None;image=None;active=[];current={}
sha=lambda data:hashlib.sha256(data).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def source_input_hashes():
 paths=[SOURCE/name for name in ('run-plan.json','snapshot-identity.json','carried-cases.json','frozen-observer.py','runtime-preflight.json')]
 for entry in PLAN['cases']:
  case_root=SOURCE/entry['id']
  paths.extend(case_root/name for name in ('case.json','verifier.py'))
  paths.extend(path for path in (case_root/'broken').rglob('*') if path.is_file())
 return {path.relative_to(SOURCE).as_posix():sha(path.read_bytes()) for path in sorted(paths)}
def freeze_check():
 assert all(sha((R/p).read_bytes())==h for p,h in IDENTITY['file_sha256'].items()),'PRODUCTION_SNAPSHOT_DRIFT'
 assert sha(subprocess.check_output(['git','diff','--binary']))==IDENTITY['tracked_diff_sha256']
 if 'untracked_sha256' in IDENTITY:
  raw=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=R)
  paths=sorted(path.decode() for path in raw.split(b'\0') if path)
  actual={path:sha((R/path).read_bytes()) for path in paths}
  assert actual==IDENTITY['untracked_sha256'],'UNTRACKED_SOURCE_SNAPSHOT_DRIFT'
freeze_check()
OUT.mkdir(parents=True,exist_ok=False)
for entry in PLAN['cases']:(OUT/entry['id']).mkdir()
assert not (OUT/'battery-report.json').exists()
carried={case['id']:case for case in json.loads((SOURCE/'carried-cases.json').read_text())}
fresh_cases=[]
for entry in PLAN['cases']:
 case={key:value for key,value in carried[entry['id']].items() if key not in ('attempts','classification','VERIFIED_AFTER')}
 case.update({'attempts':[],'classification':'NOT_STARTED','VERIFIED_AFTER':False})
 fresh_cases.append(case)
REPORT={'gate':PLAN.get('gate'),'run_id':OUT.name,'source_dir':str(SOURCE),'harness_sha256':sha(Path(__file__).read_bytes()),'source_inputs_sha256':source_input_hashes(),'plan_sha256':sha((SOURCE/'run-plan.json').read_bytes()),'snapshot_identity_sha256':sha((SOURCE/'snapshot-identity.json').read_bytes()),'snapshot_sha256':PLAN['snapshot_sha256'],'started_at':now(),'attempt_limit':PLAN['attempt_limit'],'model_timeout_seconds':MODEL_TIMEOUT_SECONDS,'verifier_timeout_seconds':VERIFIER_TIMEOUT_SECONDS,'random_seed':RANDOM_SEED,'cases':fresh_cases,'model':MODEL,'endpoint':ENDPOINT,'runtime_context_api_base_url':PLAN['runtime_context_api_base_url'],'benchmark':'NOT_EXECUTED','performance_gain':'NOT_PROVEN','swe_capability':'NOT_CLAIMED','promotion':'NOT_AUTHORIZED'}
for name in ('run-plan.json','snapshot-identity.json'):(OUT/name).write_bytes((SOURCE/name).read_bytes())
def persist():
 (OUT/'battery-report.json').write_text(json.dumps(REPORT,indent=2,default=str))
 if current.get('case'):(OUT/current['case']['id']/'report.json').write_text(json.dumps(current['case_report'],indent=2,default=str))
def put(k,path,data):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as tar:
  info=tarfile.TarInfo(Path(path).name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
 k.put_archive(str(Path(path).parent),b.getvalue())
def fetch(k,path):
 chunks,_=k.get_archive(path)
 with tarfile.open(fileobj=io.BytesIO(b''.join(chunks))) as tar:return tar.extractfile(tar.getmembers()[0]).read()
def command(k,cmd,cwd='/ecode'):
 result=k.exec_run(cmd,workdir=cwd,demux=True);a,b=result.output
 return {'command':cmd,'returncode':result.exit_code,'stdout':(a or b'').decode(errors='replace'),'stderr':(b or b'').decode(errors='replace')}
def must(k,cmd,cwd='/ecode'):
 result=command(k,cmd,cwd)
 if result['returncode']:raise RuntimeError(json.dumps(result))
 return result
def subject_bytes(case):
 root=SOURCE/case['id']/'broken'
 return {rel:(root/rel).read_bytes() for rel in case['broken_sha256']}
def install(k,files):
 must(k,['mkdir','-p','/ecode/repair'])
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as tar:
  for rel,data in files.items():
   i=tarfile.TarInfo(rel);i.size=len(data);tar.addfile(i,io.BytesIO(data))
 k.put_archive('/ecode/repair',b.getvalue())
def fresh(case,clean=False):
 k=client.containers.run(image.id,detach=True,environment={'PYTHONPATH':'/ecode/repair:/ecode','PYTHONDONTWRITEBYTECODE':'1'},extra_hosts={'host.docker.internal':'host-gateway'})
 install(k,{p:(R/p).read_bytes() for p in case['broken_sha256']} if clean else subject_bytes(case))
 return k
def verify_case(case,patch_data=None,clean=False):
 k=fresh(case,clean);detail={'started_at':now(),'container_id':k.id,'clean_control':clean,'patch_applied':False}
 try:
  put(k,'/tmp/independent-verifier.py',(SOURCE/case['id']/'verifier.py').read_bytes())
  if patch_data is not None:
   put(k,'/tmp/candidate.patch',patch_data)
   detail['apply_check']=command(k,['git','apply','--check','/tmp/candidate.patch'])
   if not detail['apply_check']['returncode']:
    detail['apply']=command(k,['git','apply','/tmp/candidate.patch']);detail['patch_applied']=detail['apply']['returncode']==0
   if not detail['patch_applied']:detail['classification']='CANDIDATE_INVALID';return detail
  detail['verifier']=command(k,['timeout',str(VERIFIER_TIMEOUT_SECONDS),'env','PYTHONPATH=/ecode/repair:/ecode','python','/tmp/independent-verifier.py'],'/tmp')
  detail['verified']=detail['verifier']['returncode']==0
  detail['final_subject_sha256']={p:sha(fetch(k,'/ecode/repair/'+p)) for p in case['broken_sha256']}
  return detail
 finally:k.remove(force=True)
# Passive metrics only; no output normalization or generated execution.
observer=(SOURCE/'frozen-observer.py').read_text()
(OUT/'observer.py').write_text(observer)
manifest_code="import json,hashlib;from pathlib import Path;r=Path('/ecode');print(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and p.name not in ('self_evo.md','model_patch.diff')},sort_keys=True))"
def filesystem(k):return json.loads(must(k,['python','-c',manifest_code])['stdout'])
def capture(proxy):
 if proxy.captured:return
 info=proxy.info;k=proxy.actual;d=Path(info['artifact_dir'])
 for path,name in [('/tmp/observer.jsonl','observer.jsonl'),('/ecode/self_evo.md','self_evo.md'),('/ecode/model_patch.diff','raw-patch.diff')]:
  try:(d/name).write_bytes(fetch(k,path))
  except Exception as exc:info.setdefault('capture_errors',{})[name]=str(exc)
 info['filesystem_after']=filesystem(k)
 info['changed_files']=command(k,['git','diff','--name-only',info.get('parent_commit','HEAD')])
 info['changed_status']=command(k,['git','diff','--name-status',info.get('parent_commit','HEAD')])
 info['diff']=command(k,['git','diff',info.get('parent_commit','HEAD')])
 allowed=['repair/'+p for p in current['case']['allowed']]
 info['changed_files_list']=info['changed_files']['stdout'].splitlines()
 before=info.get('filesystem_before',{});after=info['filesystem_after']
 differences=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
 info['filesystem_differences']=differences
 info['scope_ok']=bool(differences) and set(differences)<=set(allowed) and set(info['changed_files_list'])<=set(allowed) and all(p in after for p in differences)
 events=[json.loads(line) for line in (d/'observer.jsonl').read_text().splitlines()] if (d/'observer.jsonl').exists() else []
 info['model_calls']=[e for e in events if e['event']=='get_response_from_llm_end']
 info['tool_calls']=[e for e in events if e['event']=='process_tool_call_end']
 info['protocol_events']=[item for e in events if e['event']=='diagnose_manual_tool_response_end' for item in e['result']]
 info['observer_errors']=[e for e in events if e['event'].endswith('_error')]
 proxy.captured=True;persist()
class Proxy:
 def __init__(self,k,info):self.actual=k;self.info=info;self.captured=False
 # fresh() creates the disposable container with detach=True, so it is already
 # running when self_improve_step invokes the normal container.start() hook.
 def start(self,*args,**kwargs):return None
 def __getattr__(self,name):return getattr(self.actual,name)
 def exec_run(self,cmd,*args,**kw):
  if isinstance(cmd,list) and '/ecode/coding_agent.py' in cmd:
   self.info['original_agent_command']=cmd;self.info['parent_commit']=cmd[cmd.index('--base_commit')+1]
   self.info['filesystem_before']=filesystem(self.actual)
   effective=list(cmd);effective[effective.index('/ecode/coding_agent.py')]='/tmp/observe_agent.py';effective=['timeout',str(MODEL_TIMEOUT_SECONDS),*effective]
   self.info['effective_agent_command']=effective;kw['demux']=True
   env=dict(kw.get('environment') or {});env['PYTHONPATH']='/ecode/repair:/ecode';env['PYTHONDONTWRITEBYTECODE']='1';kw['environment']=env
   result=self.actual.exec_run(effective,*args,**kw);stdout,stderr=result.output
   self.info['agent_returncode']=result.exit_code
   (Path(self.info['artifact_dir'])/'agent.stdout').write_bytes(stdout or b'');(Path(self.info['artifact_dir'])/'agent.stderr').write_bytes(stderr or b'')
   return ExecResult(result.exit_code,(stdout or b'')+(stderr or b''))
  return self.actual.exec_run(cmd,*args,**kw)
def build_fixture(*args,**kwargs):
 info=current['attempt'];info['fixture_stage']='CREATE_DISPOSABLE_CONTAINER'
 k=fresh(current['case']);info=current['attempt'];proxy=Proxy(k,info);active.append(proxy)
 info['container_id']=k.id;info['mounts']=k.attrs.get('Mounts',[]);assert not info['mounts']
 info['fixture_stage']='INSTALL_AUXILIARY_RUNTIME'
 runtime_adapter=R/'ecode_core/adapters/ollama_runtime.py'
 if runtime_adapter.is_file():
  put(k,'/ecode/repair/ecode_core/adapters/ollama_runtime.py',runtime_adapter.read_bytes())
  info['auxiliary_runtime_files']={'ecode_core/adapters/ollama_runtime.py':sha(runtime_adapter.read_bytes())}
 env={'ECODE_OPENAI_BASE_URL':ENDPOINT,'ECODE_OPENAI_MODEL':MODEL,'ECODE_OPENAI_API_KEY':'local','PYTHONPATH':'/ecode/repair:/ecode'}
 # No clean target source exists elsewhere in the model container.
 assert command(k,['test','!','-e','/ecode/ecode_core'])['returncode']==0
 assert command(k,['test','!','-e','/ecode/tests'])['returncode']==0
 info['fixture_stage']='INSTALL_OBSERVER_AND_GIT_FIXTURE'
 put(k,'/tmp/observe_agent.py',observer.encode())
 ignore=fetch(k,'/ecode/.gitignore')+b'\n/self_evo.md\n/model_patch.diff\n';put(k,'/ecode/.gitignore',ignore)
 info['fixture_stage']='INITIALIZE_FIXTURE_GIT'
 for cmd in [['git','init'],['git','add','--all'],['git','-c','user.name=fixture','-c','user.email=fixture@localhost','commit','-m','fresh broken repository']]:must(k,cmd)
 info['runtime_import_preflight']=must(k,['env','PYTHONPATH=/ecode/repair:/ecode','python','-c','import coding_agent,llm;print("RUNTIME_IMPORT_OK")'])
 info['fixture_stage']='RETURN_PROXY'
 return proxy

_build_fixture=build_fixture
def build_fixture_observed(*args,**kwargs):
 try:return _build_fixture(*args,**kwargs)
 except BaseException as exc:
  info=current['attempt'];info['fixture_build_failure']={'stage':info.get('fixture_stage'),'exception_type':type(exc).__name__,'exception':str(exc),'traceback':traceback.format_exc()};persist();raise
def cleanup_observed(proxy):
 capture(proxy);original_cleanup(proxy)
def evaluate(agent,context):
 case=current['case'];is_parent=agent.parent_id is None
 detail=verify_case(case,None if is_parent else Path(agent.artifact.path).read_bytes())
 d=Path(current['attempt']['artifact_dir']);path=d/(agent.version_id+'-evaluation.json');path.write_text(json.dumps(detail,indent=2))
 current['attempt'].setdefault('evaluations',[]).append({'agent_id':agent.version_id,**detail})
 if is_parent:
  assert detail.get('verified') is False,'PARENT_NOT_BROKEN'
  return {'status':'COMPLETED','overall_performance':{'accuracy_score':0},'BROKEN_BEFORE':True,'artifacts':[str(path)]}
 return {'status':'COMPLETED' if detail.get('patch_applied') else 'INCOMPLETE','overall_performance':{'accuracy_score':1 if detail.get('verified') else 0},'VERIFIED_AFTER':detail.get('verified',False),'independent_verification':detail,'artifacts':[str(path)]}
def mutate(parent,parent_result,child_id,entry,ctx):
 info=current['attempt'];info['selected_parent']=parent.version_id;info['selected_parent_score']=parent_result.score;info['selected_parent_status']=parent_result.status
 env={'ECODE_OPENAI_BASE_URL':ENDPOINT,'ECODE_OPENAI_MODEL':MODEL,'ECODE_OPENAI_API_KEY':'local','ECODE_OLLAMA_API_BASE_URL':PLAN['runtime_context_api_base_url']}
 with patch.object(si,'build_ecode_container',build_fixture_observed),patch.object(si,'diagnose_problem',lambda *a,**k:current['case']['task']),patch.object(si,'get_test_description',lambda **kw:'Independent verification is withheld. Inspect the disposable repair repository; use only the actual bash/editor tools.'),patch.object(si,'cleanup_container',cleanup_observed),patch.dict(os.environ,env):
  metadata=si.self_improve(parent_commit='initial',output_dir=str(OUT/current['case']['id']/'mutation'),entry=entry,mutation_only=True,post_improve_diagnose=False,run_id=ctx.run_id)
 info['self_improve_metadata']=metadata
 for proxy in active:
  if proxy.info is info and not proxy.captured:capture(proxy)
 info['timeout']=info.get('agent_returncode')==124
 if info['timeout']:raise RuntimeError('MUTATION_TIMEOUT')
 if metadata.get('status')=='BLOCKED':raise RuntimeError('INFRASTRUCTURE_BLOCKED')
 if metadata.get('status')!='MUTATION_READY':raise RuntimeError('PATCH_EMPTY')
 patch_path=Path(metadata['model_patch_file']);info['patch_path']=str(patch_path);info['patch_sha256']=sha(patch_path.read_bytes())
 if not info.get('scope_ok'):raise RuntimeError('CANDIDATE_INVALID')
 assert info['patch_sha256']==metadata['model_patch_sha256']
 return metadata
try:
 client=docker.from_env();assert client.ping()
 REPORT['docker']=client.version()['Version'];persist()
 # Pin the exact Ollama model artifact before any model-facing call. This uses
 # a cached helper image and read-only /api/tags; failures remain explicit.
 helper=client.images.get('python:3.10-slim')
 if helper.id!=PLAN['helper_image_id']:raise RuntimeError('HELPER_IMAGE_IDENTITY_MISMATCH')
 REPORT['model_registry_preflight']={'helper_image_id':helper.id,'endpoint':PLAN['runtime_context_api_base_url']}
 probe=client.containers.run(helper.id,command=['python','-c',
  'import json,urllib.request;u='+repr(PLAN['runtime_context_api_base_url'].rstrip('/')+'/api/tags')+';print(json.dumps(json.load(urllib.request.urlopen(u,timeout=10)),sort_keys=True))'],
  detach=True,extra_hosts={'host.docker.internal':'host-gateway'})
 try:
  waited=probe.wait(timeout=20);raw=probe.logs(stdout=True,stderr=True).decode(errors='replace')
  if waited.get('StatusCode')!=0:raise RuntimeError('MODEL_REGISTRY_PREFLIGHT_FAILED: '+raw)
  tags=json.loads(raw.strip().splitlines()[-1]);matches=[m for m in tags.get('models',[]) if m.get('name')==PLAN['model_identity']['name']]
  if len(matches)!=1:raise RuntimeError('MODEL_IDENTITY_NOT_UNIQUE_OR_MISSING')
  observed=matches[0];expected=PLAN['model_identity']
  for key in ('name','digest','size','capabilities'):
   if observed.get(key)!=expected.get(key):raise RuntimeError('MODEL_IDENTITY_MISMATCH: '+key)
  for key,value in expected['details'].items():
   if observed.get('details',{}).get(key)!=value:raise RuntimeError('MODEL_IDENTITY_MISMATCH: details.'+key)
  pinned={key:observed.get(key) for key in ('name','digest','size','details','capabilities')}
  REPORT['model_registry_preflight'].update({'classification':'EXACT_PIN_CONFIRMED','model':pinned,'raw_response_sha256':sha(raw.encode())})
  (OUT/'model-registry-preflight.json').write_text(json.dumps({'classification':'EXACT_PIN_CONFIRMED','expected':expected,'observed':pinned,'raw_response_sha256':REPORT['model_registry_preflight']['raw_response_sha256'],'helper_image_id':helper.id},indent=2))
  persist()
 finally:probe.remove(force=True)
 # Runtime image contains qualified agent/protocol files, never clean repair subjects.
 b=io.BytesIO();included=[]
 with tarfile.open(fileobj=b,mode='w') as tar:
  snapshot_paths=set(IDENTITY['file_sha256'])|set(IDENTITY.get('untracked_sha256',{}))
  selected_runtime_files=('Dockerfile','requirements.txt','.gitignore','coding_agent.py','coding_agent_polyglot.py','llm.py','llm_withtools.py')
  for rel in sorted(snapshot_paths):
   if rel in selected_runtime_files or rel.startswith(('utils/','tools/','prompts/')):
    data=(R/rel).read_bytes();i=tarfile.TarInfo(rel);i.size=len(data);i.mode=0o644;tar.addfile(i,io.BytesIO(data));included.append(rel)
 REPORT['runtime_image_source_files']=included
 b.seek(0);image_id=None
 with (OUT/'image-build.jsonl').open('w') as log:
  for item in client.api.build(fileobj=b,custom_context=True,rm=True,decode=True):
   log.write(json.dumps(item)+'\n');log.flush()
   if item.get('error'):raise RuntimeError(item['error'])
   if 'aux' in item and 'ID' in item['aux']:image_id=item['aux']['ID']
   if 'Successfully built ' in item.get('stream',''):image_id=item['stream'].split('Successfully built ')[1].split()[0]
 image=client.images.get(image_id);REPORT['image_id']=image.id;persist();print('IMAGE_READY',flush=True)
 # Import benchmark-coupled host operation with forbidden boundaries and local empty dataset.
 def forbidden(*a,**kw):raise RuntimeError('FORBIDDEN_BENCHMARK_BOUNDARY')
 for module_name,function in [('swe_bench.harness','harness'),('polyglot.harness','harness'),('swe_bench.report','make_report')]:
  module=types.ModuleType(module_name);setattr(module,function,forbidden);sys.modules[module_name]=module
 module=types.ModuleType('datasets');module.load_dataset=lambda *a,**kw:{'test':[]};sys.modules['datasets']=module
 import self_improve_step as si
 original_cleanup=si.cleanup_container
 # Qualify all five oracles/broken states before the first inference.
 for entry in PLAN['cases']:
  case=json.loads((SOURCE/entry['id']/'case.json').read_text());freeze_check()
  assert all(sha(p.read_bytes())==case['broken_sha256'][str(p.relative_to(SOURCE/case['id']/'broken'))] for p in (SOURCE/case['id']/'broken').rglob('*.py'))
  clean=verify_case(case,clean=True);broken=verify_case(case)
  (OUT/case['id']/'clean-control.json').write_text(json.dumps(clean,indent=2));(OUT/case['id']/'broken-before.json').write_text(json.dumps(broken,indent=2))
  assert clean.get('verified') is True and broken.get('verified') is False, 'ORACLE_OR_DEFECT_INVALID'
  print('ORACLE_READY',case['id'],flush=True)
 # Explicitly verify the real preparatory Git boundary without model/runner calls.
 for entry in PLAN['cases']:
  case=json.loads((SOURCE/entry['id']/'case.json').read_text());k=fresh(case)
  try:
   for cmd in [['git','init'],['git','add','--all'],['git','-c','user.name=fixture','-c','user.email=fixture@localhost','commit','-m','broken baseline'],['rm','/ecode/coding_agent_polyglot.py'],['git','add','--all'],['git','-c','user.name=fixture','-c','user.email=fixture@localhost','commit','-m','preparation boundary']]:must(k,cmd)
   (OUT/case['id']/'commit-boundary-preflight.json').write_text(json.dumps({'classification':'PASS','new_model_calls':0,'mutation_runner_calls':0,'container_id':k.id},indent=2))
  finally:k.remove(force=True)
 for entry in PLAN['cases']:
  case=json.loads((SOURCE/entry['id']/'case.json').read_text());cr=next(c for c in REPORT['cases'] if c['id']==case['id'])
  if cr['classification']=='REAL_REPAIR_PASS' or len(cr['attempts'])>=PLAN['attempt_limit']:continue
  current.update({'case':case,'case_report':cr})
  print('CASE_START',case['id'],flush=True)
  for number in range(len(cr['attempts'])+1,PLAN['attempt_limit']+1):
   freeze_check();d=OUT/case['id']/f'attempt-{number}';d.mkdir();info={'attempt':number,'artifact_dir':str(d),'started_at':now()};cr['attempts'].append(info);current['attempt']=info
   ctx=EvaluationContext(f"{case['id']}-attempt-{number}",IDENTITY['base_head'],sha(json.dumps(entry,sort_keys=True).encode()),MODEL,'local-ollama-openai-compatible','controlled-repository-tests',case['id'],d,RANDOM_SEED)
   parent_path=OUT/case['id']/'parent-manifest.json'
   if not parent_path.exists():parent_path.write_text(json.dumps(case['broken_sha256'],sort_keys=True))
   h=sha(parent_path.read_bytes());parent=AgentVersion(case['id']+'-parent',None,ctx.commit_sha,h,ctx.config_sha256,ArtifactRef(str(parent_path),h),{'controlled_defect':case['id']})
   archive=Archive(KeepAll());selector=BestScoreParentSelector();engine=EvolutionEngine(archive=archive,parent_selector=selector,mutation_runner=ECodeMutationRunner(mutate_fn=mutate,entry_selector=lambda *_:case['id']),evaluator=ECodeEvaluator(evaluate),context=ctx,telemetry=JsonlTelemetry(d/'telemetry.jsonl'))
   try:
    engine.initialize(parent);archive.write(d/'before');info['parent_evaluation']=asdict(archive.results[parent.version_id]);candidate=engine.step(1)
    info['candidate']=asdict(candidate);info['evaluation']=asdict(archive.results[candidate.version_id]);selected=selector.select(archive.members,archive.results,rng=engine.rng);info['post_selection']=selected.version_id
    passed=info['evaluation']['score']==1 and info['evaluation']['metadata'].get('VERIFIED_AFTER') and selected==candidate
    info['classification']='REAL_REPAIR_PASS' if passed else ('CANDIDATE_INVALID' if info['evaluation']['status']=='INCOMPLETE' else 'VERIFICATION_FAILED')
   except Exception as exc:
    info['error']=str(exc);info['traceback']=traceback.format_exc()
    if info.get('agent_returncode')==124:
     info['classification']='MUTATION_FAILED';info['timeout']=True;info['secondary_classification']='MUTATION_TIMEOUT'
    elif 'INFRASTRUCTURE_BLOCKED' in str(exc):info['classification']='INFRASTRUCTURE_BLOCKED'
    elif 'CANDIDATE_INVALID' in str(exc):info['classification']='CANDIDATE_INVALID'
    elif any(v in str(exc) for v in ('PATCH_EMPTY','MUTATION_TIMEOUT')):info['classification']='MUTATION_FAILED'
    else:info['classification']='HARNESS_FAILURE'
   finally:
    for proxy in active:
     if proxy.info is info:
      if not proxy.captured:capture(proxy)
      try:proxy.actual.remove(force=True)
      except docker.errors.NotFound:info["cleanup_already_removed"]=True
    archive.write(d/'after');info['archive_history']=[v.version_id for v in archive.history];info['lineage']=json.loads((d/'after/lineage.json').read_text());info['finished_at']=now();freeze_check();persist()
   print('ATTEMPT_END',case['id'],number,info['classification'],flush=True)
   if info['classification']=='REAL_REPAIR_PASS':break
   if info['classification'] in ('HARNESS_FAILURE','INFRASTRUCTURE_BLOCKED'):break
  cr['classification']=info['classification'];cr['VERIFIED_AFTER']=cr['classification']=='REAL_REPAIR_PASS';persist()
 REPORT['production_snapshot_unchanged']=True;REPORT['finished_at']=now();persist()
except Exception as exc:
 REPORT['fatal_error']=str(exc);REPORT['fatal_traceback']=traceback.format_exc();persist();raise
finally:
 for proxy in active:
  try:proxy.actual.remove(force=True)
  except Exception:pass
 if image is not None:
  try:client.images.remove(image.id);REPORT['image_removed']=True
  except Exception as exc:REPORT['image_cleanup_error']=str(exc)
 persist()
