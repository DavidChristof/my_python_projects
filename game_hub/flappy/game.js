// ==================== Flappy Bird - Canvas 版 ====================
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const W = 400, H = 600, GROUND_H = 80;
const BIRD_X = 100, BIRD_R = 16;
const GRAVITY = 0.45, JUMP = -7.5;
const PIPE_W = 58, PIPE_GAP = 155, PIPE_SPEED = 3;
const PIPE_INTERVAL = 90, CAP_H = 25;

let bird = { y: 280, v: 0 };
let pipes = [];
let score = 0, frame = 0, gameOver = false;

// ===== 音效 =====
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function beep(f, d, t="square", vol=0.08) {
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = t; o.frequency.setValueAtTime(f, audioCtx.currentTime);
    g.gain.setValueAtTime(vol, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + d);
    o.connect(g); g.connect(audioCtx.destination);
    o.start(); o.stop(audioCtx.currentTime + d);
}
function jumpSound() { beep(400, 0.08); }
function scoreSound() { beep(880, 0.1); setTimeout(() => beep(1320, 0.08), 60); }
function hitSound()  { beep(80, 0.3, "sawtooth", 0.12); }

// ===== 键盘 =====
document.addEventListener("keydown", e => {
    if (e.code === "Space") {
        e.preventDefault();
        if (gameOver) {
            bird = { y: 280, v: 0 }; pipes = []; score = 0; frame = 0; gameOver = false;
        } else {
            bird.v = JUMP; jumpSound();
        }
    }
});

// ===== 碰撞 =====
function hitTest() {
    if (bird.y - BIRD_R <= 0 || bird.y + BIRD_R >= H - GROUND_H) return true;
    for (let p of pipes) {
        let h = PIPE_GAP / 2;
        if (BIRD_X + BIRD_R > p.x && BIRD_X - BIRD_R < p.x + PIPE_W) {
            if (bird.y - BIRD_R < p.gapY - h || bird.y + BIRD_R > p.gapY + h) return true;
        }
    }
    return false;
}

// ===== 绘制 =====
function drawSky() {
    let g = ctx.createLinearGradient(0, 0, 0, H - GROUND_H);
    g.addColorStop(0, "#B4DCFF"); g.addColorStop(1, "#87CEEB");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H - GROUND_H);
}

function drawClouds() {
    ctx.fillStyle = "rgba(255,255,255,0.7)";
    let c = (x, y) => {
        ctx.beginPath(); ctx.arc(x, y, 18, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x+18, y-8, 22, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x-8, y+3, 14, 0, Math.PI*2); ctx.fill();
    };
    c((80 + frame*0.3) % (W+200) - 100, 60);
    c((280 + frame*0.2) % (W+200) - 100, 110);
    c((360 + frame*0.25) % (W+200) - 100, 40);
}

function drawBird() {
    let cx = BIRD_X, cy = bird.y;
    let tilt = Math.max(-0.5, Math.min(0.5, -bird.v * 0.1));
    let wing = Math.sin(frame * 0.3) * 5;
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(tilt);
    ctx.fillStyle = "#FFDC32";
    ctx.beginPath(); ctx.ellipse(0, 0, BIRD_R, BIRD_R-4, 0, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = "#FFC800";
    ctx.beginPath(); ctx.ellipse(-2, 3, 10, 6, -0.3 + wing*0.03, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = "#FFF";
    ctx.beginPath(); ctx.arc(6, -4, 5, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = "#000";
    ctx.beginPath(); ctx.arc(8, -4, 2.5, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = "#FF8C00";
    ctx.beginPath(); ctx.moveTo(12, -1); ctx.lineTo(22, -1); ctx.lineTo(12, -6); ctx.fill();
    ctx.restore();
}

function drawPipe(p) {
    let h = PIPE_GAP / 2;
    let topH = p.gapY - h - CAP_H;
    if (topH > 0) { ctx.fillStyle = "#50B432"; ctx.fillRect(p.x, 0, PIPE_W, topH); }
    ctx.fillStyle = "#32A028";
    ctx.fillRect(p.x - 3, p.gapY - h - CAP_H, PIPE_W + 6, CAP_H);
    ctx.strokeStyle = "#3C8C1E"; ctx.lineWidth = 2;
    ctx.strokeRect(p.x - 3, p.gapY - h - CAP_H, PIPE_W + 6, CAP_H);
    ctx.fillStyle = "#32A028";
    ctx.fillRect(p.x - 3, p.gapY + h, PIPE_W + 6, CAP_H);
    ctx.strokeRect(p.x - 3, p.gapY + h, PIPE_W + 6, CAP_H);
    let botY = p.gapY + h + CAP_H;
    ctx.fillStyle = "#50B432";
    ctx.fillRect(p.x, botY, PIPE_W, H - botY);
}

function drawGround() {
    let gy = H - GROUND_H;
    ctx.fillStyle = "#DEB887"; ctx.fillRect(0, gy, W, GROUND_H);
    ctx.fillStyle = "#A0825A"; ctx.fillRect(0, gy, W, 4);
    let off = (-frame * PIPE_SPEED) % 40;
    ctx.strokeStyle = "#A0825A"; ctx.lineWidth = 2;
    for (let x = -40 + off; x < W + 40; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, gy+15); ctx.lineTo(x+20, gy+15); ctx.stroke();
    }
}

function drawUI() {
    ctx.fillStyle = "#FFF"; ctx.font = "bold 48px Microsoft YaHei";
    ctx.textAlign = "center"; ctx.fillText(score, W/2, 55);
    if (gameOver) {
        ctx.fillStyle = "rgba(0,0,0,0.5)"; ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = "#FF3232"; ctx.font = "bold 36px Microsoft YaHei";
        ctx.fillText("游戏结束", W/2, H/2 - 15);
        ctx.fillStyle = "#FFF"; ctx.font = "18px Microsoft YaHei";
        ctx.fillText("最终分数: " + score, W/2, H/2 + 25);
        ctx.fillText("按空格键重新开始", W/2, H/2 + 55);
    }
}

// ===== 主循环 =====
function update() {
    if (!gameOver) {
        bird.v += GRAVITY; bird.y += bird.v;
        frame++;
        if (frame % PIPE_INTERVAL === 0) {
            pipes.push({ x: W, gapY: 120 + Math.random() * (H - GROUND_H - 240), scored: false });
        }
        for (let p of pipes) {
            p.x -= PIPE_SPEED;
            if (p.x + PIPE_W < BIRD_X && !p.scored) { score++; p.scored = true; scoreSound(); }
        }
        pipes = pipes.filter(p => p.x + PIPE_W > 0);
        if (hitTest()) { gameOver = true; hitSound(); }
    }
    drawSky(); drawClouds();
    for (let p of pipes) drawPipe(p);
    drawGround(); drawBird(); drawUI();
}

setInterval(update, 1000/60);
