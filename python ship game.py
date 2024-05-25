import pygame
import random

pygame.init()

# Экран
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starship Game")

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Параметры игрока
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 50
PLAYER_VEL = 5
BULLET_VEL = 7
SPECIAL_BULLET_VEL = 10
MAX_BULLETS = 5
PLAYER_HP = 20 
SPECIAL_BULLET_COOLDOWN = 10000  

# Параметры врагов
ENEMY_WIDTH, ENEMY_HEIGHT = 70, 70  
ENEMY_BULLET_VEL = 5
ENEMY_SHOOT_DELAY = 3000 

# Параметры босса
BOSS_WIDTH, BOSS_HEIGHT = 100, 100
BOSS_HP = 100
BOSS_VEL = 2
BOSS_BULLET_VEL = 7
BOSS_SHOOT_DELAY = 1500  
BOSS_RESPAWN_TIME = 7000  

# Параметры щита
SHIELD_DURATION = 5000  

# Загрузка картинок
try:
    PLAYER_IMG = pygame.image.load("player.png")
    ENEMY_SCOUT_IMG = pygame.image.load("enemy_scout.png")
    ENEMY_BOMBER_IMG = pygame.image.load("enemy_bomber.png")
    BOSS_IMG = pygame.image.load("enemy_tank.png")
    ASTEROID_IMG = pygame.image.load("asteroid.png")
    SHIELD_IMG = pygame.image.load("shield.png")
    BACKGROUND_IMG = pygame.image.load("space.png")

    # Масштабирование картинок
    PLAYER_IMG = pygame.transform.scale(PLAYER_IMG, (PLAYER_WIDTH, PLAYER_HEIGHT))
    ENEMY_SCOUT_IMG = pygame.transform.scale(ENEMY_SCOUT_IMG, (ENEMY_WIDTH, ENEMY_HEIGHT))
    ENEMY_BOMBER_IMG = pygame.transform.scale(ENEMY_BOMBER_IMG, (ENEMY_WIDTH, ENEMY_HEIGHT))
    BOSS_IMG = pygame.transform.scale(BOSS_IMG, (BOSS_WIDTH, BOSS_HEIGHT))
    ASTEROID_IMG = pygame.transform.scale(ASTEROID_IMG, (ENEMY_WIDTH, ENEMY_HEIGHT))
    SHIELD_IMG = pygame.transform.scale(SHIELD_IMG, (30, 30))
    BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"Error loading images: {e}")
    pygame.quit()
    exit()

# Шрифты
FONT = pygame.font.SysFont('comicsans', 24)
SMALL_FONT = pygame.font.SysFont('comicsans', 16)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = PLAYER_IMG
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        self.hp = PLAYER_HP
        self.shielded = False
        self.shield_end_time = 0
        self.last_special_shot = pygame.time.get_ticks()

    def move(self, keys_pressed):
        if keys_pressed[pygame.K_a]:  # Налево
            self.rect.x -= PLAYER_VEL
            if self.rect.x < 0:
                self.rect.x = WIDTH - PLAYER_WIDTH
        if keys_pressed[pygame.K_d]:  # Направо
            self.rect.x += PLAYER_VEL
            if self.rect.x + PLAYER_WIDTH > WIDTH:
                self.rect.x = 0
        if keys_pressed[pygame.K_w] and self.rect.y - PLAYER_VEL > 0:  # Вверх
            self.rect.y -= PLAYER_VEL
        if keys_pressed[pygame.K_s] and self.rect.y + PLAYER_VEL + PLAYER_HEIGHT < HEIGHT:  # Вниз
            self.rect.y += PLAYER_VEL

    def can_shoot_special(self):
        now = pygame.time.get_ticks()
        return now - self.last_special_shot >= SPECIAL_BULLET_COOLDOWN

    def shoot_special(self):
        self.last_special_shot = pygame.time.get_ticks()
        return SpecialBullet(self.rect.centerx, self.rect.top)

    def activate_shield(self):
        self.shielded = True
        self.shield_end_time = pygame.time.get_ticks() + SHIELD_DURATION

    def update(self):
        if self.shielded and pygame.time.get_ticks() > self.shield_end_time:
            self.shielded = False

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_enemy=False, boss_bullet=False):
        super().__init__()
        self.image = pygame.Surface((5, 10) if not boss_bullet else (15, 30))  
        self.image.fill(RED if is_enemy else WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.is_enemy = is_enemy
        self.boss_bullet = boss_bullet

    def update(self):
        self.rect.y += BOSS_BULLET_VEL if self.boss_bullet else (ENEMY_BULLET_VEL if self.is_enemy else -BULLET_VEL)
        if self.rect.y < 0 or self.rect.y > HEIGHT:
            self.kill()

class SpecialBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 40))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, enemies_group,bosses):  
        global score
        self.rect.y -= SPECIAL_BULLET_VEL
        if self.rect.y < 0:
            self.kill()

        # Проверка попадения во врагов
        hits = pygame.sprite.spritecollide(self, enemies_group, False)  
        for enemy in hits:
            enemy.hp -= 40
            if enemy.hp <= 0:
                enemy.kill()
                score += 1
        
        # Проверка попадения в босса
        boss_hits = pygame.sprite.spritecollide(self, bosses, False)
        for boss in boss_hits:
            boss.hp -= 40
            if boss.hp <= 0:
                boss.kill()
                score += 10
                boss_spawned = False  # Флаг босса
                boss_respawn_time = pygame.time.get_ticks() + BOSS_RESPAWN_TIME  # Время респауна босса
            self.kill()
      
            

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, hp, damage, vel, image, can_shoot=True):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = hp
        self.damage = damage
        self.vel = vel
        self.last_shot = pygame.time.get_ticks()
        self.can_shoot = can_shoot

    def update(self):
        self.rect.y += self.vel
        if self.rect.y > HEIGHT:
            self.kill()

    def shoot(self):
        if self.can_shoot:
            now = pygame.time.get_ticks()
            if now - self.last_shot > ENEMY_SHOOT_DELAY:
                self.last_shot = now
                return Bullet(self.rect.centerx, self.rect.bottom, is_enemy=True)
        return None

