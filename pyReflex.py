#! /usr/bin/env python

###################################################
##                pyReflex v 1.0
## MIT License, do anything you want with this code
##                 Made by NyRe
##      Kudos to the original Reflex creator
##          Darktick, www.missionred.com
##
##           Loop authors(@flashkit.com):
##          Jakub Koter, Diode111, cuber3
###################################################

import pygame as pg
import os
from os.path import join, abspath, split
from pygame.locals import *
from random import randrange as rrange
from random import uniform
from math import sqrt

DATAPATH = join(split(abspath(__file__))[0], 'data')
FONTPATH = join(DATAPATH, 'font.ttf')

SOUND = 1
if not pg.mixer:
    print 'No sound available'
    SOUND = 0

try:
    pg.font.init()
except AttributeError:
    raise SystemExit, 'Error initializing fonts'
    
    
DRAW_FPS      = 0
PARTICLES     = 1   ##Enables particle dissolving of targets

TARGET_RADIUS = 40  ##Max radius for a target
TARGET_TTL    = 250 ##Time to live for a target
TARGET_PREAPP = 30  ##Time before target appears after registration
TEXT_COLOR    = (220, 220, 220)
LMB_COLOR     = (240, 220, 220) ##LMB = left mouse button target
LMB_FRAMECLR  = (  0, 250,   0)
RMB_COLOR     = (160,  20,  20) ##RMB = right mouse button target
RMB_FRAMECLR  = (250,   0,   0)
BG_COLOR      = ( 80,  80,  80)
BG_GRIDCOLOR  = (120, 120, 120)
BG_GRIDSTEP   = 8
RMB_PROB      = [50]#[0, 0, 0, 5, 10, 15, 25, 50] ##chances for an RMB target to appear. Indexed with round
FIRST_STAGE   = 3 ##Amount of targets on stage 1

HUD_COLOR     = (60, 60, 60)
HUD_LINECOLOR = (90, 90, 90)

FPS           = 60 ##doesn't really influence much, enables easy calculation of time
ROUND_LENGTH  = 20 ##in seconds
MAX_MISSES    = 5  ##reach this and lose the game

BASE_HITSCORE = 1000 ##Base score for hitting a target. up to 50% of this is added dependent on
                     ##proximity of hit to target's center
MISS_SCORE    = -1500

DEFAULT_HS    = [
                 ('Leonidas', 750000),
                 ('Yoda'    , 500000),
                 ('Wilhelm' , 350000),
                 ('Robin'   , 225000),
                 ('Caitlyn' , 150000),
                ]

SOUNDS        = {}

class Target(pg.sprite.Sprite):
    """Round-shaped target to kill"""
    maxrad = TARGET_RADIUS
    ttl    = TARGET_TTL
    diettl = 40
    preapp = TARGET_PREAPP
    
    def __init__(self, pos = (0, 0), group = None, buttons = (1, )):
        pg.sprite.Sprite.__init__(self, group)
        self.radius  = 0
        self.timer   = self.preapp
        self.pos     = pos
        self.on      = 0
        self.hit     = 0
        self.buttons = buttons

        if   buttons == (1, ):
            self.color = LMB_COLOR
            self.frcol = LMB_FRAMECLR
        elif buttons == (3, ):
            self.color = RMB_COLOR
            self.frcol = RMB_FRAMECLR

    def update(self):
        self.timer -= 1
        if not self.on:
            self.image = pg.Surface((1, 1))
            self.image.set_colorkey((0, 0, 0))
            self.rect  = self.image.get_rect()
            if self.timer <= 0:
                self.on = 1
                self.timer = self.ttl
        else:
            if not self.hit: 
                if self.timer <= 0:
                    self.kill()
                    pg.event.post(pg.event.Event(USEREVENT, code = 0))
                else:
                    t0 = self.ttl/2
                    t  = -abs(self.timer - t0) + t0

                    r = t*(self.maxrad - 3)/t0 + 3

                    image = pg.Surface((2*r + 1, 2*r + 1)).convert()
                    image.set_colorkey((0, 0, 0))

                    pg.draw.circle(image, self.color, (r + 1, r + 1), r)
                    pg.draw.circle(image, self.frcol, (r + 1, r + 1), r, 3)

                    rect = image.get_rect()
                    rect.center = self.pos

                    self.image  = image
                    self.rect   = rect
                    self.radius = r
            else:
                self.kill()
                pg.event.post(pg.event.Event(USEREVENT, code = 1, pos = self.pos, radius = self.radius, btn = self.buttons[0]))

    def mouseevent(self, pos, button):
        """Catch a mouseclick event and verify if the button is ok.
        Returns hit and score"""
        if not self.hit and button in self.buttons:
            x = self.pos[0] - pos[0]
            y = self.pos[1] - pos[1]
            
            hitrad = sqrt(x**2 + y**2)
            if hitrad <= self.radius:
                self.hit   = 1
                self.timer = self.diettl

                return 0, int(BASE_HITSCORE*(1.5 - 0.5*hitrad/self.maxrad))

        return 1, 0

