const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/../index.html','utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
assert.equal(scripts.length,3);scripts.forEach(s=>new vm.Script(s));
const ids=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1])),nodes={};
function elem(id){if(!ids.has(id))return null;return nodes[id]||=( {innerHTML:'',textContent:'',style:{},dataset:{},classList:{add(){},remove(){},toggle(){}},addEventListener(type,fn){this[type]=fn},appendChild(){}} );}
const document={getElementById:elem,querySelectorAll(){return[]},createElement(){return {}},body:{}};
const ctx=vm.createContext({document,window:{addEventListener(){}},Math,Date,console,setTimeout(){},clearTimeout(){},requestAnimationFrame(){}});
vm.runInContext(scripts[0],ctx,{timeout:1000});
vm.runInContext(scripts[2].split('/* ================= 启动 ================= */')[0],ctx,{timeout:1000});
ctx.G={money:199,maxWealth:10000,owned:[],cabinet:[],history:[],unlockedTier:0,shops:{0:[]},xiaojieVisits:{visited:false,cuts:0,spent:0,net:0}};
let writes=0;ctx.persist=()=>writes++;ctx.renderShop=ctx.toast=()=>{};
assert(ctx.canClaimRelief());elem('btn-relief').click();assert.equal(ctx.G.money,999);assert.equal(writes,1);
assert(!ctx.canClaimRelief());elem('btn-relief').click();assert.equal(ctx.G.money,999);assert.equal(writes,1);
assert.deepEqual(ctx.G.xiaojieVisits,{visited:false,cuts:0,spent:0,net:0});
ctx.G.money=0;ctx.G.owned=[{}];assert(!ctx.canClaimRelief());
console.log('网页破产兜底、不可重复领和统计不变通过');
