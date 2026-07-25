// ==================== 俄罗斯方块 - Canvas 版 ====================
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

// 网格
const COLS = 10, ROWS = 20, CELL = 30;
const GAME_W = COLS * CELL, GAME_H = ROWS * CELL;
const PANEL_W = 150;

// 7种方块定义
const SHAPES = {
    I: [[0,0],[0,1],[0,2],[0,3]],
    O: [[0,0],[0,1],[1,0],[1,1]],
    T: [[0,1],[1,0],[1,1],[1,2]],
    S: [[0,1],[0,2],[1,0],[1,1]],
    Z: [[0,0],[0,1],[1,1],[1,2]],
    J: [[0,0],[1,0],[1,1],[1,2]],
    L: [[0,2],[1,0],[1,1],[1,2]],
};
const COLORS = {
    I: "#0FF", O: "#FF0", T: "#A0F", S: "#0F0", Z: "#F00", J: "#00F", L: "#F80",
};
const TYPES = Object.keys(SHAPES);
const SCORE_TABLE = {1:100, 2:300, 3:500, 4:800};

// 状态
let grid = Array.from({length: ROWS}, () => Array(COLS).fill(0));
let piece = {};
let nextType = TYPES[Math.floor(Math.random() * TYPES.length)];
let score = 0, dropCount = 0, gameOver = false;
let dropInterval = 35; // 随等级递减

// ===== 音效 =====
const ac = new (window.AudioContext || window.webkitAudioContext)();
function beep(f, d, t="square", v=0.06) {
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = t; o.frequency.setValueAtTime(f, ac.currentTime);
    g.gain.setValueAtTime(v, ac.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + d);
    o.connect(g); g.connect(ac.destination);
    o.start(); o.stop(ac.currentTime + d);
}
function snd(s) {
    if (s==="move") beep(300, 0.03, "square", 0.04);
    if (s==="rotate") beep(500, 0.04, "square", 0.05);
    if (s==="drop") beep(200, 0.08, "triangle", 0.08);
    if (s==="clear") beep(600, 0.12, "square", 0.08);
    if (s==="over") beep(120, 0.4, "sawtooth", 0.12);
}

// ===== 工具函数 =====
function validPos(coords, row, col) {
    for (let [dr, dc] of coords) {
        let r = row + dr, c = col + dc;
        if (c < 0 || c >= COLS || r >= ROWS) return false;
        if (r >= 0 && grid[r][c] !== 0) return false;
    }
    return true;
}

function rotate(coords) { return coords.map(([dr, dc]) => [dc, -dr]); }

function spawn() {
    piece.type = nextType;
    nextType = TYPES[Math.floor(Math.random() * TYPES.length)];
    piece.row = 0;
    piece.col = Math.floor(COLS / 2) - 1;
    piece.coords = SHAPES[piece.type].map(c => [...c]);
    if (!validPos(piece.coords, piece.row, piece.col)) gameOver = true;
}

function lock() {
    let color = COLORS[piece.type];
    for (let [dr, dc] of piece.coords) {
        let r = piece.row + dr, c = piece.col + dc;
        if (r >= 0 && r < ROWS && c >= 0 && c < COLS) grid[r][c] = color;
    }
}

function clearLines() {
    let cleared = 0, row = ROWS - 1;
    while (row >= 0) {
        if (grid[row].every(cell => cell !== 0)) {
            cleared++;
            for (let r = row; r > 0; r--) grid[r] = [...grid[r-1]];
            grid[0] = Array(COLS).fill(0);
        } else { row--; }
    }
    if (cleared > 0) { score += SCORE_TABLE[cleared] || cleared*100; snd("clear"); }
}

function restart() {
    grid = Array.from({length: ROWS}, () => Array(COLS).fill(0));
    score = 0; dropCount = 0; gameOver = false;
    nextType = TYPES[Math.floor(Math.random() * TYPES.length)];
    spawn();
}

