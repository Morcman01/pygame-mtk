import pygame
from sys import exit
from random import randint, choice
import json
import os
import math   # >>> GEPREK: needed for wave + orbit

# -----------------------
# init
# -----------------------
pygame.init()
clock = pygame.time.Clock()
font1 = pygame.font.Font('assets/slkscr.ttf', 25)
font2 = pygame.font.Font('assets/slkscr.ttf', 20)
quiz_font = pygame.font.Font('assets/cambriamath.ttf', 20)
game_over = False
# -----------------------
# >>> CHANGED: persistence file for player's bests
# -----------------------
SAVE_FILE = "leaderboard_save.json"

def load_leaderboard_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "best_answers": data.get("best_answers", 0),
                    "best_score": data.get("best_score", 0)
                }
        except Exception:
            pass
    return {"best_answers": 0, "best_score": 0}

def save_leaderboard_save(best_answers, best_score):
    data = {"best_answers": best_answers, "best_score": best_score}
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

# load saved bests at start
saved = load_leaderboard_save()
saved_best_answers = saved["best_answers"]
saved_best_score = saved["best_score"]

# -----------------------
# Sprites and functions
# -----------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        walk1 = pygame.image.load('assets/run1.png').convert_alpha()
        walk2 = pygame.image.load('assets/run2.png').convert_alpha()
        idle1 = pygame.image.load('assets/idle1.png').convert_alpha()
        scaled_walk1 = pygame.transform.scale(walk1, (120, 155))
        scaled_walk2 = pygame.transform.scale(walk2, (120, 155))
        scaled_idle1 = pygame.transform.scale(idle1, (120, 155))
        self.walk = [scaled_idle1, scaled_walk1, scaled_idle1, scaled_walk2]
        self.player_index = 0

        self.image = self.walk[self.player_index]
        self.rect = self.image.get_rect(midbottom = (100, 400))
        self.gravity = 0

        jump1 = pygame.image.load('assets/jump1.png').convert_alpha()
        self.jump = pygame.transform.scale(jump1, (120, 155))

    def player_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= 400:
            self.gravity = -22

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 400:
            self.rect.bottom = 400
            self.gravity = 0

    def player_animation(self):
        if self.rect.bottom < 400:
            self.image = self.jump
        else:
            self.player_index += 0.1
            if self.player_index >= len(self.walk):
                self.player_index = 0
            self.image = self.walk[int(self.player_index)]

    def update(self):
        self.player_input()
        self.apply_gravity()
        self.player_animation()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self,type):
        super().__init__()
        if type == 'burung':
            burung1 = pygame.image.load('assets/burung1.png').convert_alpha()
            burung2 = pygame.image.load('assets/burung2.png').convert_alpha()
            scaled_burung1 = pygame.transform.scale(burung1, (100, 100))
            scaled_burung2 = pygame.transform.scale(burung2, (100, 100))
            self.frames = [scaled_burung1, scaled_burung2]
            y_pos = 210
        else:
            kucing1 = pygame.image.load('assets/kucing1.png').convert_alpha()
            kucing2 = pygame.image.load('assets/kucing2.png').convert_alpha()
            scaled_kucing1 = pygame.transform.scale(kucing1, (95, 70))
            scaled_kucing2 = pygame.transform.scale(kucing2, (95, 70))

            self.frames = [scaled_kucing1, scaled_kucing2]
            y_pos = 400

            kucing3 = pygame.image.load('assets/kucing3.png').convert_alpha()
            self.jump = pygame.transform.scale(kucing3, (95, 70))

        self.animation_index = 0
        self.image = self.frames[self.animation_index]
        # spawn off-screen right
        self.rect = self.image.get_rect(midbottom = (randint(800,900), y_pos))

    def obstacle_animation(self):
        self.animation_index += 0.1
        if self.animation_index >= len(self.frames):
            self.animation_index = 0
        self.image = self.frames[int(self.animation_index)]

    def update(self):
        self.obstacle_animation()
        self.rect.x -= 8
        self.destroy()

    def destroy(self):
        if self.rect.x <= -150:
            self.kill()

