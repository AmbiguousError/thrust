import pygame
import math
import sys
import random
import os # For path joining

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 128, 0); YELLOW = (255, 255, 0); CYAN = (0, 255, 255)
ORANGE = (255, 165, 0); GRAY = (128, 128, 128); SMOKE_COLOR_1 = (180, 180, 180)
SMOKE_COLOR_2 = (150, 150, 150); SMOKE_COLOR_3 = (120, 120, 120)
EXPLOSION_COLOR_1 = (255, 0, 0); EXPLOSION_COLOR_2 = (255, 165, 0)
EXPLOSION_COLOR_3 = (255, 255, 0); EXPLOSION_COLOR_4 = (255, 255, 255)

# Player ship properties
PLAYER_COLOR = WHITE
THRUST_FORCE = 0.33       # <-- Increased standard thrust further
BOOST_FORCE = 0.66        # <-- Increased boost thrust further
BOOST_TAKEOFF_KICK = 5.0
ROTATION_SPEED = 4
GRAVITY = 0.02
FRICTION = 0.995
MAX_SPEED = 12            # <-- Increased max speed significantly
MAX_FUEL = 100.0
FUEL_CONSUMPTION = 0.1
BOOST_FUEL_CONSUMPTION = 0.3
FUEL_RECHARGE_RATE = 0.5
LANDING_ANGLE_TOLERANCE = 15
LANDING_SPEED_TOLERANCE = 1.5
GEAR_DEPLOY_ALTITUDE = 120
GEAR_DEPLOY_ANGLE_TOLERANCE = 45
GEAR_LINE_THICKNESS = 2

# Laser properties (unchanged)
LASER_SPEED = 8; LASER_COOLDOWN = 200

# Beacon properties (unchanged)
NUM_BEACONS_BASE = 5; BEACON_RADIUS = 10; BEACON_SCORE = 100

# Obstacle properties (unchanged)
OBSTACLE_RADIUS_MIN = 15; OBSTACLE_RADIUS_MAX = 30; NUM_OBSTACLES_PER_LEVEL = 2

# Ground properties (unchanged)
GROUND_HEIGHT = 50

# Particle properties (unchanged)
SMOKE_PARTICLE_COUNT = 25; SMOKE_LIFESPAN_MIN = 0.4; SMOKE_LIFESPAN_MAX = 0.9
SMOKE_SPEED_MIN = 0.5; SMOKE_SPEED_MAX = 2.5
EXPLOSION_PARTICLE_COUNT = 50; EXPLOSION_LIFESPAN_MIN = 0.5; EXPLOSION_LIFESPAN_MAX = 1.2
EXPLOSION_SPEED_MIN = 1.0; EXPLOSION_SPEED_MAX = 4.0
DEATH_ANIM_DURATION = 1000

# Scoring & Lives (unchanged)
INITIAL_SHIPS = 3; EXTRA_LIFE_SCORE = 1000; LEVEL_BONUS = 500

# High Score Handling
HIGHSCORE_FILE = "pythrust_highscores.txt"
NUM_HIGH_SCORES = 3

# Game states
MENU = "MENU"; PLAYING = "PLAYING"; GAME_OVER = "GAME_OVER"
LEVEL_COMPLETE = "LEVEL_COMPLETE"; PLAYER_EXPLODING = "PLAYER_EXPLODING"

