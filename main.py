import pygame
import sys
import io
import cairosvg
import math
import os
import random
import json
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Load translations from JSON file
with open('translations.json', 'r', encoding='utf-8') as f:
    COUNTRY_TRANSLATIONS = json.load(f)

START_ROUND_SCORE = 5

# Initialize Pygame
pygame.init()
pygame.font.init()

# Window setup
window_width = 800
window_height = 600
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Викторина: флаги")

# Game constants
target_height = 250
button_height = 60
button_width = 300
font = pygame.font.SysFont('Arial', 24)

def load_flag(file_path):
    name = file_path.replace('img/Flag_of_', '').replace('.svg', '')
    svg_data = cairosvg.svg2png(url=file_path)
    image_stream = io.BytesIO(svg_data)
    original_flag = pygame.image.load(image_stream)
    
    aspect_ratio = original_flag.get_width() / original_flag.get_height()
    target_width = int(target_height * aspect_ratio)
    return name, pygame.transform.scale(original_flag, (target_width, target_height))

def load_all_flags():
    flags = {}
    flag_names = []
    max_width = 0
    
    # Get all flag files
    flag_files = set()
    for file in os.listdir('img'):
        if file.endswith('.svg'):
            name, flag = load_flag(f'img/{file}')
            flag_files.add(name)
            flags[name] = flag
            flag_names.append(name)
            max_width = max(max_width, flag.get_width())

    for name in flag_names:
        if name not in COUNTRY_TRANSLATIONS:
            print(f"Missing translation for: {name}")

    # Check which translations don't have flag files
    for country_name in COUNTRY_TRANSLATIONS:
        if country_name not in flag_files:
            print(f"Missing flag file for: {country_name} ({COUNTRY_TRANSLATIONS[country_name]})")
    
    return flags, flag_names, max_width

def create_button(index, option):
    row = index // 2
    col = index % 2
    x = window_width//2 - button_width - 10 + col * (button_width + 20)
    y = window_height - 180 + row * (button_height + 20)
    return pygame.Rect(x, y, button_width, button_height)

def new_round(flag_names, previous_flag, shown_flags):
    available_flags = [flag for flag in flag_names if flag not in shown_flags]
    if not available_flags:
        return None, None, None
    
    current_flag = random.choice(available_flags)
    shown_flags.add(current_flag)
    
    current_options = [current_flag]
    while len(current_options) < 4:
        option = random.choice(flag_names)
        if option not in current_options:
            current_options.append(option)
    random.shuffle(current_options)
    
    buttons = [create_button(i, option) for i, option in enumerate(current_options)]
    
    return current_flag, current_options, buttons

def get_score_word(score):
    if score % 10 == 1 and score % 100 != 11:
        return "очко"
    elif 2 <= score % 10 <= 4 and (score % 100 < 10 or score % 100 >= 20):
        return "очка"
    else:
        return "очков"