// ===== 键盘 =====
document.addEventListener("keydown", e => {
    e.preventDefault();
    if (e.code === "KeyR") { restart(); return; }
    if (gameOver) return;

    if (e.code === "ArrowLeft") {
        if (validPos(piece.coords, piece.row, piece.col - 1)) { piece.col--; snd("move"); }
    } else if (e.code === "ArrowRight") {
        if (validPos(piece.coords, piece.row, piece.col + 1)) { piece.col++; snd("move"); }
    } else if (e.code === "ArrowDown") {
        while (validPos(piece.coords, piece.row + 1, piece.col)) piece.row++;
        snd("drop"); lock(); clearLines(); spawn(); if (gameOver) snd("over");
    } else if (e.code === "ArrowUp") {
        if (piece.type === "O") return;
        let r = rotate(piece.coords);
        if (validPos(r, piece.row, piece.col)) { piece.coords = r; snd("rotate"); }
    }
});

// ===== 绘制 =====
function drawCell(r, c, color) {
    let x = c * CELL, y = r * CELL;
    ctx.fillStyle = color;
    ctx.fillRect(x + 1, y + 1, CELL - 2, CELL - 2);
    // 高光
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    ctx.fillRect(x + 1, y + 1, CELL - 2, 3);
    ctx.fillRect(x + 1, y + 1, 3, CELL - 2);
    // 阴影
    ctx.fillStyle = "rgba(0,0,0,0.3)";
    ctx.fillRect(x + 2, y + CELL - 4, CELL - 4, 3);
    ctx.fillRect(x + CELL - 4, y + 2, 3, CELL - 4);
}

function drawGrid() {
    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            let x = c * CELL, y = r * CELL;
            ctx.fillStyle = grid[r][c] || "#1E1E2E";
            ctx.fillRect(x, y, CELL, CELL);
            ctx.strokeStyle = "#2A2A3A";
            ctx.strokeRect(x, y, CELL, CELL);
        }
    }
    // 已固定的方块画高光
    for (let r = 0; r < ROWS; r++)
        for (let c = 0; c < COLS; c++)
            if (grid[r][c]) drawCell(r, c, grid[r][c]);
}

function drawPiece() {
    let color = COLORS[piece.type];
    for (let [dr, dc] of piece.coords) {
        let r = piece.row + dr, c = piece.col + dc;
        if (r >= 0 && r < ROWS && c >= 0 && c < COLS) drawCell(r, c, color);
    }
}

function drawPanel() {
    let px = GAME_W;
    ctx.fillStyle = "#191928";
    ctx.fillRect(px, 0, PANEL_W, GAME_H);

    ctx.fillStyle = "#FFF"; ctx.font = "bold 22px Microsoft YaHei";
    ctx.fillText("俄罗斯方块", px + 8, 30);
    ctx.fillStyle = "#444"; ctx.fillRect(px + 4, 42, PANEL_W - 8, 1);

    ctx.fillStyle = "#FFF"; ctx.font = "17px Microsoft YaHei";
    ctx.fillText("分数: " + score, px + 8, 70);
    ctx.fillText("等级: " + Math.floor(score/500), px + 8, 95);

    ctx.fillText("下一个:", px + 8, 130);
    let color = COLORS[nextType];
    for (let [dr, dc] of SHAPES[nextType]) {
        ctx.fillStyle = color;
        ctx.fillRect(px + 20 + dc * 16, 145 + dr * 16, 15, 15);
    }

    if (gameOver) {
        ctx.fillStyle = "rgba(0,0,0,0.6)";
        ctx.fillRect(0, 0, GAME_W + PANEL_W, GAME_H);
        ctx.fillStyle = "#FF3232"; ctx.font = "bold 30px Microsoft YaHei";
        ctx.textAlign = "center";
        ctx.fillText("游戏结束", GAME_W/2, GAME_H/2 - 10);
        ctx.fillStyle = "#FFF"; ctx.font = "18px Microsoft YaHei";
        ctx.fillText("按 R 重新开始", GAME_W/2, GAME_H/2 + 30);
        ctx.textAlign = "start";
    }
}

// ===== 主循环 =====
spawn();
function update() {
    if (!gameOver) {
        dropCount++;
        if (dropCount >= Math.max(5, dropInterval - Math.floor(score/500)*3)) {
            dropCount = 0;
            if (validPos(piece.coords, piece.row + 1, piece.col)) {
                piece.row++;
            } else {
                lock(); clearLines(); spawn(); if (gameOver) snd("over");
            }
        }
    }
    ctx.fillStyle = "#0F0F1A";
    ctx.fillRect(0, 0, GAME_W + PANEL_W, GAME_H);
    drawGrid();
    drawPiece();
    drawPanel();
}

setInterval(update, 1000/60);
