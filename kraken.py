from math import floor
from re import A
import pygame
from sys import exit
CHEQUER_SIZE = 76                       
POS_WITHOUT_BORDER_OF_MAP = (59,117)     
IMG = []                                # 0 宝船 1 护卫船 2 海怪 3,4,5是放大的
MAXIMIZE_RATE = 1.2                     # 图片放大倍率
RED = (255,10,10)
BLUE = (10,10,255)
WIDTH_OF_BORDER = 2                     # highlight线宽      
RECT_OF_CLICK_RULE = pygame.Rect(235,35,180,60)                 
POS_FOR_MOSTERS = ((0,3),(1,1),(1,5),(3,0),(3,6),(5,1),(5,5),(6,3))
POS_FOR_FRIGATES = ((3,2),(2,3),(4,3),(3,4))
DIR = ((0,1),(0,-1),(1,0),(-1,0))
FEASIBLE_REGIONS = []
EXIT_POS = ([0,0],[0,6],[6,0],[6,6])
VICTORY = 0                            # 1 Kraken wins 2 pirate wins

game = []
round = False                           # false 海怪 true 船
stage = False                           # false 点击 true 移动

class chequer:
    def __init__(self,pos:list,type):
        self.pos = pos
        self.type = type
        # self.highlight = False
    def draw_me(self,screen):
        screen.blit(IMG[self.type],relativepos_to_absolutepos(self.pos))
        # print(relativepos_to_absolutepos(self.pos))
    def draw_me_big(self,screen):
        temp_pos = relativepos_to_absolutepos(self.pos)
        for i in range(2):
            temp_pos[i] -= CHEQUER_SIZE * (MAXIMIZE_RATE - 1) / 2
        screen.blit(IMG[self.type + 3],floor_pos(temp_pos))

choose : chequer

def floor_pos(pos:list):
    return [floor(x) for x in pos]
        
def draw_border(screen,pos:list,color:tuple):  # pos为绝对坐标
    pos_for_draw = []       # 画线点对

    def draw_line_third(pos,dir:bool):
        if dir:                         # 横向画三段线
            pos_for_draw.append(pos)
            pos_for_draw.append(floor_pos([pos[0] + CHEQUER_SIZE / 3 , pos[1]]))
            pos_for_draw.append(floor_pos([pos[0] + CHEQUER_SIZE * 2 / 3 , pos[1]]))
            pos_for_draw.append(floor_pos([pos[0] + CHEQUER_SIZE, pos[1]]))
        else:                           # 纵向画三段线
            pos_for_draw.append(pos)
            pos_for_draw.append(floor_pos([pos[0], pos[1] + CHEQUER_SIZE / 3 ]))
            pos_for_draw.append(floor_pos([pos[0], pos[1] + CHEQUER_SIZE * 2 / 3 ]))
            pos_for_draw.append(floor_pos([pos[0], pos[1] + CHEQUER_SIZE]))
        
    draw_line_third(pos,True)
    draw_line_third(pos,False)
    draw_line_third([pos[0] + CHEQUER_SIZE,pos[1]],False)
    draw_line_third([pos[0],pos[1] + CHEQUER_SIZE],True)

    for i in range(0, len(pos_for_draw),2):
        pygame.draw.line(screen,color,pos_for_draw[i],pos_for_draw[i + 1],WIDTH_OF_BORDER)
    # 这里不可用for pos1,pos2 in pos_for_draw: 不然pos1与pos2不会是列表

def init_image():
    global IMG
    temp = pygame.transform.scale(pygame.image.load('source/宝船.png'),(CHEQUER_SIZE,CHEQUER_SIZE))
    IMG.append(temp)
    temp = pygame.transform.scale(pygame.image.load('source/护卫船.png'),(CHEQUER_SIZE,CHEQUER_SIZE))
    IMG.append(temp)
    temp = pygame.transform.scale(pygame.image.load('source/海怪.png'),(CHEQUER_SIZE,CHEQUER_SIZE))
    IMG.append(temp)
    for i in range(3):
        temp = pygame.transform.scale(IMG[i],floor_pos((CHEQUER_SIZE * MAXIMIZE_RATE,CHEQUER_SIZE * MAXIMIZE_RATE)))
        IMG.append(temp)


def relativepos_to_absolutepos(pos):
    return [POS_WITHOUT_BORDER_OF_MAP[i] + pos[i] * CHEQUER_SIZE for i in range(2)]

def absolutepos_to_relativepos(pos):
    return [floor((pos[i] - POS_WITHOUT_BORDER_OF_MAP[i]) / CHEQUER_SIZE) for i in range(2)]

def match_round_with_type(type:int) -> bool:
    if (round and 0 <= type <= 1) or (not round and type == 2):
        return True
    return False

def draw(screen):
    screen.fill((255,255,255))
    background = pygame.image.load('source/棋盘.png')
    screen.blit(background, (0,0))
    border_wait_for_draw = []
    for i in range(7):
        for j in range(7):
            if game[i][j]:
                game[i][j].draw_me(screen)
                if match_round_with_type(game[i][j].type):
                    border_wait_for_draw.append(relativepos_to_absolutepos(game[i][j].pos))
    for i in border_wait_for_draw:
        draw_border(screen,i,RED)
    
    if VICTORY != 0:
        myfont = pygame.font.Font(None,60)
        if VICTORY == 1:
            textImage = myfont.render('KRAKEN WINS!',True,BLUE)
        else:
            textImage = myfont.render('PIRATE WINS!',True,RED)
        screen.blit(textImage,(170,665))

