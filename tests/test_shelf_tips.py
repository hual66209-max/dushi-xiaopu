import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('jade_game', Path(__file__).resolve().parents[1] / 'game.py')
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)
game._catalog = lambda: {
    'tiers': ['垃圾铺'], 'fees': [100],
    'colors': ['黄沙皮'], 'fine': ['皮细'], 'crack': ['无裂'],
    'song': ['无松花'], 'mang': ['无蟒带'],
}

def stone(number, internal, crown=False):
    return {'name': f'角石料·{internal}号', 'weight': 2, 'price': 200,
            'S': 50, 'rind': dict(color=0, fine=0, crack=0, song=0, mang=0),
            'shelfNo': number, 'zhen': crown, 'id': str(internal)}

shelf = [stone(2, 586), stone(1, 763), stone(0, 999, True)]
save = {'tier': 0, 'unlockedTier': 0, 'shops': {'0': shelf}}
text = game._shelf(save, '垃圾铺')
assert '1号 角石料' in text and '2号 角石料' in text and '👑 镇店石 角石料' in text
assert not any(number in text for number in ('763号', '586号', '999号'))
assert game._selected(save, '1')[0] is shelf[1]
assert game._selected(save, '镇店')[0] is shelf[2]
assert shelf[1]['name'] == '角石料·763号'
points = [dict(name=name, level='中', colored=False, hit=False) for name in ('顶', '腰', '底')]
save['torchReadings'] = {s['id']: points for s in shelf}
light_text, changed = game._torch(save)
assert light_text.startswith('💡 打灯仅供参考，皮壳厚度和颜色会干扰结果哦~\n')
assert '1号 顶·中无色' in light_text and not changed
with tempfile.TemporaryDirectory() as folder:
    help_text = game.run('帮助', Path(folder) / 'save.json')
    assert '买 货架序号，如：买 1 / 买 镇店' in help_text
    assert '领取800' in help_text
    assert not (Path(folder) / 'save.json').exists()
print('货架序号、帮助示例、打灯提示和分享版兜底通过')