# --- Helper Functions ---
# (draw_text, draw_gauge unchanged)
def draw_text(surface, text, size, x, y, color=WHITE, align="midtop"):
    font = pygame.font.Font(pygame.font.match_font('arial'), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "midtop": text_rect.midtop = (x, y)
    elif align == "topleft": text_rect.topleft = (x, y)
    elif align == "topright": text_rect.topright = (x, y)
    surface.blit(text_surface, text_rect)

def draw_gauge(surface, x, y, width, height, current_value, max_value, color, label):
    if current_value < 0: current_value = 0
    fill_pct = current_value / max_value
    fill_width = int(width * fill_pct)
    outline_rect = pygame.Rect(x, y, width, height)
    fill_rect = pygame.Rect(x, y, fill_width, height)
    pygame.draw.rect(surface, color, fill_rect)
    pygame.draw.rect(surface, WHITE, outline_rect, 2)
    draw_text(surface, f"{label}: {current_value:.0f}", height, x + width + 5, y, WHITE, align="topleft")

# --- High Score Functions ---
# (High score functions unchanged)
def load_high_scores():
    scores = []
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                for line in f:
                    try: scores.append(int(line.strip()))
                    except ValueError: print(f"Warning: Skipping invalid score line: {line.strip()}")
        except IOError as e: print(f"Error loading high scores: {e}")
    scores.sort(reverse=True); return scores[:NUM_HIGH_SCORES]

def save_high_scores(scores):
    scores.sort(reverse=True)
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            for score in scores[:NUM_HIGH_SCORES]: f.write(f"{score}\n")
    except IOError as e: print(f"Error saving high scores: {e}")

def add_high_score(new_score, scores):
    if new_score <= 0: return scores
    scores.append(new_score); scores.sort(reverse=True)
    updated_scores = scores[:NUM_HIGH_SCORES]; save_high_scores(updated_scores)
    return updated_scores

# --- Particle Class ---
# (Particle class unchanged)
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, vel, size, color, lifespan):
        super().__init__(); self.pos = pygame.Vector2(pos); self.vel = pygame.Vector2(vel)
        self.size = int(size); self.color = color; self.lifespan = lifespan
        self.spawn_time = pygame.time.get_ticks()
        self.image = pygame.Surface([max(1, self.size), max(1, self.size)], pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.size // 2, self.size // 2), self.size // 2)
        self.rect = self.image.get_rect(center=self.pos)
    def update(self, dt):
        self.pos += self.vel; self.rect.center = self.pos
        elapsed_time = (pygame.time.get_ticks() - self.spawn_time) / 1000.0
        if elapsed_time >= self.lifespan: self.kill()
        else: self.image.set_alpha(int(max(0, 255 * (1 - (elapsed_time / self.lifespan)))))

# --- Smoke/Explosion Generation Functions ---
# (create_smoke, create_explosion unchanged)
def create_smoke(pos, num_particles, all_sprites_group):
    for _ in range(num_particles):
        angle = random.uniform(0, math.pi * 2); speed = random.uniform(SMOKE_SPEED_MIN, SMOKE_SPEED_MAX)
        p_vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        p_vel.y += random.uniform(-0.5, -1.5); p_size = random.randint(2, 6)
        p_color = random.choice([SMOKE_COLOR_1, SMOKE_COLOR_2, SMOKE_COLOR_3])
        p_lifespan = random.uniform(SMOKE_LIFESPAN_MIN, SMOKE_LIFESPAN_MAX)
        p_pos = pos + pygame.Vector2(random.randint(-5, 5), random.randint(-5, 5))
        particle = Particle(p_pos, p_vel, p_size, p_color, p_lifespan); all_sprites_group.add(particle)

def create_explosion(pos, num_particles, all_sprites_group):
    for _ in range(num_particles):
        angle = random.uniform(0, math.pi * 2); speed = random.uniform(EXPLOSION_SPEED_MIN, EXPLOSION_SPEED_MAX)
        p_vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        p_size = random.randint(3, 7)
        p_color = random.choice([EXPLOSION_COLOR_1, EXPLOSION_COLOR_2, EXPLOSION_COLOR_3, EXPLOSION_COLOR_4])
        p_lifespan = random.uniform(EXPLOSION_LIFESPAN_MIN, EXPLOSION_LIFESPAN_MAX)
        p_pos = pos + pygame.Vector2(random.randint(-8, 8), random.randint(-8, 8))
        particle = Particle(p_pos, p_vel, p_size, p_color, p_lifespan); all_sprites_group.add(particle)


# --- Laser Class ---
# (Laser class unchanged)
class Laser(pygame.sprite.Sprite):
    def __init__(self, pos, angle):
        super().__init__(); self.image = pygame.Surface([6, 2], pygame.SRCALPHA); self.image.fill(CYAN)
        self.image = pygame.transform.rotate(self.image, -angle); self.rect = self.image.get_rect(center=pos)
        rad_angle = math.radians(angle); self.vel = pygame.Vector2(math.cos(rad_angle), math.sin(rad_angle)) * LASER_SPEED
        self.pos = pygame.Vector2(pos)
    def update(self, dt):
        self.pos += self.vel; self.rect.center = self.pos
        if not pygame.display.get_surface().get_rect().colliderect(self.rect): self.kill()

# --- Beacon Class ---
# (Beacon class unchanged)
class Beacon(pygame.sprite.Sprite):
    def __init__(self, center_pos):
        super().__init__(); self.image = pygame.Surface([BEACON_RADIUS * 2, BEACON_RADIUS * 2], pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (BEACON_RADIUS, BEACON_RADIUS), BEACON_RADIUS)
        self.rect = self.image.get_rect(center=center_pos); self.pos = pygame.Vector2(center_pos); self.radius = BEACON_RADIUS
    def update(self, dt): pass

# --- Obstacle Class ---
# (Obstacle class unchanged)
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, center_pos, radius):
        super().__init__(); self.radius = radius
        self.image = pygame.Surface([self.radius * 2, self.radius * 2], pygame.SRCALPHA)
        pygame.draw.circle(self.image, GRAY, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=center_pos); self.pos = pygame.Vector2(center_pos); self.mask = pygame.mask.from_surface(self.image)
    def update(self, dt): pass


