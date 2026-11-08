/* ================= 工具与随机 ================= */
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
var _uid=Date.now()%100000;
function rnd(){return Math.random();}
function U(a,b){return a+rnd()*(b-a);}
function pickW(weights,r){var s=0,i;for(i=0;i<weights.length;i++)s+=weights[i];var x=(r||rnd)()*s;for(i=0;i<weights.length;i++){x-=weights[i];if(x<=0)return i;}return weights.length-1;}
function fmt(n){return "¥"+Math.round(n).toLocaleString("zh-CN");}
function visibleDate(s){ return s && !/^第\s*\d+\s*天$/.test(s) ? s+" · " : ""; }
function todayStr(){var d=new Date();return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function toast(msg){var t=document.getElementById("toast");t.textContent=msg;t.classList.add("show");clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove("show");},2400);}

/* ================= 数据表 ================= */
var RIND_COLORS=[{n:"黄沙皮",c:0xc9a86a,s:6},{n:"黑乌沙",c:0x4a4238,s:4},{n:"白盐沙",c:0xd8d2c2,s:2},{n:"红蜡壳",c:0x9c5a3c,s:0},{n:"青皮",c:0x6d7a6a,s:0},{n:"灰皮",c:0x8d8d84,s:-2},{n:"褐皮",c:0x77563c,s:-4},{n:"铁锈皮",c:0x7a4a30,s:-6}];
var RIND_FINE=[{n:"极细",s:12},{n:"细腻",s:6},{n:"中等",s:0},{n:"粗糙",s:-7},{n:"极粗",s:-13}];
var RIND_CRACK=[{n:"无裂",s:10},{n:"少量细裂",s:2},{n:"明显裂纹",s:-9},{n:"满布裂绺",s:-18}];
var RIND_SONG=[{n:"无松花",s:-8},{n:"星点松花",s:3},{n:"片状松花",s:9},{n:"满布松花",s:15}];
var RIND_MANG=[{n:"无蟒带",s:-4},{n:"细蟒带",s:3},{n:"明显蟒带",s:8},{n:"缠绕蟒带",s:12}];
var ZHONG=[{n:"豆种",m:0.3,glow:0.08},{n:"糯种",m:0.6,glow:0.25},{n:"糯冰种",m:1.0,glow:0.45},{n:"冰种",m:1.8,glow:0.65},{n:"高冰种",m:3.0,glow:0.82},{n:"玻璃种",m:5.5,glow:1.0}];
var COLOR=[{n:"无色",m:0.4,hex:0xe9ebe6,css:"#e9ebe6"},{n:"淡绿",m:0.7,hex:0xbfe3c0,css:"#bfe3c0"},{n:"晴水绿",m:1.0,hex:0x8fd0a8,css:"#8fd0a8"},{n:"阳绿",m:1.8,hex:0x4cc463,css:"#4cc463"},{n:"浓绿",m:2.6,hex:0x1da851,css:"#1da851"},{n:"满绿",m:4.2,hex:0x00a344,css:"#00a344"},{n:"帝王绿",m:6.0,hex:0x007a3d,css:"#007a3d"},
/* 稀有色（下标 7–10）：切开结果小赚及以上都有机会出，按石头所在铺子档次累加解锁，见 RARE_UNLOCK / rollRareColor。春带彩是多色混合（绿+紫+金），hex 只作底色，切面另用多色贴图渲染 */
{n:"黄翡",m:5.0,hex:0xe8a81c,css:"#e8a81c"},{n:"蓝水",m:5.6,hex:0x2f8fc4,css:"#2f8fc4"},{n:"紫罗兰",m:6.8,hex:0x9b6dd6,css:"#9b6dd6"},{n:"春带彩",m:9.5,hex:0x00a344,css:"linear-gradient(135deg,#00a344 0 38%,#9b6dd6 38% 72%,#e8a81c 72% 100%)"}];
var RARE_YELLOW=7, RARE_BLUE=8, RARE_VIOLET=9, RARE_SPRING=10;
function isRareColor(ci){ return ci>=RARE_YELLOW && ci<=RARE_SPRING; }
/* 稀有色累加解锁：按「石头所在档次」查，不按玩家当前所在档。
   小店解锁黄翡 / 商铺解锁蓝水 / 高档行解锁紫罗兰 / 拍卖场解锁春带彩，低档解锁的在更高档全部保留（只增不减）。 */
