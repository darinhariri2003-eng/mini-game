
const API_BASE = "http://127.0.0.1:8085";
const WS_URL = "ws://127.0.0.1:8085/ws";

const container = document.getElementById("sceneContainer");
let ws = null;
const keys = new Set();

// --- THREE.JS 3D SAHNE KURULUMU ---
const WORLD_W = 920;
const WORLD_H = 540;
const SCALE = 0.04; // 3D sahne ölçeği

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xcff4fc);
scene.fog = new THREE.Fog(0xcff4fc, 28, 65);

const camera = new THREE.PerspectiveCamera(48, container.clientWidth / container.clientHeight, 0.1, 200);
camera.position.set(0, 21, 23);
camera.lookAt(0, 0, 1.5);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
container.appendChild(renderer.domElement);

window.addEventListener("resize", () => {
  if (!container.clientWidth) return;
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
});

// Işıklar
const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
dirLight.position.set(14, 26, 16);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 1024;
dirLight.shadow.mapSize.height = 1024;
scene.add(dirLight);

// 3D Arena Zemini (Yeşil & Açık Mavi)
const arenaW3D = WORLD_W * SCALE;
const arenaD3D = WORLD_H * SCALE;

const floorGeo = new THREE.BoxGeometry(arenaW3D, 0.6, arenaD3D);
const floorMat = new THREE.MeshStandardMaterial({ color: 0x66bb6a, roughness: 0.75 });
const floorMesh = new THREE.Mesh(floorGeo, floorMat);
floorMesh.position.y = -0.3;
floorMesh.receiveShadow = true;
scene.add(floorMesh);

// Arena Kenar Çerçevesi (Açık Mavi)
const borderMat = new THREE.MeshStandardMaterial({ color: 0x29b6f6, roughness: 0.4 });
const wallThickness = 0.6;
const wallHeight = 0.9;
const walls = [
  new THREE.Mesh(new THREE.BoxGeometry(arenaW3D + wallThickness * 2, wallHeight, wallThickness), borderMat),
  new THREE.Mesh(new THREE.BoxGeometry(arenaW3D + wallThickness * 2, wallHeight, wallThickness), borderMat),
  new THREE.Mesh(new THREE.BoxGeometry(wallThickness, wallHeight, arenaD3D), borderMat),
  new THREE.Mesh(new THREE.BoxGeometry(wallThickness, wallHeight, arenaD3D), borderMat),
];
walls[0].position.set(0, 0.25, -arenaD3D / 2 - wallThickness / 2);
walls[1].position.set(0, 0.25, arenaD3D / 2 + wallThickness / 2);
walls[2].position.set(-arenaW3D / 2 - wallThickness / 2, 0.25, 0);
walls[3].position.set(arenaW3D / 2 + wallThickness / 2, 0.25, 0);
walls.forEach(w => { w.receiveShadow = true; scene.add(w); });

const gridHelper = new THREE.GridHelper(Math.max(arenaW3D, arenaD3D), 22, 0xb2ebf2, 0x81c784);
gridHelper.position.y = 0.02;
scene.add(gridHelper);

// 3D Oyuncu Modeli (State Pattern'e göre renk ve kılıç animasyonu)
const playerGroup = new THREE.Group();
const bodyGeo = new THREE.CylinderGeometry(0.55, 0.65, 1.4, 20);
const bodyMat = new THREE.MeshStandardMaterial({ color: 0x0288d1, roughness: 0.35 });
const playerBody = new THREE.Mesh(bodyGeo, bodyMat);
playerBody.position.y = 0.7;
playerBody.castShadow = true;
playerGroup.add(playerBody);

const headGeo = new THREE.SphereGeometry(0.42, 20, 20);
const headMat = new THREE.MeshStandardMaterial({ color: 0xe0f7fa, roughness: 0.3 });
const playerHead = new THREE.Mesh(headGeo, headMat);
playerHead.position.y = 1.65;
playerHead.castShadow = true;
playerGroup.add(playerHead);

// Kılıç / Yön göstergesi
const swordGeo = new THREE.BoxGeometry(0.18, 0.18, 1.3);
const swordMat = new THREE.MeshStandardMaterial({ color: 0x00e5ff, emissive: 0x00838f, emissiveIntensity: 0.4 });
const swordMesh = new THREE.Mesh(swordGeo, swordMat);
swordMesh.position.set(0.55, 0.9, 0.65);
playerGroup.add(swordMesh);

// Saldırı dalga halkası
const slashRingGeo = new THREE.RingGeometry(1.2, 2.8, 32);
const slashRingMat = new THREE.MeshBasicMaterial({
  color: 0x00e5ff,
  side: THREE.DoubleSide,
  transparent: true,
  opacity: 0.0,
});
const slashRing = new THREE.Mesh(slashRingGeo, slashRingMat);
slashRing.rotation.x = -Math.PI / 2;
slashRing.position.y = 0.08;
playerGroup.add(slashRing);