# --- Player Ship Class ---
# (Player class uses new constants but logic is unchanged)
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        raw_base_image = pygame.Surface([20, 15], pygame.SRCALPHA); raw_base_image.fill((0,0,0,0))
        pygame.draw.polygon(raw_base_image, PLAYER_COLOR, [(20, 7), (0, 0), (0, 14)])
        self.base_image_no_gear = raw_base_image
        self.base_image_with_gear = self.base_image_no_gear.copy()
        gear_color = PLAYER_COLOR
        pygame.draw.line(self.base_image_with_gear, gear_color, (2, 14), (2, 19), GEAR_LINE_THICKNESS)
        pygame.draw.line(self.base_image_with_gear, gear_color, (17, 14), (17, 19), GEAR_LINE_THICKNESS)
        pygame.draw.line(self.base_image_with_gear, gear_color, (0, 19), (4, 19), GEAR_LINE_THICKNESS)
        pygame.draw.line(self.base_image_with_gear, gear_color, (15, 19), (19, 19), GEAR_LINE_THICKNESS)
        self.image = self.base_image_no_gear
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = pygame.Vector2(self.rect.center); self.vel = pygame.Vector2(0, 0)
        self.angle = 270; self.thrusting = False; self.boosting = False
        self.landed = False; self.crashed = False; self.fuel = MAX_FUEL
        self.last_shot_time = 0; self.landing_gear_deployed = False
        self.just_landed = False; self.just_took_off = False
        self._update_rotation_visuals()
    def reset(self):
        print("Player Resetting..."); self.pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        self.vel = pygame.Vector2(0, 0); self.angle = 270; self.fuel = MAX_FUEL
        self.crashed = False; self.landed = False; self.thrusting = False; self.boosting = False
        self.landing_gear_deployed = False; self._update_rotation_visuals()
    def rotate(self, direction):
        if self.landed: return
        self.angle = (self.angle + direction * ROTATION_SPEED) % 360; self._update_rotation_visuals()
    def _update_rotation_visuals(self):
        center = self.rect.center
        current_base = self.base_image_with_gear if self.landing_gear_deployed else self.base_image_no_gear
        self.image = pygame.transform.rotate(current_base, -self.angle)
        self.rect = self.image.get_rect(center=center); self.mask = pygame.mask.from_surface(self.image)
    def shoot(self, all_sprites, lasers_group):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > LASER_COOLDOWN:
            self.last_shot_time = now; rad_angle = math.radians(self.angle)
            base_nose_offset = pygame.Vector2(self.base_image_no_gear.get_width() / 2 + 5, 0)
            rotated_offset = base_nose_offset.rotate(self.angle); laser_pos = self.pos + rotated_offset
            new_laser = Laser(laser_pos, self.angle); all_sprites.add(new_laser); lasers_group.add(new_laser)
    def update(self, dt):
        self.just_landed = False; self.just_took_off = False
        ground_level = SCREEN_HEIGHT - GROUND_HEIGHT
        altitude_above_ground = ground_level - (self.pos.y + self.rect.height / 2)
        gear_angle_diff = abs(((self.angle - 270 + 180) % 360) - 180)
        should_deploy_gear = (altitude_above_ground <= GEAR_DEPLOY_ALTITUDE and
                              gear_angle_diff <= GEAR_DEPLOY_ANGLE_TOLERANCE and not self.landed)
        if should_deploy_gear != self.landing_gear_deployed:
            self.landing_gear_deployed = should_deploy_gear; self._update_rotation_visuals()
        keys = pygame.key.get_pressed(); thrust_input = keys[pygame.K_UP] or keys[pygame.K_w]
        boost_input = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self.thrusting = False; self.boosting = False; apply_thrust_acc = pygame.Vector2(0, 0)
        if thrust_input and self.fuel > 0:
            if boost_input and self.fuel >= BOOST_FUEL_CONSUMPTION:
                self.boosting = True; self.thrusting = True; self.fuel -= BOOST_FUEL_CONSUMPTION
                if self.landed:
                    self.vel.y -= BOOST_TAKEOFF_KICK; self.landed = False; self.just_took_off = True
                    if self.landing_gear_deployed: self.landing_gear_deployed = False; self._update_rotation_visuals()
                else:
                    rad_angle = math.radians(self.angle)
                    apply_thrust_acc = pygame.Vector2(math.cos(rad_angle), math.sin(rad_angle)) * BOOST_FORCE # Uses new constant
            elif not boost_input and not self.landed and self.fuel >= FUEL_CONSUMPTION:
                self.thrusting = True; self.fuel -= FUEL_CONSUMPTION
                rad_angle = math.radians(self.angle)
                apply_thrust_acc = pygame.Vector2(math.cos(rad_angle), math.sin(rad_angle)) * THRUST_FORCE # Uses new constant
        self.vel += apply_thrust_acc
        if not self.landed: self.vel.y += GRAVITY
        if not self.landed: self.vel *= FRICTION
        speed = self.vel.length();
        if speed > MAX_SPEED: self.vel.scale_to_length(MAX_SPEED) # Uses new constant
        if not self.landed: self.pos += self.vel
        on_ground = self.pos.y + self.rect.height / 2 >= ground_level
        if self.pos.x > SCREEN_WIDTH + self.rect.width / 2: self.pos.x = -self.rect.width / 2
        elif self.pos.x < -self.rect.width / 2: self.pos.x = SCREEN_WIDTH + self.rect.width / 2
        if self.pos.y < self.rect.height / 2: self.pos.y = self.rect.height / 2;
        if self.vel.y < 0: self.vel.y = 0
        if on_ground:
            if not self.landed:
                landing_angle_diff = abs(((self.angle - 270 + 180) % 360) - 180)
                is_vertical = landing_angle_diff <= LANDING_ANGLE_TOLERANCE
                is_slow_enough = self.vel.length() <= LANDING_SPEED_TOLERANCE
                if is_vertical and is_slow_enough:
                    self.landed = True; self.just_landed = True; self.pos.y = ground_level - self.rect.height / 2
                    self.vel = pygame.Vector2(0, 0); self.angle = 270
                    if not self.landing_gear_deployed: self.landing_gear_deployed = True
                    self._update_rotation_visuals()
                else: self.crashed = True; self.thrusting = False; self.boosting = False
            if self.landed: self.fuel += FUEL_RECHARGE_RATE;
            if self.fuel > MAX_FUEL: self.fuel = MAX_FUEL
        if not self.landed and not self.crashed: self.rect.center = self.pos

