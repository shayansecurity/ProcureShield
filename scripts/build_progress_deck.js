const pptxgen = require('pptxgenjs');
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Daniel Beheshti';
pptx.subject = 'Graduate Project Progress Update';
pptx.title = 'ProcureShield Graduate Project Progress Update';
pptx.company = 'CSUDH';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US'
};
pptx.defineSlideMaster({
  title: 'MASTER',
  background: { color: 'F7F8FA' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.13, fill: { color: 'E7B64A' }, line: { color: 'E7B64A' } } },
    { text: { text: 'PROCURESHIELD  |  GRADUATE PROJECT', options: { x: 0.55, y: 0.27, w: 4.8, h: 0.24, fontFace: 'Aptos', fontSize: 9.5, bold: true, color: '6B7280', charSpacing: 1.4, margin: 0 } } },
    { text: { text: 'Daniel Beheshti', options: { x: 10.9, y: 7.13, w: 1.85, h: 0.2, fontFace: 'Aptos', fontSize: 8.5, color: '7A8496', align: 'right', margin: 0 } } }
  ],
  slideNumber: { x: 12.78, y: 7.13, color: '7A8496', fontFace: 'Aptos', fontSize: 8.5 }
});

const C = { navy:'172033', yellow:'E7B64A', text:'172033', muted:'667085', white:'FFFFFF', line:'E4E7EC', bg:'F7F8FA', green:'187A57', red:'B42318', orange:'B54708', lightYellow:'FFF8E8', pale:'EEF1F5' };

function title(slide, t, sub='') {
  slide.addText(t, {x:0.58,y:0.7,w:11.8,h:0.52,fontSize:26,bold:true,color:C.navy,margin:0,breakLine:false});
  if (sub) slide.addText(sub,{x:0.6,y:1.26,w:11.7,h:0.36,fontSize:12.5,color:C.muted,margin:0});
}
function card(slide,x,y,w,h,fill=C.white,line=C.line,r=0.13){
  slide.addShape(pptx.ShapeType.roundRect,{x,y,w,h,rectRadius:r,fill:{color:fill},line:{color:line,width:1}});
}
function metric(slide,x,y,w,label,value,accent=C.navy,foot=''){
  card(slide,x,y,w,1.05);
  slide.addText(label.toUpperCase(),{x:x+0.18,y:y+0.17,w:w-0.36,h:0.18,fontSize:9,bold:true,color:C.muted,charSpacing:0.8,margin:0});
  slide.addText(value,{x:x+0.18,y:y+0.43,w:w-0.36,h:0.32,fontSize:20,bold:true,color:accent,margin:0});
  if(foot) slide.addText(foot,{x:x+0.18,y:y+0.79,w:w-0.36,h:0.15,fontSize:8.5,color:C.muted,margin:0});
}
function pill(slide,x,y,w,text,fill,color='FFFFFF'){
  slide.addShape(pptx.ShapeType.roundRect,{x,y,w,h:0.34,rectRadius:0.17,fill:{color:fill},line:{color:fill}});
  slide.addText(text,{x:x+0.06,y:y+0.075,w:w-0.12,h:0.16,fontSize:9.5,bold:true,color,align:'center',margin:0});
}