def make_images(color):
    
    def lum(channel, step):
        out = channel + 10*step - 20
        if out < 0:
            out = 0
        if out > 255:
            out = 255
        return out
            
    images = []
        
    for i in xrange(5):
        color = tuple([lum(channel, i) for channel in color])
        image = pg.Surface((7, 7)).convert()
        image.set_colorkey((0, 0, 0))
        pg.draw.circle(image, color, (3, 3), 3)
        images.append(image)
        
    return images

class Particle(pg.sprite.Sprite):
    
    @classmethod
    def initimages(self):
        self.lmb_images = make_images(LMB_COLOR)
        self.rmb_images = make_images(RMB_COLOR)
        self.lmb_frame  = make_images(LMB_FRAMECLR)
        self.rmb_frame  = make_images(RMB_FRAMECLR)
    
    def __init__(self, pos, group, type, frame = False):
        pg.sprite.Sprite.__init__(self, group)
        if   type == 1:
            if not frame:
                image = self.lmb_images[rrange(5)].convert()
            else:
                image = self.lmb_frame[rrange(5)].convert()
        elif type == 3:
            if not frame:
                image = self.rmb_images[rrange(5)].convert()
            else:
                image = self.rmb_frame[rrange(5)].convert()
        self.image = image
        self.rect  = image.get_rect()
        self.rect.center = pos
        self.veloc = uniform(-0.5, 0.5), uniform(-0.5, 0.5)
        self.pos   = pos
        self.timer = 20
        self.alpha = 255
        
    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
        x, y = self.pos
        self.pos = x + self.veloc[0], y + self.veloc[1]

        self.rect.center = self.pos

        self.alpha = int(self.alpha * 0.85)
        self.image.set_alpha(self.alpha)

class Miss(pg.sprite.Sprite):
    ttl = 30
    def __init__(self, pos, group):
        pg.sprite.Sprite.__init__(self, group)
        image = pg.Surface((16, 16)).convert()
        image.set_colorkey((0, 0, 0))

        pointlist = [(0, 7), (5, 5), (7, 0), (9, 5),
                     (15, 7), (9, 9), (7, 15), (5, 9)]
        pg.draw.lines(image, (180, 180, 180), True, pointlist, 2)

        self.image = image
        self.rect  = image.get_rect()
        self.rect.center = pos

        self.timer = self.ttl

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

