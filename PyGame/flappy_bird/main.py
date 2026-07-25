"""
Flappy Bird - 阶段⑤：美化最终版
西北工业大学 Python 项目练习

美化内容：
  - 小鸟：椭圆身体 + 眼睛 + 嘴巴 + 翅膀动画 + 飞行倾斜
  - 管道：绿色管身 + 深绿管帽
  - 地面：棕色滚动地面
  - 天空：云朵装饰
  - 难度：分数越高，管道速度越快
"""
import pygame
import sys
import random
import math
import io
import struct
import wave

# ==================== 初始化 Pygame ====================
pygame.init()
pygame.mixer.init()  # 🆕 初始化音频模块

# ==================== 常量配置 ====================
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60
GROUND_HEIGHT = 80  # 🆕 地面高度

# 颜色
SKY_BLUE = (135, 206, 235)
SKY_TOP = (180, 220, 255)    # 🆕 天空渐变顶部色
YELLOW = (255, 220, 50)       # 小鸟身体
ORANGE = (255, 140, 0)        # 小鸟嘴巴
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (80, 180, 50)         # 管道
DARK_GREEN = (60, 140, 30)    # 管道边缘
PIPE_CAP = (50, 160, 40)      # 🆕 管帽颜色
GROUND_BROWN = (222, 184, 135)
GROUND_DARK = (160, 130, 80)
CLOUD_WHITE = (240, 248, 255)

# 小鸟配置
BIRD_X = 100
BIRD_RADIUS = 18  # 🆕 小鸟用圆形，半径为 18

# 物理参数
GRAVITY = 0.45
JUMP_STRENGTH = -7.5

# 管道配置
PIPE_WIDTH = 58
PIPE_GAP = 155
PIPE_SPEED_BASE = 3         # 🆕 基础速度
PIPE_SPAWN_INTERVAL = 90
PIPE_CAP_HEIGHT = 25        # 🆕 管帽高度

# ==================== 创建游戏窗口 ====================
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird - 最终版")
clock = pygame.time.Clock()

# 字体
FONT_NAME = "Microsoft YaHei"
font = pygame.font.SysFont(FONT_NAME, 48)
font_small = pygame.font.SysFont(FONT_NAME, 28)
font_score = pygame.font.SysFont(FONT_NAME, 56)

# 小鸟状态
bird = {"y": 280, "velocity": 0}

# 管道列表
pipes = []

# 分数 & 状态
score = 0
game_over = False
frame_count = 0

# ==================== 🆕 音效系统 ====================

def make_sound(frequency, duration, volume=0.4, freq_end=None):
    """
    用数学合成音效，不需要任何外部音频文件！
    原理：生成正弦波 PCM 数据，写入 WAV 格式字节流
    
    参数：
      frequency  - 起始频率（Hz），越高音调越高
      duration   - 持续时长（秒）
      volume     - 音量 0.0~1.0
      freq_end   - 结束频率，可做出滑音效果
    """
    sample_rate = 22050          # 采样率（CD 品质是 44100，游戏用 22050 就够了）
    n_samples = int(sample_rate * duration)
    
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wf:
        wf.setnchannels(1)       # 单声道
        wf.setsampwidth(2)       # 16-bit 采样
        wf.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = i / sample_rate
            # 频率渐变（如 400Hz → 800Hz 产生上升音效）
            if freq_end:
                progress = i / n_samples
                freq = frequency + (freq_end - frequency) * progress
            else:
                freq = frequency
            # 音量包络：快速衰减，模拟打击感
            envelope = max(0, 1 - i / n_samples)
            # 正弦波
            value = int(volume * 32767 * math.sin(2 * math.pi * freq * t) * envelope)
            wf.writeframes(struct.pack('<h', value))
    
    buf.seek(0)
    return pygame.mixer.Sound(buffer=buf.read())

# 🆕 创建三种音效
sound_jump = make_sound(400, 0.08, 0.3, freq_end=900)     # 跳跃：快速上升音
sound_score = make_sound(800, 0.1, 0.35)                   # 得分：清脆叮咚声
# 得分双音——用两个音叠加
sound_score2 = make_sound(1200, 0.08, 0.25)
sound_hit = make_sound(80, 0.25, 0.5, freq_end=40)         # 碰撞：低沉撞击

# ==================== 🆕 绘制函数 ====================