var RARE_UNLOCK=[{c:RARE_YELLOW,tier:1},{c:RARE_BLUE,tier:2},{c:RARE_VIOLET,tier:3},{c:RARE_SPRING,tier:4}];
/* 稀有色价值系数：切出稀有色时，真实价值在原盈亏比上再乘这个系数——
   一块本来小赚的料切出蓝水（×2），卖出价直接翻倍、按大涨结算 */
var RARE_MULT={}; RARE_MULT[RARE_YELLOW]=1.5; RARE_MULT[RARE_BLUE]=2; RARE_MULT[RARE_VIOLET]=2.5; RARE_MULT[RARE_SPRING]=4;
function unlockedRares(ti){ return RARE_UNLOCK.filter(function(e){ return (ti||0)>=e.tier; }); }
/* 稀有色出现概率只看切开结果（最终盈亏比）：小赚 5% / 大涨 12% / 真爆 30%，垮和小亏不出 */
function rareChanceForR(R){ return R>=6?0.30 : R>=2.5?0.12 : R>=1?0.05 : 0; }
/* roll 一次稀有色：没中或本档还没解锁任何稀有色返回 -1。
   中了之后在已解锁的稀有色里等权重抽一种；春带彩只在大涨 / 真爆里出，且权重是其他稀有色的一半 */
function rollRareColor(ti, R){
  var chance=rareChanceForR(R);
  if(chance<=0 || rnd()>=chance) return -1;
  var pool=unlockedRares(ti).filter(function(e){ return e.c!==RARE_SPRING || R>=2.5; });
  if(!pool.length) return -1;
  var weights=pool.map(function(e){ return e.c===RARE_SPRING?0.5:1; });
  return pool[pickW(weights)].c;
}
function rarePoolText(ti){
  var pool=unlockedRares(ti);
  if(!pool.length) return "这一档<b>还没解锁稀有色</b>（从小店起解锁黄翡），切出小赚也只会出绿色系。";
  var parts=pool.map(function(e){ return "<b>"+COLOR[e.c].n+" ×"+RARE_MULT[e.c]+"</b>"; });
  var txt="这一档已解锁的稀有色（累加）："+parts.join(" · ")+"。只要切开结果是<b>小赚及以上</b>就有机会出稀有色：小赚 <b>5%</b> · 大涨 <b>12%</b> · 真爆 <b>30%</b>，出稀有色按后面的系数抬价——小赚料切出蓝水（×2）直接变大涨。";
  if(pool.some(function(e){ return e.c===RARE_SPRING; })) txt+="春带彩只在大涨和真爆里出，比别的稀有色更难碰。";
  return txt;
}
var FLAW_CRACK=[{n:"无裂",m:1.0},{n:"有细裂",m:0.7},{n:"大裂贯穿",m:0.35}];
var FLAW_COTTON=[{n:"无棉",m:1.0},{n:"少棉",m:0.85},{n:"重棉",m:0.6}];
var FLAW_SPOT=[{n:"无黑点",m:1.0},{n:"有黑点",m:0.8}];
var TIER_W_ZHONG=[[34,30,18,10,5,3],[16,26,24,18,10,6],[4,12,22,28,20,14]];
var TIER_W_COLOR=[[36,26,16,11,6,3,2],[16,24,22,18,11,6,3],[4,10,18,26,20,14,8]];
var TIER_W_CRACK=[[16,34,50],[34,40,26],[62,28,10]];
var TIER_W_COTTON=[[20,36,44],[38,38,24],[64,26,10]];
var TIER_W_SPOT=[[52,48],[66,34],[82,18]];
var STONE_NAMES=["老坑料","河磨石","山石料","水石料","半山半水","角石料","砾石料","原生料"];
/* 五档铺子：解锁门槛、标价区间、五档结果分布（垮/小亏/小赚/大涨/真爆，单位 %） */
var TIERS=[
  { name:"垃圾铺", unlock:0,      pMin:200,   pMax:2000,   dist:[48,24,20,6,2] },
  { name:"小店",   unlock:15000,  pMin:1000,  pMax:5000,   dist:[50,25,18,5,2] },
  { name:"商铺",   unlock:20000,  pMin:3000,  pMax:15000,  dist:[50,26,17,5,2] },
  { name:"高档行", unlock:50000,  pMin:8000,  pMax:40000,  dist:[51,27,15,5,2] },
  { name:"拍卖场", unlock:100000, pMin:20000, pMax:100000, dist:[35,27,22,13,3], catR:[[0.02,0.35],[0.5,0.8],[1.0,1.5],[2.5,2.75],[6.0,6.5]], skew:8 }
];
/* 五个结果档的盈亏比 R 区间：垮 / 小亏 / 小赚 / 大涨(2.5–4倍) / 真爆(6–12倍)。
   前四档按「长期略亏、0.9 上下」标定（含稀有色系数抬价与乘完系数后 24 倍封顶，用页面同一公式蒙特卡洛实测）：
   平均回报 0.90 / 0.90 / 0.91 / 0.91——这是闭着眼随机买的基准线，
   会看的人靠皮壳、打灯、开窗挑石，能把自己那份回报往回拉一点，但拉不过庄家太多。
   拍卖场用自己的 catR / skew（见 TIERS）：它是最高档，定位是「全场最肥，也最狠」——
   平均回报标定在 1.0–1.05（实测 ≈1.04，上限不超 1.15），是五档里唯一略正的一档；
   但它的惩罚不靠回报率、靠「痛」：垮率 35% 不动，单块标价 ¥20,000–¥100,000，
   一垮就是几万、连垮三块十几万就没了，照样让人手抖。调参办法：分布取垮35/小亏27/小赚22/大涨13/真爆3
   （垮、小赚、大涨保持原数；小亏 +2、真爆 −2——真爆 5% 时光它一项按 6 倍下限叠稀有色系数的
   算术下限就占约 0.42，只压区间实测仍是 1.31），再把每个结果档的抽取区间压向各自下限
   （垮 [0.02,0.35] / 小亏 [0.5,0.8] / 小赚 [1.0,1.5] / 大涨 [2.5,2.75] / 真爆 [6.0,6.5]），
   向低端倾斜加大到 skew 8（别档 1.8），用页面真实公式复测才落进 1.0–1.05。 */
