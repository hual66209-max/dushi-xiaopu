import copy
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as folder:
    os.environ['JADE_DATA_DIR']=folder
    import game,web
    game._generate=lambda tier:[]
    path=game.SAVE
    assert '领取800' in game.run('帮助') and not path.exists()
    initial=web.snapshot(path)
    assert initial['save']['money']==10000
    assert '没有达到领取条件' in game.run('领取800')
    data=json.loads(path.read_text());data['money']=199;data['maxWealth']=10000
    data['xiaokeCurrent']={'played':False,'cuts':0,'spent':0,'net':0}
    before_stats=copy.deepcopy(data['xiaokeCurrent']);game._write(path,data)
    assert '领到800本金' in game.run('领取800')
    result=json.loads(path.read_text())
    assert result['money']==999 and result['xiaokeCurrent']==before_stats and result['maxWealth']==10000
    assert '没有达到领取条件' in game.run('领取800')
    data['money']=250;data['unlockedTier']=1;data['shops']={'0':[{'price':200,'zhen':False,'shelfNo':1}],'1':[{'price':1000,'zhen':False,'shelfNo':1}]}
    game._write(path,data);assert '没有达到领取条件' in game.run('领取800')
    data['shops']['0']=[];game._write(path,data)
    assert '领到800本金' in game.run('领取800')
    data=json.loads(path.read_text());data['money']=0
    data['owned']=[{'id':'held'}];data['activeCut']={'stoneId':'held','phase':'new','grindFees':0}
    game._write(path,data);assert '先把手里这块切完' in game.run('领取800')
    data['owned']=[];data.pop('activeCut');data['shops']={'0':[],'1':[]};game._write(path,data)
    snap=web.snapshot(path);game.run('领取800')
    stale=copy.deepcopy(snap['save']);stale['money']=1
    assert web.save_update(path,snap['revision'],stale) is None
    assert web.snapshot(path)['save']['money']==800
print('独立存档、破产判定、领取及防重复、统计保持、网页旧版本保护通过')
