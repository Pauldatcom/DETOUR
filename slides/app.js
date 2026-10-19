(()=>{
  const deck=window.COURSE_DECK||[];
  const stage=document.getElementById('stage');
  const counter=document.getElementById('counter');
  const progress=document.getElementById('progressBar');
  const menu=document.getElementById('menuPanel');
  const exercisePanel=document.getElementById('exercisePanel');
  const exerciseButton=document.getElementById('exerciseButton');
  const exerciseBody=document.getElementById('exerciseBody');
  const exerciseLink=document.getElementById('exerciseLink');
  const days=[...document.querySelectorAll('[data-day]')];
  const preview=new URLSearchParams(location.search).has('preview');
  let day=1,index=0;

  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function markdown(src){
    let html='',list='',code=false,table=false;
    const close=()=>{if(list){html+=`</${list}>`;list=''}if(table){html+='</tbody></table>';table=false}};
    for(const raw of src.split(/\r?\n/)){
      const line=raw.trimEnd();
      if(line.startsWith('```')){close();html+=code?'</code></pre>':'<pre><code>';code=!code;continue}
      if(code){html+=esc(raw)+'\n';continue}
      if(!line.trim()){close();continue}
      if(/^\|.+\|$/.test(line)){
        if(/^\|[\s:|\-]+\|$/.test(line))continue;
        if(!table){close();html+='<table><tbody>';table=true}
        html+='<tr>'+line.slice(1,-1).split('|').map(x=>`<td>${inline(x.trim())}</td>`).join('')+'</tr>';continue;
      }
      if(table){html+='</tbody></table>';table=false}
      const h=line.match(/^(#{1,3})\s+(.*)$/);
      if(h){close();html+=`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`;continue}
      const ul=line.match(/^[-*]\s+(.*)$/),ol=line.match(/^\d+\.\s+(.*)$/);
      if(ul||ol){const type=ul?'ul':'ol';if(list!==type){close();html+=`<${type}>`;list=type}html+=`<li>${inline((ul||ol)[1])}</li>`;continue}
      close();
      if(line.startsWith('>'))html+=`<blockquote>${inline(line.slice(1).trim())}</blockquote>`;
      else html+=`<p>${inline(line)}</p>`;
    }
    close();if(code)html+='</code></pre>';return html;
  }
  function inline(s){return esc(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\[([^\]]+)\]\(([^)]+)\)/g,(all,label,url)=>/^(https?:\/\/|\.{0,2}\/|[A-Za-z0-9][A-Za-z0-9._/-]*$)/.test(url)?`<a href="${url}" target="_blank" rel="noopener">${label}</a>`:all)}
  function current(){return deck.filter(s=>s.day===day)}
  function render(broadcast=true){
    const slides=current(),slide=slides[index];if(!slide)return;
    stage.dataset.day=String(day);
    stage.innerHTML=`<section class="slide"><div class="eyebrow">${esc(slide.eyebrow||'DÉTOUR')}</div>${slide.hero?`<h1>${slide.title}</h1>`:`<h2>${slide.title}</h2>`}${slide.subtitle?`<p class="subtitle">${slide.subtitle}</p>`:''}<div class="visual">${slide.html||''}</div></section>`;
    stage.scrollTop=0;
    counter.textContent=`${index+1} / ${slides.length}`;
    progress.style.width=`${100*(index+1)/slides.length}%`;
    progress.style.background=[2,3,4].includes(day)?'var(--teal)':'var(--orange)';
    document.getElementById('previousButton').disabled=index===0;
    document.getElementById('nextButton').disabled=index===slides.length-1;
    exerciseButton.disabled=!slide.exercise;
    if(!slide.exercise)exercisePanel.hidden=true;
    else if(!exercisePanel.hidden)loadExercise(slide.exercise);
    days.forEach(b=>b.classList.toggle('is-active',Number(b.dataset.day)===day));
    document.getElementById('moduleSelect').value=String(day);
    buildMenu();
    location.hash=`j${day}-${index+1}`;
    if(broadcast&&!preview)window.DeckSync.publish(day,index);
  }
  function buildMenu(){
    menu.innerHTML=current().map((s,i)=>`<button data-index="${i}" class="${i===index?'is-active':''}"><small>${String(i+1).padStart(2,'0')}</small>${s.menu||s.title.replace(/<[^>]+>/g,'')}</button>`).join('');
    menu.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{index=Number(b.dataset.index);menu.hidden=true;render()}));
  }
  async function loadExercise(path){
    const url=new URL(path,location.href);exerciseLink.href=url.href;exerciseBody.innerHTML='<p>Chargement…</p>';
    try{const r=await fetch(url);if(!r.ok)throw Error('Énoncé introuvable');exerciseBody.innerHTML=markdown(await r.text());exerciseBody.querySelectorAll('a[href]').forEach(a=>{if(!/^https?:\/\//.test(a.getAttribute('href')))a.href=new URL(a.getAttribute('href'),url).href})}catch(e){exerciseBody.innerHTML=`<p>${esc(e.message)}</p>`}
  }
  function go(n){const slides=current();index=Math.max(0,Math.min(slides.length-1,index+n));render()}
  function selectDay(n){if(![1,2,3,4,5,6,7].includes(n))return;day=n;index=0;exercisePanel.hidden=true;render()}
  document.getElementById('previousButton').onclick=()=>go(-1);
  document.getElementById('nextButton').onclick=()=>go(1);
  days.forEach(b=>b.onclick=()=>selectDay(Number(b.dataset.day)));
  document.getElementById('moduleSelect').onchange=e=>selectDay(Number(e.target.value));
  document.getElementById('menuButton').onclick=()=>menu.hidden=!menu.hidden;
  exerciseButton.onclick=()=>{if(exerciseButton.disabled)return;exercisePanel.hidden=!exercisePanel.hidden;if(!exercisePanel.hidden)loadExercise(current()[index].exercise)};
  document.getElementById('presenterButton').onclick=()=>{
    const url=new URL('./presenter.html',location.href);
    url.hash=`j${day}-${index+1}`;
    window.open(url.href,'detour-presenter','popup,width=1380,height=900');
  };
  document.getElementById('closeExercise').onclick=()=>exercisePanel.hidden=true;
  document.getElementById('fullscreenButton').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
  document.addEventListener('keydown',e=>{
    if(e.target instanceof Element&&e.target.closest('button,select,input,textarea,a,[contenteditable="true"]'))return;
    if(['ArrowRight','ArrowDown',' '].includes(e.key)){e.preventDefault();go(1)}
    else if(['ArrowLeft','ArrowUp'].includes(e.key)){e.preventDefault();go(-1)}
    else if(['1','2','3','4','5','6','7'].includes(e.key))selectDay(Number(e.key));
    else if(e.key.toLowerCase()==='t')exerciseButton.click();
    else if(e.key.toLowerCase()==='p'&&!preview&&!document.getElementById('presenterButton').hidden)document.getElementById('presenterButton').click();
    else if(e.key.toLowerCase()==='f')document.getElementById('fullscreenButton').click();
    else if(e.key==='Escape'){menu.hidden=true;exercisePanel.hidden=true}
  });
  let touch=0;stage.addEventListener('touchstart',e=>touch=e.changedTouches[0].clientX,{passive:true});stage.addEventListener('touchend',e=>{const diff=touch-e.changedTouches[0].clientX;if(Math.abs(diff)>70)go(diff>0?1:-1)},{passive:true});
  window.addEventListener('hashchange',()=>{const m=location.hash.match(/^#j([1-7])-(\d+)$/);if(!m)return;const targetDay=Number(m[1]),targetIndex=Math.max(0,Math.min(deck.filter(s=>s.day===targetDay).length-1,Number(m[2])-1));if(day!==targetDay||index!==targetIndex){day=targetDay;index=targetIndex;render()}});
  const match=location.hash.match(/^#j([1-7])-(\d+)$/);if(match){day=Number(match[1]);index=Math.max(0,Math.min(current().length-1,Number(match[2])-1))}
  if(preview)document.body.classList.add('is-preview');
  if(!preview){
    window.DeckSync.onSlide((targetDay,targetIndex)=>{
      const slides=deck.filter(s=>s.day===targetDay);
      if(!slides.length)return;
      targetIndex=Math.min(targetIndex,slides.length-1);
      if(day===targetDay&&index===targetIndex)return;
      day=targetDay;index=targetIndex;exercisePanel.hidden=true;render(false);
    });
    window.DeckSync.onRequest(()=>window.DeckSync.publish(day,index));
  }
  render(!preview);
})();