scene.add(playerGroup);

// 3D Düşman Havuzu (Factory Method: Goblin & Boss)
const enemyMeshes = new Map();

function to3DX(x2d) {
  return (x2d - WORLD_W / 2) * SCALE;
}
function to3DZ(y2d) {
  return (y2d - WORLD_H / 2) * SCALE;
}

function getOrCreateEnemyMesh(e) {
  if (enemyMeshes.has(e.id)) return enemyMeshes.get(e.id);

  const group = new THREE.Group();
  const isBoss = e.type === "boss";
  const r = isBoss ? 1.15 : 0.62;
  const h = isBoss ? 2.1 : 1.15;

  const geo = isBoss
    ? new THREE.DodecahedronGeometry(r, 0)
    : new THREE.ConeGeometry(r, h, 16);
  const mat = new THREE.MeshStandardMaterial({
    color: isBoss ? 0x00695c : 0x2e7d32,
    roughness: 0.4,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.y = isBoss ? r : h / 2;
  mesh.castShadow = true;
  group.add(mesh);

  // Can çubuğu (3D üst bar)
  const hpBg = new THREE.Mesh(
    new THREE.PlaneGeometry(r * 2.1, 0.22),
    new THREE.MeshBasicMaterial({ color: 0x004d40, side: THREE.DoubleSide })
  );
  hpBg.position.y = (isBoss ? r * 2 : h) + 0.45;
  group.add(hpBg);

  const hpBar = new THREE.Mesh(
    new THREE.PlaneGeometry(r * 2.0, 0.16),
    new THREE.MeshBasicMaterial({ color: 0x4dd0e1, side: THREE.DoubleSide })
  );
  hpBar.position.set(0, hpBg.position.y, 0.02);
  group.add(hpBar);

  scene.add(group);
  const record = { group, mesh, mat, hpBar, isBoss, baseColor: isBoss ? 0x00695c : 0x2e7d32 };
  enemyMeshes.set(e.id, record);
  return record;
}

// --- WEB AUDIO (Observer AudioEngine) ---
let audioCtx = null;
function playCue(cue) {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;
    if (cue === "slash") {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(360, now);
      osc.frequency.exponentialRampToValueAtTime(120, now + 0.09);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
      osc.start(now); osc.stop(now + 0.09);
    } else if (cue === "hit" || cue === "kill") {
      osc.type = "sine";
      osc.frequency.setValueAtTime(cue === "kill" ? 540 : 220, now);
      osc.frequency.exponentialRampToValueAtTime(85, now + 0.12);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      osc.start(now); osc.stop(now + 0.12);
    } else if (cue === "spawn") {
      osc.type = "sine";
      osc.frequency.setValueAtTime(200, now);
      osc.frequency.exponentialRampToValueAtTime(320, now + 0.08);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now); osc.stop(now + 0.08);
    }
  } catch (_) {}
}

// --- WEBSOCKET & KONTROLLER ---
function connectWS() {
  const badge = document.getElementById("connStatus");
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    badge.textContent = "Bağlantı Aktif ";
    badge.className = "badge online";
    sendInputVector();
  };

  ws.onclose = () => {
    badge.textContent = "Bağlantı Kesildi";
    badge.className = "badge offline";
    setTimeout(connectWS, 1200);
  };

  ws.onmessage = (ev) => {
    const snap = JSON.parse(ev.data);
    if (Array.isArray(snap.audio_cues)) {
      snap.audio_cues.forEach(playCue);
    }
    renderUI(snap);
    update3DScene(snap);
  };
}

function sendInputVector() {
  let mx = 0, my = 0;
  if (keys.has("KeyA") || keys.has("ArrowLeft")) mx -= 1;
  if (keys.has("KeyD") || keys.has("ArrowRight")) mx += 1;
  if (keys.has("KeyW") || keys.has("ArrowUp")) my -= 1;
  if (keys.has("KeyS") || keys.has("ArrowDown")) my += 1;

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "input", mx, my }));
  }
}

window.addEventListener("keydown", (e) => {
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(e.code)) {
    e.preventDefault();
  }
  if (e.code === "Space" && !e.repeat) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "attack" }));
    }
    return;
  }
  if (!keys.has(e.code)) {
    keys.add(e.code);
    sendInputVector();
  }
});

window.addEventListener("keyup", (e) => {
  if (keys.has(e.code)) {
    keys.delete(e.code);
    sendInputVector();
  }
});

async function postControl(path, body = null) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });
  if (res.ok) {
    const snap = await res.json();
    if (snap && snap.frame !== undefined) {
      renderUI(snap);
      update3DScene(snap);
    }
  }
}