var CAT_R=[[0.02,0.5],[0.5,1.0],[1.0,2.5],[2.5,4.0],[6.0,12.0]];
/* 进货费：付钱给当前档换一批新货，按档次定价。 */
var RESTOCK_FEE=[100,300,1000,3000,8000];
/* 每档「买一块的平均回报」：用页面同一公式蒙特卡洛实测（含稀有色系数抬价与乘完系数后 24 倍封顶）。
   前四档长期略亏、0.9 上下；拍卖场 ≈1.04（标定 1.0–1.05）——五档里唯一略正，但 35% 垮率配上几万一块的标价，狠在单块金额，见 TIERS 上方注释 */
var TIER_EV=[0.90,0.90,0.91,0.91,1.04];

/* ================= 原石生成（两条独立随机流） ================= */
function scoreRind(r){
  var s=50+RIND_COLORS[r.color].s+RIND_FINE[r.fine].s+RIND_CRACK[r.crack].s+RIND_SONG[r.song].s+RIND_MANG[r.mang].s;
  return Math.max(5,Math.min(98,s));
}
function genStone(tierIdx, isZhen){
  var T=TIERS[tierIdx||0];
  var seed=(++_uid)*7919+Math.floor(rnd()*1e9);
  var rind;
  if(isZhen){ // 镇店石：皮壳按高分权重抽，看着就是全场最好的那块
    rind={ color:pickW([26,22,16,12,10,6,5,3]), fine:pickW([42,32,16,7,3]), crack:pickW([55,28,11,6]), song:pickW([4,20,34,42]), mang:pickW([6,22,34,38]) };
  } else {
    rind={ color:Math.floor(rnd()*8), fine:pickW([16,26,28,18,12]), crack:pickW([22,34,26,18]), song:pickW([38,30,20,12]), mang:pickW([40,28,19,13]) };
  }
  var weight=Math.round(U(0.6,4.8)*10)/10;
  var S=scoreRind(rind);
  // —— 随机流 A：标价，只看所在档次与皮壳 ——
  // 在本档区间内对数均匀取点，再按皮壳评分小幅挪位（皮好靠上限、皮差靠下限），最后夹回区间
  var lp=Math.log(T.pMin)+(Math.log(T.pMax)-Math.log(T.pMin))*rnd();
  var price=Math.exp(lp)*(0.72+(S/100)*0.56);
  price=Math.max(T.pMin,Math.min(T.pMax,price));
  if(isZhen) price=T.pMax*U(1.5,2.3); // 镇店石贵出本档上限一大截
  price=Math.max(50,Math.round(price/10)*10);
  // —— 随机流 B：真实价值，先按本档分布抽结果档，再抽内部 ——
  var cat=pickW(T.dist);
  var rr=(T.catR?T.catR[cat]:CAT_R[cat]); // 拍卖场用自己压到低端的大涨/真爆区间，别档用全局 CAT_R
  var R=rr[0]+(rr[1]-rr[0])*Math.pow(rnd(), T.skew||1.8); // 档内向低端倾斜（拍卖场 skew 更大、压得更狠）
  var inner=sampleInner([0,0,1,2,3][cat]); // 垮/小亏共用最差权重行，小赚中档，大涨高档，真爆强制
  // —— 稀有色：按最终盈亏比 roll（小赚 5% / 大涨 12% / 真爆 30%），中了换色并按系数抬价值，
  //    最终档位在结算时按抬完的实际盈亏比复核（一块小赚料切出蓝水 ×2，就是按大涨结算）
  var rareC=rollRareColor(tierIdx||0, R);
  if(rareC>=0){ inner.color=rareC; R*=RARE_MULT[rareC]; }
  if(R>24) R=24; // 两段封顶：底子 R 由结果档区间定死、最高就是真爆上限 12 倍；乘完稀有色系数后封顶 24 倍——真爆+春带彩最多 24 倍，稀有色不再被 12 倍封顶白给（镇店石与普通石共用这一套生成，没有单独倍数）
  var value=Math.max(20,Math.round(price*R)); R=value/price;
  var name=STONE_NAMES[Math.floor(rnd()*STONE_NAMES.length)]+"·"+(seed%997+1)+"号";
  // —— 打灯欺骗位：约 20% 的石头生成时就定死「打灯表现与内在不一致」——
  //    照着亮、切开是白肉，或者照着全黑、里面闷着绿。打灯函数读到这个标记就把透光/有色信号反着报（见 torchAt）。
  var torchLie = rnd()<0.20;
  // —— 局部团块（开窗/磨只能看到的那一小块）：整块的种色并不均匀，某一小片区域的种色和整块不同。
  //    整块偏白时，那一片可能是全场唯一的绿（开窗见绿、切开只有窗口那点绿）；
  //    整块是好色时，那一片也可能是块死白（窗口一般、切开里面满绿）。
  //    窗口/磨口落在团块上，看到的就是团块的真种色——是真的，只是不代表整块（见 localInnerAt）。
  var pocket=null;
  var prng=mulberry32(seed*41+9);
  function prandDir(){ var th=Math.acos(-1+prng()*2), ph=prng()*Math.PI*2; return { x:Math.sin(th)*Math.cos(ph), y:Math.cos(th), z:Math.sin(th)*Math.sin(ph) }; }
  if(inner.color<=2 && rnd()<0.30){ // 白料里的一团绿
    var pd=prandDir();
    pocket={ x:pd.x, y:pd.y, z:pd.z, radius:U(0.45,0.65), color:3+pickW([30,42,28]), zhong:Math.min(5, inner.zhong+1+Math.floor(rnd()*2)) };
  } else if(inner.color>=4 && rnd()<0.30){ // 好料里的一块死白
    var qd=prandDir();
    pocket={ x:qd.x, y:qd.y, z:qd.z, radius:U(0.45,0.65), color:Math.floor(rnd()*2), zhong:Math.max(0, inner.zhong-1-Math.floor(rnd()*2)) };
  } else if(rnd()<0.18){ // 中档料的局部偏差：那一片比整块明显好或明显差
    var md=prandDir();
    var shift=(rnd()<0.5?-2:2);
    pocket={ x:md.x, y:md.y, z:md.z, radius:U(0.45,0.65), color:Math.max(0,Math.min(5,inner.color+shift)), zhong:Math.max(0,Math.min(5,inner.zhong+(shift>0?1:-1))) };
  }
  return { id:"s"+seed+"_"+_uid, seed:seed, name:name, rind:rind, S:S, weight:weight, price:price, inner:inner, value:value, tier:tierIdx||0, zhen:!!isZhen, windowed:false, grindStep:0, winDir:null, sliceDir:null, torchLie:torchLie, pocket:pocket };
}
function sampleInner(tier){
  /* 真爆：强制玻璃种 + 轻微瑕疵，颜色先强制满绿/帝王绿。
     稀有色不在这里抽：genStone 在价值定档之后按最终盈亏比统一 roll（小赚及以上都有机会，见 rollRareColor），
     所以这里的颜色权重表只有 7 个绿色系 */
  if(tier===3) return { zhong:5, color:(rnd()<0.5?5:6), crack:pickW([80,20,0]), cotton:pickW([75,25,0]), spot:0 };
  return { zhong:pickW(TIER_W_ZHONG[tier]), color:pickW(TIER_W_COLOR[tier]), crack:pickW(TIER_W_CRACK[tier]), cotton:pickW(TIER_W_COTTON[tier]), spot:pickW(TIER_W_SPOT[tier]) };
}

