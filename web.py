"""Local-only browser entry for the same save as the MCP tool."""
import fcntl
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

import game

ROOT=Path(__file__).resolve().parent
LIMIT=2*1024*1024
MUTABLE={'money','maxWealth','tier','unlockedTier','shops','owned','cabinet','history',
         'activeCut','pendingNpc','torchReadings','xiaojieVisits','shelfVersion'}

def revision(raw):return hashlib.sha256(raw).hexdigest()

def read_save(path):
    with open(path,'rb') as source:raw=source.read(LIMIT+1)
    if len(raw)>LIMIT:raise ValueError('存档过大')
    data=json.loads(raw)
    if not isinstance(data,dict):raise ValueError('存档格式异常')
    return raw,data

def snapshot(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(str(path)+'.lock','a',encoding='utf-8') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        if not path.exists():game._write(path,game._new())
        raw,data=read_save(path)
        return {'revision':revision(raw),'save':data}

def validate(old,new):
    if not isinstance(new,dict):raise ValueError('存档格式异常')
    if any(k not in new or new[k]!=v for k,v in old.items() if k not in MUTABLE):raise ValueError('其他字段被改动')
    if any(k not in old and k not in MUTABLE for k in new):raise ValueError('未知字段')
    if any(k not in new for k in ('money','maxWealth','tier','unlockedTier','shops','owned','cabinet','history','xiaojieVisits')):raise ValueError('缺少字段')
    if type(new['money']) is not int or new['money']<0 or type(new['maxWealth']) is not int:raise ValueError('金额异常')
    if type(new['tier']) is not int or type(new['unlockedTier']) is not int or not 0<=new['tier']<=new['unlockedTier']<=4:raise ValueError('铺子状态异常')
    if not isinstance(new['shops'],dict) or any(not isinstance(v,list) for v in new['shops'].values()):raise ValueError('货架异常')
    if any(not isinstance(new[k],list) for k in ('owned','cabinet','history')) or len(new['owned'])>1:raise ValueError('石头状态异常')
    visit=new['xiaojieVisits'];previous=old.get('xiaojieVisits',{})
    if not isinstance(visit,dict) or set(visit)!={'visited','cuts','spent','net'} or type(visit['visited']) is not bool:raise ValueError('玩家统计异常')
    if any(type(visit[k]) is not int for k in ('cuts','spent','net')) or visit['cuts']<0 or visit['spent']<0:raise ValueError('玩家统计异常')
    if previous.get('visited') and (not visit['visited'] or visit['cuts']<previous.get('cuts',0) or visit['spent']<previous.get('spent',0)):raise ValueError('玩家统计不能被网页清空')
    for shelf in new['shops'].values():
        if any(not isinstance(s,dict) for s in shelf):raise ValueError('货架异常')
        normal=[s for s in shelf if not s.get('zhen')]
        numbers=[s.get('shelfNo') for s in normal]
        if len(normal)>4 or sum(bool(s.get('zhen')) for s in shelf)>1:raise ValueError('货架异常')
        if any(type(n) is not int or not 1<=n<=4 for n in numbers) or len(set(numbers))!=len(numbers):raise ValueError('编号异常')
    if new['owned']:
        active=new.get('activeCut')
        if not isinstance(active,dict) or active.get('stoneId')!=new['owned'][0].get('id'):raise ValueError('正在切的石头不匹配')
    elif new.get('activeCut'):raise ValueError('正在切的石头不存在')

def save_update(path,expected,new):
    with open(str(path)+'.lock','a',encoding='utf-8') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        raw,old=read_save(path)
        if expected!=revision(raw):return None
        validate(old,new)
        encoded=json.dumps(new,ensure_ascii=False).encode()
        if len(encoded)>LIMIT:raise ValueError('存档过大')
        game._write(path,new)
        return revision(path.read_bytes())

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def allowed_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
    def send(self,status,body,kind='application/json; charset=utf-8'):
        if isinstance(body,dict):body=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',kind)
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self' 'unsafe-inline' data:; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if not self.allowed_host():return self.send(403,{'ok':False})
        try:
            if self.path in ('/','/index.html'):return self.send(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
            if self.path=='/api/save':return self.send(200,{'ok':True,**snapshot(game.SAVE)})
            self.send(404,{'ok':False})
        except (OSError,ValueError,json.JSONDecodeError):self.send(500,{'ok':False,'error':'存档暂时无法读取'})
    def do_POST(self):
        if not self.allowed_host():return self.send(403,{'ok':False})
        if self.path!='/api/save':return self.send(404,{'ok':False})
        origins=(f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}')
        if self.headers.get('Origin') not in origins:return self.send(403,{'ok':False,'error':'来源不允许'})
        if self.headers.get_content_type()!='application/json':return self.send(415,{'ok':False,'error':'格式不允许'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=LIMIT:raise ValueError('请求大小异常')
            payload=json.loads(self.rfile.read(size))
            if not isinstance(payload,dict) or set(payload)!={'revision','save'}:raise ValueError('请求格式异常')
            updated=save_update(game.SAVE,payload['revision'],payload['save'])
            if updated is None:return self.send(409,{'ok':False,'error':'存档已更新，请重新打开'})
            self.send(200,{'ok':True,'revision':updated})
        except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):self.send(400,{'ok':False,'error':'保存失败，原存档未更改'})

if __name__=='__main__':
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8088
    http=HTTPServer(('127.0.0.1',port),Handler)
    print(f'赌石小铺：http://127.0.0.1:{http.server_port}/',flush=True)
    http.serve_forever()
