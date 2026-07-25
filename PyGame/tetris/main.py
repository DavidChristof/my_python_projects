"""
俄罗斯方块 - 阶段⑥：音效 + 难度递增 + 最终打磨
西北工业大学 Python 项目练习

最终版包含：
  - 7 种方块 + 旋转 + 硬降
  - 消行加分（1行100, 2行300, 3行500, 4行800）
  - 程序化合成音效（无需外部文件）
  - 难度递增（分数越高下落越快）
  - 下一个方块预览
  - 等级显示
"""
import pygame
import sys
import random
import io
import struct
import wave
import math

# ==================== 初始化 ====================
pygame.init()
pygame.mixer.init()  # 🆕 音频

# ==================== 常量 ====================
COLS = 10
ROWS = 20
CELL_SIZE = 30

GAME_WIDTH = COLS * CELL_SIZE
GAME_HEIGHT = ROWS * CELL_SIZE
PANEL_WIDTH = 150
SCREEN_WIDTH = GAME_WIDTH + PANEL_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT

FPS = 60
DROP_INTERVAL_BASE = 35  # 🆕 基础下落间隔（帧数），会随等级递减

# 颜色
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)
WHITE = (255, 255, 255)
PANEL_BG = (25, 25, 35)

# 7 种方块定义
SHAPES = {
    "I": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "O": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "T": [(0, 1), (1, 0), (1, 1), (1, 2)],
    "S": [(0, 1), (0, 2), (1, 0), (1, 1)],
    "Z": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "J": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "L": [(0, 2), (1, 0), (1, 1), (1, 2)],
}