class Asteroid(Enemy):
        def __init__(self, x, y):
            super().__init__(x, y, 1, 10, 4, ASTEROID_IMG, can_shoot=False)

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = BOSS_IMG
        self.rect = self.image.get_rect(center=(WIDTH // 2, 50))
        self.hp = BOSS_HP
        self.vel = BOSS_VEL
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.vel
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.vel = -self.vel

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > BOSS_SHOOT_DELAY:
            self.last_shot = now
            return Bullet(self.rect.centerx, self.rect.bottom, is_enemy=True, boss_bullet=True)
        return None

class Shield(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = SHIELD_IMG
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y += 2
        if self.rect.y > HEIGHT:
            self.kill()

def draw_health_bar(surface, x, y, hp, max_hp):
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (hp / max_hp) * BAR_LENGTH
    border_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surface, GREEN, fill_rect)
    pygame.draw.rect(surface, WHITE, border_rect, 2)

def draw_special_cooldown_bar(surface, x, y, player):
    now = pygame.time.get_ticks()
    cooldown_time = now - player.last_special_shot
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (cooldown_time / SPECIAL_BULLET_COOLDOWN) * BAR_LENGTH
    fill = min(fill, BAR_LENGTH)  
    border_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surface, YELLOW, fill_rect)
    pygame.draw.rect(surface, WHITE, border_rect, 2)

def draw_score(surface, score):
    score_text = FONT.render(f"Score: {score}", True, WHITE)
    surface.blit(score_text, (WIDTH - score_text.get_width() - 10, 10))

def draw_controls(surface):
    controls_text = [
        "Move: WASD",
        "Shoot: Space",
        "Special: K"
    ]
    y_offset = HEIGHT - 80
    for line in controls_text:
        text_surface = SMALL_FONT.render(line, True, WHITE)
        surface.blit(text_surface, (WIDTH - text_surface.get_width() - 10, y_offset))
        y_offset += 20

def draw_shield_effect(surface, player):
    if player.shielded:
        radius = player.rect.width // 2 + 5
        center = player.rect.center
        pygame.draw.circle(surface, YELLOW, center, radius, width=2)
        pygame.draw.circle(surface, YELLOW, center, radius + 2, width=1)
        pygame.draw.circle(surface, YELLOW, center, radius + 4, width=1)

def show_game_over(surface):
    game_over_text = FONT.render("Type R to play again", True, WHITE)
    surface.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - game_over_text.get_height() // 2))

def main():
    run = True
    clock = pygame.time.Clock()

    player = Player()
    player_group = pygame.sprite.Group(player)
    bullets = pygame.sprite.Group()
    special_bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    shields = pygame.sprite.Group()
    bosses = pygame.sprite.Group()

    global score
    score = 0
    damage_effect_time = 0
    boss_spawned = False
    boss_respawn_time = 0

    game_start_time = pygame.time.get_ticks()

    def spawn_enemy():
        enemy_type = random.choices([1, 2, 4], weights=[15, 15, 20])[0]  
        if enemy_type == 1:
            enemy = Enemy(random.randint(0, WIDTH - ENEMY_WIDTH), -ENEMY_HEIGHT, 15, 1, 3, ENEMY_SCOUT_IMG)
        elif enemy_type == 2:
            enemy = Enemy(random.randint(0, WIDTH - ENEMY_WIDTH), -ENEMY_HEIGHT, 25, 3, 1, ENEMY_BOMBER_IMG)
        elif enemy_type == 4:
            enemy = Asteroid(random.randint(0, WIDTH - ENEMY_WIDTH), -ENEMY_HEIGHT)
        enemies.add(enemy)

    def spawn_boss():
        boss = Boss()
        bosses.add(boss)

    def spawn_shield():
        shield = Shield(random.randint(0, WIDTH - 30), -30)
        shields.add(shield)

    def restart_game():
        global player, bullets, special_bullets, enemies, enemy_bullets, shields, bosses, score, boss_spawned, boss_respawn_time
        player = Player()
        player_group = pygame.sprite.Group(player)
        bullets = pygame.sprite.Group()
        special_bullets = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        enemy_bullets = pygame.sprite.Group()
        shields = pygame.sprite.Group()
        bosses = pygame.sprite.Group()
        score = 0
        boss_spawned = False
        boss_respawn_time = 0

    while run:
        game_over=False
        clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_SPACE and len(bullets) < MAX_BULLETS:
                    bullet = Bullet(player.rect.centerx, player.rect.top)
                    bullets.add(bullet)
                if event.key == pygame.K_k and player.can_shoot_special():
                    special_bullet = player.shoot_special()
                    special_bullets.add(special_bullet)
                if event.key == pygame.K_r and player.hp <= 0:
                    game_over=False
                    restart_game()
                    player.hp=PLAYER_HP

        
        
        if not game_over:
            keys_pressed = pygame.key.get_pressed()
            player.move(keys_pressed)
            player.update()
            bullets.update()
            special_bullets.update(enemies,bosses)
            enemies.update()
            enemy_bullets.update()
            shields.update()
            bosses.update()
            
            if player.hp <= 0:
                game_over = True
                show_game_over(WIN)
                enemies.empty()
                enemy_bullets.empty()
                bosses.empty()
                shields.empty()
                boss_spawned = False  
                boss_respawn_time = 0
                restart_game()
                player.rect.center = (WIDTH // 2, HEIGHT - 30)

            pygame.display.update()
            # Проверка попадения обычных пуль игрока
            for bullet in bullets:
                hits = pygame.sprite.spritecollide(bullet, enemies, False)
                for enemy in hits:
                    enemy.hp -= 5
                    if enemy.hp <= 0:
                        enemy.kill()
                        score += 1
                    bullet.kill()

            # Проверка попадения супер пули игрока
            for special_bullet in special_bullets:
                hits = pygame.sprite.spritecollide(special_bullet, enemies, False)
                for enemy in hits:
                    enemy.hp -= 40
                    if enemy.hp <= 0:
                        enemy.kill()
                        score += 1
                        
                boss_hits = pygame.sprite.spritecollide(special_bullet, bosses, False)
                for boss in boss_hits:
                    boss.hp -= 40
                    if boss.hp <= 0:
                        boss.kill()
                        score += 10
                
                if special_bullet.rect.y < 0:
                    special_bullet.kill()

            # Проверка вражеских пуль
            hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
            for hit in hits:
                if player.shielded:
                    player.shielded = False
                else:
                    player.hp -= 5 if hit.boss_bullet else hit.is_enemy
                    damage_effect_time = current_time

            # Проверка попадения вражеских пуль в игрока
            hits = pygame.sprite.spritecollide(player, enemies, True)
            for hit in hits:
                if player.shielded:
                    player.shielded = False
                else:
                    player.hp -= hit.damage
                    damage_effect_time = current_time

            # Проверка взятия щита
            hits = pygame.sprite.spritecollide(player, shields, True)
            for hit in hits:
                player.activate_shield()

            # Проверка попадения пуль босса
            for bullet in bullets:
                boss_hits = pygame.sprite.spritecollide(bullet, bosses, False)
                for boss in boss_hits:
                    boss.hp -= 5
                    if boss.hp <= 0:
                        boss.kill()
                        score += 10
                        boss_respawn_time = current_time + BOSS_RESPAWN_TIME
                    bullet.kill()

            # Выстрел босса
            for boss in bosses:
                bullet = boss.shoot()
                if bullet:
                    enemy_bullets.add(bullet)

            # Выстрел врага
            for enemy in enemies:
                bullet = enemy.shoot()
                if bullet:
                    enemy_bullets.add(bullet)

            # Эффект при получении урона
            if current_time - damage_effect_time < 300:
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                WIN.blit(BACKGROUND_IMG, (offset_x, offset_y))
                damage_overlay = pygame.Surface((WIDTH, HEIGHT))
                damage_overlay.set_alpha(100)
                damage_overlay.fill(RED)
                WIN.blit(damage_overlay, (0, 0))
            else:
                WIN.blit(BACKGROUND_IMG, (0, 0))

            player_group.draw(WIN)
            bullets.draw(WIN)
            special_bullets.draw(WIN)
            enemies.draw(WIN)
            enemy_bullets.draw(WIN)
            shields.draw(WIN)
            bosses.draw(WIN)
            draw_shield_effect(WIN, player)
            draw_health_bar(WIN, 10, 10, player.hp, PLAYER_HP)
            draw_special_cooldown_bar(WIN, 10, 30, player)
            draw_score(WIN, score)
            draw_controls(WIN)


            # Спаун врагов
            if random.randint(1, 30) == 1:  
                spawn_enemy()

            # Спаун щитов
            if random.randint(1, 500) == 1:  
                spawn_shield()

            # Спаун босса
            if score >= 10 and (not boss_spawned or (boss_respawn_time and current_time >= boss_respawn_time)):
                spawn_boss()
                boss_spawned = True
                boss_respawn_time = 0
            
    pygame.quit()

if __name__ == "__main__":
    main()
