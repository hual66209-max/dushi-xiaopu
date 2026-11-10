"""赌石小铺文字版第一步：打开存档、查看货架。"""
import fcntl
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import shutil
import sys
import tempfile
import time
from datetime import date

ROOT = Path(__file__).resolve().parent
SAVE = Path(os.environ.get('JADE_DATA_DIR', str(ROOT / 'data'))).expanduser().resolve() / 'save.json'


def _catalog():
    return json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))


def _write(path, data):
    fd, tmp = tempfile.mkstemp(prefix='.save-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _generate(tier):
    result = subprocess.run([(shutil.which('node') or 'node'), '--max-old-space-size=64', str(ROOT / 'engine.cjs'), 'generate', str(tier)],
                            text=True, capture_output=True, timeout=8, check=True)
    shelf = json.loads(result.stdout)
    if not isinstance(shelf, list) or len(shelf) != 5 or sum(s.get('zhen') is True for s in shelf) != 1:
        raise ValueError('货架生成失败')
    for number,stone in enumerate((s for s in shelf if not s['zhen']),1):
        stone['shelfNo']=number
    return shelf


def _ensure_shelf_numbers(save):
    for shelf in save['shops'].values():
        normal=[s for s in shelf if not s['zhen']]
        used=set()
        for stone in normal:
            if 'shelfNo' in stone:
                number=stone['shelfNo']
                if type(number) is not int or not 1<=number<=4 or number in used:
                    raise ValueError('货架编号异常')
                used.add(number)
        for stone in normal:
            if 'shelfNo' not in stone:
                number=next((n for n in range(1,5) if n not in used),None)
                if number is None:raise ValueError('货架普通石超过四块')
                stone['shelfNo']=number;used.add(number)


def _new():
    return {'money': 10000, 'maxWealth': 10000, 'tier': 0, 'unlockedTier': 0,
            'shelfVersion': 1, 'shops': {'0': _generate(0)}, 'owned': [], 'cabinet': [], 'history': [],
            'xiaokeLast': {'played': False, 'cuts': 0, 'spent': 0, 'net': 0},
            'xiaojieVisits': {'visited': False, 'cuts': 0, 'spent': 0, 'net': 0}}


def _stats(stat, flag, empty):
    if not stat[flag]:
        return empty
    net = stat['net']
    profit = ('净赚' if net >= 0 else '净亏') + f'¥{abs(net):,}'
    return f"切了{stat['cuts']}块，花¥{stat['spent']:,}，{profit}"


def _open(save,stone=None,active=None):
    names = '、'.join(_catalog()['tiers'][:save['unlockedTier'] + 1])
    lines=[f"💰 本金：{save['money']:,}",
        '🪨 AI上次：' + _stats(save['xiaokeLast'], 'played', '还没玩过'),
        '👀 玩家来过：' + _stats(save['xiaojieVisits'], 'visited', '还没来过')]
    if stone is not None:lines.append(_current_display(save,stone,active))
    lines.extend((f"🎒 珍藏柜：{len(save['cabinet'])}件",'🏪 能去：'+names))
    return '\n'.join(lines)


def _shelf(save, name):
    catalog = _catalog()
    if name not in catalog['tiers']:
        return '没有这家铺子。'
    tier = catalog['tiers'].index(name)
    if tier > save['unlockedTier']:
        return f'{name}还没解锁。'
    shelf = save['shops'].get(str(tier))
    if shelf is None:
        raise ValueError('已解锁铺子缺少货架')
    fee = catalog['fees'][tier]
    if not shelf:
        return f'货架空了，刷新¥{fee:,}'
    def detail(stone):
        r = stone['rind']
        attrs = ' '.join(catalog[key][r[key if key != 'colors' else 'color']]
                         for key in ('colors', 'fine', 'crack', 'song', 'mang'))
        name = re.sub(r'·\d+号$', '', stone['name'])
        return f"{name} {stone['weight']}kg ¥{stone['price']:,} 皮壳{stone['S']}｜{attrs}"
    normal = sorted((stone for stone in shelf if not stone['zhen']),key=lambda s:s['shelfNo'])
    crown = [stone for stone in shelf if stone['zhen']]
    lines = [f'{name} ｜ 刷新¥{fee:,}']
    lines.extend(f"{stone['shelfNo']}号 {detail(stone)}" for stone in normal)
    lines.extend('👑 镇店石 ' + detail(stone) for stone in crown)
    return '\n'.join(lines)


def _ordered(shelf):
    return (sorted((s for s in shelf if not s['zhen']),key=lambda s:s['shelfNo']), [s for s in shelf if s['zhen']])


def _selected(save, selection):
    shelf=save['shops'][str(save['tier'])]
    normal,crown=_ordered(shelf)
    if selection=='镇店':
        return (crown[0], '镇店石') if crown else (None, '')
    number=int(selection)
    return next(((s,f'{number}号') for s in normal if s['shelfNo']==number),(None,''))


def _npc_data():
    return json.loads((ROOT/'npc.json').read_text(encoding='utf-8'))


def _flaws(inner):
    crack=('无裂','有细裂','大裂贯穿')[inner['crack']]
    cotton=('无棉','少棉','重棉')[inner['cotton']]
    spot=('无黑点','有黑点')[inner['spot']]
    return f'{crack} {cotton} {spot}'


def _choose(lines):
    return lines[math.floor(random.random()*len(lines))]


def _raise(price):
    return price+max(10, math.floor(price*(0.10+random.random()*0.10)/10+0.5)*10)


def _purchase(save, stone, label, price):
    if save['money']<price:
        return f'本金不够，要¥{price:,}', False
    save['money']-=price
    current=save.setdefault('xiaokeCurrent',_round_stats())
    current['played']=True;current['spent']+=price;current['net']-=price
    save['shops'][str(save['tier'])]=[s for s in save['shops'][str(save['tier'])] if s['id']!=stone['id']]
    lights=save.get('torchReadings',{}).pop(stone['id'],None)
    stone['price']=price
    save['owned'].append(stone)
    save['activeCut']={'stoneId':stone['id'],'phase':'new','grindFees':0,'lights':lights}
    save.pop('pendingNpc',None)
    third='松花处' if stone['rind']['song'] else '底下'
    return f"买下 {label} ¥{price:,}｜本金 {save['money']:,}\n怎么切？一刀切 / 擦窗 顶上·腰上·{third} / 慢慢磨", True


def _buy(save, selection):
    stone,label=_selected(save,selection)
    if stone is None:
        if selection.isdigit() and 1<=int(selection)<=4:
            return f'{int(selection)}号已经没了',False
        return '货架上没有这块石头。',False
    if save['money']<stone['price']:
        return f"本金不够，要¥{stone['price']:,}",False
    roll=random.random()
    if roll<0.70:
        return _purchase(save,stone,label,stone['price'])
    info=_npc_data()
    pending={'stone_id':stone['id'],'tier':save['tier'],'label':label,'price':stone['price']}
    if roll<0.85:
        r=random.random()
        pending.update(kind='boss',total=1 if r<0.50 else 2 if r<0.85 else 3,done=1)
        pending['price']=_raise(pending['price'])
        save['pendingNpc']=pending
        return f"🧔{_choose(info['NPC_BOSS_INTROS'])}他出价 ¥{pending['price']:,}。跟 / 不要了",True
    kind='uncle' if roll<0.95 else 'shill'
    pending['kind']=kind
    save['pendingNpc']=pending
    lines=info['NPC_UNCLE_LINES' if kind=='uncle' else 'NPC_SHILL_LINES']
    return ('👴' if kind=='uncle' else '🗣️')+_choose(lines)+' 还要吗？（要 / 不要了）',True


def _pending(save, command):
    p=save['pendingNpc']
    if command not in ('跟','要','不要了'):
        return ('请先回答：跟 / 不要了。' if p['kind']=='boss' else '请先回答：要 / 不要了。'),False
    shelf=save['shops'][str(p['tier'])]
    stone=next((s for s in shelf if s['id']==p['stone_id']),None)
    if stone is None or p['tier']!=save['tier']:
        raise ValueError('待处理石头不存在')
    if command=='不要了':
        save.pop('pendingNpc')
        if p['kind']!='boss':
            return '好，不买了。',True
        save['shops'][str(p['tier'])]=[s for s in shelf if s['id']!=stone['id']]
        save.get('torchReadings',{}).pop(stone['id'],None)
        info=_npc_data()
        inner=stone['inner']
        diff=stone['value']-p['price']
        ratio=stone['value']/stone['price']
        tier=4 if ratio>=6 and inner['zhong']==5 and inner['color']>=5 else 0 if ratio<0.5 else 1 if ratio<1 else 2 if ratio<2.5 else 3
        save['history'].append({'id':stone['id'],'name':stone['name'],'date':date.today().isoformat(),
            'price':p['price'],'got':stone['value'],'tier':tier,'inner':inner,'method':'围观老板切石','kept':False,'watched':True})
        profit=('赚了' if diff>=0 else '亏了')+f'¥{abs(diff):,}'
        return f"🧔老板抱着{p['label']}走了，当场一刀……{info['zhong'][inner['zhong']]} {info['colors'][inner['color']]}｜{_flaws(inner)}｜{profit}",True
    if p['kind']=='boss' and command=='跟':
        if save['money']<p['price']:
            return f"本金不够，要¥{p['price']:,}",False
        if p['done']>=p['total']:
            return _purchase(save,stone,p['label'],p['price'])
        p['done']+=1
        p['price']=_raise(p['price'])
        return f"🧔老板又加价：「我出 ¥{p['price']:,}！」跟 / 不要了",True
    if p['kind']!='boss' and command=='要':
        return _purchase(save,stone,p['label'],p['price'])
    return ('请先回答：跟 / 不要了。' if p['kind']=='boss' else '请先回答：要 / 不要了。'),False


def _torch(save):
    tier=save['tier']
    shelf=save['shops'][str(tier)]
    if not shelf:
        return f"货架空了，刷新¥{_catalog()['fees'][tier]:,}",False
    cache=save.setdefault('torchReadings',{})
    needs=[s for s in shelf if s['id'] not in cache or any('hit' not in p for p in cache[s['id']])]
    if needs:
        result=subprocess.run([(shutil.which('node') or 'node'),'--max-old-space-size=64',str(ROOT/'engine.cjs'),'torch'],
            input=json.dumps(needs,ensure_ascii=False),text=True,capture_output=True,timeout=8,check=True)
        readings=json.loads(result.stdout)
        if len(readings)!=len(needs) or any(len(points)!=3 or any(type(p.get('hit')) is not bool for p in points) for points in readings):
            raise ValueError('打灯计算异常')
        for stone,points in zip(needs,readings):
            if stone['id'] not in cache:
                cache[stone['id']]=points
            else:
                old=cache[stone['id']]
                if len(old)!=3 or any(a['name']!=b['name'] for a,b in zip(old,points)):
                    raise ValueError('已有打灯点位不匹配')
                for a,b in zip(old,points):
                    a['hit']=b['hit']
    remarks={('强',True):'底下多半有色，种也不差',('强',False):'种水不错，偏白肉',
        ('中',True):'种和色都有些盼头，说不准',('中',False):'多半是白肉，种可能还行',
        ('弱',True):'可能有层薄色，也可能是松花晃眼',('弱',False):'没什么盼头，也说不准是皮太厚',
        ('暗',False):'皮厚或里面干，也有好货闷着'}
    ranks={'暗':0,'弱':1,'中':2,'强':3}
    def line(label,stone):
        points=cache[stone['id']]
        best=max(points,key=lambda p:(ranks[p['level']], p['colored'] if p['level']!='暗' else False))
        def show(p):
            return p['name']+'·'+p['level']+('有色' if p['colored'] else '无色' if p['level']!='暗' else '') if p['level']!='暗' else p['name']+'·暗'
        result=label+' '+' '.join(show(p) for p in points)+'｜'+remarks[(best['level'],best['colored'] if best['level']!='暗' else False)]
        names={'顶':'顶上','腰':'腰上','松花':'松花处','底':'底下'}
        hit=[names[p['name']] for p in points if p['hit']]
        if hit:
            amount={1:'这处',2:'这两处',3:'这三处'}[len(hit)]
            result+='（'+'、'.join(hit)+amount+'跟别处不太一样）'
        return result
    normal,crown=_ordered(shelf)
    result=[line(f"{s['shelfNo']}号",s) for s in normal]+[line('👑',s) for s in crown]
    return '💡 打灯仅供参考，皮壳厚度和颜色会干扰结果哦~\n' + '\n'.join(result),bool(needs)


def _round_stats():
    return {'played':False,'cuts':0,'spent':0,'net':0}


def _active(save):
    owned=save['owned']
    if len(owned)>1:
        raise ValueError('手里有多块旧石头，不能自动选择')
    if not owned:
        if save.get('activeCut'):
            raise ValueError('正在切的石头不存在')
        return None,None
    stone=owned[0]
    active=save.get('activeCut')
    if active is None:
        active={'stoneId':stone['id'],'phase':'new','grindFees':0,
                'lights':save.get('torchReadings',{}).get(stone['id'])}
        save['activeCut']=active
        current=save.setdefault('xiaokeCurrent',_round_stats())
        current['played']=True;current['spent']+=stone['price'];current['net']-=stone['price']
    if active.get('stoneId')!=stone['id']:
        raise ValueError('正在切的石头不匹配')
    return stone,active


def _engine(action, payload):
    proc=subprocess.run([(shutil.which('node') or 'node'),'--max-old-space-size=64',str(ROOT/'engine.cjs'),action],
                        input=json.dumps(payload,ensure_ascii=False),text=True,capture_output=True,timeout=8,check=True)
    return json.loads(proc.stdout)


def _lights(stone,active):
    points=active.get('lights')
    if not points or any('hit' not in p for p in points):
        generated=_engine('torch',[stone])[0]
        if points:
            if len(points)!=3 or any(a['name']!=b['name'] for a,b in zip(points,generated)):
                raise ValueError('已有打灯点位不匹配')
            for a,b in zip(points,generated):a['hit']=b['hit']
        else:
            points=generated
        active['lights']=points
    def show(p):
        return p['name']+'·'+p['level']+('有色' if p['colored'] else '无色') if p['level']!='暗' else p['name']+'·暗'
    result=' '.join(show(p) for p in points)
    names={'顶':'顶上','腰':'腰上','松花':'松花处','底':'底下'}
    hit=[names[p['name']] for p in points if p['hit']]
    if hit:result+='（'+'、'.join(hit)+{1:'这处',2:'这两处',3:'这三处'}[len(hit)]+'跟别处不太一样）'
    return result


def _current_display(save,stone,active):
    rind=stone['rind'];catalog=_catalog()
    attrs=' '.join(catalog[key][rind[key if key!='colors' else 'color']] for key in ('colors','fine','crack','song','mang'))
    lines=[f"🔪 正在切：{stone['name']} {stone['weight']}kg ¥{stone['price']:,}｜{attrs}",
           '   打灯：'+_lights(stone,active)]
    info=_npc_data()
    if active.get('window'):
        w=active['window'];li=w['inner']
        lines.append(f"   已擦窗{w['position']}：局部 {info['zhong'][li['zhong']]} {info['colors'][li['color']]}｜窗口报价¥{w['offer']:,}")
    if active['phase'] in ('grind1','grind2'):
        li=active['local'];visible=info['zhong'][li['zhong']]
        if active['phase']=='grind2':visible+=' '+info['colors'][li['color']]
        lines.append(f"   已磨：局部 {visible}｜磨口报价¥{active['offer']:,}")
    if active['phase']=='revealed':
        li=stone['inner'];lines.append(f"   已切开：{info['zhong'][li['zhong']]} {info['colors'][li['color']]}｜{_flaws(li)}｜估价¥{stone['value']:,}")
    choices={'new':'切 / 擦窗 / 磨','window':'卖 / 切 / 磨','grind1':'卖 / 磨',
             'grind2':'卖 / 磨','revealed':'卖 / 收藏'}
    lines.append('   接下来：'+choices[active['phase']])
    return '\n'.join(lines)


def _refresh_unlocked(save):
    thresholds=[0,15000,20000,50000,100000]
    while save['unlockedTier']<4:
        next_tier=save['unlockedTier']+1
        balance=save['maxWealth'] if next_tier==1 else save['money']
        if balance<thresholds[next_tier]:break
        if str(next_tier) not in save['shops']:
            save['shops'][str(next_tier)]=_generate(next_tier)
        save['unlockedTier']=next_tier


def _finish(save,stone,active,keep):
    phase=active['phase']
    if keep and phase!='revealed':return '这块还没有完全切开，不能收藏。'
    if phase not in ('window','grind1','grind2','revealed'):return '先把这块石头切开或擦窗、磨一磨。'
    offer=stone['value'] if phase=='revealed' else active['offer']
    received=0 if keep else offer
    current=save.setdefault('xiaokeCurrent',_round_stats())
    current['played']=True;current['cuts']+=1;current['net']+=received
    if keep:
        item=dict(stone);item['value']=offer;item['keptDay']=date.today().isoformat()
        item.pop('_winOffer',None)
        item['keptMethod']=active.get('method','一刀切');save['cabinet'].append(item)
    else:
        save['money']+=offer;save['maxWealth']=max(save['maxWealth'],save['money'])
    ratio=offer/stone['price'];inner=stone['inner']
    tier=4 if ratio>=6 and inner['zhong']==5 and inner['color']>=5 else 0 if ratio<.5 else 1 if ratio<1 else 2 if ratio<2.5 else 3
    save['history'].append({'id':stone['id'],'name':stone['name'],'date':date.today().isoformat(),
        'price':stone['price'],'got':received,'tier':tier,'inner':inner,'method':active.get('method','切石'),
        'kept':keep,'grindFees':active['grindFees']})
    save['owned']=[];save.pop('activeCut',None);save.get('torchReadings',{}).pop(stone['id'],None)
    if not keep:_refresh_unlocked(save)
    return f"{'收藏' if keep else '卖出'} ¥{offer:,}｜本金 {save['money']:,}"


def _cabinet(save):
    info=_npc_data();lines=[]
    for i,item in enumerate(save['cabinet'],1):
        li=item['inner'];lines.append(f"{i}. {item['name']}｜{info['zhong'][li['zhong']]} {info['colors'][li['color']]}｜{_flaws(li)}｜估值¥{item['value']:,}")
    return '\n'.join(lines) if lines else '珍藏柜是空的。'


def _sell_cabinet(save,index):
    if index<1 or index>len(save['cabinet']):return '珍藏柜里没有这一件。'
    item=save['cabinet'].pop(index-1);value=item['value']
    save['money']+=value;save['maxWealth']=max(save['maxWealth'],save['money'])
    for entry in save['history']:
        if entry['id']==item['id'] and entry.get('kept'):
            entry['got']=value;entry['kept']=False;break
    current=save.setdefault('xiaokeCurrent',_round_stats());current['played']=True;current['net']+=value
    _refresh_unlocked(save)
    return f"卖出柜里{index} ¥{value:,}｜本金 {save['money']:,}"


def _cut(save,stone,active,command):
    phase=active['phase'];info=_npc_data()
    if command=='切':
        if phase not in ('new','window'):return '接下来：'+('卖 / 收藏' if phase=='revealed' else '卖 / 磨')
        active.update(phase='revealed',method='一刀切',offer=stone['value'])
        li=stone['inner'];diff=stone['value']-stone['price']-active['grindFees']
        return f"一刀下去……{info['zhong'][li['zhong']]} {info['colors'][li['color']]}｜{_flaws(li)}｜估价¥{stone['value']:,}（{diff:+,}）\n卖 / 收藏"
    if command.startswith('擦窗'):
        if stone.get('windowed') or active.get('window'):return '这块石头已经擦过窗了。'
        third='松花处' if stone['rind']['song'] else '底下'
        positions={'顶上':'顶','腰上':'腰',third:'松花' if stone['rind']['song'] else '底'}
        position=command[2:].strip()
        if phase!='new':return '现在不能擦窗。'
        if position not in positions:return f'这块能擦：顶上、腰上、{third}'
        result=_engine('window',{'stone':stone,'position':positions[position]})
        stone['winDir']=result['dir'];stone['windowed']=True;stone['_winOffer']=result['offer']
        active.update(phase='window',window={'position':position,'inner':result['inner'],'offer':result['offer']},
                      offer=result['offer'],method='擦窗后窗口卖出')
        li=result['inner']
        return f"擦开{position}……局部 {info['zhong'][li['zhong']]} {info['colors'][li['color']]}｜窗口报价¥{result['offer']:,}\n卖 / 切 / 磨"
    if command=='磨':
        if phase not in ('new','window','grind1','grind2'):return '接下来：卖 / 收藏'
        step=0 if phase=='new' else 1 if phase in ('window','grind1') else 2
        fee=max(20,min(500,math.floor(stone['price']*.01/10+.5)*10))
        if save['money']<fee:return f'本金不够，磨工费要¥{fee:,}'
        result=None if step==2 else _engine('grind',{'stone':stone,'step':step})
        save['money']-=fee;active['grindFees']+=fee;stone['grindStep']=max(stone.get('grindStep',0),step+1)
        current=save.setdefault('xiaokeCurrent',_round_stats());current['played']=True;current['spent']+=fee;current['net']-=fee
        if step==2:
            active.update(phase='revealed',method='慢慢磨',offer=stone['value'])
            li=stone['inner'];diff=stone['value']-stone['price']-active['grindFees']
            return f"磨透了……{info['zhong'][li['zhong']]} {info['colors'][li['color']]}｜{_flaws(li)}｜估价¥{stone['value']:,}（{diff:+,}）\n卖 / 收藏"
        active.update(phase='grind1' if step==0 else 'grind2',local=result['inner'],offer=result['offer'],method=f'磨到一半卖出（第{step+1}步）')
        li=result['inner'];visible=info['zhong'][li['zhong']] if step==0 else info['colors'][li['color']]
        return f"磨开第{step+1}步……局部 {visible}｜磨口报价¥{result['offer']:,}\n卖 / 磨"
    if command=='卖':return _finish(save,stone,active,False)
    if command=='收藏':return _finish(save,stone,active,True)
    return '先把手里这块切完。'


def run(command, path=SAVE):
    command = str(command or '').strip()
    if command=='一刀切':command='切'
    known=(command in ('帮助','打开','刷新','打灯','跟','要','不要了','切','磨','卖','收藏','看珍藏柜','领取800') or
           command.startswith('擦窗') or (command.startswith('去') and bool(command[1:].strip())) or
           bool(re.fullmatch(r'买\s*(?:[0-9]+|镇店)',command)) or bool(re.fullmatch(r'卖\s*柜里\s*[0-9]+',command)))
    help_text=('打开：查看本金、统计和能去的铺子。\n去 铺子名：查看货架，例如“去 垃圾铺”。\n'
               '刷新：付费刷新当前铺子。\n打灯：查看当前货架的打灯表现，照到和别处不一样的地方会提示。\n'
               '买 货架序号，如：买 1 / 买 镇店；遇到 NPC 时按提示说“跟”“要”或“不要了”。\n'
               '切 / 擦窗 顶上、腰上或松花处、底下 / 磨：处理手里的石头，每块只能擦窗一次。\n'
               '卖 / 收藏：处理切好的石头；看珍藏柜 / 卖 柜里1：查看或卖掉珍藏。\n'
               '买不起所有可用货架上的石头且手里没有石头时，可说“领取800”获得800本金。')
    path = Path(path)
    if command=='帮助' and not path.exists():
        return help_text
    if not known and not path.exists():
        return '请说“帮助”查看可用动作。'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + '.lock', 'a', encoding='utf-8') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            with open(path, encoding='utf-8') as source:
                save = json.load(source)
        else:
            save = _new()
            _write(path, save)
        _ensure_shelf_numbers(save)
        if not known and not save.get('pendingNpc'):
            return '请说“帮助”查看可用动作。'
        now=time.time()
        if command=='打开' and not save.get('pendingNpc'):
            last=save.get('lastActionAt')
            if isinstance(last,(int,float)) and now-last>3600:
                save['xiaokeLast']=save.get('xiaokeCurrent',_round_stats())
                save['xiaokeCurrent']=_round_stats()
        if known:save['lastActionAt']=now
        save.setdefault('xiaokeCurrent',_round_stats())
        if save.get('pendingNpc'):
            result,changed=_pending(save,command)
            if known or changed:_write(path,save)
            return result
        if command=='帮助':
            _write(path,save)
            return help_text
        stone,active=_active(save)
        if command == '打开':
            result = _open(save,stone,active)
            if save['xiaojieVisits']['visited']:
                save['xiaojieVisits'] = {'visited': False, 'cuts': 0, 'spent': 0, 'net': 0}
            _write(path,save)
            return result
        if command=='看珍藏柜':
            result=_cabinet(save);_write(path,save);return result
        cabinet_match=re.fullmatch(r'卖\s*柜里\s*([0-9]+)',command)
        if cabinet_match:
            result=_sell_cabinet(save,int(cabinet_match.group(1)));_write(path,save);return result
        if stone is not None:
            result=_cut(save,stone,active,command);_write(path,save);return result
        if command in ('切','磨','卖','收藏') or command.startswith('擦窗'):
            _write(path,save);return '手里没有正在切的石头。'
        if command.startswith('去'):
            name=command[1:].strip()
            result=_shelf(save,name)
            catalog=_catalog()
            if name in catalog['tiers'] and catalog['tiers'].index(name)<=save['unlockedTier']:
                tier=catalog['tiers'].index(name)
                if tier!=save['tier']:
                    save['tier']=tier
            _write(path,save)
            return result
        if command=='领取800':
            prices=[s['price'] for tier in range(save['unlockedTier']+1) for s in save['shops'].get(str(tier),[])]
            eligible=save['money'] < min(prices) if prices else save['money'] < 200
            if not eligible:
                _write(path,save)
                return '还没有达到领取条件：手头的钱还能买到石头。'
            save['money']+=800
            save['maxWealth']=max(save['maxWealth'],save['money'])
            _write(path,save)
            return f"领到800本金｜本金 {save['money']:,}"
        if command=='刷新':
            tier=save['tier'];fee=_catalog()['fees'][tier]
            if save['money']<fee:
                _write(path,save)
                return f'本金不够，刷新要¥{fee:,}'
            new=_generate(tier)
            for stone in save['shops'][str(tier)]:
                save.get('torchReadings',{}).pop(stone['id'],None)
            save['shops'][str(tier)]=new;save['money']-=fee
            current=save['xiaokeCurrent'];current['played']=True;current['spent']+=fee;current['net']-=fee
            _write(path,save)
            return _shelf(save,_catalog()['tiers'][tier])
        if command=='打灯':
            result,changed=_torch(save)
        elif command.startswith('买'):
            result,changed=_buy(save,re.fullmatch(r'买\s*([0-9]+|镇店)',command).group(1))
        else:
            _write(path,save);return '当前没有需要回答的 NPC。'
        _write(path,save)
        return result


def tool_result(command):
    try:
        return run(command)
    except (OSError, ValueError, KeyError, IndexError, TypeError, subprocess.SubprocessError):
        return '赌石存档暂时无法读取，原数据没有修改。'


if __name__ == '__main__':
    try:
        print(run(' '.join(sys.argv[1:])))
    except (OSError, ValueError, KeyError, IndexError, TypeError, subprocess.SubprocessError):
        print('赌石存档暂时无法读取，原数据没有修改。')
        sys.exit(1)
