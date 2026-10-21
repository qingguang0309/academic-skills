// CR2032 扣式电池测试夹具:anatomy 画装置示意图的学术模板(paper-figures/references/apparatus-anatomy.md)。
// anatomy 在本仓库 skills/anatomy(装到 ~/.claude/skills/anatomy),这里按 ANATOMY_DIR 或默认安装位置找它的 kit,脚本本身可以放在任何项目里。
//   node build.mjs --light      → coin-cell-light.html(幻灯/论文用浅色版)
//   python3 ../../scripts/anatomy_export.py coin-cell-light.html -o clamp.png
import { existsSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ANATOMY = process.env.ANATOMY_DIR || join(homedir(), ".claude", "skills", "anatomy");
if (!existsSync(join(ANATOMY, "kit", "iso-kit.mjs"))) {
  console.error(`找不到 anatomy 的 kit:${ANATOMY}。先 npx skills add wheresryan22/anatomy -g -a claude-code,或设 ANATOMY_DIR`);
  process.exit(1);
}
const k = await import(pathToFileURL(join(ANATOMY, "kit", "iso-kit.mjs")).href);
const { kitScript } = await import(pathToFileURL(join(ANATOMY, "scripts", "inline-kit.mjs")).href);

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";

const WIDTH = 600;
const HEIGHT = 440;
const U = 3;

const PLATE = { x: -112, y: -64, w: 224, d: 128, r: 8 };
const PLATE_H = 12;
const FOOT_H = 5;

const BLOCK = { x: -48, y: -44, w: 96, d: 88, r: 4 };
const BLOCK_TOP = 16;
const LOWER_R = 34;
const LOWER_TOP = BLOCK_TOP + 1.5;
const TAB = { x: -44, y: 19, w: 30, d: 14, r: 1.5 };
const POST_A = [-36, 26];

const CAN_R = 10 * U;
const CAN_TOP = LOWER_TOP + 8.1;
const CAP_R = 8.3 * U;
const CELL_TOP = LOWER_TOP + 3.2 * U;

const GAP0 = 3 * U;
const ELEC_R = 14;
const E0 = CELL_TOP + GAP0;
const HOLDER = [E0 + 1.4, E0 + 7.4];
const ROD_TOP = HOLDER[1] + 26;
const COLLAR_TOP0 = ROD_TOP + 3;

const DISCS = 5;
const DISC_T = 1.4;
const DISC_R = 13;
const FREE_PITCH = 4.2;
const SOLID_PITCH = 1.8;
const SEAT_BOT0 = COLLAR_TOP0 + DISCS * FREE_PITCH;
const SEAT_TOP0 = SEAT_BOT0 + 2.5;
const RATE = 2.5;
const TRAVEL = GAP0 + DISCS * (FREE_PITCH - SOLID_PITCH);
const POSE = GAP0 + 2 * U;

const BUSH_BOT = SEAT_TOP0 + 4;
const BAR_BOT = BUSH_BOT + 8;
const BAR_TOP = BAR_BOT + 12;
const BAR = { x: -88, y: -12, w: 176, d: 24, r: 3 };
const POSTS = [-76, 76];
const NUT_TOP = BAR_TOP + 5;
const KNOB_BOT0 = NUT_TOP + 4 + TRAVEL;
const KNOB_H = 9;
const KNOB_R = 12;
const POST_B = [40, 0];

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), ...k.boxCorners(BAR, BAR_BOT, BAR_TOP), [0, 0, KNOB_BOT0 + KNOB_H + 2]],
  WIDTH,
  HEIGHT,
  { pad: 28, azimuth: 42 },
);

const at = (point) => k.iso(point, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));

function screwHead(x, y, z, r = 2.2) {
  return L(k.ring(x, y, r, z, P, 16), { tone: "lo" }) + D([at([x, y, z])], { size: 0.5 });
}