function localInnerAt(st, dir){
  var li={ zhong:st.inner.zhong, color:st.inner.color, crack:st.inner.crack, cotton:st.inner.cotton, spot:st.inner.spot };
  if(st.pocket && dir){
    var dx=dir.x-st.pocket.x, dy=dir.y-st.pocket.y, dz=dir.z-st.pocket.z;
    if(Math.sqrt(dx*dx+dy*dy+dz*dz) < st.pocket.radius){ li.zhong=st.pocket.zhong; li.color=st.pocket.color; }
  }
  return li;
}

var TORCH_SIG=[0,0.2,0.4,0.65,0.85,1,1, 0.9,0.9,0.95,1];
function featureLayoutSong(st){
  var rng=mulberry32(st.seed*3+11);
  function U2(r,a,b){ return a+r()*(b-a); }
  function randDir(){ var th=Math.acos(U2(rng,-1,1)), ph=U2(rng,0,Math.PI*2);
    return { x:Math.sin(th)*Math.cos(ph), y:Math.cos(th), z:Math.sin(th)*Math.sin(ph) }; }
  var song=[], songCount=[0,6,13,24][st.rind.song];
  for(var i=0;i<songCount;i++){ var d=randDir(); U2(rng,0.05,0.13); song.push(d); }
  return song;
}
function torchAt(st, local){
  var dirN={ x:local.x, y:local.y, z:local.z };
  var dl=Math.sqrt(dirN.x*dirN.x+dirN.y*dirN.y+dirN.z*dirN.z)||1;
  dirN.x/=dl; dirN.y/=dl; dirN.z/=dl;
  var li=localInnerAt(st, dirN);
  var zh=ZHONG[li.zhong];
  var songBoost=st.rind.song*0.09;
  var pts=featureLayoutSong(st);
  for(var i=0;i<pts.length;i++){
    var dx=dirN.x-pts[i].x, dy=dirN.y-pts[i].y, dz=dirN.z-pts[i].z;
    var d=Math.sqrt(dx*dx+dy*dy+dz*dz);
    if(d<0.45) songBoost=Math.max(songBoost, 0.34*(1-d/0.45));
  }
  var rng=mulberry32(st.seed+Math.floor(local.x*97)+Math.floor(local.y*57)*3+Math.floor(local.z*37)*7);
  var thickness=0.75+0.25*Math.sin(local.x*3.1+st.seed%5)*Math.cos(local.y*2.3);
  var SIG=TORCH_SIG;
  var sig=SIG[li.color]||0, glow=zh.glow;
  if(st.torchLie){ sig = sig>0.05 ? 0 : 0.9; glow = 1.02-glow; }
  var level=Math.max(0,Math.min(1,(glow*0.8+0.12+songBoost*0.3)*thickness*(0.78+rng()*0.44)));
  var colored=(sig*0.85+songBoost*0.6)*thickness*(0.78+rng()*0.44)>0.30;
  var html, colorHex;
  if(level>0.6 && colored){ html="<b>透光程度：强 · 有色</b><br>光圈大、透得深，还返出色来——底下多半有色，种也不差。不过打灯终究只是打灯。"; colorHex=0x7fe870; }
  else if(level>0.6){ html="<b>透光程度：强 · 无色</b><br>光透得很深，却一点不返色——多种水不错、里面偏白肉。"; colorHex=0xfff0b0; }
  else if(level>0.38 && colored){ html="<b>透光程度：中 · 有色</b><br>透得过去，也有点色意，种和色都有些盼头，说不准。"; colorHex=0x9fe870; }
  else if(level>0.38){ html="<b>透光程度：中 · 无色</b><br>光过得去，但没见着色，多半是白肉，种可能还行。"; colorHex=0xfff0b0; }
  else if(level>0.18 && colored){ html="<b>透光程度：弱 · 有色</b><br>只飘出一点色意：可能真有一层薄色，也可能只是松花晃眼。"; colorHex=0x9fe870; }
  else if(level>0.18){ html="<b>透光程度：弱 · 无色</b><br>光勉强吃进去一点，不返色，没什么盼头——也说不准是皮太厚。"; colorHex=0xd8d2b8; }
  else { html="<b>发暗不透</b><br>光吃不进去：皮太厚、里面干，都有可能；也有好货闷在里面、灯下照样黑的。"; colorHex=0x666655; }
  var lv = level>0.6 ? "强" : level>0.38 ? "中" : level>0.18 ? "弱" : "发暗不透";
  return { level:level, colored:colored, colorHex:colorHex, html:html, label:lv };
}

