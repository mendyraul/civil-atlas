'use strict';
const $ = selector => document.querySelector(selector);
const notice = $('#notice');
function say(message, error = false) {
  notice.textContent = message; notice.dataset.error = String(error);
  notice.setAttribute('role', error ? 'alert' : 'status');
}
let session;
async function api(path, body) {
  const response = await fetch(path, {
    credentials: 'same-origin', method: body ? 'POST' : 'GET',
    headers: body ? {'Content-Type':'application/json', 'X-CSRF-Token': session?.csrf || ''} : {},
    ...(body ? {body: JSON.stringify(body)} : {})
  });
  let data;
  try { data = await response.json(); } catch { throw new Error('The backend did not return a review response. Try refreshing.'); }
  if (!response.ok) {
    if (response.status === 401 && !$('#login-form')) window.location.assign('/editor/login');
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Check the review fields and try again.');
  }
  return data;
}
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function link(text, href) { const node = el('a', text); node.href = href; return node; }
function externalLink(text, href) {
  try {
    const url = new URL(href);
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) return el('span', text);
    const node = link(text, url.href); node.target = '_blank'; node.rel = 'noopener noreferrer'; return node;
  } catch { return el('span', text); }
}
function badge(text) { return el('span', text.replaceAll('_',' '), 'badge ' + text); }
function dates(target) {
  const start = target.valid_from_year ?? target.start_year;
  const end = target.valid_to_year ?? target.end_year;
  const year = value => value < 0 ? `${-value} BCE` : `${value} CE`;
  return Number.isFinite(start) && Number.isFinite(end) ? `${year(start)} – ${year(end)}` : 'Date range not supplied';
}
async function busy(button, operation) {
  button.disabled = true;
  try { await operation(); } catch (error) { say(error.message, true); } finally { button.disabled = false; }
}
if ($('#login-form')) {
  $('#login-form').addEventListener('submit', event => {
    event.preventDefault(); const form = event.currentTarget;
    const reviewer = form.elements.reviewer.value.trim();
    const key = form.elements.key.value; form.elements.key.value = '';
    busy(form.querySelector('button'), async () => {
      await api('/editor/session', {reviewer, key}); window.location.assign('/editor');
    });
  });
} else {
  let queueRows = [], selected = new Map(), detail;
  let baseExtent = null, extent = null;
  const assignment = window.location.pathname.startsWith('/editor/reviews/') ? decodeURIComponent(window.location.pathname.slice('/editor/reviews/'.length)) : null;
  const params = new URLSearchParams(window.location.search);
  function updateBulkButton() {
    $('#bulk-submit').textContent = `Approve ${selected.size} selected record${selected.size === 1 ? '' : 's'}`;
    $('#bulk-submit').disabled = selected.size === 0;
  }
  async function loadQueue() {
    say('Loading review queue…');
    const data = await api('/editor/api/queue?' + params);
    queueRows = data.rows; selected = new Map(); updateBulkButton();
    $('#queue-count').textContent = `${data.total} matching records · page ${data.page}`;
    $('#queue-list').replaceChildren();
    for (const row of queueRows) {
      const item = el('article', undefined, 'queue-row');
      const meta = el('div', undefined, 'row-meta');
      meta.append(badge(row.assignment.current_review_status), el('span', row.kind.replaceAll('_',' ')), el('span', `${row.confidence} confidence`), el('span', `${row.assignment.priority} priority`));
      const title = el('h2'); title.append(link(row.title, '/editor/reviews/' + encodeURIComponent(row.assignment.id)));
      const citations = row.source_records.map(r => r.title || r.citation || r.id).join(' · ');
      item.append(meta, title, el('p', citations || 'No source citation linked', 'fine'));
      if (!row.bulk_ineligible_reason) {
        const label = el('label', undefined, 'check'); const checkbox = el('input'); checkbox.type = 'checkbox'; checkbox.setAttribute('aria-label', 'Select ' + row.title);
        checkbox.addEventListener('change', () => {
          if (checkbox.checked && selected.size >= 20) { checkbox.checked = false; say('Review at most 20 citation records in one batch.', true); return; }
          if (checkbox.checked) selected.set(row.assignment.id, row.version); else selected.delete(row.assignment.id);
          updateBulkButton();
        });
        label.append(checkbox, el('span', 'Select for citation batch')); item.append(label);
      } else item.append(el('p', row.bulk_ineligible_reason, 'fine'));
      $('#queue-list').append(item);
    }
    if (!queueRows.length) $('#queue-list').append(el('p', 'No records match these filters.', 'panel'));
    $('#pagination').replaceChildren();
    function pageLink(page, label) { const p = new URLSearchParams(params); p.set('page', page); return link(label, '/editor?' + p); }
    if (data.page > 1) $('#pagination').append(pageLink(data.page - 1, '← Previous'));
    if (data.has_more) $('#pagination').append(pageLink(data.page + 1, 'Next →'));
    say('');
  }
  function sourceCard(record) {
    const card = el('article', undefined, 'source-card');
    card.append(el('h3', record.title || record.source_name || record.id), el('p', record.citation || 'Citation not supplied'));
    if (record.link || record.url) card.append(externalLink('Open source ↗', record.link || record.url));
    const tags = [record.license, record.dataset_version, record.confidence, record.review_status].filter(Boolean);
    card.append(el('p', tags.join(' · '), 'fine'));
    if (record.notes) card.append(el('p', record.notes, 'fine'));
    return card;
  }
  const ns = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs = {}, text) {
    const node = document.createElementNS(ns, tag);
    for (const [key,value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function polygons(geometry) {
    if (geometry?.type === 'Polygon') return [geometry.coordinates];
    if (geometry?.type === 'MultiPolygon') return geometry.coordinates;
    return [];
  }
  function points(geometry) { return polygons(geometry).flat(2).filter(p => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1])); }
  function currentPrimary() {
    const id = $('#primary-select').value;
    return detail.primary_layers.find(layer => layer.id === id) || null;
  }
  function fit() {
    const coordinates = [...points(detail.target.geometry_json), ...points(currentPrimary()?.geometry_json)];
    if (!coordinates.length) { extent = baseExtent = [-180,-90,180,90]; drawMaps(); return; }
    const xs = coordinates.map(p => p[0]), ys = coordinates.map(p => p[1]);
    const west = Math.min(...xs), east = Math.max(...xs), south = Math.min(...ys), north = Math.max(...ys);
    const padX = Math.max(1,(east-west)*.1), padY = Math.max(1,(north-south)*.1);
    extent = baseExtent = [west-padX,south-padY,east+padX,north+padY]; drawMaps();
  }
  function drawMap(selector, geometry) {
    const svg = $(selector); svg.replaceChildren();
    const width = 600, height = 320;
    const xRange = extent[2]-extent[0], yRange = extent[3]-extent[1];
    const scale = Math.min((width-44)/xRange,(height-36)/yRange);
    const midX=(extent[0]+extent[2])/2, midY=(extent[1]+extent[3])/2;
    const project = p => [width/2+(p[0]-midX)*scale,height/2-(p[1]-midY)*scale];
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    for (let i=0;i<=4;i++) {
      const lon=extent[0]+xRange*i/4, lat=extent[1]+yRange*i/4;
      const top=project([lon,extent[3]]), bottom=project([lon,extent[1]]);
      const left=project([extent[0],lat]), right=project([extent[2],lat]);
      svg.append(svgEl('line',{x1:top[0],y1:top[1],x2:bottom[0],y2:bottom[1]}),svgEl('line',{x1:left[0],y1:left[1],x2:right[0],y2:right[1]}));
      svg.append(svgEl('text',{x:top[0]+3,y:height-3},`${lon.toFixed(1)}°`),svgEl('text',{x:3,y:left[1]-3},`${lat.toFixed(1)}°`));
    }
    for (const polygon of polygons(geometry)) {
      const path = polygon.map(ring => ring.map((point,i) => `${i?'L':'M'}${project(point).join(',')}`).join(' ')+' Z').join(' ');
      svg.append(svgEl('path',{d:path,class:'boundary'}));
    }
    if (!points(geometry).length) svg.append(svgEl('text',{x:40,y:160},'No boundary geometry available'));
  }
  function drawMaps() {
    drawMap('#proposed-map', detail.target.geometry_json);
    const primary = currentPrimary();
    drawMap('#primary-map', primary?.geometry_json);
    $('#primary-sources').replaceChildren(...(detail.primary_source_records[primary?.id] || []).map(sourceCard));
    $('#primary-caption').textContent = primary
      ? `${primary.name} · ${dates(primary)} · ${primary.confidence || 'unknown'} confidence · ${primary.review_status}${primary.is_placeholder ? ' · Placeholder geometry' : ''}`
      : detail.primary_layers.length ? 'Choose a published primary above to compare it.' : 'No published primary boundary overlaps this record. No substitute has been drawn.';
  }
  async function loadDetail() {
    say('Loading record and source evidence…');
    detail = await api('/editor/api/reviews/' + encodeURIComponent(assignment));
    $('#record-heading').replaceChildren();
    const title = detail.target.name || detail.target.title || detail.target.label || detail.target.id;
    $('#page-title').textContent = title;
    $('#subtitle').textContent = 'Review the proposed record, its sources and any published primary boundary.';
    const meta = el('div', undefined, 'row-meta');
    meta.append(badge(detail.assignment.current_review_status), el('span',detail.kind.replaceAll('_',' ')), el('span',(detail.target.confidence || 'unknown')+' confidence'), el('span', dates(detail.target)));
    $('#record-heading').append(el('h2', detail.assignment.entity_id), meta);
    $('#original-record').textContent = JSON.stringify(detail.target,null,2);
    $('#sources').replaceChildren(...detail.source_records.map(sourceCard),...detail.sources.map(sourceCard));
    if (!detail.source_records.length && !detail.sources.length) $('#sources').append(el('p','No source citations are linked to this record. Check the original record before deciding.'));
    $('#history').replaceChildren();
    for (const d of detail.history.slice().reverse()) {
      const item = el('article'); item.append(el('strong',d.reviewer+' · '+d.decision_type.replaceAll('_',' ')), el('p',d.rationale), el('p',d.created_at,'fine')); $('#history').append(item);
    }
    if (!detail.history.length) $('#history').append(el('p','No decisions recorded yet.'));
    const selectedPrimary = $('#primary-select').value || params.get('primary');
    $('#primary-select').replaceChildren();
    if (detail.primary_layers.length !== 1) $('#primary-select').append(new Option(detail.primary_layers.length ? 'Choose a published primary' : 'No published primary in this date range',''));
    for (const layer of detail.primary_layers) $('#primary-select').append(new Option(layer.name+' · '+dates(layer),layer.id));
    if (selectedPrimary && detail.primary_layers.some(layer => layer.id === selectedPrimary)) $('#primary-select').value = selectedPrimary;
    $('#primary-label').hidden = detail.primary_layers.length < 2;
    $('#proposed-caption').textContent = detail.target.geometry_json ? dates(detail.target) : 'This record has no boundary geometry.';
    $('#primary-caption').textContent = detail.primary_layers.length ? 'Published primary boundaries overlapping the proposed date range.' : 'No published primary boundary overlaps this record. No substitute has been drawn.';
    $('#maps').hidden = detail.kind !== 'layers'; $('.map-toolbar').hidden = detail.kind !== 'layers';
    $('#approval-warning').textContent = detail.target.import_review_blocked || (detail.target.is_placeholder ? 'This is placeholder geometry. Replace it with source-backed geometry before approval.' : '');
    fit(); say('');
  }
  async function refresh() { if (assignment) await loadDetail(); else await loadQueue(); }
  $('#refresh').addEventListener('click', event => busy(event.currentTarget,refresh));
  $('#logout').addEventListener('click', event => busy(event.currentTarget,async()=>{await api('/editor/logout',{});window.location.assign('/editor/login');}));
  $('#filters').addEventListener('submit', event => {
    event.preventDefault(); window.location.assign('/editor?' + new URLSearchParams(new FormData(event.currentTarget)));
  });
  for (const [name,value] of params) { if ($('#filters').elements[name]) $('#filters').elements[name].value = value; }
  $('#decision-form').addEventListener('submit', event => {
    event.preventDefault(); const form = event.currentTarget;
    busy(form.querySelector('button'),async()=>{
      await api('/editor/api/review-actions',{assignment_id:assignment,expected_version:detail.version,decision_type:form.elements.decision_type.value,rationale:form.elements.rationale.value,confirmed:form.elements.confirmed.checked});
      form.reset(); await loadDetail(); say('Decision saved with your reviewer label and rationale.');
    });
  });
  $('#bulk-form').addEventListener('submit',event=>{
    event.preventDefault(); const form=event.currentTarget;
    busy(form.querySelector('button'),async()=>{
      await api('/editor/api/review-actions/bulk',{records:[...selected].map(([assignment_id,expected_version])=>({assignment_id,expected_version})),rationale:form.elements.rationale.value,confirmed:form.elements.confirmed.checked});
      form.reset();await loadQueue();say('Citation batch approved. Every decision has been recorded.');
    }).then(updateBulkButton);
  });
  $('#primary-select').addEventListener('change',()=>{params.set('primary',$('#primary-select').value);history.replaceState(null,'',window.location.pathname+'?'+params);fit();});
  $('#fit-map').addEventListener('click',fit);
  function zoom(factor) {
    if (!extent || !baseExtent) return;
    const midX=(extent[0]+extent[2])/2, midY=(extent[1]+extent[3])/2;
    const width=Math.min((baseExtent[2]-baseExtent[0])*4,Math.max(.01,(extent[2]-extent[0])*factor));
    const height=Math.min((baseExtent[3]-baseExtent[1])*4,Math.max(.01,(extent[3]-extent[1])*factor));
    extent=[midX-width/2,midY-height/2,midX+width/2,midY+height/2];drawMaps();
  }
  $('#zoom-in').addEventListener('click',()=>zoom(.7)); $('#zoom-out').addEventListener('click',()=>zoom(1.4));
  async function start() {
    try {
      session=await api('/editor/api/session'); $('#reviewer').textContent=session.reviewer;
      $('#queue-view').hidden=Boolean(assignment); $('#detail-view').hidden=!assignment;
      await refresh();
    } catch(error) { say(error.message,true); }
  }
  start();
}