function plate() {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
    out.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  out.push(k.corners(PLATE, 10).map(([x, y]) => screwHead(x, y, 0)).join(""));
  const label = { x: 50, y: 34, w: 44, d: 18, r: 1.5 };
  out.push(S(k.slabOf(label, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  out.push(D([at([label.x + 2.6, label.y + 2.6, 0.6]), at([label.x + label.w - 2.6, label.y + label.d - 2.6, 0.6])], { size: 0.4 }));
  out.push(k.faceTextSvg(k.topMatrix([label.x + label.w / 2, label.y + 7], 0.6, P, "x"), "CR2032", { size: 3.2, tone: "mid", anchor: "middle" }));
  for (const [i, w] of [[0, 30], [1, 24], [2, 27]]) {
    const y = label.y + 11 + i * 2.6;
    out.push(L(k.lineOnTop([label.x + 7, y], [label.x + 7 + w, y], 0.6, P), { tone: "faint", free: true }));
  }
  return out.join("");
}

function post(x) {
  const out = [];
  out.push(S(k.cylinder(x, 0, 10, 0, 4, P, 28, 0.6), { tone: "mid" }));
  out.push(S(k.cylinder(x, 0, 7, 4, BAR_BOT - 4, P, 28), { tone: "mid", crease: "none" }));
  out.push(L([30, 60, 90].map((z) => k.sideArc(x, 0, 7, z, P, 16)).join(""), { tone: "faint" }));
  return out.join("");
}

function block() {
  const out = [`<path class="iso-halo" d="${k.haloOf(k.insetPlan(BLOCK, 4), 0, 0.1, P)}" style="filter:blur(4px)"/>`];
  out.push(S(k.slabOf(BLOCK, 0, BLOCK_TOP, P, 6, 0.8), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(BLOCK, 3.5), BLOCK_TOP, P, 6), { tone: "faint" }));
  out.push(k.corners(BLOCK, 9).map(([x, y]) => screwHead(x, y, BLOCK_TOP, 1.9)).join(""));
  out.push(S(k.slabOf(TAB, BLOCK_TOP, LOWER_TOP - BLOCK_TOP, P, 3), { tone: "hi", crease: "none" }));
  out.push(S(k.cylinder(0, 0, LOWER_R, BLOCK_TOP, LOWER_TOP - BLOCK_TOP, P, 72, 0.3), { tone: "hi" }));
  out.push(L(k.ring(0, 0, LOWER_R - 2.2, LOWER_TOP, P, 72), { tone: "faint" }));
  return out.join("");
}

function bindingPost([x, y], z) {
  const out = [];
  out.push(S(k.cylinder(x, y, 5.6, z, 3, P, 6, 0.3), { tone: "mid" }));
  out.push(S(k.cylinder(x, y, 3.2, z + 3, 7, P, 20), { tone: "mid", crease: "none" }));
  out.push(L(k.sideArc(x, y, 3.2, z + 6, P, 12), { tone: "lo" }));
  out.push(S(k.cylinder(x, y, 5, z + 10, 6, P, 28, 0.6), { tone: "mid" }));
  out.push(L(k.knurl(x, y, 5, z + 10.6, z + 15.4, 24, P), { tone: "lo" }));
  out.push(L(k.ring(x, y, 1.8, z + 16, P, 12), { tone: "lo" }));
  out.push(D([at([x, y, z + 16])], { size: 0.5 }));
  return out.join("");
}

function cell() {
  const out = [];
  out.push(S(k.cylinder(0, 0, CAN_R, LOWER_TOP, CAN_TOP - LOWER_TOP, P, 96, 0.8), { tone: "hi", lit: true }));
  out.push(L(k.sideArc(0, 0, CAN_R, LOWER_TOP + 1.6, P, 48), { tone: "faint" }));
  out.push(L(k.ring(0, 0, CAN_R - 1.4, CAN_TOP, P, 96), { tone: "lo" }));
  out.push(S(k.cylinder(0, 0, 27, CAN_TOP, 0.5, P, 96), { tone: "lo", crease: "none" }));
  out.push(S(k.cylinder(0, 0, CAP_R, CAN_TOP + 0.5, CELL_TOP - CAN_TOP - 0.5, P, 96, 0.4), { tone: "hi", lit: true }));
  return out.join("");
}

function plunger() {
  const out = [];
  out.push(S(k.cylinder(0, 0, ELEC_R, E0, 1.4, P, 56, 0.3), { tone: "hi" }));
  out.push(S(k.cylinder(0, 0, 17, HOLDER[0], HOLDER[1] - HOLDER[0], P, 56, 0.8), { tone: "mid" }));
  out.push(L(k.sideArc(0, 0, 17, HOLDER[0] + 3, P, 32), { tone: "faint" }));
  out.push(S(k.cylinder(0, 0, 4.5, HOLDER[1], ROD_TOP - HOLDER[1], P, 24), { tone: "mid", crease: "none" }));
  out.push(S(k.cylinder(0, 0, DISC_R, ROD_TOP, 3, P, 48, 0.5), { tone: "mid" }));
  return out.join("");
}

const discRest = (i) => COLLAR_TOP0 + i * FREE_PITCH + (FREE_PITCH - DISC_T) / 2;
const disc = (i) => S(k.cylinder(0, 0, DISC_R - 0.6, discRest(i), DISC_T, P, 48, 0.3), { tone: "mid" });

function lowerScrew() {
  const out = [];
  const top = BAR_TOP;
  out.push(S(k.cylinder(0, 0, 4, SEAT_TOP0, top - SEAT_TOP0, P, 24), { tone: "mid", crease: "none" }));
  const threads = [];
  for (let z = SEAT_TOP0 + 2; z < top - 1; z += 2) threads.push(k.sideArc(0, 0, 4, z, P, 12));
  out.push(L(threads.join(""), { tone: "lo" }));
  out.push(S(k.cylinder(0, 0, DISC_R, SEAT_BOT0, SEAT_TOP0 - SEAT_BOT0, P, 48, 0.5), { tone: "mid" }));
  return out.join("");
}

function crossbar() {
  const out = [];
  out.push(S(k.cylinder(0, 0, 9, BUSH_BOT, BAR_BOT - BUSH_BOT, P, 36, 0.5), { tone: "mid" }));
  out.push(S(k.slabOf(BAR, BAR_BOT, BAR_TOP - BAR_BOT, P, 4, 0.8), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(BAR, 3), BAR_TOP, P, 4), { tone: "faint" }));
  out.push(POSTS.map((x) => screwHead(x, 0, BAR_TOP, 3.2)).join(""));
  out.push(S(k.cylinder(0, 0, 8, BAR_TOP, NUT_TOP - BAR_TOP, P, 6, 0.4), { tone: "mid" }));
  return out.join("");
}

const shank = (s) => S(k.cylinder(0, 0, 4, NUT_TOP - 0.2, KNOB_BOT0 - s - NUT_TOP + 0.4, P, 24), { tone: "mid", crease: "none" });

function knob() {
  const out = [];
  const z = KNOB_BOT0;
  out.push(S(k.cylinder(0, 0, KNOB_R, z, KNOB_H, P, 48, 0.8), { tone: "mid" }));
  out.push(L(k.knurl(0, 0, KNOB_R, z + 1.6, z + KNOB_H - 1.6, 40, P), { tone: "lo" }));
  out.push(L([z + 1.6, z + KNOB_H - 1.6].map((h) => k.sideArc(0, 0, KNOB_R, h, P, 40)).join(""), { tone: "lo" }));
  out.push(L(k.ring(0, 0, KNOB_R - 3, z + KNOB_H, P, 40), { tone: "faint" }));
  out.push(D([at([0, 0, z + KNOB_H])], { size: 0.5 }));
  return out.join("");
}

const svg = k.figureSvg({
  width: WIDTH,
  height: HEIGHT,
  label:
    "A coin-cell test clamp. A CR2032 cell, 20 mm across and 3.2 mm thick, lies on a gold lower electrode set in a PEEK block. Above it a knob drives a lead screw through a crossbar on two posts; the screw pushes a seat, five disc springs and a plunger whose gold upper electrode comes down onto the cell. After the 3 mm gap closes, the springs compress and set the contact force.",
  body: [
    plate(),
    post(POSTS[0]),
    block(),
    bindingPost(POST_A, LOWER_TOP),
    cell(),
    `<g data-part="plunger">${plunger()}</g>`,
    ...Array.from({ length: DISCS }, (_, i) => `<g data-part="disc">${disc(i)}</g>`),
    `<g data-part="screw">${lowerScrew()}</g>`,
    post(POSTS[1]),
    crossbar(),
    `<g data-part="shank">${shank(0)}</g>`,
    `<g data-part="knob">${knob()}</g>`,
    bindingPost(POST_B, BAR_TOP),
  ],
});

const live = `
const P = ${JSON.stringify(P)};
const GAP0 = ${GAP0}, TRAVEL = ${TRAVEL}, U = ${U}, RATE = ${RATE}, DISCS = ${DISCS}, DISC_T = ${DISC_T};
const COLLAR_TOP0 = ${COLLAR_TOP0}, SEAT_BOT0 = ${SEAT_BOT0}, FREE_PITCH = ${FREE_PITCH}, NUT_TOP = ${NUT_TOP}, KNOB_BOT0 = ${KNOB_BOT0};
const STOPS = [0, GAP0 * 0.5, GAP0, ${POSE}, TRAVEL];
const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
const plunger = svg.querySelector('[data-part="plunger"]');
const discs = [...svg.querySelectorAll('[data-part="disc"]')];
const screw = svg.querySelector('[data-part="screw"]');
const shankG = svg.querySelector('[data-part="shank"]');
const knobG = svg.querySelector('[data-part="knob"]');
const readout = document.querySelector("[data-readout]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const shank = ${shank.toString().replace(/k\./g, "").replace(/\bS\(/g, "solidSvg(")};
const KNOB_R = ${KNOB_R};
let s = ${POSE}, target = s, frame = 0, last = 0, clock = 0, touring = !still.matches, visible = false, idle = 0, drawn = -1;
function draw() {
  const move = Math.min(s, GAP0);
  plunger.setAttribute("transform", translateAlong(P, [0, 0, -move]));
  const collar = COLLAR_TOP0 - move, seat = SEAT_BOT0 - s, pitch = (seat - collar) / DISCS;
  discs.forEach((g, i) => {
    const rest = COLLAR_TOP0 + i * FREE_PITCH + (FREE_PITCH - DISC_T) / 2;
    const now = collar + i * pitch + (pitch - DISC_T) / 2;
    g.setAttribute("transform", translateAlong(P, [0, 0, now - rest]));
  });
  screw.setAttribute("transform", translateAlong(P, [0, 0, -s]));
  knobG.setAttribute("transform", translateAlong(P, [0, 0, -s]));
  const key = Math.round(s * 20);
  if (key !== drawn) { shankG.innerHTML = shank(s); drawn = key; }
  const squeeze = Math.max(0, s - GAP0) / U;
  const text = s < GAP0 - 0.01 ? "gap " + ((GAP0 - s) / U).toFixed(1) + " mm · 0.0 N" : "contact · " + (squeeze * RATE).toFixed(1) + " N";
  if (readout.textContent !== text) readout.textContent = text;
  stage.setAttribute("aria-valuenow", (s / U).toFixed(1));
  stage.setAttribute("aria-valuetext", text);
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  if (touring) { clock += dt; target = STOPS[Math.floor(clock / 2.4) % STOPS.length]; }
  s = still.matches ? target : s + (target - s) * (1 - Math.exp(-dt / 0.35));
  if (Math.abs(target - s) < 0.01) s = target;
  draw();
  frame = visible && (touring || s !== target) ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
const steer = (next) => { touring = false; target = clamp(next, 0, TRAVEL); clearTimeout(idle); idle = setTimeout(() => { touring = !still.matches; clock = 0; run(); }, 3600); run(); };
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
stage.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  steer(clamp(((event.clientY - box.top) / box.height - 0.2) / 0.6, 0, 1) * TRAVEL);
});
stage.addEventListener("keydown", (event) => {
  const step = U * 0.5;
  let to = null;
  if (event.key === "ArrowDown" || event.key === "ArrowRight") to = target + step;
  if (event.key === "ArrowUp" || event.key === "ArrowLeft") to = target - step;
  if (event.key === "Home") to = 0;
  if (event.key === "End") to = TRAVEL;
  if (to === null) return;
  event.preventDefault();
  steer(to);
});
draw();
`;

const body = k.plateHtml({
  fig: "Fig 1",
  title: "Coin-cell clamp",
  hint: "Hover up and down to turn the knob",
  readout: `contact · ${(((POSE - GAP0) / U) * RATE).toFixed(1)} N`,
  keys: [
    { mark: "lit", label: "CR2032 cell, 20.0 × 3.2 mm" },
    { mark: "raised", label: "Five disc springs, 2.5 N/mm as a stack (model value)" },
  ],
  caption:
    "Turning the knob drives the screw down 7 mm in all. The first 3 mm close the gap above the cell; after that the plunger stops on the cell and the disc springs take up the rest, so the contact force rises 2.5 N for every millimetre, to 10 N when the stack is solid.",
  body: `<div class="iso-stage" tabindex="0" role="slider" aria-label="Coin-cell clamp: arrow keys turn the knob" aria-valuemin="0" aria-valuemax="${(TRAVEL / U).toFixed(1)}" aria-valuenow="${(POSE / U).toFixed(1)}">${svg}</div>`,
});

const name = `coin-cell${theme === "light" ? "-light" : ""}.html`;
writeFileSync(join(HERE, name), k.pageHtml({ title: "Coin-cell clamp", theme, body, script: kitScript() + live }));
console.log("wrote", name);
