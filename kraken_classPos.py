from copy import deepcopy
from math import floor
from pkgutil import read_code
import pygame
from sys import exit
import os
CHEQUER_SIZE = 76                       
POS_WITHOUT_BORDER_OF_MAP = (56,117)
IMG = []                                # 0 宝船 1 护卫船 2 海怪 3,4,5是放大的
MAXIMIZE_RATE = 1.2                     # 图片放大倍率
RED = (255,10,10)
BLUE = (10,10,255)
WIDTH_OF_BORDER = 2                     # highlight线宽      
RECT_OF_CLICK_RULE = pygame.Rect(235,35,180,60)                 
POS_FOR_MOSTERS = [(0,3),(1,1),(1,5),(3,0),(3,6),(5,1),(5,5),(6,3)]
POS_FOR_FRIGATES = [(3,2),(2,3),(4,3),(3,4)]
DIR = [(0,1),(0,-1),(1,0),(-1,0)]
FEASIBLE_REGIONS = []
EXIT_POS = [[0,0],[0,6],[6,0],[6,6]]
VICTORY = 0                            # 1 Kraken wins 2 pirate wins
RULE = False

game = []
round = False                           # false 海怪 true 船
stage = False                           # false 点击 true 移动

class Pos:
    def __init__(self,x,y):
        self.x = x
        self.y = y
    
    def __add__(self,other):
        return Pos(self.x + other.x, self.y + other.y)

    def __iadd__(self,other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self,other):
        return Pos(self.x - other.x, self.y - other.y)

    def __str__(self) -> str:
        return f'({self.x},{self.y})'

    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y

    def multiply(self,n):
        return Pos(self.x * n, self.y * n)

    def divide(self,n):
        return Pos(self.x / n, self.y / n)

    def floor(self):
        self.x = floor(self.x)
        self.y = floor(self.y)
        return self

    def to_absolute(self):
        return self.multiply(CHEQUER_SIZE) + POS_WITHOUT_BORDER_OF_MAP

    def to_relative(self):
        return ((self - POS_WITHOUT_BORDER_OF_MAP).divide(CHEQUER_SIZE)).floor()

    def to_tuple(self):
        return (self.x, self.y)

    def cross_border(self) -> bool:
        return not (0 <= self.x <= 6 and 0 <= self.y <= 6)

POS_WITHOUT_BORDER_OF_MAP = Pos(*POS_WITHOUT_BORDER_OF_MAP)

class chequer:
    def __init__(self,pos:Pos,type:int):
        self.pos = pos
        self.type = type

    def draw_me(self,screen):
        screen.blit(IMG[self.type],self.pos.to_absolute().to_tuple())

    def draw_me_big(self,screen):
        temp_pos = self.pos.to_absolute()
        temp_pos += Pos(- CHEQUER_SIZE * (MAXIMIZE_RATE - 1) / 2, - CHEQUER_SIZE * (MAXIMIZE_RATE - 1) / 2)
        screen.blit(IMG[self.type + 3],temp_pos.floor().to_tuple())

choose : chequer

def Game(pos:Pos):
    return game[pos.x][pos.y]

def transform_tuple_list_to_pos():
    global POS_FOR_MOSTERS,POS_FOR_FRIGATES,DIR,EXIT_POS
    def transform_iter(iter):
        for i in range(0,len(iter)):
            iter[i] = Pos(*iter[i])
    transform_iter(POS_FOR_MOSTERS)
    transform_iter(POS_FOR_FRIGATES)
    transform_iter(DIR)
    transform_iter(EXIT_POS)
        
def draw_border(screen,pos:Pos,color:tuple):  # pos为relative
    pos = pos.to_absolute()
    pos_for_draw = []       # 画线点对

    def draw_line_third(pos1:Pos,dir:bool):
        pos_for_draw.append(pos1)
        temp = deepcopy(pos1)
        for i in range(3):
            if dir:
                temp.x += CHEQUER_SIZE // 3
            else:
                temp.y += CHEQUER_SIZE // 3
            pos_for_draw.append(temp)
        
    draw_line_third(pos,True)
    draw_line_third(pos,False)
    draw_line_third(pos + Pos(CHEQUER_SIZE,0),False)
    draw_line_third(pos + Pos(0,CHEQUER_SIZE),True)

    for i in range(0,len(pos_for_draw),2):
        pos1 = pos_for_draw[i]
        pos2 = pos_for_draw[i + 1]
        pygame.draw.line(screen,color,pos1.to_tuple(),pos2.to_tuple(),WIDTH_OF_BORDER)

def init_image():
    global IMG
    temp = pygame.transform.scale(pygame.image.load('source/宝船.png'),(CHEQUER_SIZE,CHEQUER_SIZE))
    IMG.append(temp)
    temp = pygame.transform.scale(pygame.image.load('source/护卫船.png'),(CHEQUER_SIZE,CHEQUER_SIZE))
    IMG.append(temp)
    temp = pygame.transform.scale(pygame.image.load('source/海怪.png'),(CHEQUER_SIZE,CHEQUER_SIZE))
    IMG.append(temp)
    for i in range(3):
        scale_length = floor(CHEQUER_SIZE * MAXIMIZE_RATE)
        temp = pygame.transform.scale(IMG[i],(scale_length,scale_length))
        IMG.append(temp)