# --- Menu Function ---
# (show_menu unchanged)
def show_menu(screen, clock, font_small, font_large, high_scores, last_score):
    menu_running = True
    while menu_running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return 'QUIT'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return 'QUIT'
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER: return 'START'
        screen.fill(BLACK)
        draw_text(screen, "PyThrust II", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 8, YELLOW)
        inst_y = SCREEN_HEIGHT / 3.5; inst_spacing = 25
        draw_text(screen, "Instructions:", 22, SCREEN_WIDTH / 2, inst_y, WHITE)
        draw_text(screen, "Arrows / WASD : Rotate & Thrust", 18, SCREEN_WIDTH / 2, inst_y + inst_spacing * 1.5, WHITE)
        draw_text(screen, "Spacebar : Fire Laser", 18, SCREEN_WIDTH / 2, inst_y + inst_spacing * 2.5, WHITE)
        draw_text(screen, "Shift + Thrust : Boost", 18, SCREEN_WIDTH / 2, inst_y + inst_spacing * 3.5, WHITE)
        draw_text(screen, "Esc : Quit Game", 18, SCREEN_WIDTH / 2, inst_y + inst_spacing * 4.5, WHITE)
        hs_y = SCREEN_HEIGHT * 0.65
        draw_text(screen, "High Scores:", 22, SCREEN_WIDTH / 2, hs_y, WHITE)
        if not high_scores: draw_text(screen, "No scores yet!", 18, SCREEN_WIDTH / 2, hs_y + 30, GRAY)
        else:
            for i, score_val in enumerate(high_scores):
                score_text = f"{i+1}. {score_val}"; color = YELLOW if score_val == last_score and last_score > 0 else WHITE
                draw_text(screen, score_text, 18, SCREEN_WIDTH / 2, hs_y + 30 + i * 25, color)
        draw_text(screen, "Press Enter to Start", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.9, ORANGE)
        pygame.display.flip()
    return 'QUIT'


