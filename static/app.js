const state={token:localStorage.getItem('postgram_token'),email:localStorage.getItem('postgram_email')||''};
const $=s=>document.querySelector(s);
const authView=$('#authView'),feedView=$('#feedView'),feed=$('#feed'),empty=$('#emptyState'),toast=$('#toast');

function showToast(msg){toast.textContent=msg;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2500)}
function setAuthMessage(msg,error=false){const el=$('#authMessage');el.textContent=msg;el.className='message'+(error?' error':'')}
function api(path,options={}){options.headers={...(options.headers||{}),...(state.token?{Authorization:'Bearer '+state.token}:{})};return fetch(path,options)}
function showFeed(){authView.classList.add('hidden');feedView.classList.remove('hidden');$('#profileEmail').textContent=state.email||'Signed in';loadFeed()}
function showAuth(){feedView.classList.add('hidden');authView.classList.remove('hidden')}
function escapeHtml(v=''){return v.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}
function formatDate(v){try{return new Intl.DateTimeFormat(undefined,{day:'numeric',month:'short',year:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(v))}catch{return v}}

document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');const login=t.dataset.auth==='login';$('#loginForm').classList.toggle('hidden',!login);$('#registerForm').classList.toggle('hidden',login);setAuthMessage('')});

$('#loginForm').onsubmit=async e=>{e.preventDefault();setAuthMessage('Signing you in…');const body=new URLSearchParams({username:$('#loginEmail').value,password:$('#loginPassword').value});try{const r=await fetch('/auth/jwt/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});const d=await r.json();if(!r.ok)throw Error(d.detail||'Invalid email or password');state.token=d.access_token;state.email=$('#loginEmail').value;localStorage.setItem('postgram_token',state.token);localStorage.setItem('postgram_email',state.email);showFeed()}catch(err){setAuthMessage(err.message,true)}};

$('#registerForm').onsubmit=async e=>{e.preventDefault();setAuthMessage('Creating your account…');try{const r=await fetch('/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('#registerEmail').value,password:$('#registerPassword').value})});const d=await r.json();if(!r.ok)throw Error(d.detail?.[0]?.msg||d.detail||'Registration failed');setAuthMessage('Account created. Sign in to continue.');document.querySelector('[data-auth="login"]').click();$('#loginEmail').value=$('#registerEmail').value}catch(err){setAuthMessage(err.message,true)}};

async function loadFeed(){feed.innerHTML='<div class="empty"><p>Loading your moments…</p></div>';try{const r=await api('/feed');if(r.status===401){logout(false);return}const d=await r.json();const posts=d.posts||[];feed.innerHTML='';empty.classList.toggle('hidden',posts.length>0);posts.forEach(post=>{const card=document.createElement('article');card.className='post';const media=post.file_type==='video'?'<video class="post-media" controls preload="metadata" src="'+post.url+'"></video>':'<img class="post-media" loading="lazy" src="'+post.url+'" alt="'+escapeHtml(post.file_name)+'">';card.innerHTML=media+'<div class="post-body"><div class="post-meta"><span class="post-email">'+escapeHtml(post.email||'Postgram user')+'</span><span>'+formatDate(post.created_at)+'</span></div>'+(post.caption?'<p class="caption">'+escapeHtml(post.caption)+'</p>':'')+(post.is_owner?'<button class="delete-btn" data-id="'+post.id+'">Delete post</button>':'')+'</div>';feed.appendChild(card)});feed.querySelectorAll('.delete-btn').forEach(b=>b.onclick=()=>deletePost(b.dataset.id))}catch(e){feed.innerHTML='<div class="empty"><h3>Could not load feed</h3><p>Check that the API server is running.</p></div>'}}
async function deletePost(id){if(!confirm('Delete this post?'))return;try{const r=await api('/delete/'+encodeURIComponent(id),{method:'DELETE'});const d=await r.json();if(!r.ok)throw Error(d.detail||d.message||'Delete failed');showToast('Post deleted');loadFeed()}catch(e){showToast(e.message)}}

function openComposer(){ $('#composer').classList.remove('hidden');$('#uploadMessage').textContent=''}
function closeComposer(){$('#composer').classList.add('hidden');$('#uploadForm').reset();$('#fileLabel').textContent='Choose a photo or video'}
$('#openComposer').onclick=openComposer;$('#emptyPostBtn').onclick=openComposer;document.querySelectorAll('[data-close="composer"]').forEach(x=>x.onclick=closeComposer);
$('#postFile').onchange=e=>{if(e.target.files[0])$('#fileLabel').textContent=e.target.files[0].name};
$('#uploadForm').onsubmit=async e=>{e.preventDefault();const file=$('#postFile').files[0];if(!file)return;$('#uploadMessage').textContent='Uploading…';const fd=new FormData();fd.append('file',file);fd.append('caption',$('#caption').value);try{const r=await api('/upload',{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw Error(d.detail||'Upload failed');closeComposer();showToast('Moment published');loadFeed()}catch(err){$('#uploadMessage').textContent=err.message;$('#uploadMessage').className='message error'}};

function logout(show=true){state.token=null;state.email='';localStorage.removeItem('postgram_token');localStorage.removeItem('postgram_email');showAuth();if(show)showToast('Signed out')}
$('#logoutBtn').onclick=()=>logout();$('#profileBtn').onclick=()=>$('#profileMenu').classList.toggle('hidden');$('#refreshBtn').onclick=()=>state.token&&loadFeed();document.addEventListener('click',e=>{if(!e.target.closest('#profileBtn')&&!e.target.closest('#profileMenu'))$('#profileMenu').classList.add('hidden')});
document.querySelector('.brand').onclick=e=>{e.preventDefault();if(state.token)showFeed()};
if(state.token)showFeed();else showAuth();
