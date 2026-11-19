import json
items=json.load(open('build/narration-timed.json',encoding='utf-8'))
PAD={'title':2.6,'notice':2.6,'zoom':2.2,'facility':2.2,'flip':3.0,'p2title':2.0,'result':2.6,'reflect':2.4,'end':4.5}
LEAD=0.6;t=0.0;out=[]
for it in items:
    d=round(it['audio']+LEAD+PAD.get(it['id'],1.2),2)
    out.append({'id':it['id'],'s':round(t,2),'d':d,'lead':LEAD,'audio':it['audio'],'sub':it['sub']})
    t+=d
open('build/timeline.js','w',encoding='utf-8').write('window.TIMELINE='+json.dumps(out,ensure_ascii=False)+';')
json.dump(out,open('build/timeline.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('total',round(t,2))
