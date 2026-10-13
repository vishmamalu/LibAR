/**
 * LibAR Mobile Application Frontend Logic
 * Supports intelligent search, recommendations, dynamic wayfinding, and AR/VR launching
 */

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

// Map layout coordinates for SVG floorplan rendering (0-1000, 0-600 scale)
const nodePos = {
  ENTRANCE: [100, 516],
  MAIN_DESK: [300, 396],
  A1: [500, 324],
  A2: [620, 396],
  CS_SHELF: [780, 228],
  AI_SHELF: [780, 84],
  DB_SHELF: [700, 324],
  NETWORK_SHELF: [520, 132],
  EXIT: [900, 516]
};

let currentBooks = [];
let selectedBookData = null;
let currentCategory = 'all';
let availableOnly = false;
let searchDebounceTimer = null;

async function jsonFetch(url, options = {}) {
  const r = await fetch(url, options);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'Request failed');
  return data;
}

// Load library statistics
async function loadStats() {
  try {
    const s = await jsonFetch('/api/stats');
    $('titles').textContent = s.titles;
    $('available').textContent = s.available_titles;
    $('subjects').textContent = s.subjects;
    $('shelves').textContent = s.shelves;
  } catch (e) {
    showError(e.message);
  }
}

function showError(msg) {
  const el = $('error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function clearError() {
  $('error').classList.add('hidden');
}

function toast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2600);
}

// Render Catalogue Books
function renderBooks(books) {
  currentBooks = books;
  $('resultCount').textContent = `${books.length} title${books.length === 1 ? '' : 's'}`;
  const el = $('results');
  if (!books.length) {
    el.className = 'results empty';
    el.innerHTML = '<div class="empty-icon">📖</div>No matching books found. Try another query or category.';
    return;
  }
  el.className = 'results';
  el.innerHTML = books.map(b => `
    <article class="book-card" data-id="${b.id}">
      <div class="book-icon">
        <span>LIB</span>
        <span style="font-size:12px;color:var(--accent)">AR</span>
      </div>
      <div class="book-main">
        <div class="book-top">
          <h3>${esc(b.title)}</h3>
          ${b.relevance ? `<span class="relevance-tag">${b.relevance}% match</span>` : ''}
        </div>
        <p class="book-author">By ${esc(b.author)}</p>
        <div class="chips">
          <span class="shelf-chip">📍 ${esc(b.shelf_label || b.shelf)}</span>
          <span>${esc(b.subject)}</span>
          <span class="${b.available ? 'ok' : 'no'}">${esc(b.availability)}</span>
        </div>
      </div>
      <div class="card-actions">
        <button class="find-btn" data-id="${b.id}">Navigate in AR / 3D →</button>
      </div>
    </article>`).join('');

  el.querySelectorAll('.find-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      selectBook(btn.dataset.id);
    });
  });

  el.querySelectorAll('.book-card').forEach(card => {
    card.addEventListener('click', () => {
      selectBook(card.dataset.id);
    });
  });
}

// Render Related Recommendations
function renderRecs(books) {
  const el = $('recommendations');
  if (!books.length) {
    el.className = 'results empty';
    el.innerHTML = '<div class="empty-icon">💡</div>Search for a book to view content-based recommendations.';
    return;
  }
  el.className = 'results';
  el.innerHTML = books.map((b, i) => `
    <article class="rec-card" data-id="${b.id}">
      <span class="rec-index">${String(i + 1).padStart(2, '0')}</span>
      <div class="rec-info">
        <b>${esc(b.title)}</b>
        <small>${esc(b.author)} · ${esc(b.shelf_label || b.shelf)} · ${b.relevance ? b.relevance + '% similarity' : ''}</small>
      </div>
    </article>`).join('');

  el.querySelectorAll('.rec-card').forEach(card => {
    card.addEventListener('click', () => selectBook(card.dataset.id));
  });
}

// Search and Filter Books
async function searchBooks() {
  clearError();
  const q = $('search').value.trim();
  $('results').className = 'results loading';
  $('results').innerHTML = '<div class="empty">Searching academic catalogue…</div>';

  try {
    let url = `/api/books?q=${encodeURIComponent(q)}&category=${encodeURIComponent(currentCategory)}&available_only=${availableOnly}`;
    let recUrl = `/api/recommendations?q=${encodeURIComponent(q || (currentBooks[0] ? currentBooks[0].title : 'machine learning'))}`;

    const [books, recs] = await Promise.all([
      jsonFetch(url),
      jsonFetch(recUrl).catch(() => [])
    ]);

    renderBooks(books);
    renderRecs(recs);
  } catch (e) {
    showError(e.message);
  }
}