def match_round_with_type(type:int) -> bool:
    if (round and 0 <= type <= 1) or (not round and type == 2):
        return True
    return False

def draw(screen):
    screen.fill((255,255,255))
    background = pygame.image.load('source/棋盘.png')
    screen.blit(background, (-3,0))
    border_wait_for_draw = []
    for i in range(7):
        for j in range(7):
            if game[i][j]:
                game[i][j].draw_me(screen)
                if match_round_with_type(game[i][j].type):
                    border_wait_for_draw.append(game[i][j].pos)
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
        game[temp_pos.x][temp_pos.y] = chequer(temp_pos,2)
    for temp_pos in POS_FOR_FRIGATES:
        game[temp_pos.x][temp_pos.y] = chequer(temp_pos,1)
    game[3][3] = chequer(Pos(3,3),0)

def update_feasible_region_in_stage_1():
    global FEASIBLE_REGIONS
    FEASIBLE_REGIONS.clear()
    for i in range(7):
        for j in range(7):
            if game[i][j] and match_round_with_type(game[i][j].type):
                FEASIBLE_REGIONS.append(game[i][j].pos)         # 可行域为棋子
    
    # for i in range(FEASIBLE_REGIONS):
    #     print(i,end=' ')
            
def click_is_available(pos:Pos) -> bool:
    for available_region in FEASIBLE_REGIONS:
        if pos == available_region:
            return True
    return False

def move_is_available(pos:Pos) -> bool:
    if pos.cross_border():
        return False
    if Game(pos):
        return False
    if not round and pos in EXIT_POS:
        return False
    if choose.type == 1 and pos in EXIT_POS:    # 护卫船不许进出口
        return False
    return True

def converging_attack(pos:Pos) -> list:
    attack_dir = []
    my_type = Game(pos).type
    if my_type == 0:
        return attack_dir

    def friend(pos:Pos) -> int:                # 0 friend 1 not friend 2 error
        if pos in EXIT_POS or (pos == Pos(3,3) and not game[3][3]):
            return 0
        if not Game(pos):
            return 2
        if my_type == 2:
            if Game(pos).type == my_type:
                return 0
            else:
                return 1
        else:
            if Game(pos).type != 2 and Game(pos).type != 0:
                return 0
            else:
                return 1    

    for i in range(0,len(DIR)):
        direction = DIR[i]
        dirpos1 = pos + direction
        if( not dirpos1.cross_border() and Game(dirpos1) and Game(dirpos1).type == 0 and my_type == 2):     # 对宝船单独判断
            temp = True
            for direction2 in DIR:
                pos_judge = dirpos1 + direction2
                if pos_judge.cross_border():
                    continue
                if pos_judge in EXIT_POS or pos_judge == Pos(3,3) or (Game(pos_judge) and Game(pos_judge).type == 2):
                    continue
                else:
                    temp = False
                    break
            if temp:
                attack_dir.append(i)
            continue
                    
        dirpos2 = direction + dirpos1
        if dirpos2.cross_border() :       # 二格越界
            continue

        if friend(dirpos1) == 1 and friend(dirpos2) == 0:
            attack_dir.append(i)

    return attack_dir
        
def victory():
    global VICTORY
    for exit_pos in EXIT_POS:
        if Game(exit_pos) and Game(exit_pos).type == 0:
            VICTORY = 2
            return
    update_feasible_region_in_stage_1()
    if len(FEASIBLE_REGIONS) == 0:
        if not round:
            VICTORY = 2
        else:
            VICTORY = 1

if __name__ == "__main__":

    transform_tuple_list_to_pos()
    init_image()
    update_chequer_firstly()

    pygame.init()
    screen = pygame.display.set_mode((646,725), 0, 32)
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
                    os.system('start source/规则.png')
                    break
                
                relative_mousepos = Pos(*mousepos).to_relative()

                if not stage:                                               # 点击自己棋子的阶段
                    update_feasible_region_in_stage_1()

                    if not click_is_available(relative_mousepos):
                        break
                    
                    choose = Game(relative_mousepos)
                    stage = not stage
                    FEASIBLE_REGIONS.clear()
                    for direction in DIR:
                        now_pos = relative_mousepos + direction
                        while move_is_available(now_pos):
                            if now_pos != Pos(3,3) or choose.type == 0:
                                FEASIBLE_REGIONS.append(now_pos)
                            now_pos += direction
                            
                    for available_region in FEASIBLE_REGIONS:
                        draw_border(screen,available_region,BLUE)
                    choose.draw_me_big(screen)
                
                else:
                    stage = not stage
                    if not click_is_available(relative_mousepos):
                        draw(screen)
                        break
                    round = not round

                    game[choose.pos.x][choose.pos.y] = 0
                    choose.pos = relative_mousepos
                    game[relative_mousepos.x][relative_mousepos.y] = choose

                    attack_dir = converging_attack(relative_mousepos)
                    for direction in attack_dir:
                        temp = relative_mousepos + direction
                        if Game(temp).type == 0:
                            VICTORY = 1
                        game[temp.x][temp.y] = 0
                    
                    victory()
                    draw(screen)


        pygame.display.update()