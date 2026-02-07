#Импортируем библиотеки
import pygame
import sqlite3
import random
from datetime import datetime

#Запускаем PyGame
pygame.init()

#Графические константы: стороны экрана, фпс, цвета
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)

class Player: #Игрок
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.color = BLUE
        self.speed = 5
        self.score = 0
        
    def move(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
            
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        #Добавим глазки для красоты
        pygame.draw.circle(screen, WHITE, (self.rect.x + 10, self.rect.y + 10), 5)
        pygame.draw.circle(screen, WHITE, (self.rect.x + 30, self.rect.y + 10), 5)
        pygame.draw.circle(screen, BLACK, (self.rect.x + 10, self.rect.y + 10), 2)
        pygame.draw.circle(screen, BLACK, (self.rect.x + 30, self.rect.y + 10), 2)

class Coin: #Монета
    def __init__(self):
        self.radius = 15
        self.color = YELLOW
        self.respawn()
        
    def respawn(self):
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = random.randint(self.radius, SCREEN_HEIGHT - self.radius)
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                               self.radius * 2, self.radius * 2)
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, WHITE, (self.x - 5, self.y - 5), 4)

class Enemy: #Враг
    def __init__(self):
        self.width = 50
        self.height = 50
        self.color = RED
        self.respawn()
        #Задаем врагам при спавне рандомное направение движения
        self.speed_x = random.choice([-3, -2, 2, 3])
        self.speed_y = random.choice([-3, -2, 2, 3])
        
    def respawn(self):
        #Враги респавнятся в случайных местах в пределах экрана
        self.x = random.randint(self.width, SCREEN_WIDTH - self.width)
        self.y = random.randint(self.height, SCREEN_HEIGHT - self.height)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        
        #Отскок от стен: враг коснулся границы экрана - полетел в противоположную сторону
        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
            self.speed_x = -self.speed_x
        if self.y <= 0 or self.y >= SCREEN_HEIGHT - self.height:
            self.speed_y = -self.speed_y
            
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        #Добавляем злые глазки
        pygame.draw.rect(screen, BLACK, (self.rect.x + 10, self.rect.y + 10, 8, 15))
        pygame.draw.rect(screen, BLACK, (self.rect.x + 32, self.rect.y + 10, 8, 15))

class Database:
    #Работа с БД SQLite
    def __init__(self, db_name="scores.db"):
        self.db_name = db_name
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
    def add_score(self, name, score): #Добавляем результат в БД
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO scores (name, score) VALUES (?, ?)", (name, score))
        conn.commit()
        conn.close()
        
    def get_top_scores(self, limit=5): #Получаем ТОП-5 результатов
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name, score FROM scores ORDER BY score DESC LIMIT ?", (limit,))
        results = cursor.fetchall()
        conn.close()
        return results

