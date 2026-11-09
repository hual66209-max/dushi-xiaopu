const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'shared.html'),'utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
assert.equal(scripts.length,3);scripts.forEach(s=>new vm.Script(s));
function context(source){
  let state=123456;const math=Object.create(Math);
  math.random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};
  const ctx=vm.createContext({Math:math,Date,console,setTimeout(){},clearTimeout(){}});
  vm.runInContext(source,ctx,{timeout:1000});ctx._uid=0;return ctx;
}
const front=context(scripts[0]);
const code=fs.readFileSync(path.join(root,'engine.cjs'),'utf8').split('const action=process.argv[2];')[0];
const backend=context(code);let cracks=0;
for(let tier=0;tier<5;tier++)for(const crown of [false,true])for(let i=0;i<64;i++){
  const a=front.genStone(tier,crown),b=backend.genStone(tier,crown);
  assert.equal(JSON.stringify(a),JSON.stringify(b));
  assert(a.value>=20&&a.value<=a.price*24);
  if(a.inner.crack===2){assert(a.value<=a.price*.8);cracks++}
  if(a.inner.crack===1)assert(a.value<=a.price*3.9);
}
assert(cracks>0);assert(html.includes('v22 · 2026-11-08'));
console.log('v22 前后端生成一致，裂纹价值封顶通过');
