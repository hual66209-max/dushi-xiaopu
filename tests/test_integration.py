"""MCP stdio and HTTP share one temporary save; does not touch a real game."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

async def test(folder):
    os.environ['JADE_DATA_DIR']=folder
    import web
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    server=web.HTTPServer(('127.0.0.1',0),web.Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    base=f'http://127.0.0.1:{server.server_port}'
    def request(path,method='GET',body=None,headers=None):
        req=Request(base+path,data=None if body is None else json.dumps(body).encode(),
                    headers=headers or {},method=method)
        try:
            with urlopen(req,timeout=4) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    try:
        code,initial=request('/api/save');assert code==200 and initial['save']['money']==10000
        assert request('/api/save',headers={'Host':'untrusted.example'})[0]==403
        params=StdioServerParameters(command=sys.executable,args=[str(ROOT/'mcp_server.py')],
            env={'JADE_DATA_DIR':folder,'PATH':os.environ.get('PATH','/usr/bin:/bin')})
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools();assert [t.name for t in tools.tools]==['jade_shop']
                result=await session.call_tool('jade_shop',{'text':'帮助'})
                assert not result.isError and any('领取800' in b.text for b in result.content if b.type=='text')
                result=await session.call_tool('jade_shop',{'text':'刷新'})
                assert not result.isError
                code,after=request('/api/save');assert code==200 and after['save']['money']==9900
                assert after['save']['xiaokeCurrent']['spent']==100
                payload={'revision':initial['revision'],'save':initial['save']}
                assert request('/api/save','POST',payload,{'Content-Type':'application/json','Origin':base})[0]==409
                assert request('/api/save','POST',payload,{'Content-Type':'application/json','Origin':'https://example.com'})[0]==403
                assert request('/api/save')[1]['save']['money']==9900
    finally:
        server.shutdown();server.server_close();worker.join()

with tempfile.TemporaryDirectory() as folder:
    asyncio.run(test(folder))
print('真实 MCP 握手、工具调用、网页读同一临时存档、旧页冲突与来源检查通过')