# -----------------------
# >>> GEPREK: new sprite class for geprek pickup
# -----------------------
class Geprek(pygame.sprite.Sprite):
    def __init__(self, image, y_pos, speed=8, amplitude=20, wavelength=120, phase=0):
        super().__init__()
        # base image (scaled)
        self.base_image = pygame.transform.scale(image, (70, 70))  # main geprek size
        self.image = self.base_image.copy()
        # use midbottom as baseline so y_pos indicates midbottom
        self.rect = self.image.get_rect(midbottom=(900, y_pos))
        self.start_x = self.rect.x
        self.speed = speed  # move left
        # wave parameters
        self.amplitude = amplitude
        self.wavelength = wavelength
        self.phase = phase
        self.spawn_time = pygame.time.get_ticks()
        # baseline midbottom center (used for wave calc)
        self.y_center = y_pos

    def update(self):
        # horizontal movement (right -> left)
        self.rect.x -= self.speed

        # compute wave offset based on horizontal traveled distance
        x_moved = self.start_x - self.rect.x
        y_offset = self.amplitude * math.sin(2 * math.pi * x_moved / self.wavelength + self.phase)

        # We want midbottom position = y_center + y_offset, but ensure it doesn't go below ground
        # GROUND_Y will be defined globally (see below). We clamp rect.bottom <= GROUND_Y - ground_margin
        ground_margin = 2  # small gap so it doesn't overlap ground visually
        max_bottom = GROUND_Y - ground_margin  # global

        # compute target bottom from baseline midbottom + offset
        target_bottom = int(self.y_center + y_offset)
        # clamp so geprek does not go below ground surface
        if target_bottom > max_bottom:
            target_bottom = max_bottom

        # apply
        self.rect.bottom = target_bottom

        # destroy if off-screen
        if self.rect.right < -50:
            self.kill()

# -----------------------
# Shield: visual protection comprised of many small geprek orbiting player
# -----------------------
class Shield(pygame.sprite.Sprite):
    def __init__(self, player_sprite, small_image, count=8, radius=60, duration_ms=10000):
        super().__init__()
        self.player = player_sprite  # reference to player.sprite
        self.small_image = pygame.transform.scale(small_image, (30, 30))
        self.count = count
        self.radius = radius
        self.duration_ms = duration_ms
        self.start_time = pygame.time.get_ticks()
        # store angles for each orbiting small geprek
        self.angles = [i * (2 * math.pi / count) for i in range(count)]
        # rotate speed (radians per frame)
        self.rotate_speed = 0.08
        # create rects for drawing (list of [surf, rect, angle])
        self.items = []
        for a in self.angles:
            surf = self.small_image
            rect = surf.get_rect(center=self.player.rect.center)
            self.items.append([surf, rect, a])

    def update(self):
        # if duration passed, kill shield
        if pygame.time.get_ticks() - self.start_time >= self.duration_ms:
            self.kill()
            return
        # update angles and positions relative to player center
        cx, cy = self.player.rect.center
        for i in range(len(self.items)):
            surf, rect, ang = self.items[i]
            ang += self.rotate_speed
            self.items[i][2] = ang
            # position
            x = cx + int(self.radius * math.cos(ang))
            y = cy + int(self.radius * math.sin(ang))
            rect.center = (x, y)

    def draw(self, surface):
        # draw each small geprek
        for surf, rect, ang in self.items:
            surface.blit(surf, rect)