def draw_end_screen(screen, score):
    screen.fill((200, 200, 255))
    
    # Draw "Конец игры"
    game_over_font = pygame.font.SysFont('Arial', 72)
    game_over_text = game_over_font.render('Конец игры', True, (0, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(window_width//2, window_height//2 - 50))
    screen.blit(game_over_text, game_over_rect)
    
    # Draw score with correct word form
    score_font = pygame.font.SysFont('Arial', 36)
    score_text = score_font.render(f'Вы набрали {score} {get_score_word(score)}', True, (0, 0, 0))
    score_rect = score_text.get_rect(center=(window_width//2, window_height//2 + 50))
    screen.blit(score_text, score_rect)
    
    # Update instructions to show both options
    restart_font = pygame.font.SysFont('Arial', 24)
    restart_text = restart_font.render('Пробел - новая игра, ESC - выход', True, (0, 0, 0))
    restart_rect = restart_text.get_rect(center=(window_width//2, window_height//2 + 120))
    screen.blit(restart_text, restart_rect)

def draw_exit_confirmation(screen):
    # Draw semi-transparent overlay
    overlay = pygame.Surface((window_width, window_height))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)
    screen.blit(overlay, (0, 0))
    
    # Draw confirmation text
    exit_font = pygame.font.SysFont('Arial', 36)
    exit_text = exit_font.render('Вы хотите выйти?', True, (255, 255, 255))
    exit_rect = exit_text.get_rect(center=(window_width//2, window_height//2 - 30))
    screen.blit(exit_text, exit_rect)
    
    # Draw instructions
    inst_font = pygame.font.SysFont('Arial', 24)
    space_text = inst_font.render('Пробел - выйти', True, (255, 255, 255))
    esc_text = inst_font.render('ESC - вернуться', True, (255, 255, 255))
    
    space_rect = space_text.get_rect(center=(window_width//2, window_height//2 + 30))
    esc_rect = esc_text.get_rect(center=(window_width//2, window_height//2 + 70))
    
    screen.blit(space_text, space_rect)
    screen.blit(esc_text, esc_rect)

def handle_click(mouse_pos, buttons, current_options, current_flag, disabled_buttons):
    for i, button in enumerate(buttons):
        if button.collidepoint(mouse_pos) and i not in disabled_buttons:
            if current_options[i] == current_flag:
                return i, True
            else:
                disabled_buttons.add(i)
                return i, False
    return None, False

def main():
    flags, flag_names, max_width = load_all_flags()
    
    def start_new_game():
        return {
            'score': 0,
            'time': 0,
            'previous_flag': None,
            'round_score': START_ROUND_SCORE,
            'disabled_buttons': set(),
            'highlight_end_time': 0,
            'correct_button': None,
            'shown_flags': set(),
            'game_over': False,
            'show_exit_confirmation': False
        }
    
    game_state = start_new_game()
    current_flag, current_options, buttons = new_round(flag_names, game_state['previous_flag'], game_state['shown_flags'])
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state['show_exit_confirmation']:
                        game_state['show_exit_confirmation'] = False
                    elif game_state['game_over']:
                        pygame.quit()
                        sys.exit()
                    elif not game_state['game_over']:
                        game_state['show_exit_confirmation'] = True
                elif event.key == pygame.K_SPACE:
                    if game_state['show_exit_confirmation']:
                        pygame.quit()
                        sys.exit()
                    elif game_state['game_over']:
                        game_state = start_new_game()
                        current_flag, current_options, buttons = new_round(flag_names, game_state['previous_flag'], game_state['shown_flags'])
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_state['game_over'] and game_state['correct_button'] is None and not game_state['show_exit_confirmation']:
                mouse_pos = pygame.mouse.get_pos()
                clicked_button, is_correct = handle_click(mouse_pos, buttons, current_options, current_flag, game_state['disabled_buttons'])
                if is_correct:
                    game_state['correct_button'] = clicked_button
                    game_state['score'] += game_state['round_score']
                    game_state['highlight_end_time'] = pygame.time.get_ticks() + 1000
                elif clicked_button is not None:
                    game_state['round_score'] = 0
                    game_state['score'] -= 1
                    if game_state['score'] < 0:
                        game_state['score'] = 0
                        game_state['game_over'] = True

        if game_state['game_over']:
            draw_end_screen(screen, game_state['score'])
        else:
            screen.fill((200, 200, 255))
            
            score_text = font.render(f'Очки: {game_state["score"]}', True, (0, 0, 0))
            screen.blit(score_text, (20, 20))
            
            draw_flag(screen, flags[current_flag], game_state['time'])
            
            for i, (button, option) in enumerate(zip(buttons, current_options)):
                draw_button(screen, button, option, i == game_state['correct_button'], 
                          i in game_state['disabled_buttons'], game_state['highlight_end_time'])
        
        if game_state['show_exit_confirmation']:
            draw_exit_confirmation(screen)

        # Move this block outside of the exit confirmation check
        if game_state['correct_button'] is not None and pygame.time.get_ticks() >= game_state['highlight_end_time']:
            game_state['previous_flag'] = current_flag
            current_flag, current_options, buttons = new_round(flag_names, game_state['previous_flag'], game_state['shown_flags'])
            if current_flag is None:
                game_state['game_over'] = True
            else:
                game_state['round_score'] = START_ROUND_SCORE
                game_state['disabled_buttons'].clear()
                game_state['correct_button'] = None
        
        game_state['time'] += 0.1

        pygame.display.flip()
        pygame.time.delay(20)

def draw_flag(screen, flag_image, time):
    base_x = (window_width - flag_image.get_width()) // 2
    base_y = 70
    
    for i in range(flag_image.get_width()):
        amplitude_factor = i / flag_image.get_width()
        wave = calculate_wave(i, time, amplitude_factor)
        
        section = pygame.Surface((1, flag_image.get_height()), pygame.SRCALPHA)
        section.blit(flag_image, (-i, 0))
        screen.blit(section, (base_x + i, base_y + wave))

def calculate_wave(i, time, amplitude_factor):
    return (
        math.sin(i / 30 - time * 3) * 8 * amplitude_factor +
        math.sin(i / 20 - time * 4) * 4 * amplitude_factor +
        math.sin(i / 15 - time * 2) * 2 * amplitude_factor +
        math.sin(-time * 2) * 1.5 * amplitude_factor
    )

def draw_button(screen, button, option, is_correct, is_disabled, highlight_time):
    if is_correct and pygame.time.get_ticks() < highlight_time:
        pygame.draw.rect(screen, (255, 255, 0), button)
    elif is_disabled:
        pygame.draw.rect(screen, (150, 150, 150), button)
    else:
        pygame.draw.rect(screen, (220, 220, 220), button)
    
    pygame.draw.rect(screen, (100, 100, 100), button, 2)
    translated_name = COUNTRY_TRANSLATIONS.get(option, option)
    
    # Try to split long names into two lines
    if len(translated_name) > 15:
        words = translated_name.split()
        first_line = []
        second_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) <= 15:
                first_line.append(word)
                current_length += len(word) + 1
            else:
                second_line.append(word)
        
        text_lines = [' '.join(first_line), ' '.join(second_line)]
        current_font_size = 24
    else:
        text_lines = [translated_name]
        current_font_size = 24
    
    # Try different font sizes until text fits
    while current_font_size > 12:
        current_font = pygame.font.SysFont('Arial', current_font_size)
        total_height = sum(current_font.size(line)[1] for line in text_lines)
        max_width = max(current_font.size(line)[0] for line in text_lines)
        
        if max_width <= button.width - 20 and total_height <= button.height - 10:
            break
            
        current_font_size -= 2
    
    # Render text
    rendered_lines = [current_font.render(line, True, (0, 0, 0)) for line in text_lines]
    total_height = sum(text.get_height() for text in rendered_lines)
    
    # Calculate starting y position to center all lines vertically
    y = button.centery - total_height // 2
    
    # Draw each line
    for text in rendered_lines:
        text_rect = text.get_rect(centerx=button.centerx, y=y)
        screen.blit(text, text_rect)
        y += text.get_height()

if __name__ == "__main__":
    main()