// Python Sentinel frontend. Django REST-style JSON endpoints + ORM + CSRF.
'use strict';
const view = document.getElementById('view');
const toasts = document.getElementById('toasts');
let lastAlertId = null;
let lastDashboard = null;
let renderCycle = 0;
let historyFrom = '';
let historyTo = '';
let historyPreset = 'all';
let alertsStatus = '';
let lastEmailAnalysis = null;
let busy = false;

function h(value) { // Escape every backend value before inserting into HTML.
  return String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function time(value) { return value ? h(value) : '—'; }
function badge(text) {
  const label = String(text || 'Info');
  const styles = {Open:'red',Reviewed:'green',Medium:'amber',Low:'blue',High:'red',Normal:'green',ACTIVE:'green',STOPPED:'amber',Enabled:'green',Disabled:'amber',Info:'blue'};
  return `<span class="pill ${styles[label] || 'blue'}">${h(label)}</span>`;
}
function toast(message, error=false) {
  const el = document.createElement('div');
  el.className = `toast${error?' error':''}`;
  el.textContent = message;
  toasts.appendChild(el);
  setTimeout(() => el.remove(), 4800);
}
async function api(path, options={}) {
  const response = await fetch(path, {...options, cache:'no-store'});
  let data;
  try { data = await response.json(); } catch { throw new Error('Unexpected server response.'); }
  if (!response.ok) throw new Error(data.error || `Server error ${response.status}`);
  return data;
}
function getCookie(name) {
  const found=document.cookie.split('; ').find(x => x.startsWith(name+'='));
  return found ? decodeURIComponent(found.substring(name.length+1)) : '';
}
function post(path, data={}) {
  return api(path, {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCookie('csrftoken')}, body:JSON.stringify(data)});
}
function header(title, description, actions='') {
  return `<div class="page-head"><div><p class="eyebrow">AUTOMATED MONITORING & ALERT PLATFORM</p><h1>${h(title)}</h1><p class="sub">${h(description)}</p></div><div class="head-actions">${actions}</div></div>`;
}
function card(title, subtitle, body, aside='') {
  return `<section class="panel"><div class="panel-head"><div><h2>${title}</h2>${subtitle?`<p>${subtitle}</p>`:''}</div>${aside}</div>${body}</section>`;
}
function makeTable(columns, rows, emptyMessage='No records to display yet.') {
  if (!rows.length) return `<div class="empty">${h(emptyMessage)}</div>`;
  return `<div class="table-wrap"><table><thead><tr>${columns.map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
}
function action(label, name, id, style='') {return `<button class="btn ${style}" data-action="${h(name)}" data-id="${h(id)}">${h(label)}</button>`;}
function statusHeader(status) {
  document.getElementById('modeBadge').textContent = status.mode === 'windows' ? 'WINDOWS LIVE' : 'DEMO MODE';
  document.getElementById('modeBadge').classList.toggle('live', status.mode === 'windows');
  const element = document.getElementById('topStatus');
  element.textContent = status.active ? '● Monitoring active' : '● Monitoring stopped';
  element.classList.toggle('active', !!status.active);
}
function banner(status) {
  let result = '';
  if (status.mode === 'demo') result += `<div class="banner"><strong>SIMULATED SECURITY MONITORING:</strong> All sources beginning with SIMULATED / are fictional test data, not real Windows security incidents. ${status.public_demo ? 'This public demo lets visitors try sample scenarios; data and rule settings are shared, and the website does not scan anyone\'s device.' : 'To monitor supported Windows logs locally, restart with <code>SENTINEL_MODE=windows</code> on Windows with pywin32 and appropriate permissions.'}</div>`;
  if (status.warning) result += `<div class="banner warning"><strong>Monitoring warning:</strong> ${h(status.warning)}</div>`;
  if (status.error) result += `<div class="banner error"><strong>Monitoring error:</strong> ${h(status.error)}</div>`;
  return result;
}
function eventRows(events) {
  return events.map(e=>`<tr><td class="td-strong">#${e.event_id}</td><td>${time(e.event_time)}</td><td>${h(e.source)}${e.source?.startsWith("SIMULATED")?'<span class="demo-tag">TEST DATA</span>':''}</td><td class="td-strong">${h(e.event_type)}</td><td>${h(e.username)}</td><td>${badge(e.severity)}</td><td><a href="#/events/${e.event_id}" class="link">View</a></td></tr>`);
}
function alertRows(alerts) {
  return alerts.map(a=>`<tr><td class="td-strong">#${a.alert_id}</td><td>${time(a.alert_time)}</td><td>${badge(a.severity)}</td><td class="td-strong">${h(a.rule_name)}${a.source?.startsWith("SIMULATED")?'<span class="demo-tag">SIMULATED</span>':''}</td><td>${h(a.description)}</td><td>${badge(a.status)}</td><td><a href="#/alerts/${a.alert_id}" class="link">View details →</a></td></tr>`);
}
function fmtCount(n) {return Number(n || 0).toLocaleString();}
function activityChart(days=[]) {
  if (!days.length) return '';
  const maximum=Math.max(1,...days.map(d=>Number(d.events)||0));
  const bars=days.map((d,i)=>{
    const e=Number(d.events)||0, a=Number(d.alerts)||0;
    const eh=Math.max(e?7:0,(e/maximum)*100), ah=Math.max(a?7:0,(a/maximum)*100);
    return `<div class="chart-column" title="${h(d.date)}: ${e} events, ${a} alerts"><div class="chart-bars"><div class="event-bar" style="height:${eh}%"></div><div class="alert-bar" style="height:${ah}%"></div></div><span>${i%6===0?h(d.date.slice(5)):''}</span></div>`;
  }).join('');
  return card('Security Activity · Last 30 Days','Real stored record counts, including clearly labeled simulated examples',
    `<div class="chart-legend"><span><i class="event-dot"></i>Events</span><span><i class="alert-dot"></i>Alerts</span></div><div class="activity-chart" role="img" aria-label="Event and alert totals over the last 30 days">${bars}</div>`);
}
function scenarioButtons(){
 const list=[['Normal Login','NORMAL_LOGIN','demo-normal'],['Failed Login','FAILED_LOGIN','demo-failed'],['File Change','FILE_CHANGE','demo-file'],['Suspicious Process','SUSPICIOUS_PROCESS','demo-process'],['Privilege Change','PRIVILEGE_CHANGE','demo-privilege'],['Account Lockout','ACCOUNT_LOCKOUT','demo-lockout'],['Service Stopped','SERVICE_STOPPED','demo-service'],['Audit Log Cleared','SECURITY_LOG_CLEARED','demo-audit'],['Unusual Network','SUSPICIOUS_NETWORK','demo-network']];
 return list.map(([label,type,actionName])=>`<button type="button" class="btn scenario ${type==='NORMAL_LOGIN'?'normal':type==='FAILED_LOGIN'?'primary':''}" data-action="${actionName}" title="Generate SIMULATED ${h(type)} event">${h(label)} <span>↗</span></button>`).join('');
}
function dashboard(data) {
  const m = data.monitor, s = data.summary;
  const actions = action(m.active?'■ Stop Monitoring':'▶ Start Monitoring', m.active?'stop':'start', '', m.active?'danger':'primary');
  let html = header('Security Dashboard','Monitor supported events, review detections, and respond to suspicious activity.',actions) + banner(m);
  html += `<div class="stats">
    <div class="stat"><div class="stat-title">MONITORING STATUS <span class="glyph">◉</span></div><div class="stat-value">${badge(m.active?'ACTIVE':'STOPPED')}</div><div class="stat-note">${m.active?'Collecting supported events':'Press Start Monitoring'}</div></div>
    <div class="stat"><div class="stat-title">EVENTS PROCESSED <span class="glyph">☷</span></div><div class="stat-value">${fmtCount(s.events_processed)}</div><div class="stat-note">Stored in database</div></div>
    <div class="stat"><div class="stat-title">OPEN ALERTS <span class="glyph">⚑</span></div><div class="stat-value">${fmtCount(s.open_alerts)}</div><div class="stat-note">Needs review</div></div>
    <div class="stat"><div class="stat-title">LAST UPDATE <span class="glyph">◷</span></div><div class="stat-value small">${time(s.last_update)}</div><div class="stat-note">Local event time</div></div>
  </div>`;
  if (m.mode === 'demo') {
    html += card('Interactive Security Test Lab','Start monitoring and generate clearly labeled simulated events. Click any scenario to check rule matching.',
      `<div class="panel-body"><div class="demo-actions scenario-grid">${scenarioButtons()}</div>
       <div class="demo-foot"><p>Normal Login creates no alert; the other events create alerts only if their matching rules are enabled.</p>
       ${action('＋ Prepare 75 Days of Demo History','seed-demo','','dark')}
       </div><div class="custom-simulation"><label for="customSeedDate">SIMULATE A SPECIFIC DATE</label>
       <input type="date" id="customSeedDate" max="${offsetDate(0)}" value="${offsetDate(10)}" aria-label="Date to generate historical example events">
       ${action('Generate 3 Events on This Date','seed-date','','primary')}</div></div>`);
  }
  html += card('Email Threat Analysis','Additional sample-based detection module',
    `<div class="panel-body"><p class="intro">Paste a sample email to review phishing indicators. The app records only a redacted event summary.</p><a href="#/email" class="btn primary">Open Email Analyzer →</a></div>`);
  html += activityChart(data.activity || []);
  html += card('Recent Alerts','Suspicious events matched to enabled detection rules',
    makeTable(['ID','Alert Time','Severity','Rule','Description','Status','Action'],alertRows(data.alerts),'No alerts yet. Try a failed-login test event.'),
    `<a href="#/alerts">View all alerts →</a>`);
  html += card('Recent Events','Most recently collected or simulated event information',
    makeTable(['ID','Time','Source','Event Type','Username','Severity','Action'], eventRows(data.events), 'No events yet. Start monitoring to begin.'),
    `<a href="#/events">View all events →</a>`);
  html += card('How the System Works','How Python Sentinel processes monitoring events',
    '<div class="panel-body intro"><b>Security event → Event collection → Normalization → Enabled detection rules → Database storage → Alert + notification → Dashboard</b></div>');
  return html;
}
function eventsPage(data) {
  return header('Event History','All recorded Windows events and classroom test events.',
    `<button class="btn" data-action="refresh">↻ Refresh</button>`) +
    card('Collected Events',`${data.events.length} latest event record(s)`,
    makeTable(['Event ID','Time','Source','Event Type','Username','Severity','Details'],eventRows(data.events),'There are no stored events yet.'));
}
function eventDetailsPage(e) {
  if (!e) return header('Event Not Found', 'Return to Event History.');
  return header(`Event #${e.event_id}`,'Selected event details from the prototype',
    '<a class="btn" href="#/events">← Event History</a>') + card('Selected Event','Captured data as stored in the Events table',
    `<div class="panel-body"><dl class="detail-rows">
    <dt>Event ID</dt><dd>#${e.event_id}</dd>
    <dt>Event Time</dt><dd>${time(e.event_time)}</dd>
    <dt>Source</dt><dd>${h(e.source)}</dd>
    <dt>Event Type</dt><dd>${h(e.event_type)}</dd>
    <dt>Username</dt><dd>${h(e.username)}</dd>
    <dt>Severity</dt><dd>${badge(e.severity)}</dd>
    <dt>Message</dt><dd>${h(e.message)}</dd>
    <dt>Related Alert</dt><dd>${e.first_alert_id?`<a class="link" href="#/alerts/${e.first_alert_id}">View Alert #${e.first_alert_id} →</a>`:'No detection rule matched this event.'}</dd>
    </dl></div>`);
}
function alertsPage(data) {
  return header('Security Alerts','Review suspicious events identified by active detection rules.',
      '<button class="btn" data-action="refresh">↻ Refresh</button>') +
    `<section class="panel"><div class="filter"><div class="field"><label for="alertFilter">STATUS FILTER</label><select id="alertFilter"><option value="">All Alerts</option><option value="Open" ${alertsStatus==='Open'?'selected':''}>Open</option><option value="Reviewed" ${alertsStatus==='Reviewed'?'selected':''}>Reviewed</option></select></div><button class="btn primary" data-action="filter-alerts">Apply Filter</button></div></section>`+
    card('Alert History',`${data.alerts.length} alert(s) in current view`,
    makeTable(['Alert ID','Time','Severity','Rule','Description','Status','Action'],alertRows(data.alerts),'No alerts match this filter.'));
}
function detailRows(items) {
  return `<div class="panel-body"><dl class="detail-rows">${items.map(([name,val])=>`<dt>${h(name)}</dt><dd>${val}</dd>`).join('')}</dl></div>`;
}
function alertDetailsPage(a) {
  const review = a.status === 'Open' ? action('✓ Mark Reviewed','review',a.alert_id,'primary') : badge('Reviewed');
  return header(`Alert #${a.alert_id}`,'Trace the warning to the specific event and rule that generated it.',
    `<a href="#/alerts" class="btn">← Back to Alerts</a>${review}`) +
   `<div class="details-grid">
     ${card('Alert Information','This alert was generated when a configured condition matched',detailRows([
       ['Alert ID',`#${a.alert_id}`],['Alert Time',time(a.alert_time)],['Severity',badge(a.severity)],
       ['Status',badge(a.status)],['Description',h(a.description)]]))}
     ${card('Related Event','Source data for this detection',detailRows([
       ['Event ID',`<a href="#/events/${a.event_id}" class="link">#${a.event_id} →</a>`],
       ['Event Time',time(a.event_time)],['Source',h(a.source)],['Event Type',h(a.event_type)],
       ['Username',h(a.username)],['Message',h(a.event_message)]]))}
     ${card('Matched Detection Rule','Rule-to-alert relationship required by the SRS',detailRows([
       ['Rule ID',`#${a.rule_id}`],['Rule',h(a.rule_name)],['Pattern',`<code>${h(a.pattern)}</code>`],
       ['Enabled Now',badge(a.rule_enabled?'Enabled':'Disabled')],['Description',h(a.rule_description)]]))}
   </div>`;
}
function rulesPage(data) {
  const rows = data.rules.map(r=>`<tr><td class="td-strong">#${r.rule_id}</td><td class="td-strong">${h(r.rule_name)}</td><td>${h(r.description)}</td><td><code>${h(r.pattern)}</code></td><td>${badge(r.severity)}</td><td>${badge(r.enabled?'Enabled':'Disabled')}</td><td>${action(r.enabled?'Disable':'Enable','toggle-rule',r.rule_id,r.enabled?'':'primary')}</td></tr>`);
  return header('Detection Rules','View and enable/disable supported predefined suspicious-activity patterns.')+
    `<div class="banner"><strong>Rule logic:</strong> An event triggers an alert only when its event type equals the configured pattern and that rule is enabled. This is intentionally simple, testable rule-based detection.</div>`+
    card('Configured Detection Rules',`${data.rules.length} rules available`,makeTable(['ID','Rule Name','Description','Pattern','Severity','Status','Action'],rows));
}
function emailAnalyzerPage() {
  const result = lastEmailAnalysis;
  let results = '';
  if (result) {
    const rows=result.findings.map(f=>`<li><strong>${h(f.title)}</strong> <span class="muted">(+${h(f.points)} points)</span><p>${h(f.explanation)}</p></li>`).join('');
    results=card('Analysis Result','Rule-based heuristic assessment of this sample',
      `<div class="panel-body">
      <div class="email-result-top"><span class="email-risk">${badge(result.risk)}</span><strong>Risk score: ${h(result.score)}</strong><span class="muted">${h(result.indicators)} indicator(s)</span></div>
      ${rows ? `<ul class="email-findings">${rows}</ul>` : '<p class="intro">No configured phishing indicators were found. This does not guarantee the email is safe.</p>'}
      <p class="email-disclaimer">${h(result.disclaimer)}</p>
      <p class="intro"><strong>Saved event:</strong> <a class="link" href="#/events/${Number(result.event_id)}">#${Number(result.event_id)}</a>
      ${result.alert_ids.length ? ` · <strong>Generated alert:</strong> <a class="link" href="#/alerts/${Number(result.alert_ids[0])}">#${Number(result.alert_ids[0])}</a>` : ' · No alert generated for this assessment.'}</p>
      </div>`);
  }
  return header('Phishing Email Analyzer','Inspect a pasted sample email using explainable rules without connecting to an inbox.') +
    `<div class="banner"><strong>Manual analysis only:</strong> This checks submitted text for warning signs. It does not open links, inspect attachments, access email accounts, or confirm that an email is malicious. Do not paste private or sensitive messages into a shared public demonstration.</div>`+
    card('Analyze an Email','Enter a sample message or load a prepared classroom example',
      `<div class="panel-body"><div class="email-examples"><button type="button" class="btn" data-action="email-normal">Load Normal Sample</button><button type="button" class="btn" data-action="email-phishing">Load Suspicious Sample</button></div>
      <form class="email-form" id="emailForm" autocomplete="off">
      <div class="email-input-grid">
      <div class="field"><label for="emailSender">FROM (OPTIONAL)</label><input id="emailSender" type="text" maxlength="254" placeholder="sender@example.com"></div>
      <div class="field"><label for="emailReplyTo">REPLY-TO (OPTIONAL)</label><input id="emailReplyTo" type="text" maxlength="254" placeholder="reply@example.com"></div>
      </div>
      <div class="field"><label for="emailSubject">SUBJECT</label><input id="emailSubject" type="text" maxlength="250" placeholder="Email subject"></div>
      <div class="field"><label for="emailBody">EMAIL BODY</label><textarea id="emailBody" maxlength="6000" rows="8" placeholder="Paste a sample email's text here (do not paste passwords or personal messages)."></textarea></div>
      <div class="email-form-actions"><button class="btn primary" type="submit">Analyze and Save Result</button><span class="muted">Up to 6,000 characters · Summary only stored</span></div>
      </form></div>`)+results+
    card('What It Looks For','Examples of explainable checks',
      `<div class="panel-body intro">Urgent language · Password or verification requests · Threats of account suspension · Payment requests · Unsecured HTTP links · Numeric IP links · Link shorteners · Sender/reply-to mismatch · Executable attachment filenames.</div>`);
}

function offsetDate(daysAgo) {
  const d=new Date(); d.setDate(d.getDate()-daysAgo);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function historyPage(data) {
  const opts = [['all','All Dates'],['2','Last 2 Days'],['30','Last 30 Days'],['60','Last 2 Months (60 days)'],['custom','Custom Range']];
  return header('Detection History','Review previous alerts with a date-range filter, as defined in your implementation plan.') +
    `<section class="panel"><div class="filter"><div class="field"><label for="historyPreset">DATE RANGE</label><select id="historyPreset">${opts.map(([v,t])=>`<option value="${v}" ${historyPreset===v?'selected':''}>${t}</option>`).join('')}</select></div>
    <div class="field"><label for="historyFrom">FROM</label><input type="date" id="historyFrom" value="${h(historyFrom)}"></div><div class="field"><label for="historyTo">TO</label><input type="date" id="historyTo" value="${h(historyTo)}"></div>
    <button class="btn primary" data-action="history-filter">Apply Filter</button><button class="btn" data-action="history-reset">Reset</button></div></section>`+
    card('Historical Detections',`${data.alerts.length} alert(s) match date filters`,
    makeTable(['ID','Time','Severity','Rule','Description','Status','Details'],alertRows(data.alerts),'No detections were found in this date range.'));
}
function pageParts() {
  const parts = (location.hash || '#/dashboard').replace(/^#\/?/, '').split('/');
  return parts.length ? parts : ['dashboard'];
}
async function render(quiet=false) {
  const cycle=++renderCycle, parts=pageParts();
  const name=parts[0] || 'dashboard';
  document.querySelectorAll('[data-page]').forEach(a=>a.classList.toggle('active',a.dataset.page===name));
  document.querySelector('.sidebar').classList.remove('show');
  const names={dashboard:'Dashboard',events:'Events',alerts:'Alerts',rules:'Detection Rules',history:'Detection History',email:'Email Analyzer'};
  document.getElementById('breadcrumb').textContent=names[name] || 'Dashboard';
  if (!quiet) view.innerHTML='<div class="loading">Loading Python Sentinel…</div>';
  try {
    let html;
    if (name === 'dashboard') {
      const data=await api('/api/dashboard');
      if (lastAlertId === null) lastAlertId=data.alerts[0]?.alert_id || 0;
      lastDashboard=data;
      statusHeader(data.monitor);
      html=dashboard(data);
    } else if (name === 'events') {
      const data=await api('/api/events?limit=200');
      if(parts[1]) { const detail=await api(`/api/events/${Number(parts[1])}`); html=eventDetailsPage(detail.event); }
      else html=eventsPage(data);
    } else if(name==='alerts') {
      if(parts[1]) { const data=await api(`/api/alerts/${Number(parts[1])}`); html=alertDetailsPage(data.alert); }
      else {const data=await api(`/api/alerts?limit=200&status=${encodeURIComponent(alertsStatus)}`);html=alertsPage(data);}
    } else if(name==='rules') {
      html=rulesPage(await api('/api/rules'));
    } else if(name==='email') {
      html=emailAnalyzerPage();
    } else if(name==='history') {
      const params=new URLSearchParams({limit:'500'});
      if(historyFrom)params.set('from',historyFrom);
      if(historyTo)params.set('to',historyTo);
      html=historyPage(await api('/api/alerts?'+params.toString()));
    } else {location.hash='#/dashboard';return;}
    if(cycle===renderCycle)view.innerHTML=html;
  } catch(err) {
    if(cycle===renderCycle) view.innerHTML=header('Unable to load', 'Check whether the local Python server is running.')+
      `<div class="banner error">${h(err.message)}</div><button class="btn primary" data-action="refresh">Try Again</button>`;
  }
}
async function sendAction(actionName,id) {
  if(busy)return;
  busy=true;
  try {
    switch(actionName) {
      case 'start': await post('/api/monitor/start');toast('Monitoring started.');break;
      case 'stop':await post('/api/monitor/stop');toast('Monitoring stopped.');break;
      case 'demo-normal':await post('/api/demo/event',{event_type:'NORMAL_LOGIN'});toast('Normal event stored — no alert should be generated.');break;
      case 'demo-failed':await post('/api/demo/event',{event_type:'FAILED_LOGIN'});toast('Failed-login test event sent. Check the alert.');break;
      case 'demo-file':await post('/api/demo/event',{event_type:'FILE_CHANGE'});toast('File-change test event sent.');break;
      case 'demo-process':await post('/api/demo/event',{event_type:'SUSPICIOUS_PROCESS'});toast('Suspicious-process simulation created.');break;
      case 'demo-privilege':await post('/api/demo/event',{event_type:'PRIVILEGE_CHANGE'});toast('Privilege-change simulation created.');break;
      case 'demo-lockout':await post('/api/demo/event',{event_type:'ACCOUNT_LOCKOUT'});toast('Account lockout simulation created.');break;
      case 'demo-service':await post('/api/demo/event',{event_type:'SERVICE_STOPPED'});toast('Service-stop simulation created.');break;
      case 'demo-audit':await post('/api/demo/event',{event_type:'SECURITY_LOG_CLEARED'});toast('Audit-log simulation created.');break;
      case 'demo-network':await post('/api/demo/event',{event_type:'SUSPICIOUS_NETWORK'});toast('Unusual-network simulation created.');break;
      case 'seed-demo':{const out=await post('/api/demo/seed');toast(out.result.already_seeded?'Historical demo data is already loaded.':`Generated ${out.result.created} simulated events across 75 days.`);break;}
      case 'seed-date':{const date=document.getElementById('customSeedDate').value;
        if (!date)throw new Error('Choose a date to simulate.');
        const out=await post('/api/demo/date',{date});
        historyPreset='custom';historyFrom=date;historyTo=date;
        location.hash='#/history';
        toast(out.result.already_seeded?'Examples already exist for this date.':'Created 3 clearly labeled simulated events on '+date+'.');break;}
      case 'review':await post(`/api/alerts/${id}/review`);toast('Alert marked Reviewed.');break;
      case 'toggle-rule':{
        const rules=await api('/api/rules');const rule=rules.rules.find(r=>r.rule_id===Number(id));
        if(!rule)throw new Error('Rule not found');
        await post(`/api/rules/${id}/toggle`,{enabled:!Boolean(rule.enabled)});
        toast(`Rule ${rule.enabled?'disabled':'enabled'}.`);break;
      }
      case 'filter-alerts':alertsStatus=document.getElementById('alertFilter').value;break;
      case 'history-reset':historyPreset='all';historyFrom='';historyTo='';break;
      case 'history-filter':{
        historyPreset=document.getElementById('historyPreset').value;
        const from=document.getElementById('historyFrom').value,to=document.getElementById('historyTo').value;
        if(historyPreset==='custom') {historyFrom=from;historyTo=to;}
        else if(historyPreset==='all') {historyFrom='';historyTo='';}
        else {historyFrom=offsetDate(Number(historyPreset)-1);historyTo=offsetDate(0);}
        if(historyFrom && historyTo && historyFrom>historyTo)throw new Error('From date must not be after To date.');
        break;
      }
      case 'email-normal':{
        document.getElementById('emailSender').value='team@example.com';
        document.getElementById('emailReplyTo').value='';
        document.getElementById('emailSubject').value='Project meeting on Friday';
        document.getElementById('emailBody').value='Hello team, our project meeting is on Friday at 2 PM. Please bring your notes. Thanks!';
        return;
      }
      case 'email-phishing':{
        document.getElementById('emailSender').value='support@campus-example.test';
        document.getElementById('emailReplyTo').value='help@unrelated-example.test';
        document.getElementById('emailSubject').value='URGENT: Account will be suspended';
        document.getElementById('emailBody').value='Act now! Your mailbox will be disabled unless you verify your password immediately at http://192.0.2.55/account. Never enter a real password into this classroom sample.';
        return;
      }
      case 'email-analyze':{
        const payload={
          sender:document.getElementById('emailSender').value,
          reply_to:document.getElementById('emailReplyTo').value,
          subject:document.getElementById('emailSubject').value,
          body:document.getElementById('emailBody').value,
        };
        const outcome=await post('/api/email/analyze',payload);
        lastEmailAnalysis=outcome.analysis;
        toast(outcome.analysis.alert_ids.length ? 'Email assessment completed; linked alert saved.' : 'Email assessment completed; event saved without an alert.');
        break;
      }
      case 'refresh':break;
      default:return;
    }
    await render();
  } catch(err){toast(err.message,true);} finally{busy=false;}
}
document.body.addEventListener('click',ev=>{
  const target=ev.target.closest('[data-action]');
  if(target){ev.preventDefault();sendAction(target.dataset.action,target.dataset.id||'');}
});
document.body.addEventListener('submit',ev=>{
  if(ev.target?.id==='emailForm'){ev.preventDefault();sendAction('email-analyze','');}
});
document.getElementById('menuToggle').addEventListener('click',()=>document.querySelector('.sidebar').classList.toggle('show'));
window.addEventListener('hashchange',()=>render());
setInterval(async()=>{
  try{
    const status=await api('/api/status'); statusHeader(status);
    const alerts=await api('/api/alerts?limit=1');
    const newest=alerts.alerts[0]?.alert_id||0;
    if(lastAlertId===null) lastAlertId=newest;
    else if(newest>lastAlertId){toast(`⚑ New suspicious-activity alert #${newest}. View Alerts for details.`);lastAlertId=newest;}
    if(pageParts()[0]==='dashboard'&&!busy&&!document.activeElement?.matches('input,select'))await render(true);
  } catch(err){/* Keep page usable if the server temporarily stops. */}
},5000);
render();

// Persistent light/dark switch. Use only browser localStorage for a UI preference.
const themeToggle=document.getElementById('themeToggle');
function setTheme(theme) {
  theme=theme==='light'?'light':'dark';
  document.documentElement.dataset.theme=theme;
  themeToggle.setAttribute('aria-pressed',String(theme==='light'));
  document.getElementById('themeIcon').textContent=theme==='light'?'☾':'☀';
  document.getElementById('themeLabel').textContent=theme==='light'?'Dark mode':'Light mode';
  try{localStorage.setItem('ps-theme',theme);}catch(e){}
}
setTheme(document.documentElement.dataset.theme);
themeToggle.addEventListener('click',()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));

// Smooth intro with reduced-motion accessibility and an immediate Skip option.
const splash=document.getElementById('splash');
let splashClosed=false;
function hideSplash() {
  if(splashClosed)return;
  splashClosed=true;
  splash.classList.add('splash-gone');
  window.setTimeout(()=>splash.remove(),700);
}
document.getElementById('skipSplash').addEventListener('click',hideSplash);
window.setTimeout(hideSplash,window.matchMedia('(prefers-reduced-motion: reduce)').matches?150:2100);