// Slide 1
{
  const s=pptx.addSlide('MASTER');
  s.background={color:C.navy};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.13,fill:{color:C.yellow},line:{color:C.yellow}});
  s.addText('GRADUATE PROJECT  •  PROGRESS UPDATE',{x:0.78,y:1.05,w:5.4,h:0.28,fontSize:12,bold:true,color:C.yellow,charSpacing:1.6,margin:0});
  s.addText('Supplier Cyber Risk &\nOperational Resilience Platform',{x:0.78,y:1.52,w:7.2,h:1.45,fontSize:34,bold:true,color:C.white,margin:0,breakLine:false});
  s.addText('From project design to a working, testable prototype',{x:0.8,y:3.23,w:6.8,h:0.38,fontSize:17,color:'D7DDEA',margin:0});
  s.addShape(pptx.ShapeType.line,{x:0.8,y:3.87,w:5.2,h:0,line:{color:C.yellow,width:2}});
  s.addText('Daniel Beheshti  |  M.S. Cybersecurity',{x:0.8,y:4.15,w:5.5,h:0.32,fontSize:15,color:C.white,margin:0});
  s.addText('Current focus: deterministic scoring • dashboard • validation • evidence-grounded AI',{x:0.8,y:4.55,w:8.7,h:0.35,fontSize:12.5,color:'B8C2D5',margin:0});
  // right-side clean status stack
  card(s,9.15,1.32,3.05,3.3,'24324D','33435F');
  s.addText('CURRENT STATUS',{x:9.45,y:1.68,w:2.4,h:0.25,fontSize:10,bold:true,color:C.yellow,charSpacing:1.1,margin:0});
  s.addText('Core prototype\nimplemented',{x:9.45,y:2.08,w:2.25,h:0.9,fontSize:28,bold:true,color:C.white,margin:0});
  pill(s,9.45,3.2,1.45,'SCORING','2E4A66');
  pill(s,10.98,3.2,0.98,'RAG','2E4A66');
  pill(s,9.45,3.67,1.45,'SQLITE','2E4A66');
  pill(s,10.98,3.67,0.98,'TESTS','2E4A66');
  s.addText('Next: live OpenAI + Chroma validation',{x:9.45,y:4.23,w:2.35,h:0.42,fontSize:11.5,color:'D7DDEA',margin:0});
}

// Slide 2
{
  const s=pptx.addSlide('MASTER');
  title(s,'What I accomplished since the last report','The project moved from requirements and architecture into an implemented core prototype.');
  const items=[
    ['01','Deterministic scoring','Five weighted risk domains, explicit factors, risk tiers, top-driver logic, and Not Verified handling.'],
    ['02','Controlled test dataset','16 synthetic supplier scenarios: four each for Low, Medium, High, and Critical risk.'],
    ['03','Evidence + persistence','Offline RAG fallback over a curated knowledge base plus SQLite assessment history.'],
    ['04','Dashboard workflow','Streamlit interface code for supplier selection / CSV upload, what-if editing, evidence, validation, and history.']
  ];
  items.forEach((it,i)=>{
    const x=i%2===0?0.62:6.78; const y=i<2?1.8:4.03;
    card(s,x,y,5.92,1.8);
    s.addText(it[0],{x:x+0.22,y:y+0.24,w:0.58,h:0.36,fontSize:24,bold:true,color:C.yellow,margin:0});
    s.addText(it[1],{x:x+0.9,y:y+0.23,w:4.6,h:0.3,fontSize:17,bold:true,color:C.navy,margin:0});
    s.addText(it[2],{x:x+0.9,y:y+0.66,w:4.55,h:0.76,fontSize:12,color:C.muted,margin:0,breakLine:false});
  });
  s.addText('Also included in the package: OpenAI Responses API integration, ChromaDB embeddings path, optional n8n High/Critical webhook, Docker files, and automated tests.',{x:0.72,y:6.2,w:11.8,h:0.48,fontSize:11.5,color:C.muted,margin:0});
}

// Slide 3
{
  const s=pptx.addSlide('MASTER');
  title(s,'Implemented system architecture','The score is calculated independently before retrieval or generative AI is involved.');
  const boxes=[
    ['1','Supplier data','Synthetic CSV / upload'],
    ['2','Validate + score','Known / Not Verified inputs\nDeterministic model'],
    ['3','Dashboard','Tier, domains, drivers'],
    ['4','RAG evidence','Local fallback / Chroma'],
    ['5','Risk brief','OpenAI or safe fallback'],
    ['6','Store + follow up','SQLite / optional n8n']
  ];
  const boxW=1.72, gap=0.37, startX=0.58;
  boxes.forEach((b,i)=>{
    const x=startX+i*(boxW+gap);
    card(s,x,2.18,boxW,2.15,i===1?C.lightYellow:C.white,i===1?C.yellow:C.line);
    s.addShape(pptx.ShapeType.ellipse,{x:x+0.16,y:2.36,w:0.38,h:0.38,fill:{color:i===1?C.yellow:C.navy},line:{color:i===1?C.yellow:C.navy}});
    s.addText(b[0],{x:x+0.16,y:2.44,w:0.38,h:0.14,fontSize:9.5,bold:true,color:i===1?C.navy:C.white,align:'center',margin:0});
    s.addText(b[1],{x:x+0.17,y:2.93,w:boxW-0.34,h:0.45,fontSize:14.2,bold:true,color:C.navy,margin:0});
    s.addText(b[2],{x:x+0.17,y:3.45,w:boxW-0.34,h:0.62,fontSize:10.0,color:C.muted,margin:0});
    if(i<boxes.length-1){ s.addShape(pptx.ShapeType.chevron,{x:x+boxW+0.06,y:3.0,w:0.28,h:0.42,fill:{color:C.yellow},line:{color:C.yellow}}); }
  });
  card(s,0.92,5.12,11.48,1.07,'172033','172033');
  s.addText('Design principle',{x:1.22,y:5.43,w:1.6,h:0.22,fontSize:11,bold:true,color:C.yellow,charSpacing:0.8,margin:0});
  s.addText('Same supplier inputs → same numeric score.  RAG supplies evidence.  AI explains the result but cannot override the score.',{x:2.75,y:5.33,w:8.95,h:0.38,fontSize:15.5,bold:true,color:C.white,margin:0});
}