// Live Autocomplete Suggestions
async function fetchSuggestions(query) {
  const suggBox = $('suggestions');
  if (!query || query.length < 2) {
    suggBox.classList.add('hidden');
    return;
  }
  try {
    const suggestions = await jsonFetch(`/api/suggest?q=${encodeURIComponent(query)}`);
    if (!suggestions || suggestions.length === 0) {
      suggBox.classList.add('hidden');
      return;
    }
    suggBox.innerHTML = suggestions.map(s => `
      <div class="suggestion-item" data-val="${esc(s)}">
        <span class="suggestion-icon">🔍</span>
        <span>${esc(s)}</span>
      </div>`).join('');
    suggBox.classList.remove('hidden');

    suggBox.querySelectorAll('.suggestion-item').forEach(item => {
      item.addEventListener('click', () => {
        $('search').value = item.dataset.val;
        suggBox.classList.add('hidden');
        $('clearSearchBtn').classList.remove('hidden');
        searchBooks();
      });
    });
  } catch (e) {
    suggBox.classList.add('hidden');
  }
}

// Select a book and compute route
async function selectBook(id) {
  clearError();
  try {
    const book = await jsonFetch('/api/books/' + id);
    selectedBookData = book;
    const startNode = $('startNodeSelect').value || 'ENTRANCE';
    const route = await jsonFetch(`/api/route?target=${encodeURIComponent(book.shelf)}&start=${encodeURIComponent(startNode)}`);

    $('routeEmpty').classList.add('hidden');
    $('routeContent').classList.remove('hidden');
    $('routeStatus').textContent = book.title;

    $('selectedBook').innerHTML = `
      <div class="selected-icon">📚</div>
      <div>
        <h3>${esc(book.title)}</h3>
        <p>By ${esc(book.author)}</p>
        <small>📍 Shelf: ${esc(route.destination_label)} · Floor ${route.floor}</small>
      </div>`;

    $('routeDistance').textContent = `${route.distance_meters}m (${route.distance_units} units)`;
    $('routeWaypoints').textContent = `${route.waypoints} waypoints`;
    $('routeTime').textContent = `~${route.estimated_time_seconds}s walk`;

    $('routeAvailability').textContent = book.available ? '✓ In Stock & Ready' : '⚠ Reserved';
    $('routeAvailability').className = 'stat-pill ' + (book.available ? 'good' : 'bad');

    // Build rich maneuver list
    if (route.maneuvers && route.maneuvers.length > 0) {
      $('routeSteps').innerHTML = route.maneuvers.map((m, i) => `
        <li class="route-step-item ${m.is_final_leg ? 'final-step' : ''}">
          <span class="step-badge">${i + 1}</span>
          <div class="step-details">
            <strong>${esc(m.instruction)}</strong>
            <small>${m.distance_meters}m · Heading: ${m.bearing_degrees}°</small>
          </div>
        </li>`).join('');
    } else {
      $('routeSteps').innerHTML = route.path.map((p, i) => `
        <li class="route-step-item ${i === route.path.length - 1 ? 'final-step' : ''}">
          <span class="step-badge">${i + 1}</span>
          <div class="step-details">
            <strong>${i === 0 ? 'Start at ' : i === route.path.length - 1 ? 'Arrive at destination ' : 'Walk to '}${esc(labelFor(p))}</strong>
          </div>
        </li>`).join('');
    }

    // Set up AR / VR URLs with rich parameters
    const params = new URLSearchParams({
      book: book.id,
      title: book.title,
      author: book.author,
      shelf: book.shelf,
      shelf_label: route.destination_label,
      floor: route.floor,
      start: startNode,
      route: route.path.join('→'),
      distance: route.distance_meters
    });

    $('launchAR').href = '/static/ar.html?' + params.toString() + '&mode=camera';
    $('launchVR').href = '/static/ar.html?' + params.toString() + '&mode=desktop';

    drawRoute(route.path);

    document.querySelectorAll('.map-node').forEach(n => {
      const isPath = route.path.includes(n.dataset.node);
      const isDest = (n.dataset.node === book.shelf);
      n.classList.toggle('active', isPath);
      n.classList.toggle('destination', isDest);
    });

    toast(`Route calculated to ${route.destination_label}`);

    // Smooth scroll down to route panel on mobile
    const panel = $('routePanel');
    if (panel) {
      panel.scrollIntoView({ behavior: 'smooth' });
    }
  } catch (e) {
    showError(e.message);
  }
}

