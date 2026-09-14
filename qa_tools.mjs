import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
const read=p=>fs.readFileSync(p,"utf8");
const scripts=new Map();
const paths=["tools/tfsa-room/index.html","tools/oas-clawback/index.html","tools/mortgage-renewal/index.html","tools/gic-ladder/index.html","tools/cpp-start-age/index.html","resources/next-bank-of-canada-announcement/index.html"];
let checks=0;
function near(actual,expected,tol=0.00001){assert.ok(Math.abs(actual-expected)<tol,actual+" != "+expected);checks++;}
for(const p of [...paths,"tools/index.html"]){
 const h=read(p);
 for(const m of h.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)){const d=JSON.parse(m[1]);assert.ok(["WebPage","CollectionPage"].includes(d["@type"]));}
 const js=[...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join("\n");
 new vm.Script(js,{filename:p});
 scripts.set(p,js);
 assert.doesNotMatch(h,/URLSearchParams|history\.replaceState|localStorage|sessionStorage|sendBeacon|fetch\(|XMLHttpRequest|fonts\.google|\/terms\/|NEXT_LIMIT_PROJECTED|NewsArticle/);
 assert.match(h,/connect-src 'none'/);assert.match(h,/form-action 'none'/);
 assert.match(h,/Human factual review is not documented|Constants do not update automatically/);
 checks++;
}
function expose(script,cut,names){const c={result:null};vm.createContext(c);vm.runInContext(script.slice(0,script.indexOf(cut)).replace("(function(){","")+";\nresult={"+names+"};",c);return c.result;}
const m=scripts.get(paths[2]);const mc={};vm.createContext(mc);vm.runInContext(m.slice(m.indexOf("  function periodRate"),m.indexOf("  function num"))+"result={periodRate,payment,balanceAfter,periodsToRepay};",mc);
const M=mc.result, rate=M.periodRate(4,12), pay=M.payment(500000,rate,300);
near(pay,2630.101026);near(M.balanceAfter(500000,rate,pay,60),435269.576212);
near(M.payment(435269.576212,M.periodRate(6,12),240),3099.939613);
near(M.payment(500000,0,300),1666.6666666667);
near(M.balanceAfter(500000,0,500000/300,60),400000);
near(M.payment(0,M.periodRate(6,12),240),0);
assert.equal(M.periodsToRepay(100000,.01,500),Infinity);checks++;
const tf=scripts.get(paths[0]);const T=expose(tf,"  const $","contributionRoom");
near(T.contributionRoom(2009,0,0),109000);near(T.contributionRoom(2015,40000,5000),43000);near(T.contributionRoom(2026,7000,0),0);near(T.contributionRoom(2026,8000,0),-1000);
const o=scripts.get(paths[1]);const O=expose(o,"  const $","annualRepayment");
near(O.annualRepayment(93454,93454,8000),0);near(O.annualRepayment(100000,93454,8000),981.9);near(O.annualRepayment(100000,93454,500),500);near(O.annualRepayment(200000,93454,0),0);near(O.annualRepayment(96323,95323,8000),150);
const cp=scripts.get(paths[4]);const C=expose(cp,"  // populate selects","factor,cum,breakEven");
near(1000*C.factor(720),640);near(1000*C.factor(780),1000);near(1000*C.factor(840),1420);
assert.equal(C.breakEven(720,780,1000,0),887);assert.equal(C.breakEven(780,840,1000,0),983);assert.equal(C.breakEven(720,780,0,0),null);checks+=3;
near(C.cum(780,900,1000,0),120000);
const g=scripts.get(paths[3]);const gc={};vm.createContext(gc);vm.runInContext(g.slice(g.indexOf("  function simulate"),g.indexOf("  function compute"))+"result={simulate,lumpAt};",gc);
const G=gc.result;
let sim=G.simulate(50000,5,{1:0,2:0,3:0,4:0,5:0},true,10);near(sim.valueAt[9],50000);
sim=G.simulate(50000,5,{1:2.45,2:2.5,3:2.55,4:2.65,5:2.75},false,10);
near(sim.events[0].matured[0].cash,10245);near(sim.events[1].matured[0].cash,10506.25);near(sim.valueAt[9],sim.valueAt[4]);
const fy=/const firstYear = ([^;]+);/.exec(g)[1];near(vm.runInNewContext(fy,{P:50000,rung:10000,blended:2.58}),1290);
near(G.simulate(50000,5,{1:3,2:3,3:3,4:3,5:3},true,10).valueAt[9],50000*Math.pow(1.03,10));
const b=scripts.get(paths[5]);const B=expose(b,"  const now","announcementInstant");
assert.equal(B.announcementInstant("2026-10-28").toISOString(),"2026-10-28T13:45:00.000Z");
assert.equal(B.announcementInstant("2026-12-09").toISOString(),"2026-12-09T14:45:00.000Z");checks+=2;
const built=read("_site/sitemap.xml");const news=read("_site/sitemap-news.xml");
for(const p of [...paths,"tools/index.html"]){const route="/"+p.replace(/index.html$/,"");assert.equal(built.split("<loc>https://imperiumpost.com"+route+"</loc>").length-1,1);assert.ok(!news.includes(route));checks++;}
console.log("tools checks: "+checks+" passed — independent examples, caps/zeros, maturity cash flows, CPP month crossovers, DST, syntax, privacy and sitemap classification");