// Slide 4
{
  const s=pptx.addSlide('MASTER');
  title(s,'Current dashboard prototype','Example shown from the implemented Critical synthetic scenario (C01).');
  s.addImage({path:'/mnt/data/ProcureShield_Graduate_Project/demo/dashboard_preview.png',x:0.62,y:1.64,w:12.1,h:5.15});
  s.addText('Dashboard preview generated from the actual scoring engine and current synthetic dataset.',{x:0.72,y:6.87,w:7.2,h:0.2,fontSize:9.5,color:C.muted,margin:0});
}

// Slide 5
{
  const s=pptx.addSlide('MASTER');
  title(s,'Validation results and next development step','The core prototype now has reproducible checks; live AI-output validation is the next major milestone.');
  metric(s,0.62,1.82,2.78,'Expected-tier checks','16 / 16',C.green,'4 Low • 4 Medium • 4 High • 4 Critical');
  metric(s,3.52,1.82,2.78,'Repeat scoring','48 / 48',C.green,'16 scenarios × 3 executions');
  metric(s,6.42,1.82,2.78,'Sensitivity checks','10 / 10',C.green,'One-factor changes moved as expected');
  metric(s,9.32,1.82,2.78,'Offline RAG checks','6 / 6',C.green,'Relevant evidence found in top 3');
  card(s,0.62,3.35,5.8,2.45);
  s.addText('Working now',{x:0.9,y:3.68,w:2.2,h:0.3,fontSize:18,bold:true,color:C.navy,margin:0});
  const done=[
    'Deterministic five-domain scoring',
    'Synthetic supplier data + what-if testing',
    'Offline evidence retrieval and SQLite history',
    '8 automated pytest tests passing'
  ];
  done.forEach((t,i)=>{s.addText('✓',{x:0.92,y:4.18+i*0.37,w:0.25,h:0.22,fontSize:13,bold:true,color:C.green,margin:0}); s.addText(t,{x:1.25,y:4.15+i*0.37,w:4.75,h:0.26,fontSize:12,color:C.text,margin:0});});
  card(s,6.72,3.35,5.4,2.45,C.lightYellow,'F0D99A');
  s.addText('Next steps',{x:7.0,y:3.68,w:2.2,h:0.3,fontSize:18,bold:true,color:C.navy,margin:0});
  const next=[
    'Run Streamlit locally and capture live demo behavior',
    'Enable ChromaDB + OpenAI Responses API with API key',
    'Manually grade AI briefs: Supported / Unsupported / Incorrect',
    'Connect optional n8n follow-up and refine model from results'
  ];
  next.forEach((t,i)=>{s.addText(String(i+1),{x:7.02,y:4.16+i*0.37,w:0.25,h:0.22,fontSize:11,bold:true,color:C.orange,margin:0}); s.addText(t,{x:7.35,y:4.13+i*0.37,w:4.38,h:0.28,fontSize:11.5,color:C.text,margin:0});});
  s.addText('Important: these numbers validate the deterministic core and curated offline retriever — not the final OpenAI response accuracy yet.',{x:0.78,y:6.2,w:11.5,h:0.42,fontSize:11,bold:true,color:C.red,align:'center',margin:0});
}

pptx.writeFile({ fileName: '/mnt/data/Daniel_Beheshti_Graduate_Project_Progress_Working_Prototype.pptx' });