function genShopForTier(ti){
  var arr=[genStone(ti,true)]; // 第一块就是镇店石
  for(var i=0;i<4;i++) arr.push(genStone(ti,false));
  return arr;
}

function samplePoints(st){
  const top={x:0,y:1,z:0}, waist={x:1,y:0,z:0};
  const songs=featureLayoutSong(st);
  let third={x:0,y:-1,z:0}, label='底';
  if(songs.length){
    third=songs.reduce((a,b)=>dist2(b,waist)<dist2(a,waist)?b:a);
    label='松花';
  }
  return [["顶",top],["腰",waist],[label,third]];
}
function dist2(a,b){return (a.x-b.x)**2+(a.y-b.y)**2+(a.z-b.z)**2;}
function sampleLight(st){
  return samplePoints(st).map(([name,point])=>{
    const r=torchAt(st,point);
    const len=Math.sqrt(point.x*point.x+point.y*point.y+point.z*point.z)||1;
    const dir={x:point.x/len,y:point.y/len,z:point.z/len};
    const hit=!!st.pocket && Math.sqrt(dist2(dir,st.pocket))<st.pocket.radius;
    return {name,level:r.label==='发暗不透'?'暗':r.label,colored:r.colored,hit};
  });
}

const THREE={Vector3:class {
  constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z;}
  lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z;}
  normalize(){const d=Math.sqrt(this.lengthSq())||1;this.x/=d;this.y/=d;this.z/=d;return this;}
  distanceTo(v){return Math.sqrt((this.x-v.x)**2+(this.y-v.y)**2+(this.z-v.z)**2);}
}};
function U2(rng,a,b){ return a+rng()*(b-a); }
function qualityOf(inner){ return ZHONG[inner.zhong].m*COLOR[inner.color].m*FLAW_CRACK[inner.crack].m*FLAW_COTTON[inner.cotton].m*FLAW_SPOT[inner.spot].m; }
function windowDirFor(st){
  if(st.winDir){ // 玩家擦窗时自选的点位，之后擦窗/磨都接着这个点
    var v=new THREE.Vector3(st.winDir.x, st.winDir.y, st.winDir.z);
    if(v.lengthSq()>0.01) return v.normalize();
  }
  var rng=mulberry32(st.seed*7+5);
  var th=Math.acos(U2(rng,-0.2,0.85)), ph=U2(rng,0,Math.PI*2);
  return new THREE.Vector3(Math.sin(th)*Math.cos(ph),Math.cos(th),Math.sin(th)*Math.sin(ph)).normalize();
}
var cur=null;
function grindOffer(step){
  var wd=windowDirFor(cur);
  var li=localInnerAt(cur, { x:wd.x, y:wd.y, z:wd.z });
  var q = step===0 ? ZHONG[li.zhong].m*1.0*0.8 : ZHONG[li.zhong].m*COLOR[li.color].m*0.8;
  var pq=Math.max(0,Math.min(1,(Math.log(q+0.05)-Math.log(0.05))/(Math.log(20)-Math.log(0.05))));
  var spread = step===0 ? [0.85,1.15] : [0.92,1.08]; // 看得越少，买家压价/抬价的浮动越大
  return Math.max(30,Math.round(cur.price*(0.25+pq*1.6)*U(spread[0],spread[1])/10)*10);
}