def update_chequer_firstly():
    global game
    for i in range(7):          # 制作棋盘
        game.append([])
        for j in range(7):
            game[i].append(0)   # 使用0占位
    for temp_pos in POS_FOR_MOSTERS:
        game[temp_pos[0]][temp_pos[1]] = chequer(list(temp_pos),2)
    for temp_pos in POS_FOR_FRIGATES:
        game[temp_pos[0]][temp_pos[1]] = chequer(list(temp_pos),1)
    game[3][3] = chequer([3,3],0)

def update_feasible_region_in_stage_1():
    global FEASIBLE_REGIONS
    FEASIBLE_REGIONS.clear()
    for i in range(7):
        for j in range(7):
            if game[i][j] and match_round_with_type(game[i][j].type):
                FEASIBLE_REGIONS.append(game[i][j].pos)         # 可行域为棋子
            
def click_is_available(pos:list) -> bool:
    if pos in FEASIBLE_REGIONS:
        return True
    return False

def judge_cross_the_border(pos:list) -> bool:
    return not (0 <= pos[0] <= 6 and 0 <= pos[1] <= 6)

def move_is_available(pos:list) -> bool:
    if judge_cross_the_border(pos):
        return False
    if game[pos[0]][pos[1]]:
        return False
    if not round and pos in EXIT_POS:
        return False
    if choose.type == 1 and pos in EXIT_POS:    # 护卫船不许进出口
        return False
    return True

def converging_attack(pos:list) -> list:
    attack_dir = []
    my_type = game[pos[0]][pos[1]].type

    def friend(pos:list) -> int:                # 0 friend 1 not friend 2 error
        if pos in EXIT_POS or (pos == [3,3] and not game[3][3]):
            return 0
        if not game[pos[0]][pos[1]]:
            return 2
        if my_type == 2:
            if game[pos[0]][pos[1]].type == my_type:
                return 0
            else:
                return 1
        else:
            if game[pos[0]][pos[1]].type != 2:
                return 0
            else:
                return 1    

    for i in range(0,len(DIR)):
        direction = DIR[i]
        if judge_cross_the_border([pos[i] + direction[i] * 2 for i in range(2)]):
            continue
        
        if friend([pos[i] + direction[i] for i in range(2)]) == 1 and friend([pos[i] + direction[i] * 2 for i in range(2)]) == 0:
            attack_dir.append(i)
            attackdown_chequer = game[pos[0] + DIR[i][0]][pos[1] + DIR[i][1]]
            if attackdown_chequer.type == 0:  # 四面夹击
                for temp_direction in DIR:
                    surrounding_pos = [attackdown_chequer.pos[i] + temp_direction[i] for i in range(2)]
                    if (judge_cross_the_border(surrounding_pos) or 
                    not game[surrounding_pos[0]][surrounding_pos[1]] or 
                    game[surrounding_pos[0]][surrounding_pos[1]].type != 2):
                        print(f'dir {temp_direction} is poped')
                        attack_dir.pop()
                        break
    return attack_dir
        
def victory():
    global VICTORY
    for exit_pos in EXIT_POS:
        if game[exit_pos[0]][exit_pos[1]] and game[exit_pos[0]][exit_pos[1]].type == 0:
            VICTORY = 2
            return
    update_feasible_region_in_stage_1()
    if len(FEASIBLE_REGIONS) == 0:
        if not round:
            VICTORY = 2
        else:
            VICTORY = 1

if __name__ == "__main__":

    init_image()
    update_chequer_firstly()

    pygame.init()
    screen = pygame.display.set_mode((649,725), 0, 32)
    pygame.display.set_caption('kraken made by |x|')
    draw(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if VICTORY:
                    draw(screen)
                    continue
                mousepos = pygame.mouse.get_pos()
                if RECT_OF_CLICK_RULE.collidepoint(mousepos):
                    break
                    # rule
                
                relative_mousepos = absolutepos_to_relativepos(mousepos)

                if not stage:                                               # 点击自己棋子的阶段
                    update_feasible_region_in_stage_1()
                    if not click_is_available(relative_mousepos):
                        break
                    
                    choose = game[relative_mousepos[0]][relative_mousepos[1]]
                    stage = not stage
                    FEASIBLE_REGIONS.clear()
                    for direction in DIR:
                        now_pos = [relative_mousepos[i] + direction[i] for i in range(2)]
                        while move_is_available(now_pos):
                            if now_pos != [3,3] or choose.type == 0:
                                FEASIBLE_REGIONS.append(now_pos)
                            now_pos = [now_pos[i] + direction[i] for i in range(2)]
                            
                    for available_region in FEASIBLE_REGIONS:
                        draw_border(screen,relativepos_to_absolutepos(available_region),BLUE)
                    choose.draw_me_big(screen)
                
                else:
                    stage = not stage
                    if not click_is_available(relative_mousepos):
                        draw(screen)
                        break
                    round = not round

                    game[choose.pos[0]][choose.pos[1]] = 0
                    choose.pos = relative_mousepos
                    game[relative_mousepos[0]][relative_mousepos[1]] = choose

                    attack_dir = converging_attack(relative_mousepos)
                    for direction in attack_dir:
                        if game[relative_mousepos[0] + DIR[direction][0]][relative_mousepos[1] + DIR[direction][1]].type == 0:
                            VICTORY = 1
                        game[relative_mousepos[0] + DIR[direction][0]][relative_mousepos[1] + DIR[direction][1]] = 0
                    
                    victory()
                    draw(screen)


        pygame.display.update()