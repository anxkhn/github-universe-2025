from badgeware import screen, io, brushes, shapes, PixelFont
import time

player_y = cpu_y = 48.0
ball_x, ball_y = 80.0, 60.0
vx, vy = -70.0, 35.0
player_score = cpu_score = 0
playing = False
last_tick = None
white = brushes.color(255, 255, 255)
background = brushes.color(20, 30, 35)


def init():
    screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")


def serve(direction):
    global ball_x, ball_y, vx, vy
    ball_x, ball_y = 80.0, 60.0
    vx, vy = direction * 70.0, 35.0


def update():
    global player_y, cpu_y, ball_x, ball_y, vx, vy
    global player_score, cpu_score, playing, last_tick
    now = time.ticks_ms()
    dt = min(0.05, max(0, time.ticks_diff(now, last_tick) / 1000)) if last_tick is not None else 0
    last_tick = now
    if io.BUTTON_B in io.pressed and not playing:
        player_score = cpu_score = 0
        serve(-1)
        playing = True
    if playing:
        player_y += (int(io.BUTTON_DOWN in io.held) - int(io.BUTTON_UP in io.held)) * 100 * dt
        player_y = max(18, min(94, player_y))
        cpu_y += max(-65 * dt, min(65 * dt, ball_y - cpu_y - 12))
        cpu_y = max(18, min(94, cpu_y))
        ball_x += vx * dt
        ball_y += vy * dt
        if ball_y < 18 or ball_y > 116:
            ball_y = max(18, min(116, ball_y))
            vy = -vy
        if vx < 0 and ball_x <= 8 and cpu_y - 3 <= ball_y <= cpu_y + 24:
            ball_x = 8
            vx = min(150, -vx * 1.08)
            vy = (ball_y - cpu_y - 12) * 5
        if vx > 0 and ball_x >= 148 and player_y - 3 <= ball_y <= player_y + 24:
            ball_x = 148
            vx = -min(150, vx * 1.08)
            vy = (ball_y - player_y - 12) * 5
        if ball_x < 0:
            player_score += 1
            serve(1)
        elif ball_x > 160:
            cpu_score += 1
            serve(-1)
        if max(player_score, cpu_score) >= 6:
            playing = False
    screen.brush = background
    screen.clear()
    screen.brush = white
    screen.text("%d  TENNIS  %d" % (cpu_score, player_score), 35, 2)
    for y in range(20, 120, 10):
        screen.draw(shapes.rectangle(79, y, 2, 5))
    screen.draw(shapes.rectangle(4, cpu_y, 4, 24))
    screen.draw(shapes.rectangle(152, player_y, 4, 24))
    screen.draw(shapes.circle(ball_x, ball_y, 2))
    if not playing:
        text = "YOU WIN" if player_score >= 6 else "CPU WINS" if cpu_score >= 6 else "UP/DOWN: move"
        for label, y in ((text, 42), ("B: start", 65)):
            width, _ = screen.measure_text(label)
            screen.text(label, 80 - width / 2, y)