document.getElementById("btnStart").onclick = () => postControl("/api/control/start");
document.getElementById("btnPause").onclick = () => postControl("/api/control/pause");
document.getElementById("btnStep").onclick = () => postControl("/api/control/step");
document.getElementById("btnSpawnGoblin").onclick = () => postControl("/api/spawn", { enemy_type: "goblin" });
document.getElementById("btnSpawnBoss").onclick = () => postControl("/api/spawn", { enemy_type: "boss" });
document.getElementById("btnAttack").onclick = () => {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "attack" }));
};
document.getElementById("btnRevive").onclick = () => postControl("/api/control/revive");
document.getElementById("btnReset").onclick = () => postControl("/api/control/reset");

function formatTree(node, depth = 0) {
  const pad = "  ".repeat(depth);
  const hpInfo = node.hp !== undefined ? ` [HP:${node.hp}]` : "";
  let line = `${pad}- ${node.name} (${node.kind})${hpInfo}\n`;
  for (const ch of (node.children || [])) {
    line += formatTree(ch, depth + 1);
  }
  return line;
}

function renderUI(snap) {
  const p = snap.player;
  document.getElementById("waveVal").textContent = snap.wave;
  document.getElementById("scoreVal").textContent = snap.score;
  document.getElementById("frameVal").textContent = snap.frame;
  document.getElementById("stateVal").textContent = p.state;

  document.getElementById("hpText").textContent = `${Math.round(p.hp)}/${p.max_hp}`;
  document.getElementById("staminaText").textContent = `${Math.round(p.stamina)}/${p.max_stamina}`;
  document.getElementById("hpFill").style.width = `${Math.max(0, (p.hp / p.max_hp) * 100)}%`;
  document.getElementById("staminaFill").style.width = `${Math.max(0, (p.stamina / p.max_stamina) * 100)}%`;

  if (snap.ui_summary) {
    document.getElementById("observerSummary").textContent = snap.ui_summary;
  }

  const ul = document.getElementById("eventList");
  ul.innerHTML = (snap.events || [])
    .slice(0, 12)
    .map(ev => `<li><span class="tag">[${ev.pattern}]</span>${ev.message}</li>`)
    .join("");

  document.getElementById("sceneTree").textContent = formatTree(snap.scene_tree);
}

function update3DScene(snap) {
  const p = snap.player;
  const px = to3DX(p.x);
  const pz = to3DZ(p.y);
  playerGroup.position.set(px, 0, pz);

  // Bakış yönü rotasyonu
  const angle = Math.atan2(p.facing_x, p.facing_y);
  playerGroup.rotation.y = angle;

  // State Pattern görsel durumu
  if (p.hit_flash > 0.1) {
    bodyMat.color.setHex(0xffffff);
  } else if (p.state === "DeadState") {
    bodyMat.color.setHex(0x90a4ae);
    playerGroup.rotation.z = Math.PI / 2;
  } else if (p.state === "AttackingState") {
    bodyMat.color.setHex(0x00e5ff);
    playerGroup.rotation.z = 0;
    swordMesh.rotation.y = 1.1;
    slashRingMat.opacity = 0.75;
  } else {
    bodyMat.color.setHex(0x0288d1);
    playerGroup.rotation.z = 0;
    swordMesh.rotation.y = 0;
    slashRingMat.opacity = 0.0;
  }

  // Aktif düşmanları güncelle
  const activeIds = new Set();
  for (const e of (snap.enemies || [])) {
    activeIds.add(e.id);
    const rec = getOrCreateEnemyMesh(e);
    rec.group.position.set(to3DX(e.x), 0, to3DZ(e.y));

    if (rec.isBoss) {
      rec.mesh.rotation.y += 0.03;
    }

    if (e.hit_flash > 0.1) {
      rec.mat.color.setHex(0xffffff);
    } else {
      rec.mat.color.setHex(rec.baseColor);
    }

    const ratio = Math.max(0.01, e.hp / e.max_hp);
    rec.hpBar.scale.x = ratio;
  }

  // Ölen düşmanları 3D sahneden kaldır
  for (const [id, rec] of enemyMeshes.entries()) {
    if (!activeIds.has(id)) {
      scene.remove(rec.group);
      enemyMeshes.delete(id);
    }
  }

  // Kamera oyuncuyu yumuşak takip etsin
  camera.position.x += (px * 0.35 - camera.position.x) * 0.08;
  camera.lookAt(px * 0.25, 0, pz * 0.25);
}

// Sürekli 3D render döngüsü
function animate3D() {
  requestAnimationFrame(animate3D);
  renderer.render(scene, camera);
}
animate3D();
connectWS();