class Bg(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        image = pg.Surface((480, 480)).convert()

        image.fill(BG_COLOR)
        step  = BG_GRIDSTEP
        lines = 480/step
        color = BG_GRIDCOLOR
        for i in range(lines):
            pg.draw.line(image, color, (0, step/2 + i*step),
                         (480, step/2 + i*step))
            pg.draw.line(image, color, (step/2 + i*step, 0),
                         (step/2 + i*step, 480))

        self.image = image
        self.rect  = image.get_rect()

class FlyingText(pg.sprite.Sprite):
    font = pg.font.Font(FONTPATH, 12)
    ttl  = 30
    def __init__(self, pos, text, group):
        pg.sprite.Sprite.__init__(self, group)
        self.image = self.font.render(text, False, TEXT_COLOR, (0, 0, 0)).convert()
        self.image.set_colorkey((0, 0, 0))
        self.rect  = self.image.get_rect()
        self.rect.bottomleft = pos

        self.alpha = 255
        self.timer = self.ttl

    def update(self):
        if self.timer:
            self.timer -= 1
            
            self.rect = self.rect.move((1, -1))
            self.image.set_alpha(self.alpha)

            self.alpha -= 255/self.ttl
        else:
            self.kill()

class CenterText(pg.sprite.Sprite):
    font = pg.font.Font(FONTPATH, 22)
    ttl  = 140
    def __init__(self, text, group):
        pg.sprite.Sprite.__init__(self, group)
        self.image = self.font.render(text, False, TEXT_COLOR, (0, 0, 0)).convert()
        self.image.set_colorkey((0, 0, 0))
        self.rect  = self.image.get_rect()
        self.rect.center = 240, 240
        
        self.alpha = 0
        self.timer = self.ttl
        
    def update(self):
        if self.timer:
            self.timer -= 1
            
            self.image.set_alpha(self.alpha)
            
            if self.timer > 3*self.ttl/4:
                self.alpha += 255*4/self.ttl
            elif self.timer < self.ttl/4:
                self.alpha -= 255*4/self.ttl
                
        else:
            self.kill()
            
class PersistentText(pg.sprite.Sprite):
    font = pg.font.Font(FONTPATH, 22)
    fade = 30
    def __init__(self, text, group):
        pg.sprite.Sprite.__init__(self, group)
        self.image = self.font.render(text, False, TEXT_COLOR, (0, 0, 0)).convert()
        self.image.set_colorkey((0, 0, 0))
        self.rect  = self.image.get_rect()
        self.rect.center = 240, 240
        
        self.alpha = 0
        self.timer = self.fade
        self.dead  = 0
        
    def update(self):
        self.timer -= 1
        if not self.dead:
            if self.timer > 0:
                self.alpha += 255/self.fade
                self.image.set_alpha(self.alpha)
        elif self.dead:
            if self.timer > 0:
                self.alpha -= 255/self.fade
                self.image.set_alpha(self.alpha)
            elif self.timer <= 0:
                self.kill()
            
    def die(self):
        self.dead  = 1
        self.timer = self.fade

class Hud(pg.sprite.Sprite):
    
    class PropWidget(object):
        labelfont = pg.font.Font(FONTPATH, 12)
        valuefont = pg.font.Font(FONTPATH, 19)
        def __init__(self, label):
            image = pg.Surface((140, 34)).convert()
            image.set_colorkey((0, 0, 0))
            
            self.rect = image.get_rect()
            pg.draw.rect(image, HUD_LINECOLOR, self.rect, 1)
            pg.draw.line(image, HUD_LINECOLOR, (0, 13), (139, 13))
            
            fontsurf = self.labelfont.render(label, False, TEXT_COLOR).convert()
            fontrect = fontsurf.get_rect()
            fontrect.center = (70, 8)
            
            image.blit(fontsurf, fontrect)
            self.image = image
            
        def draw(self, value, target, topleft):
            fontsurf = self.valuefont.render(value, False, TEXT_COLOR, (0, 0, 0)).convert()
            fontrect = fontsurf.get_rect()
            fontrect.center = (70, 24)
            
            self.image.blit(fontsurf, fontrect)
            
            target.blit(self.image, topleft)
            
    class PropWidgetSmall(object):
        labelfont = pg.font.Font(FONTPATH, 12)
        valuefont = pg.font.Font(FONTPATH, 12)
        def __init__(self, label):
            image = pg.Surface((40, 25)).convert()
            image.set_colorkey((0, 0, 0))
            
            self.rect = image.get_rect()
            pg.draw.rect(image, HUD_LINECOLOR, self.rect, 1)
            pg.draw.line(image, HUD_LINECOLOR, (0, 12), (139, 12))
            
            fontsurf = self.labelfont.render(label, False, TEXT_COLOR).convert()
            fontrect = fontsurf.get_rect()
            fontrect.center = (20, 8)
            
            image.blit(fontsurf, fontrect)
            self.image = image
            
        def draw(self, value, target, topleft):
            fontsurf = self.valuefont.render(value, False, TEXT_COLOR, (0, 0, 0)).convert()
            fontrect = fontsurf.get_rect()
            fontrect.center = (20, 19)
            
            self.image.blit(fontsurf, fontrect)
            
            target.blit(self.image, topleft)
            
    class MissBoardWidget(object):
        labelfont = pg.font.Font(FONTPATH, 12)
        def __init__(self):
            image = pg.Surface((140, 40))
            image.set_colorkey((0, 0, 0))
            
            self.rect = image.get_rect()
            pg.draw.rect(image, HUD_LINECOLOR, self.rect, 1)
            pg.draw.line(image, HUD_LINECOLOR, (0, 13), (139, 13), 1)
            
            fontsurf = self.labelfont.render('Misses:', False, TEXT_COLOR).convert()
            fontrect = fontsurf.get_rect()
            fontrect.center = (70, 8)
            
            image.blit(fontsurf, fontrect)
            self.image = image
            
        def draw(self, value, target, topleft):
            for i in xrange(5):
                if value > i:
                    color = (200, 0, 0)
                else:
                    color = (10, 10, 10)
                pg.draw.circle(self.image, color, (18 + i*26, 27), 10)
                pg.draw.circle(self.image, HUD_LINECOLOR, (18 + i*26, 27), 10, 1)
                
            target.blit(self.image, topleft)
        
    class ScoreListWidget(object):
        labelfont = pg.font.Font(FONTPATH, 12)
        valuefont = pg.font.Font(FONTPATH, 13)
        def __init__(self):
            image = pg.Surface((140, 88)).convert()
            image.set_colorkey((0, 0, 0))
            
            self.rect = image.get_rect()
            pg.draw.rect(image, HUD_LINECOLOR, self.rect, 1)
            pg.draw.line(image, HUD_LINECOLOR, (0, 13), (139, 13), 1)
            
            fontsurf = self.labelfont.render('High Scores:', False, TEXT_COLOR).convert()
            fontrect = fontsurf.get_rect()
            fontrect.center = (70, 8)
            
            image.blit(fontsurf, fontrect)
            self.bimage = image
            
            self.hs = []
            
        def draw(self, value, target, topleft):
            
            if value != self.hs:
                self.hs    = value[:]
                self.image = self.bimage.copy()
                for i in xrange(len(value)):
                    name, score = value[i]
                    score = str(score).rjust(7)
                    if len(name) > 9:
                        name = name[0:9]
                    record = (name + ':').ljust(10) + score
                    
                    fontsurf = self.valuefont.render(record, False, TEXT_COLOR).convert()
                    fontrect = fontsurf.get_rect()
                    fontrect.center = (70, 22 + 14*i)
                    
                    self.image.blit(fontsurf, fontrect)
                    
            target.blit(self.image, topleft)

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((160, 480)).convert()
        self.image.fill(HUD_COLOR)
        self.rect  = self.image.get_rect()
        pg.draw.rect(self.image, HUD_LINECOLOR, self.rect, 1)
        self.rect.topleft = 480, 0
        
        self.scoreboard = self.PropWidget('Score:')
        self.timeboard  = self.PropWidget('Elapsed Time:')
        self.roundboard = self.PropWidget('Round Time:')
        
        self.hitboard   = self.PropWidgetSmall('Hit:')
        self.voidboard  = self.PropWidgetSmall('Miss:')
        self.accboard   = self.PropWidgetSmall('Acc:')
        
        self.highscores = self.ScoreListWidget()
        self.missboard  = self.MissBoardWidget()
        
        if DRAW_FPS:
            self.fps = self.PropWidgetSmall('FPS:')
        
    def update(self, misses, ticks, score, highscores, hits, voidhits, cur_fps):
        self.image.fill((60, 60, 60))
        pg.draw.rect(self.image, HUD_LINECOLOR, self.image.get_rect(), 3)
        
        strscore = str(score).zfill(7)
        self.scoreboard.draw(strscore, self.image, (10, 355))
        
        fps = FPS
        
        eltime      = ticks/fps
        elapsed_str = str(eltime/60).zfill(2) + '.' + str(eltime%60).zfill(2)
        self.timeboard.draw(elapsed_str, self.image, (10, 435))
        
        round_length = ROUND_LENGTH * fps
        rtime        = (round_length - ticks%round_length - 1)/fps
        round_str   = str(rtime/60).zfill(2) + '.' + str(rtime%60 + 1).zfill(2)
        self.roundboard.draw(round_str, self.image, (10, 395))
        
        self.hitboard.draw(str(hits).rjust(4), self.image, (10, 110))
        self.voidboard.draw(str(voidhits).rjust(4), self.image, (60, 110))
        if hits + voidhits:
            fh = float(hits)
            fm = float(voidhits)
            acc = str(int((fh/(fh + fm))*100)).rjust(3) + '%'
        else:
            acc = '100%'
        self.accboard.draw(acc, self.image, (110, 110))
        
        self.highscores.draw(highscores, self.image, (10, 10))
        
        self.missboard.draw(misses, self.image, (10, 145))
        
        if DRAW_FPS:
            self.fps.draw(str(cur_fps), self.image, (60, 320))

class Cursor(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        image = pg.Surface((17, 17)).convert()
        self.rect  = image.get_rect()
        self.pos   = (240, 240)
        
        image.set_colorkey((0, 0, 0))
        image.set_alpha(180)
        
        pg.draw.line(image, (10, 10, 10), (1, 8), (16, 8), 2)
        pg.draw.line(image, (10, 10, 10), (8, 1), (8, 16), 2)
        pg.draw.line(image, (240, 240, 240), (0, 8), (17, 8), 1)
        pg.draw.line(image, (240, 240, 240), (8, 0), (8, 17), 1)
        
        self.image = image
        
    def update(self):
        self.pos = pg.mouse.get_pos()
        self.rect.center = self.pos

def spawner(targets, stage):
    n_targets = stage + FIRST_STAGE
    if len(targets.sprites()) < n_targets:
        rnum = rrange(100)
        try:
            rmb_prob = RMB_PROB[stage]
        except IndexError:
            rmb_prob = RMB_PROB[len(RMB_PROB)-1]
        if rnum >= rmb_prob:
            buttons = (1, )
        else:
            buttons = (3, )
        Target((rrange(0 + TARGET_RADIUS, 480 - TARGET_RADIUS),
               rrange(0 + TARGET_RADIUS, 480 - TARGET_RADIUS)),
               targets, buttons)

def update_highscores(score, highscores):
    name = get_username()
    highscores.append((name, score))
    highscores.sort(hscmp)
    
    path = join(DATAPATH, 'highscore.dat')
    with open(path, 'w+') as f:
        for record in highscores[:5]:
            f.write(record[0] + '=' + str(record[1]) + '\n')

def read_highscores():
    path = join(DATAPATH, 'highscore.dat')
    try:
        with open(path) as f:
            scores = []
            for record in f.readlines():
                delim = record.find('=')
                if delim == -1:
                    raise IOError
                name  = record[:delim]
                try:
                    value = int(record[delim + 1:])
                except ValueError:
                    raise IOError
                scores.append((name, value))
            if len(scores) != 5:
                raise IOError
            return scores
    except IOError:
        print 'Error loading highscore.dat, rebuilding'
        with open(path, 'w+') as f:
            for record in DEFAULT_HS:
                f.write(record[0] + '=' + str(record[1]) + '\n')
        return DEFAULT_HS

def get_username():
    if os.name == 'nt':
        return os.getenv('USERNAME', 'Player')
    elif os.name in ('mac', 'posix'):
        return os.getenv('LOGNAME', 'Player')
    else:
        return 'Player'
        
def hscmp(x, y):
    if   x[1] < y[1]:
        return 1
    elif x[1] > y[1]:
        return -1
    elif x[1] == y[1]:
        return 0

def spawn_particles(pos, radius, group, type):
    for i in xrange(2*radius):
        for j in xrange(2*radius):
            if not i%4 and not j%4:
                if sqrt((i-radius)**2 + (j-radius)**2) < radius:
                    Particle((pos[0] - radius + i, pos[1] - radius + j), group, type)
                    if sqrt((i-radius)**2 + (j-radius)**2) > radius - 3:
                        Particle((pos[0] - radius + i, pos[1] - radius + j), group, type, True)

def main():
    if SOUND:
        pg.mixer.pre_init(44100, -16, 4, 1024)
    pg.init()
    screen = pg.display.set_mode((640, 480))
    pg.display.set_caption('pyReflex')
    pg.mouse.set_visible(False)

    Particle.initimages()
    
    if SOUND:
        pg.mixer.music.load(join(DATAPATH, 'loop.wav'))
        pg.mixer.music.play(-1)
    
        SOUNDS = {
            'hit' : pg.mixer.Sound(join(DATAPATH, 'hit.wav')),
            'miss': pg.mixer.Sound(join(DATAPATH, 'miss.wav')),
            'warp': pg.mixer.Sound(join(DATAPATH, 'warp.wav'))
            }

    clock  = pg.time.Clock()
    bg     = pg.sprite.GroupSingle(Bg())
    hud    = pg.sprite.GroupSingle(Hud())
    cursor = pg.sprite.GroupSingle(Cursor())

    quit_prompt  = 0
    round_length = ROUND_LENGTH * FPS
    
    newgame_prompt = 0
    game_over      = 0
    ticks          = 0
    stage          = 0
    misses         = 0
    score          = 0
    hits           = 0
    voidhits       = 0
    
    while not quit_prompt: ##GAME LOOP
        
        highscores = read_highscores()
        
        targets = pg.sprite.RenderPlain()
        decal   = pg.sprite.RenderPlain()
        texts   = pg.sprite.RenderPlain()
        parts   = pg.sprite.RenderPlain()
        
        if 1:
            buttonpressed = 0
            centertext = PersistentText('CLICK TO START', texts)
            while not (buttonpressed or quit_prompt): ##MINI-LOOP FOR START
                for event in pg.event.get():
                    if event.type == MOUSEBUTTONDOWN:
                        buttonpressed = 1
                        centertext.die()
                    elif event.type == QUIT:
                        quit_prompt = 1
                        break
                    elif event.type == KEYDOWN and event.key == K_ESCAPE:
                        quit_prompt = 1
                        break
                
                texts.update()
                cursor.update()
                hud.update(misses, ticks, score, highscores, hits, voidhits, 60)
                bg.draw(screen)
                hud.draw(screen)
                texts.draw(screen)
                cursor.draw(screen)
                
                pg.display.flip()
                
        newgame_prompt = 0
        game_over      = 0
        ticks          = 0
        stage          = 0
        misses         = 0
        score          = 0
        hits           = 0
        voidhits       = 0
        
        CenterText('ROUND 1', texts)
        if SOUND:
            SOUNDS['warp'].play()
    
        while not (quit_prompt or newgame_prompt): ##GAME INSTANCE LOOP
            clock.tick(FPS)
            ticks += 1

            if not (ticks%round_length or game_over):
                stage += 1
                misses = 0
                CenterText('ROUND ' + str(stage + 1), texts)
                if SOUND:
                    SOUNDS['warp'].play()
            
            for event in pg.event.get():
                if event.type == QUIT:
                    quit_prompt = 1
                    break
                elif event.type == MOUSEBUTTONDOWN and not game_over and event.pos < (480, 480):
                    missed = 1
                    for target in targets.sprites():
                        missed, scoreadd = target.mouseevent(event.pos, event.button)
                        if not missed:
                            FlyingText(event.pos, str(scoreadd), texts)
                            score += scoreadd
                            hits  += 1
                            if SOUND:
                                SOUNDS['hit'].play()
                            break
                    if missed:
                        Miss(event.pos, decal)
                        scoreadd = MISS_SCORE
                        score    += scoreadd
                        voidhits += 1
                        if SOUND:
                            SOUNDS['miss'].play()
                        FlyingText(event.pos, str(scoreadd), texts)
                elif event.type == KEYDOWN and event.key == K_n:
                    newgame_prompt = 1
                    break
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    quit_prompt = 1
                    break
                elif event.type == USEREVENT and event.code == 0:
                    misses += 1
                elif event.type == USEREVENT and event.code == 1:
                    spawn_particles(event.pos, event.radius, parts, event.btn)

            if misses >= MAX_MISSES and not game_over:
                game_over = ticks
                PersistentText('GAME OVER', texts)
                if SOUND:
                    SOUNDS['warp'].play()

            if not game_over:
                spawner(targets, stage)
            
            if game_over and ticks > game_over + 100:
                newgame_prompt = 1

            targets.update()
            cursor.update()
            decal.update()
            texts.update()
            parts.update()
            
            hud.update(misses, ticks, score, highscores, hits, voidhits, int(clock.get_fps()))

            ##RENDERING
            bg.draw(screen)
            decal.draw(screen)
            parts.draw(screen)
            targets.draw(screen)
            hud.draw(screen)
            texts.draw(screen)
            cursor.draw(screen)

            pg.display.flip()
            ##RENDERING END
            
        update_highscores(score, highscores)
            
    pg.quit()

if __name__ == "__main__":
    main()