COLORS = {
    "I": (0, 240, 240),
    "O": (255, 255, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (255, 160, 0),
}

PIECE_TYPES = list(SHAPES.keys())

# ==================== 创建窗口 ====================
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("俄罗斯方块 - 最终版")
clock = pygame.time.Clock()

# ==================== 游戏状态 ====================
grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
drop_counter = 0

# 当前方块（先占位，函数定义后再 spawn）
current_piece = {}

# 🆕 分数 & 状态
score = 0
game_over = False
next_piece_type = random.choice(PIECE_TYPES)  # 🆕 下一个方块类型

# 🆕 消行计分表：消1行100分，2行300，3行500，4行800
SCORE_TABLE = {1: 100, 2: 300, 3: 500, 4: 800}

# ==================== 🆕 音效系统（程序化合成） ====================

def make_sound(frequency, duration, volume=0.3, freq_end=None):
    """用数学合成 WAV 音效，不依赖外部文件"""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            freq = frequency + (freq_end - frequency) * i / n_samples if freq_end else frequency
            envelope = max(0, 1 - i / n_samples)
            value = int(volume * 32767 * math.sin(2 * math.pi * freq * t) * envelope)
            wf.writeframes(struct.pack('<h', value))
    buf.seek(0)
    return pygame.mixer.Sound(buffer=buf.read())

sound_move = make_sound(300, 0.03, 0.15)                    # 移动：短促咔嗒
sound_rotate = make_sound(500, 0.04, 0.2)                   # 旋转：轻微转音
sound_drop = make_sound(200, 0.08, 0.3, freq_end=60)        # 硬降：坠落声
sound_clear = make_sound(600, 0.12, 0.35, freq_end=1200)    # 消行：清脆上升
sound_gameover = make_sound(120, 0.4, 0.5, freq_end=40)     # 游戏结束：低沉

# ==================== 字体 ====================
FONT_NAME = "Microsoft YaHei"
font_title = pygame.font.SysFont(FONT_NAME, 24, bold=True)
font_info = pygame.font.SysFont(FONT_NAME, 18)

# ==================== 🆕 碰撞检测 ====================

def is_valid_position(coords, row, col):
    """
    检测方块在 (row, col) 位置是否合法
    coords: 4 个相对坐标 [(dr, dc), ...]
    """
    for (dr, dc) in coords:
        r = row + dr
        c = col + dc
        if c < 0 or c >= COLS:
            return False
        if r >= ROWS:
            return False
        if r >= 0 and grid[r][c] != 0:
            return False
    return True


def rotate_coords(coords):
    """🆕 顺时针旋转 90°：(dr, dc) → (dc, -dr)"""
    return [(dc, -dr) for (dr, dc) in coords]


def lock_piece():
    """将当前方块固定到 grid 中"""
    color = COLORS[current_piece["type"]]
    for (dr, dc) in current_piece["coords"]:
        r = current_piece["row"] + dr
        c = current_piece["col"] + dc
        if 0 <= r < ROWS and 0 <= c < COLS:
            grid[r][c] = color


def spawn_piece():
    """生成新方块：当前方块 = 之前预览的，并生成新的预览"""
    global game_over, next_piece_type
    piece_type = next_piece_type
    next_piece_type = random.choice(PIECE_TYPES)
    current_piece["type"] = piece_type
    current_piece["row"] = 0
    current_piece["col"] = COLS // 2 - 1
    current_piece["coords"] = SHAPES[piece_type][:]
    if not is_valid_position(current_piece["coords"],
                             current_piece["row"],
                             current_piece["col"]):
        game_over = True


def clear_lines():
    """🆕 消除已填满的行，返回消除行数"""
    global score
    lines_cleared = 0
    row = ROWS - 1  # 从底部往上检查
    while row >= 0:
        # 检查第 row 行是否全部填满（没有 0）
        if all(grid[row][col] != 0 for col in range(COLS)):
            lines_cleared += 1
            # 将 row 以上的所有行整体下移一行
            for r in range(row, 0, -1):
                grid[r] = grid[r - 1][:]  # 复制上一行的数据
            grid[0] = [0] * COLS  # 最顶部变为空行
            # row 不变，因为上面行下移后需要重新检查当前行
        else:
            row -= 1  # 这一行没满，检查上一行
    
    # 🆕 根据消除行数加分
    if lines_cleared > 0:
        score += SCORE_TABLE.get(lines_cleared, lines_cleared * 100)
        sound_clear.play()  # 🆕 消行音效

    return lines_cleared


def get_level():
    """🆕 根据分数计算等级：每 500 分升一级"""
    return score // 500


def get_drop_interval():
    """🆕 根据等级计算下落间隔：等级越高越快（最低 5 帧）"""
    level = get_level()
    return max(5, DROP_INTERVAL_BASE - level * 3)

# ==================== 绘制函数 ====================

def draw_cell(row, col, color):
    """绘制单个格子（带立体高光）"""
    x = col * CELL_SIZE
    y = row * CELL_SIZE
    pygame.draw.rect(screen, color, (x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2))
    lighter = tuple(min(255, c + 50) for c in color)
    pygame.draw.line(screen, lighter, (x + 1, y + 1), (x + CELL_SIZE - 3, y + 1), 2)
    pygame.draw.line(screen, lighter, (x + 1, y + 1), (x + 1, y + CELL_SIZE - 3), 2)
    darker = tuple(max(0, c - 50) for c in color)
    pygame.draw.line(screen, darker, (x + 2, y + CELL_SIZE - 2), (x + CELL_SIZE - 2, y + CELL_SIZE - 2), 2)
    pygame.draw.line(screen, darker, (x + CELL_SIZE - 2, y + 2), (x + CELL_SIZE - 2, y + CELL_SIZE - 2), 2)


def draw_grid():
    """绘制游戏区域"""
    for row in range(ROWS):
        for col in range(COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            color = grid[row][col] if grid[row][col] else DARK_GRAY
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)


def draw_current_piece():
    """绘制当前活动方块"""
    color = COLORS[current_piece["type"]]
    for (dr, dc) in current_piece["coords"]:
        row = current_piece["row"] + dr
        col = current_piece["col"] + dc
        if 0 <= row < ROWS and 0 <= col < COLS:
            draw_cell(row, col, color)


def draw_panel():
    """绘制右侧信息面板"""
    panel_x = GAME_WIDTH
    pygame.draw.rect(screen, PANEL_BG, (panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    title = font_title.render("俄罗斯方块", True, WHITE)
    screen.blit(title, (panel_x + 8, 20))
    pygame.draw.line(screen, GRAY, (panel_x + 5, 55), (panel_x + PANEL_WIDTH - 5, 55), 1)

    # 🆕 分数
    score_label = font_info.render(f"分数: {score}", True, WHITE)
    screen.blit(score_label, (panel_x + 8, 65))

    # 🆕 等级
    level_label = font_info.render(f"等级: {get_level()}", True, WHITE)
    screen.blit(level_label, (panel_x + 8, 90))

    # 🆕 下一个方块预览
    next_label = font_info.render("下一个:", True, WHITE)
    screen.blit(next_label, (panel_x + 8, 125))
    # 绘制预览方块（小格子，居中显示）
    preview_color = COLORS[next_piece_type]
    preview_size = 18  # 预览格子比实际略小
    offset_x = panel_x + 20
    offset_y = 155
    for (dr, dc) in SHAPES[next_piece_type]:
        px = offset_x + dc * preview_size
        py = offset_y + dr * preview_size
        pygame.draw.rect(screen, preview_color,
                         (px, py, preview_size - 1, preview_size - 1))

    # 🆕 游戏结束提示
    if game_over:
        over_text = font_title.render("游戏结束", True, (255, 50, 50))
        screen.blit(over_text, (panel_x + 8, 240))
        restart = font_info.render("按R重新开始", True, WHITE)
        screen.blit(restart, (panel_x + 8, 275))


# ==================== 主循环 ====================
spawn_piece()
print("🎮 俄罗斯方块 最终版已启动！← → ↓ ↑ 操控，R 重开。")

running = True
while running:
    # ----- 1. 处理事件 -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
                score = 0
                game_over = False
                drop_counter = 0
                next_piece_type = random.choice(PIECE_TYPES)
                spawn_piece()
                continue

            if game_over:
                continue

            if event.key == pygame.K_LEFT:
                if is_valid_position(current_piece["coords"],
                                     current_piece["row"],
                                     current_piece["col"] - 1):
                    current_piece["col"] -= 1
                    sound_move.play()  # 🆕

            elif event.key == pygame.K_RIGHT:
                if is_valid_position(current_piece["coords"],
                                     current_piece["row"],
                                     current_piece["col"] + 1):
                    current_piece["col"] += 1
                    sound_move.play()  # 🆕

            elif event.key == pygame.K_DOWN:
                while is_valid_position(current_piece["coords"],
                                        current_piece["row"] + 1,
                                        current_piece["col"]):
                    current_piece["row"] += 1
                sound_drop.play()  # 🆕 硬降音效
                lock_piece()
                clear_lines()
                spawn_piece()
                if game_over:
                    sound_gameover.play()  # 🆕

            elif event.key == pygame.K_UP:
                if current_piece["type"] == "O":
                    continue
                rotated = rotate_coords(current_piece["coords"])
                if is_valid_position(rotated,
                                     current_piece["row"],
                                     current_piece["col"]):
                    current_piece["coords"] = rotated
                    sound_rotate.play()  # 🆕

    # ----- 2. 自动下落（🆕 动态速度） -----
    if not game_over:
        drop_counter += 1
        if drop_counter >= get_drop_interval():
            drop_counter = 0
            if is_valid_position(current_piece["coords"],
                                 current_piece["row"] + 1,
                                 current_piece["col"]):
                current_piece["row"] += 1
            else:
                lock_piece()
                clear_lines()
                spawn_piece()
                if game_over:
                    sound_gameover.play()  # 🆕

    # ----- 3. 绘制 -----
    screen.fill(BLACK)
    draw_grid()
    draw_current_piece()
    draw_panel()
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