# --- Game Loop Function ---
# (game_loop unchanged)
def game_loop(screen, clock, font_small, font_large, ship_icon_surf, start_level=1, initial_score=0, start_ships=INITIAL_SHIPS):
    level = start_level; score = initial_score; ships = start_ships
    extra_life_threshold = (initial_score // EXTRA_LIFE_SCORE + 1) * EXTRA_LIFE_SCORE
    pygame.display.set_caption(f"PyThrust - Level {level}")
    player = Player(); all_sprites = pygame.sprite.Group(); lasers = pygame.sprite.Group()
    beacons = pygame.sprite.Group(); obstacles = pygame.sprite.Group(); all_sprites.add(player)
    num_beacons_this_level = NUM_BEACONS_BASE + level - 1; num_obstacles_this_level = 0
    if level >= 2: num_obstacles_this_level = (level - 1) * NUM_OBSTACLES_PER_LEVEL
    spawn_avoid_group = pygame.sprite.Group(player); beacon_spawn_attempts = 0
    while len(beacons) < num_beacons_this_level and beacon_spawn_attempts < 200:
        bx = random.randrange(BEACON_RADIUS, SCREEN_WIDTH - BEACON_RADIUS); by = random.randrange(BEACON_RADIUS, SCREEN_HEIGHT - GROUND_HEIGHT - BEACON_RADIUS * 4)
        new_beacon = Beacon((bx, by));
        if not pygame.sprite.spritecollide(new_beacon, spawn_avoid_group, False):
             beacons.add(new_beacon); all_sprites.add(new_beacon); spawn_avoid_group.add(new_beacon)
        beacon_spawn_attempts += 1
    if len(beacons) < num_beacons_this_level: print(f"Warning: Could only spawn {len(beacons)} beacons.")
    obstacle_spawn_attempts = 0
    while len(obstacles) < num_obstacles_this_level and obstacle_spawn_attempts < 200:
         orad = random.randint(OBSTACLE_RADIUS_MIN, OBSTACLE_RADIUS_MAX)
         ox = random.randrange(orad, SCREEN_WIDTH - orad); oy = random.randrange(orad, SCREEN_HEIGHT - GROUND_HEIGHT - orad * 2)
         new_obstacle = Obstacle((ox, oy), orad)
         if not pygame.sprite.spritecollide(new_obstacle, spawn_avoid_group, False, pygame.sprite.collide_circle):
              obstacles.add(new_obstacle); all_sprites.add(new_obstacle); spawn_avoid_group.add(new_obstacle)
         obstacle_spawn_attempts += 1
    if len(obstacles) < num_obstacles_this_level: print(f"Warning: Could only spawn {len(obstacles)} obstacles.")
    game_state = PLAYING; death_anim_start_time = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return score
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return score
                if event.key == pygame.K_SPACE and game_state == PLAYING and player.groups() and not player.landed: player.shoot(all_sprites, lasers)
        if game_state == PLAYING and player.groups():
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: player.rotate(-1)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player.rotate(1)
        if game_state == PLAYING:
            if not player.crashed: all_sprites.update(dt)
            else:
                 if player.groups():
                     for sprite in all_sprites:
                         if sprite != player: sprite.update(dt)
                 else: all_sprites.update(dt)
            if player.groups():
                if player.just_landed: create_smoke((player.rect.centerx, player.rect.bottom), SMOKE_PARTICLE_COUNT, all_sprites)
                if player.just_took_off: create_smoke((player.rect.centerx, player.rect.bottom), SMOKE_PARTICLE_COUNT, all_sprites)
            if player.groups():
                beacon_hits = pygame.sprite.groupcollide(lasers, beacons, True, True)
                if beacon_hits:
                    score += len(beacon_hits) * BEACON_SCORE; print(f"Score: {score}")
                    if score >= extra_life_threshold: ships += 1; extra_life_threshold += EXTRA_LIFE_SCORE; print(f"Extra life! Ships: {ships}, Next at: {extra_life_threshold}")
                obstacle_hits = pygame.sprite.spritecollide(player, obstacles, False, pygame.sprite.collide_mask)
                if obstacle_hits and not player.crashed: player.crashed = True; print("CRASH! Hit obstacle.")
            player_is_alive = player.groups() is not None and len(player.groups()) > 0
            player_died_condition = False
            if player_is_alive: player_died_condition = player.crashed or (player.fuel <= 0 and not player.landed)
            if player_died_condition:
                if player.crashed:
                    print("Player crashed, starting explosion."); create_explosion(player.rect.center, EXPLOSION_PARTICLE_COUNT, all_sprites)
                    player.kill(); game_state = PLAYER_EXPLODING; death_anim_start_time = pygame.time.get_ticks()
                else:
                    print("Player out of fuel mid-air.")
                    if ships <= 1: ships = 0; game_state = GAME_OVER; print("GAME OVER - Final ship lost (fuel).")
                    else: ships -= 1; print(f"Ship lost! Ships remaining: {ships}"); player.reset()
            elif not beacons and game_state == PLAYING: game_state = LEVEL_COMPLETE; print("Level Complete!")
        elif game_state == PLAYER_EXPLODING:
            all_sprites.update(dt)
            if pygame.time.get_ticks() - death_anim_start_time > DEATH_ANIM_DURATION:
                print("Explosion finished.")
                if ships <= 1: ships = 0; game_state = GAME_OVER; print("GAME OVER - Final ship lost (crash).")
                else:
                    ships -= 1; print(f"Ship lost! Ships remaining: {ships}")
                    player = Player(); all_sprites.add(player); game_state = PLAYING
        screen.fill(BLACK)
        ground_rect = pygame.Rect(0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT); pygame.draw.rect(screen, GREEN, ground_rect)
        all_sprites.draw(screen)
        player_is_alive = player.groups() is not None and len(player.groups()) > 0
        if player_is_alive and (player.thrusting or player.boosting) and not player.crashed:
            flame_color = RED; rad_angle = math.radians(player.angle); flame_offset_dist = 12
            flame_pos_x = player.pos.x - flame_offset_dist * math.cos(rad_angle); flame_pos_y = player.pos.y - flame_offset_dist * math.sin(rad_angle)
            pygame.draw.circle(screen, flame_color, (int(flame_pos_x), int(flame_pos_y)), 4)
        current_fuel = player.fuel if player_is_alive else 0; current_angle = player.angle if player_is_alive else 0; is_landed = player.landed if player_is_alive else False
        draw_gauge(screen, 10, 10, 100, 15, current_fuel, MAX_FUEL, ORANGE, "Fuel")
        angle_text = f"Angle: {current_angle:.0f}"; draw_text(screen, angle_text, 18, SCREEN_WIDTH / 2, 10)
        status_text = "Landed" if is_landed else ""; draw_text(screen, status_text, 18, SCREEN_WIDTH / 2, 30, YELLOW if is_landed else RED)
        draw_text(screen, f"Beacons: {len(beacons)}", 18, SCREEN_WIDTH - 10, 10, align="topright")
        draw_text(screen, f"Score: {score}", 18, SCREEN_WIDTH - 10, 30, align="topright")
        draw_text(screen, f"Level: {level}", 18, SCREEN_WIDTH - 10, 50, align="topright")
        ship_icon_rect = ship_icon_surf.get_rect(topright=(SCREEN_WIDTH - 35, 70)); screen.blit(ship_icon_surf, ship_icon_rect)
        draw_text(screen, f"x {ships}", 18, SCREEN_WIDTH - 10, 70, align="topright")
        if game_state == GAME_OVER:
             overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0,0))
             draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED)
             draw_text(screen, f"Final Score: {score}", 32, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
             pygame.display.flip(); pygame.time.wait(2500)
             return score
        elif game_state == LEVEL_COMPLETE:
             overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0,0))
             draw_text(screen, "LEVEL COMPLETE!", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, YELLOW)
             final_level_score = score + LEVEL_BONUS
             draw_text(screen, f"Level {level} Bonus: +{LEVEL_BONUS}", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
             pygame.display.flip(); pygame.time.wait(2000)
             if final_level_score >= extra_life_threshold: ships += 1; print(f"Extra life from bonus! Ships: {ships}")
             return game_loop(screen, clock, font_small, font_large, ship_icon_surf, start_level=level + 1, initial_score=final_level_score, start_ships=ships)
        pygame.display.flip()
    print("Game loop exited unexpectedly?"); return score

# --- Main Execution Function ---
def main():
    """Main function to handle menu and game execution."""
    pygame.init(); pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PyThrust II"); clock = pygame.time.Clock()
    font_small = pygame.font.Font(pygame.font.match_font('arial'), 18)
    font_large = pygame.font.Font(pygame.font.match_font('arial'), 48)
    ship_icon_surf = pygame.Surface([10, 8], pygame.SRCALPHA)
    pygame.draw.polygon(ship_icon_surf, WHITE, [(10, 4), (0, 0), (0, 7)])
    high_scores = load_high_scores(); last_score = -1
    running = True
    while running:
        action = show_menu(screen, clock, font_small, font_large, high_scores, last_score)
        if action == 'QUIT': running = False
        elif action == 'START':
            final_score = game_loop(screen, clock, font_small, font_large, ship_icon_surf,
                                     start_level=1, initial_score=0, start_ships=INITIAL_SHIPS)
            last_score = final_score; print(f"Game finished with score: {last_score}")
            high_scores = add_high_score(last_score, high_scores); print(f"High scores: {high_scores}")
    pygame.quit(); sys.exit()

# --- Start Game ---
if __name__ == '__main__':
    main()