def draw_sky():
    """绘制渐变天空背景"""
    for i in range(SCREEN_HEIGHT - GROUND_HEIGHT):
        ratio = i / (SCREEN_HEIGHT - GROUND_HEIGHT)
        r = int(SKY_TOP[0] + (SKY_BLUE[0] - SKY_TOP[0]) * ratio)
        g = int(SKY_TOP[1] + (SKY_BLUE[1] - SKY_TOP[1]) * ratio)
        b = int(SKY_TOP[2] + (SKY_BLUE[2] - SKY_TOP[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))


def draw_clouds():
    """绘制装饰性云朵（根据帧数缓慢移动）"""
    cloud_positions = [
        (80 + (frame_count * 0.3) % (SCREEN_WIDTH + 200) - 100, 60),
        (250 + (frame_count * 0.2) % (SCREEN_WIDTH + 200) - 100, 120),
        (350 + (frame_count * 0.25) % (SCREEN_WIDTH + 200) - 100, 40),
    ]
    for cx, cy in cloud_positions:
        # 用多个椭圆组成云朵
        pygame.draw.ellipse(screen, CLOUD_WHITE, (cx, cy, 60, 30))
        pygame.draw.ellipse(screen, CLOUD_WHITE, (cx + 20, cy - 15, 50, 35))
        pygame.draw.ellipse(screen, CLOUD_WHITE, (cx - 10, cy + 5, 45, 25))


def draw_bird(y, velocity):
    """绘制小鸟：椭圆身体 + 眼睛 + 嘴巴 + 翅膀动画"""
    # 🆕 根据速度计算倾斜角度（向上飞时仰头，下落时低头）
    tilt = max(-30, min(30, -velocity * 6))

    # 🆕 翅膀动画：翅膀上下扇动
    wing_offset = math.sin(frame_count * 0.3) * 6

    cx = BIRD_X
    cy = int(y)

    # --- 身体（椭圆） ---
    body_surf = pygame.Surface((BIRD_RADIUS * 2 + 10, BIRD_RADIUS * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(body_surf, YELLOW, (0, 4, BIRD_RADIUS * 2, BIRD_RADIUS * 2 - 8))
    # 旋转身体
    body_surf = pygame.transform.rotate(body_surf, tilt)
    body_rect = body_surf.get_rect(center=(cx, cy))
    screen.blit(body_surf, body_rect)

    # --- 翅膀（椭圆，上下扇动） ---
    wing_surf = pygame.Surface((20, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(wing_surf, (255, 200, 0), (0, 0, 20, 14))
    wing_surf = pygame.transform.rotate(wing_surf, tilt + wing_offset * 2)
    wing_rect = wing_surf.get_rect(center=(cx - 2, cy + 3))
    screen.blit(wing_surf, wing_rect)

    # --- 眼睛（白色椭圆 + 黑色瞳孔） ---
    eye_x = cx + 7
    eye_y = cy - 5
    # 白色眼眶
    pygame.draw.circle(screen, WHITE, (int(eye_x), int(eye_y)), 6)
    # 黑色瞳孔
    pygame.draw.circle(screen, BLACK, (int(eye_x + 2), int(eye_y)), 3)

    # --- 嘴巴（橙色三角形） ---
    beak_x = cx + 14
    beak_y = cy - 2
    pygame.draw.polygon(screen, ORANGE, [
        (beak_x, beak_y),
        (beak_x + 12, beak_y),
        (beak_x, beak_y - 6)
    ])


def draw_pipe(pipe):
    """绘制单组管道（管帽 + 管身）"""
    px = pipe["x"]
    gap_center = pipe["gap_y"]
    half_gap = PIPE_GAP // 2

    # 上方管道
    top_body_h = gap_center - half_gap - PIPE_CAP_HEIGHT
    if top_body_h > 0:
        pygame.draw.rect(screen, GREEN, (px, 0, PIPE_WIDTH, top_body_h))
    # 上方管帽
    cap_top_y = gap_center - half_gap - PIPE_CAP_HEIGHT
    pygame.draw.rect(screen, PIPE_CAP, (px - 3, cap_top_y,
                                         PIPE_WIDTH + 6, PIPE_CAP_HEIGHT))
    pygame.draw.rect(screen, DARK_GREEN, (px - 3, cap_top_y,
                                           PIPE_WIDTH + 6, PIPE_CAP_HEIGHT), 2)

    # 下方管帽
    cap_bottom_y = gap_center + half_gap
    pygame.draw.rect(screen, PIPE_CAP, (px - 3, cap_bottom_y,
                                         PIPE_WIDTH + 6, PIPE_CAP_HEIGHT))
    pygame.draw.rect(screen, DARK_GREEN, (px - 3, cap_bottom_y,
                                           PIPE_WIDTH + 6, PIPE_CAP_HEIGHT), 2)
    # 下方管道
    bottom_body_y = cap_bottom_y + PIPE_CAP_HEIGHT
    pygame.draw.rect(screen, GREEN,
                     (px, bottom_body_y, PIPE_WIDTH, SCREEN_HEIGHT - bottom_body_y))


def draw_ground():
    """绘制滚动地面"""
    ground_y = SCREEN_HEIGHT - GROUND_HEIGHT
    # 地面主体
    pygame.draw.rect(screen, GROUND_BROWN, (0, ground_y, SCREEN_WIDTH, GROUND_HEIGHT))
    # 地面上边缘
    pygame.draw.rect(screen, GROUND_DARK, (0, ground_y, SCREEN_WIDTH, 4))
    # 🆕 地面纹理条纹（滚动）
    offset = (-frame_count * PIPE_SPEED_BASE) % 40
    for x in range(-40 + int(offset), SCREEN_WIDTH + 40, 40):
        pygame.draw.line(screen, GROUND_DARK, (x, ground_y + 15),
                         (x + 20, ground_y + 15), 2)


def check_collision(bird_y):
    """碰撞检测（小鸟是圆形，管道是矩形）"""
    bird_rect = pygame.Rect(BIRD_X - BIRD_RADIUS, bird_y - BIRD_RADIUS,
                             BIRD_RADIUS * 2, BIRD_RADIUS * 2)

    # 撞到天花板或地面
    ground_y = SCREEN_HEIGHT - GROUND_HEIGHT
    if bird_rect.top <= 0 or bird_rect.bottom >= ground_y:
        return True

    for pipe in pipes:
        half_gap = PIPE_GAP // 2
        # 上方管道碰撞体（含管帽）
        top_pipe = pygame.Rect(pipe["x"] - 3, 0,
                               PIPE_WIDTH + 6, pipe["gap_y"] - half_gap)
        # 下方管道碰撞体（含管帽）
        bottom_pipe = pygame.Rect(pipe["x"] - 3, pipe["gap_y"] + half_gap,
                                  PIPE_WIDTH + 6, SCREEN_HEIGHT)

        if bird_rect.colliderect(top_pipe) or bird_rect.colliderect(bottom_pipe):
            return True

    return False


# ==================== 游戏主循环 ====================
print("🎮 Flappy Bird 最终版已启动！按【空格键】操控小鸟！")

running = True
while running:
    # ----- 1. 处理事件 -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_over:
                    bird["y"] = 280
                    bird["velocity"] = 0
                    pipes.clear()
                    score = 0
                    frame_count = 0
                    game_over = False
                else:
                    bird["velocity"] = JUMP_STRENGTH
                    sound_jump.play()  # 🆕 跳跃音效

    # ----- 2. 更新逻辑 -----
    if not game_over:
        # 2a. 小鸟物理
        bird["velocity"] += GRAVITY
        bird["y"] += bird["velocity"]

        # 2b. 🆕 难度递增：每得 5 分，管道速度 +0.3
        current_speed = PIPE_SPEED_BASE + (score // 5) * 0.3

        # 2c. 生成新管道
        frame_count += 1
        if frame_count % PIPE_SPAWN_INTERVAL == 0:
            ground_y = SCREEN_HEIGHT - GROUND_HEIGHT
            gap_y = random.randint(130, ground_y - 130)
            pipes.append({"x": SCREEN_WIDTH, "gap_y": gap_y, "scored": False})

        # 2d. 移动管道
        for pipe in pipes:
            pipe["x"] -= current_speed

        # 2e. 计分
        for pipe in pipes:
            if pipe["x"] + PIPE_WIDTH < BIRD_X and not pipe["scored"]:
                score += 1
                pipe["scored"] = True
                sound_score.play()  # 🆕 得分音效

        # 2f. 碰撞检测
        if check_collision(bird["y"]):
            game_over = True
            sound_hit.play()  # 🆕 碰撞音效

        # 2g. 删除移出屏幕的管道
        pipes = [p for p in pipes if p["x"] + PIPE_WIDTH > 0]

    # ----- 3. 绘制画面 -----
    draw_sky()
    draw_clouds()

    for pipe in pipes:
        draw_pipe(pipe)

    draw_ground()
    draw_bird(bird["y"], bird["velocity"])

    # 分数显示
    score_text = font_score.render(str(score), True, WHITE)
    score_shadow = font_score.render(str(score), True, (0, 0, 0, 100))
    screen.blit(score_shadow, (SCREEN_WIDTH // 2 - score_text.get_width() // 2 + 2, 12))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 10))

    # 游戏结束画面
    if game_over:
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        over_text = font.render("游戏结束", True, RED)
        over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(over_text, over_rect)

        final_score = font_small.render(f"最终分数: {score}", True, WHITE)
        fs_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 15))
        screen.blit(final_score, fs_rect)

        restart_text = font_small.render("按空格键重新开始", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(restart_text, restart_rect)

    # ----- 4. 刷新屏幕 -----
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