# -----------------------
# UI helper: simple Button
# -----------------------
class Button:
    def __init__(self, rect, text, font, action=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.action = action

    def draw(self, surface):
        pygame.draw.rect(surface, (50, 50, 100), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 3)
        txt_surf = self.font.render(self.text, True, 'White')
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# -----------------------
# Score / quiz / health etc.
# -----------------------
def display_score():
    global current_time
    # current_time is the value we use as "score" (units: int(pygame.time.get_ticks()/10) - start_time)
    current_time = int(pygame.time.get_ticks()/10) - start_time
    score_surface = font1.render(f'{current_time}', False, 'White')
    score_rect = score_surface.get_rect(center = (360, 50))
    screen.blit(score_surface,score_rect)

def display_quiztimer():
    time_left_ms = max(0, next_quiz_time_ms - pygame.time.get_ticks())
    seconds_left = time_left_ms / 1000.0
    quiztimer_surf = font1.render(f'Quiz in: {seconds_left:.1f}s', False, 'White')
    quiztimer_rect = quiztimer_surf.get_rect(topleft=(10, 10))
    screen.blit(quiztimer_surf, quiztimer_rect)

# >>> CHANGED: handle game end and persist bests
def end_game():
    global saved_best_answers, saved_best_score, correctAns, current_time
    global game_state_active, game_over   # <<< TAMBAHKAN INI !!!

    final_score = int(pygame.time.get_ticks()/10) - start_time
    final_answers = correctAns

    if final_answers > saved_best_answers:
        saved_best_answers = final_answers
    if final_score > saved_best_score:
        saved_best_score = final_score

    save_leaderboard_save(saved_best_answers, saved_best_score)

    pygame.time.set_timer(geprek_timer, 0)

    geprek_group.empty()
    shield_group.empty()

    game_state_active = False
    game_over = True   # <<< BARU SEKARANG MENJADI GLOBAL


# >>> CHANGED: health_counter now respects shield: if shield active, obstacle hit consumes shield and does not reduce life
def health_counter():
    global nyawa, game_state_active
    # detect collisions and remove collided obstacles
    collided = pygame.sprite.spritecollide(player.sprite, obstacle_group, True)
    if collided:
        # If shield active, consume shield and do NOT reduce nyawa
        if len(shield_group) > 0:
            # consume all shields (or only one if you prefer); here we remove all instances to be safe
            for sh in shield_group:
                sh.kill()  # shield disappears on hit
            # optionally you can play a sound or spawn effect here
        else:
            # no shield: lose one life per collision event (keep previous behavior: decrement by 1)
            nyawa -= 1
            if nyawa <= 0:
                end_game()

def jawaban(playerAnswer: bool):
    global correctAns, game_state_quiz, current_question, start_time, nyawa, next_quiz_time_ms
    if playerAnswer == current_question[1]:
        correctAns += 1
    else:
        nyawa -= 1
    paused_amount = int(pygame.time.get_ticks()/10) - pause_start_time
    start_time += paused_amount
    game_state_quiz = False
    current_question = None
    pygame.time.set_timer(quiz_timer, 10000)
    next_quiz_time_ms = pygame.time.get_ticks() + 10000

def quiz():
    global game_state_quiz, current_question, start_time, pause_start_time, quiz_timer, next_quiz_time_ms
    pygame.draw.rect(screen, 'White', pygame.Rect(0, 0, 720, 480))
    instruction_surf = quiz_font.render('Jawab benar dengan ↑ atau salah dengan ↓', True, 'Black')
    instruction_rect = instruction_surf.get_rect(center=(360, 130))
    screen.blit(instruction_surf, instruction_rect)

    q_text = current_question[0] if current_question else "Question missing"
    question_surface = quiz_font.render(q_text, True, 'Black')
    question_rect = question_surface.get_rect(center=(360, 200))
    screen.blit(question_surface, question_rect)

    time_left_units = max(0, quiz_end_time - int(pygame.time.get_ticks()/10))
    seconds_left = time_left_units / 100.0
    timer_surf = quiz_font.render(f'Time left: {seconds_left:.1f}s', True, 'Black')
    timer_rect = timer_surf.get_rect(center=(360, 240))
    screen.blit(timer_surf, timer_rect)

    if int(pygame.time.get_ticks()/10) >= quiz_end_time:
        paused_amount = int(pygame.time.get_ticks()/10) - pause_start_time
        start_time += paused_amount
        game_state_quiz = False
        current_question = None
        pygame.time.set_timer(quiz_timer, 10000)
        next_quiz_time_ms = pygame.time.get_ticks() + 10000

def draw_game_over():
    screen.fill((0, 0, 0))
    over_surf = font1.render("GAME OVER", True, "White")
    over_rect = over_surf.get_rect(center=(360, 160))
    screen.blit(over_surf, over_rect)

    score_surf = font1.render(f"Your Score : {current_time}", True, "White")
    score_rect = score_surf.get_rect(center=(360, 220))
    screen.blit(score_surf, score_rect)

    retry_surf = font2.render("Press ENTER to restart", True, "White")
    retry_rect = retry_surf.get_rect(center=(360, 280))
    screen.blit(retry_surf, retry_rect)

    menu_surf = font2.render("Press ESC or M to go back to Menu", True, "White")
    menu_rect = menu_surf.get_rect(center=(360, 320))
    screen.blit(menu_surf, menu_rect)



# -----------------------
# helper: restart & back-to-menu
# -----------------------
def restart_game():
    global nyawa, correctAns, start_time, game_over, game_state_active, next_quiz_time_ms
    # reset player values
    nyawa = 3
    correctAns = 0
    player.sprite.rect.midbottom = (100, 400)
    player.sprite.gravity = 0
    # reset timers and schedule
    start_time = int(pygame.time.get_ticks()/10)
    pygame.time.set_timer(quiz_timer, 10000)
    next_quiz_time_ms = pygame.time.get_ticks() + 10000
    schedule_next_geprek()
    # clear groups (just in case)
    obstacle_group.empty()
    geprek_group.empty()
    shield_group.empty()
    # set states
    game_over = False
    game_state_active = True

def back_to_menu():
    global game_over, game_state_active, show_leaderboard
    # stop timers
    pygame.time.set_timer(geprek_timer, 0)
    pygame.time.set_timer(quiz_timer, 0)
    # clear moving things
    obstacle_group.empty()
    geprek_group.empty()
    shield_group.empty()
    # reset flags to menu
    game_over = False
    game_state_active = False
    show_leaderboard = False
    # optionally reset background positions
    tiang_rect.x = 720
    awan1_rect.x = 720
    awan2_rect.x = 720

# -----------------------
# screen, assets, groups
# -----------------------
screen = pygame.display.set_mode((720, 480))
pygame.display.set_caption('Limit Runner')
icon = pygame.image.load('assets/heart.png').convert_alpha()
pygame.display.set_icon(icon)

# menu assets / texts
menu_bg = pygame.image.load('assets/menu_bg.png').convert_alpha()
menu_bg_rect = menu_bg.get_rect(topleft = (0,0))

menu_text1 = font1.render('Press Enter', False, 'White')  # kept but not shown
menu_text1_rect = menu_text1.get_rect(center = (520, 340))
menu_text2 = font1.render('to play!', False, 'White')    # kept but not shown
menu_text2_rect = menu_text2.get_rect(center = (520, 370))

# -----------------------
# >>> CHANGE BUTTON POSITION HERE (kanan bawah)
button_width = 200
button_height = 50
margin_right = 20
margin_bottom = 20
base_x = screen.get_width() - button_width - margin_right
base_y = screen.get_height() - button_height - margin_bottom
gap = 12

button_play = Button((base_x, base_y - 2 * (button_height + gap), button_width, button_height), 'Play', font2, action='play')
button_leader = Button((base_x, base_y - (button_height + gap), button_width, button_height), 'Leaderboard', font2, action='leaderboard')
button_exit = Button((base_x, base_y, button_width, button_height), 'Exit', font2, action='exit')

# Game assets
player = pygame.sprite.GroupSingle()
player.add(Player())

# >>> GROUND_Y must be defined so geprek logic can clamp; define from player's rect bottom
# >>> GEPREK CHANGED: ground level reference (sync with player starting bottom)
GROUND_Y = player.sprite.rect.bottom  # typically 400 in your setup

obstacle_group = pygame.sprite.Group()

# >>> GEPREK assets + groups
geprek_img = pygame.image.load('assets/geprek.png').convert_alpha()  # >>> GEPREK: main asset
geprek_group = pygame.sprite.Group()
shield_group = pygame.sprite.Group()  # holds Shield instances (singleton-ish)

game_bg = pygame.image.load('assets/danau.png').convert_alpha()
scaled_game_bg = pygame.transform.scale(game_bg, (800,490))
game_bg_rect = scaled_game_bg.get_rect(topleft = (0,0))

tanah = pygame.image.load('assets/tanah.png').convert_alpha()
tanah_rect = tanah.get_rect(topleft = (0,0))
# --- GROUND SCROLL SETUP ---
tanah_x1 = 0
tanah_x2 = tanah.get_width()


tiang = pygame.image.load('assets/tiang.png').convert_alpha()
scaled_tiang = pygame.transform.scale(tiang, (950,635))
tiang_rect = scaled_tiang.get_rect(topleft = (0,-140))

awan1 = pygame.image.load('assets/awan1.png').convert_alpha()
awan1_rect = awan1.get_rect(topleft = (0,0))

awan2 = pygame.image.load('assets/awan2.png').convert_alpha()
awan2_rect = awan2.get_rect(topleft = (0,0))

hati = pygame.image.load('assets/heart.png').convert_alpha()
scaled_hati1 = pygame.transform.scale(hati, (40, 40))
scaled_hati2 = pygame.transform.scale(hati, (40, 40))
scaled_hati3 = pygame.transform.scale(hati, (40, 40))
hati_rect1 = scaled_hati1.get_rect(midbottom = (680,50))
hati_rect2 = scaled_hati2.get_rect(midbottom = (635,50))
hati_rect3 = scaled_hati3.get_rect(midbottom = (590,50))

# Questions (same as before)
easy_questions = [
    ("(B/S) Suatu fungsi adalah relasi dimana setiap input memiliki tepat satu output.", True),
    ("(B/S) Domain fungs f(x) = x² adalah semua bilangan real", True),
    ("(B/S) Fungsi f(x)= √x terdefinisi untuk semua bilangan real.", False),
    ("(B/S) Notasi lim x -> 2 f(x) artinya nilai x yang dimasukkan harus tepat 2.", False),
    ("(B/S) lim x -> 2 (2x + 1) = 7", False),
    ("(B/S) Jika f(2) = 5, maka  pasti 5.", False),
    ("(B/S) Turunan fungsi f(x) di titik x = a menyatakan gradien garis singgung di titik tersebut.", True),
    ("(B/S) Turunan dari fungsi konstan f(x) = 5 adalah 0.", True),
    ("(B/S) Notasi f' (x) menyatakan turunan pertama dari f(x).", True),
    ("(B/S) Integral adalah kebalikan dari turunan.", True),
    ("(B/S) ∫2xdx = x²+ c.", True),
    ("(B/S) Integral tentu hasilnya adalah suatu fungsi", False)]
medium_questions = [ 
    ("(B/S) Fungsi f(x) = 1/x-1 kontinu di x = 1", False),
    ("(B/S) Jika lim x->c f(x) dan lim x->c g(x) ada, maka lim x->c [f(x)•g(x)] juga ada", True),
    ("(B/S) Nilai lim x-> 0 sin x/x = 1.", True),
    ("(B/S) Jika f'(c) = 0, f(x) pasti memiliki titik maksimum atau minimum di x = c.", False),
    ("(B/S) Turunan dari f(x) = eˣ adalah eˣ", True),
    ("(B/S) Aturan rantai digunakan untuk mencari turunan dari fungsi komposisi", True),
    ("(B/S) ₐ∫ᵇ f(x)dx = -₆∫ᵃ f(x)dx.", True),
    ("(B/S) Integral ∫(3x² + 2x)dx menghasilkan x³+ x²+ c", True),
    ("(B/S) Integral tentu ₁∫³ 2xdx menyatakan luas daerah di bawah garis y = 2x dari x = 1 sampai x = 3.", True)]
hard_questions = [
    ("(B/S) Suatu fungsi dapat memiliki limit di suatu titik dimana fungsi tersebut tidak terdefinisi.", True),
    ("(B/S) Jika lim x->c f(x) = L dan lim x -> c g(x) = L, maka f(c) = g(c).", False),
    ("(B/S) Fungsi f(x) = [x², jika x ≠ 0 dan 1, jika x = 0] kontinu di x = 0", False),
    ("(B/S) Jika sebuah fungsi dapat didiferensialkan di suatu titik, maka fungsi tersebut pasti kontinu di titik tersebut.", True),
    ("(B/S) Fungsi f(x) = |x-2| memiliki turunan di x = 2.", False),
    ("(B/S) Turunan kedua f′′(x) menyatakan laju perubahan dari f′(x).", True),
    ("(B/S) Menurut teorema dasar kalkulus, d/dx ₐ∫ˣ f(t)dt = f(x)", True),
    ("(B/S) Nilai ₋₁∫¹ x³dx adalah 0", True),
    ("(B/S)  Integral ∫ln xdx adalah contoh integral yang diselesaikan dengan metode substitusi.", False),
    ]

# Timers and counters
obstacle_timer = pygame.USEREVENT + 1
quiz_timer = pygame.USEREVENT + 2
geprek_timer = pygame.USEREVENT + 3  # >>> GEPREK: timer event for geprek spawn
pygame.time.set_timer(obstacle_timer,1800)
pygame.time.set_timer(quiz_timer, 10000)  # quiz every something seconds
# geprek timer will be scheduled when game starts
next_quiz_time_ms = pygame.time.get_ticks() + 10000

correctAns = 0
nyawa = 3

# Game state
game_state_active = False
game_state_quiz = False
start_time = 0
current_time = 0

tiang_interval = 800
next_tiang_time = 0

awan_interval = 200
next_awan_time = 0

current_question = None
quiz_duration = 500            # units used by your code (int(pygame.time.get_ticks()/10)), ~5s
quiz_end_time = 0
pause_start_time = 0

# --- FIX: define these before loop to avoid NameError ---
tiang_active = False
awan_active = False

# >>> LEADERBOARD FIXED ENTRIES (unchanged)
leaderboard_answers = [
    ("alexa", 6),
    ("bobby", 8),
    ("fauzan", 15),
    ("kucing", 21),
    ("mark xyz f(x)", 67),
]
leaderboard_scores = {
    "alexa": 1000,
    "bobby": 1400,
    "fauzan": 3200,
    "kucing": 5400,
    "mark xyz f(x)": 10000,
}

show_leaderboard = False
leaderboard_mode = 'answers'  # 'answers' or 'scores'

# Helper: set geprek spawn timer to random between 5-10 second (ms)
def schedule_next_geprek():
    # >>> GEPREK: random between 5_000 and 10_000 ms 
    interval = randint(5_000, 10_000)
    pygame.time.set_timer(geprek_timer, interval)
    return interval

# -----------------------
# main loop
# -----------------------
while True:
    events = pygame.event.get()
    for event in events:
        # --- handle keys while at game over screen ---
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:   # Enter = restart
                restart_game()
                continue
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_m:  # Esc or M = back to menu
                back_to_menu()
                continue

        if event.type == pygame.QUIT:
            if game_over:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    # reset game
                    nyawa = 3
                    correctAns = 0
                    player.sprite.rect.midbottom = (100,400)
                    player.sprite.gravity = 0
                    start_time = int(pygame.time.get_ticks()/10)
                    pygame.time.set_timer(quiz_timer, 10000)
                    next_quiz_time_ms = pygame.time.get_ticks() + 10000
                    schedule_next_geprek()
                    game_over = False
                    game_state_active = True
                    continue

            # save on quit as well
            save_leaderboard_save(saved_best_answers, saved_best_score)
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN and game_state_quiz:
            if event.key == pygame.K_UP:
                jawaban(True)
            if event.key == pygame.K_DOWN:
                jawaban(False)

            # ⬇⬇⬇ keluarkan ke level yang sama dengan event lain
        if event.type == obstacle_timer and game_state_active and not game_state_quiz:
                obstacle_group.add(Obstacle(choice(['kucing', 'kucing', 'burung'])))

        if event.type == quiz_timer:
            if game_state_active and not game_state_quiz:
                game_state_quiz = True
                rand = randint(0,2)
                if rand == 0 and easy_questions:
                    current_question = choice(easy_questions)
                    easy_questions.remove(current_question)
                    quiz_duration = 1000
                elif rand == 1 and medium_questions:
                    current_question = choice(medium_questions)
                    medium_questions.remove(current_question)
                    quiz_duration = 2000
                elif hard_questions:
                    current_question = choice(hard_questions)
                    hard_questions.remove(current_question)
                    quiz_duration = 3000
                else:
                    current_question = ("No more questions", True)
                    quiz_duration = 1000
                pause_start_time = int(pygame.time.get_ticks()/10)
                quiz_end_time = pause_start_time + quiz_duration
                pygame.time.set_timer(quiz_timer, 0)

        # >>> GEPREK spawn event handling
        if event.type == geprek_timer and game_state_active and not game_state_quiz:
            # choose y position around cat level or slightly above
            # y_pos is used as midbottom baseline for Geprek class
            y_candidates = [210, 300, 340, 380]  # candidate midbottom positions (above ground)
            y_pos = choice(y_candidates)
            # ensure it doesn't start below ground
            spawn_margin = 6
            if y_pos > (GROUND_Y - spawn_margin):
                y_pos = GROUND_Y - spawn_margin
            # phase randomize so wave differs
            phase = randint(0, 360) * math.pi / 180.0
            # speed same as kucing (8)
            g = Geprek(geprek_img, y_pos, speed=8, amplitude=22, wavelength=140, phase=phase)
            geprek_group.add(g)
            # schedule next spawn
            schedule_next_geprek()
        

        # --------------------
        # Menu interactions (mouse clicks / keyboard)
        # --------------------
        if not game_state_active and not game_state_quiz:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if button_play.is_clicked(pos):
                    print('mulai main (clicked Play)')
                    game_state_active = True
                    nyawa = 3
                    correctAns = 0
                    player.sprite.rect.midbottom = (100,400)
                    player.sprite.gravity = 0
                    start_time = int(pygame.time.get_ticks()/10)

                    next_tiang_time = start_time + tiang_interval
                    tiang_rect.x = 720
                    awan1_rect.x = 720
                    awan2_rect.x = 720
                    tiang_active = True
                    awan_active = True

                    pygame.time.set_timer(quiz_timer, 10000)
                    next_quiz_time_ms = pygame.time.get_ticks() + 10000

                    # >>> GEPREK: start geprek timer when game starts
                    schedule_next_geprek()

                elif button_leader.is_clicked(pos):
                    show_leaderboard = True
                elif button_exit.is_clicked(pos):
                    save_leaderboard_save(saved_best_answers, saved_best_score)
                    pygame.quit()
                    exit()

            if event.type == pygame.KEYDOWN and show_leaderboard:
                if event.key == pygame.K_ESCAPE:
                    show_leaderboard = False

        # handle leaderboard mode clicks
        if show_leaderboard and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            box_rect = pygame.Rect(100, 60, 520, 380)
            tab_w, tab_h = 150, 34
            tab_x = box_rect.x + 20
            tab_y = box_rect.y + 40
            tab_answers = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
            tab_scores = pygame.Rect(tab_x + tab_w + 12, tab_y, tab_w, tab_h)
            if tab_answers.collidepoint(event.pos):
                leaderboard_mode = 'answers'
            if tab_scores.collidepoint(event.pos):
                leaderboard_mode = 'scores'


    if game_state_active and not game_state_quiz:

                # --- SCROLL TANAH ---
                tanah_x1 -= 8
                tanah_x2 -= 8

                # reset posisi ketika keluar layar
                if tanah_x1 <= -tanah.get_width():
                    tanah_x1 = tanah.get_width()

                if tanah_x2 <= -tanah.get_width():
                    tanah_x2 = tanah.get_width()
    # -----------------------
    # Rendering / Game states
    # -----------------------
    if game_state_active:
        if game_state_quiz:
            quiz()
        else:
            screen.blit(scaled_game_bg,game_bg_rect)
            # --- DRAW SCROLLING GROUND ---
            screen.blit(tanah, (tanah_x1, tanah_rect.y))
            screen.blit(tanah, (tanah_x2, tanah_rect.y))

            # --- scroll tiang ---
            tiang_rect.x -= 4
            if tiang_rect.right <= 0:
                tiang_rect.left = 720


            if tiang_active and current_time >= next_tiang_time:
                tiang_active = True
            if tiang_active:
                tiang_rect.x -= 4
                screen.blit(scaled_tiang, tiang_rect)
                if tiang_rect.right < 0:
                    tiang_active = False
                    next_tiang_time = current_time + tiang_interval

            if awan_active and current_time >= next_awan_time:
                awan_active = True
            if awan_active:
                awan1_rect.x -= 1
                awan2_rect.x -= 1
                screen.blit(awan1, awan1_rect)
                screen.blit(awan2, awan2_rect)
                if awan1_rect.right < 0:
                    awan_active = False
                    next_awan_time = current_time + awan_interval

            player.draw(screen)
            player.update()

            obstacle_group.draw(screen)
            obstacle_group.update()

            # >>> GEPREK: update and draw geprek group
            geprek_group.update()
            geprek_group.draw(screen)

            # update shields
            shield_group.update()
            # draw shields (they are visual only)
            for s in shield_group.sprites():
                s.draw(screen)

            # collision: player touches geprek -> remove geprek and give +1 nyawa + shield
            collided = pygame.sprite.spritecollide(player.sprite, geprek_group, True)
            if collided:
                # increase nyawa by 1 (cap at 3)
                nyawa = min(3, nyawa + 1)
                # create shield visual: many small geprek orbiting player
                # if there's already a shield, refresh its duration instead of stacking
                if len(shield_group) == 0:
                    sh = Shield(player.sprite, geprek_img, count=8, radius=60, duration_ms=10000)
                    shield_group.add(sh)
                else:
                    for sh in shield_group:
                        sh.start_time = pygame.time.get_ticks()

            # >>> CHANGED: call health_counter which now checks shield and consumes it on hit
            health_counter()

            # display hearts based on nyawa
            if nyawa == 3:
                screen.blit(scaled_hati1, hati_rect1)
                screen.blit(scaled_hati2, hati_rect2)
                screen.blit(scaled_hati3, hati_rect3)
            elif nyawa == 2:
                screen.blit(scaled_hati1, hati_rect1)
                screen.blit(scaled_hati2, hati_rect2)
            elif nyawa == 1:
                screen.blit(scaled_hati1, hati_rect1)

            # display_score updates current_time used as score
            display_score()
            display_quiztimer()

            correctAns_surf = font2.render(f'Jawaban Benar: {correctAns}', False, 'White')
            correctAns_rect = correctAns_surf.get_rect(topleft=(10, 40))
            screen.blit(correctAns_surf, correctAns_rect)
        
    elif game_over:
         # game over
            draw_game_over()

    else:
        # MENU
        screen.blit(menu_bg,menu_bg_rect)
        button_play.draw(screen)
        button_leader.draw(screen)
        button_exit.draw(screen)

        pygame.time.set_timer(quiz_timer, 0)

        if show_leaderboard:
            # bigger leaderboard box to fit entries and hint
            box = pygame.Rect(100, 60, 520, 380)
            pygame.draw.rect(screen, (240,240,240), box)

            title = font1.render('Leaderboard', True, 'Black')
            screen.blit(title, (box.x + 180, box.y + 12))

            # DRAW toggle tabs (Answers / Scores)
            tab_w, tab_h = 150, 34
            tab_x = box.x + 20
            tab_y = box.y + 40
            tab_answers = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
            tab_scores = pygame.Rect(tab_x + tab_w + 12, tab_y, tab_w, tab_h)

            if leaderboard_mode == 'answers':
                pygame.draw.rect(screen, (70,120,180), tab_answers)
                pygame.draw.rect(screen, (180,180,180), tab_scores)
            else:
                pygame.draw.rect(screen, (180,180,180), tab_answers)
                pygame.draw.rect(screen, (70,120,180), tab_scores)

            a_text = font2.render('By Answers', True, 'White')
            s_text = font2.render('By Scores', True, 'White')
            screen.blit(a_text, a_text.get_rect(center=tab_answers.center))
            screen.blit(s_text, s_text.get_rect(center=tab_scores.center))

            # Build merged list depending on mode
            if leaderboard_mode == 'answers':
                # copy fixed answers list then append player's saved best
                merged = leaderboard_answers.copy()
                merged.append(("You", saved_best_answers))
                merged_sorted = sorted(merged, key=lambda e: e[1], reverse=True)
                display_list = merged_sorted[:5]
                label = 'Correct Answers (best)'
            else:
                # use saved best score for "You", and other fixed players
                merged_scores = [(name, scoreboard) for name, scoreboard in leaderboard_scores.items()]
                merged_scores.append(("You", saved_best_score))
                merged_sorted = sorted(merged_scores, key=lambda e: e[1], reverse=True)
                display_list = merged_sorted[:5]
                label = 'Score (best)'

            label_surf = font2.render(label, True, 'Black')
            screen.blit(label_surf, (box.x + 36, box.y + 84))

            y = box.y + 120
            rank = 1
            you_in_top5 = False
            for name, val in display_list:
                display_name = name
                if name == "You":
                    display_name = "You (You)"
                    you_in_top5 = True
                line = font2.render(f'{rank}. {display_name}: {val}', True, 'Black')
                screen.blit(line, (box.x + 36, y))
                y += 36
                rank += 1

            if not you_in_top5:
                player_rank = None
                player_val = None
                if leaderboard_mode == 'answers':
                    for idx, e in enumerate(merged_sorted, start=1):
                        if e[0] == "You" and e[1] == saved_best_answers:
                            player_rank = idx
                            player_val = e[1]
                            break
                else:
                    for idx, e in enumerate(merged_sorted, start=1):
                        if e[0] == "You" and e[1] == saved_best_score:
                            player_rank = idx
                            player_val = e[1]
                            break

                if player_rank is None:
                    player_rank = len(merged_sorted)
                    player_val = saved_best_answers if leaderboard_mode == 'answers' else saved_best_score

                y += 6
                your_line = font2.render(f'Your rank: {player_rank}    You: {player_val}', True, 'Black')
                screen.blit(your_line, (box.x + 36, y))
                y += 36

            # hint moved lower in box (if not fit, box enlarged above)
            hint = font2.render('Press Esc to go back', True, 'Black')
            hint_pos = (box.x + 36, box.y + box.height - 28)
            screen.blit(hint, hint_pos)

    pygame.display.update()
    clock.tick(60)