function labelFor(node) {
  const labels = {
    ENTRANCE: 'Library Entrance',
    MAIN_DESK: 'Main Help Desk',
    A1: 'A1 Algorithms Shelf',
    A2: 'A2 AI / ML Section',
    CS_SHELF: 'CS Computer Science Shelf',
    AI_SHELF: 'AI Artificial Intelligence Shelf',
    DB_SHELF: 'DB Database Shelf',
    NETWORK_SHELF: 'Networks & Cloud Shelf',
    EXIT: 'Exit'
  };
  return labels[node] || node;
}

// Draw dynamic animated SVG polyline on the 2D floorplan
function drawRoute(path) {
  const svg = $('routeLine');
  svg.innerHTML = '';
  const points = path.map(n => nodePos[n]).filter(Boolean);
  if (points.length < 2) return;

  const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  poly.setAttribute('points', points.map(([x, y]) => `${x},${y}`).join(' '));
  poly.setAttribute('fill', 'none');
  poly.setAttribute('stroke', 'currentColor');
  poly.setAttribute('stroke-width', '10');
  poly.setAttribute('stroke-linecap', 'round');
  poly.setAttribute('stroke-linejoin', 'round');
  poly.setAttribute('stroke-dasharray', '16 12');
  poly.style.animation = 'dash 1.2s linear infinite';
  svg.appendChild(poly);
}

// QR Code and Mobile Share Handlers
function initModals() {
  const qrBtn = $('qrShareBtn');
  const qrModal = $('qrModal');
  const closeQr = $('closeQrModal');
  const qrBackdrop = $('qrModalBackdrop');
  const copyBtn = $('copyUrlBtn');
  const urlInput = $('mobileUrlInput');

  function openQR() {
    const currentUrl = window.location.origin;
    urlInput.value = currentUrl;
    $('qrCodeContainer').innerHTML = '';
    if (window.QRCode) {
      QRCode.toCanvas(document.createElement('canvas'), currentUrl, { width: 200, margin: 1 }, (err, canvas) => {
        if (!err && canvas) {
          $('qrCodeContainer').appendChild(canvas);
        }
      });
    }
    qrModal.classList.remove('hidden');
  }

  function closeQR() {
    qrModal.classList.add('hidden');
  }

  if (qrBtn) qrBtn.addEventListener('click', openQR);
  if (closeQr) closeQr.addEventListener('click', closeQR);
  if (qrBackdrop) qrBackdrop.addEventListener('click', closeQR);

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(urlInput.value).then(() => {
        toast('Link copied to clipboard!');
      });
    });
  }

  // Hiro Marker modal
  const markerBtn = $('markerRefBtn');
  const markerModal = $('markerModal');
  const closeMarker = $('closeMarkerModal');
  const markerBackdrop = $('markerModalBackdrop');

  if (markerBtn) {
    markerBtn.addEventListener('click', () => markerModal.classList.remove('hidden'));
  }
  if (closeMarker) closeMarker.addEventListener('click', () => markerModal.classList.add('hidden'));
  if (markerBackdrop) markerBackdrop.addEventListener('click', () => markerModal.classList.add('hidden'));
}

// Setup event listeners
function initApp() {
  $('searchBtn').addEventListener('click', searchBooks);
  $('search').addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      $('suggestions').classList.add('hidden');
      searchBooks();
    }
  });

  $('search').addEventListener('input', e => {
    const q = e.target.value.trim();
    $('clearSearchBtn').classList.toggle('hidden', !q);
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      fetchSuggestions(q);
    }, 200);
  });

  $('clearSearchBtn').addEventListener('click', () => {
    $('search').value = '';
    $('clearSearchBtn').classList.add('hidden');
    $('suggestions').classList.add('hidden');
    searchBooks();
  });

  // Filter pills
  document.querySelectorAll('.pill[data-category]').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.pill[data-category]').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentCategory = pill.dataset.category;
      searchBooks();
    });
  });

  // Available only toggle
  $('availableOnlyToggle').addEventListener('click', () => {
    availableOnly = !availableOnly;
    $('availableOnlyToggle').classList.toggle('active', availableOnly);
    searchBooks();
  });

  // Starting location change
  $('startNodeSelect').addEventListener('change', () => {
    if (selectedBookData) {
      selectBook(selectedBookData.id);
    }
  });

  // Clicking outside suggestions closes it
  document.addEventListener('click', e => {
    if (!e.target.closest('.search-box-wrap')) {
      $('suggestions').classList.add('hidden');
    }
  });

  initModals();
  loadStats();
  searchBooks(); // Initial load of all books
}

window.addEventListener('DOMContentLoaded', initApp);