function windowResult(st, name){
  const entry=samplePoints(st).find(([label])=>label===name);
  if(!entry) throw Error('invalid position');
  const wd=entry[1];
  var noise=U(-0.12,0.14);
  var songBonus=0;
  var songSpots=featureLayoutSong(st);
  for(var si=0;si<songSpots.length;si++){
    var dd=Math.sqrt(dist2(wd,songSpots[si]));
    if(dd<0.5) songBonus=Math.max(songBonus,0.10*(1-dd/0.5));
  }
  var li=localInnerAt(st,wd);
  var patchQ=Math.max(0,Math.min(1,(Math.log(qualityOf(li)+0.05)-Math.log(0.05))/(Math.log(20)-Math.log(0.05))+noise+songBonus));
  var offer=Math.max(30,Math.round(st.price*(0.25+patchQ*1.6)*U(0.9,1.1)/10)*10);
  return {dir:wd,inner:li,offer:offer};
}
function grindResult(st, step){
  if(step!==0 && step!==1) throw Error('invalid grind step');
  cur=st;
  const wd=windowDirFor(st);
  const li=localInnerAt(st,{x:wd.x,y:wd.y,z:wd.z});
  return {dir:{x:wd.x,y:wd.y,z:wd.z},inner:li,offer:grindOffer(step)};
}