class Game: #Основной класс самой игры
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Сбор монет - избегайте красных врагов!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        
        #Игровые объекты
        self.player = None
        self.coins = []
        self.enemies = []
        self.database = Database()
        self.player_name = ""
        self.game_state = "ENTER_NAME"  #Состояния: ENTER_NAME, PLAYING, GAME_OVER, WIN, SHOW_TOP
        self.current_input = ""
        self.coins_to_win = 10  #Количество монет для выигрыша
        self.enemies_count = 5  #Количество врагов
        
    def reset_game(self):
        #При сбросе игры реинициализируем все объекты, т.е. заново спавним
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.coins = [Coin() for _ in range(self.coins_to_win)]
        self.enemies = [Enemy() for _ in range(self.enemies_count)]
        self.player.score = 0
        
    def draw_text(self, text, color, x, y, center=True, font_type="normal"):
        #Отрисовка текста
        if font_type == "small":
            text_surface = self.small_font.render(text, True, color)
        else:
            text_surface = self.font.render(text, True, color)
            
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
            
        self.screen.blit(text_surface, text_rect)
        return text_rect
        
    def handle_name_input(self, event):
        if event.key == pygame.K_RETURN:
            if self.current_input.strip():
                self.player_name = self.current_input.strip()
                self.reset_game()
                self.game_state = "PLAYING"
                self.current_input = ""
        elif event.key == pygame.K_BACKSPACE:
            self.current_input = self.current_input[:-1]
        else:
            if len(self.current_input) < 15:
                self.current_input += event.unicode
                
    def draw_name_input_screen(self):   #Экран для ввода имени игрока
        self.screen.fill((50, 50, 100))
        
        self.draw_text("Введите ваше имя", GREEN, SCREEN_WIDTH // 2, 150)
        self.draw_text("(затем нажмите ENTER)", WHITE, SCREEN_WIDTH // 2, 200)
        
        #Поле ввода
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 250, 300, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect, 2)
        
        #Текст в поле ввода
        input_text = self.current_input if self.current_input else "Введите имя здесь..."
        text_color = RED if self.current_input else (100, 100, 100)
        self.draw_text(input_text, text_color, SCREEN_WIDTH // 2, 275)
        
        #Инструкции
        self.draw_text("ЦЕЛЬ ИГРЫ:", YELLOW, SCREEN_WIDTH // 2, 350)
        self.draw_text("Соберите 10 желтых монет, избегая красных врагов", WHITE, SCREEN_WIDTH // 2, 390)
        self.draw_text("Управление: Стрелки на клавиатуре", WHITE, SCREEN_WIDTH // 2, 430)
        self.draw_text("Нажмите ESC в любой момент для выхода", WHITE, SCREEN_WIDTH // 2, 470)
        
    def draw_game_screen(self): #Отрисовка игрового экрана и объектов на нем
        
        self.screen.fill((40, 40, 80))  #Темно-синий фон
        
        for coin in self.coins:
            coin.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        
        self.draw_text(f"Игрок: {self.player_name}", WHITE, 120, 20)
        self.draw_text(f"Монеты: {self.player.score}/{self.coins_to_win}", YELLOW, SCREEN_WIDTH - 120, 20)
        
        # Отображение оставшихся монет
        coins_left = len(self.coins)
        self.draw_text(f"Осталось собрать: {coins_left}", GREEN if coins_left <= 3 else WHITE, 
                      SCREEN_WIDTH // 2, 20)
        
        # Отображение подсказок
        self.draw_text("Собирайте желтые монеты, избегайте красных врагов!", WHITE, 
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30, font_type="small")
        
    def draw_game_over_screen(self, win=False): #Рисуем экран геймовера

        self.screen.fill((50, 50, 100))
        
        if win:
            title = "ПОБЕДА!"
            color = GREEN
            message = f"Вы собрали все {self.coins_to_win} монет!"
        else:
            title = "ИГРА ОКОНЧЕНА"
            color = RED
            message = "Вы столкнулись с врагом!"
            
        self.draw_text(title, color, SCREEN_WIDTH // 2, 150)
        self.draw_text(message, WHITE, SCREEN_WIDTH // 2, 200)
        self.draw_text(f"Ваш счет: {self.player.score}", YELLOW, SCREEN_WIDTH // 2, 250)
        self.draw_text("Нажмите ПРОБЕЛ, чтобы увидеть топ-5 игроков", WHITE, SCREEN_WIDTH // 2, 320)
        self.draw_text("Нажмите ESC для выхода", WHITE, SCREEN_WIDTH // 2, 370)
        
    def draw_top_scores_screen(self): #Экран с топом результатов
        self.screen.fill((50, 50, 100))
        
        self.draw_text("ТОП-5 ИГРОКОВ", YELLOW, SCREEN_WIDTH // 2, 100)
        
        top_scores = self.database.get_top_scores()
        
        if not top_scores:
            self.draw_text("Пока нет результатов", WHITE, SCREEN_WIDTH // 2, 200)
        else:
            for i, (name, score) in enumerate(top_scores, 1):
                color = GREEN if name == self.player_name else WHITE
                self.draw_text(f"{i}. {name}: {score} монет", color, SCREEN_WIDTH // 2, 150 + i * 50)
                
        self.draw_text("Нажмите R для новой игры", WHITE, SCREEN_WIDTH // 2, 450)
        self.draw_text("Нажмите ESC для выхода", WHITE, SCREEN_WIDTH // 2, 500)
        
    def check_collisions(self): #Проверяем коллизии (столкновения)
        #Столкновения с монетами
        for coin in self.coins[:]:
            if self.player.rect.colliderect(coin.rect):
                self.coins.remove(coin)
                self.player.score += 1
                
        #Столкновения с врагами
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.game_state = "GAME_OVER"
                self.database.add_score(self.player_name, self.player.score)
                return
                
        #Проверка на победу
        if self.player.score >= self.coins_to_win:
            self.game_state = "WIN"
            self.database.add_score(self.player_name, self.player.score)
            
    def run(self): #Основной игровой цикл
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        
                    #Обработка ввода имени
                    if self.game_state == "ENTER_NAME":
                        self.handle_name_input(event)
                        
                    #Переход к топам после игры
                    if self.game_state in ["GAME_OVER", "WIN"] and event.key == pygame.K_SPACE:
                        self.game_state = "SHOW_TOP"
                        
                    #Новая игра после просмотра топов
                    if self.game_state == "SHOW_TOP" and event.key == pygame.K_r:
                        self.game_state = "ENTER_NAME"
                        
            #Обновление состояния игры
            if self.game_state == "PLAYING":
                keys = pygame.key.get_pressed()
                self.player.move(keys)
                
                for enemy in self.enemies:
                    enemy.move()
                    
                self.check_collisions()
                
            #Отрисовка экранов в зависимости от состояния
            if self.game_state == "ENTER_NAME":
                self.draw_name_input_screen()
                
            elif self.game_state == "PLAYING":
                self.draw_game_screen()
                
            elif self.game_state in ["GAME_OVER", "WIN"]:
                self.draw_game_over_screen(win=(self.game_state == "WIN"))
                
            elif self.game_state == "SHOW_TOP":
                self.draw_top_scores_screen()
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()

#НАКОНЕЦ запускаемся!
if __name__ == "__main__":
    game = Game()
    game.run()