const action=process.argv[2];
if(action==='simulate'){
  let withPocket=0, hit=0;
  for(let i=0;i<1000;i++){
    const st=genStone(0,i%5===0);
    if(!st.pocket)continue;
    withPocket++;
    if(samplePoints(st).some(([,p])=>dist2(p,st.pocket)<st.pocket.radius**2)) hit++;
  }
  console.log(JSON.stringify({total:1000,ordinary:800,crown:200,withPocket,hit}));
} else if(action==='generate' && /^[0-4]$/.test(process.argv[3]||'')){
  console.log(JSON.stringify(genShopForTier(Number(process.argv[3]))));
} else if(action==='window' || action==='grind'){
  let input='';process.stdin.setEncoding('utf8');
  process.stdin.on('data',part=>{input+=part;if(input.length>1048576)process.exit(2);});
  process.stdin.on('end',()=>{const v=JSON.parse(input);console.log(JSON.stringify(action==='window'?windowResult(v.stone,v.position):grindResult(v.stone,v.step)));});
} else if(action==='torch'){
  let input='';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data',part=>{input+=part;if(input.length>1048576)process.exit(2);});
  process.stdin.on('end',()=>{
    const data=JSON.parse(input);
    if(!Array.isArray(data)||data.length>5)process.exit(2);
    console.log(JSON.stringify(data.map(sampleLight)));
  });
} else process.exitCode=2;
