import pygame
import neat
import time
import os
import random
pygame.font.init()
WIN_WIDTH = 500
WIN_HEIGHT = 800
gen = 0
clock = pygame.time.Clock()
Quit = False
STAT_FONT = pygame.font.SysFont("comicsans", 30)

gameDisplay = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
def pygameImage(img):
    x = pygame.transform.scale2x(pygame.image.load(os.path.join('FB', img)))
    return x
BG = pygameImage('bg.png')
class Bird:
    BIRD_IMG = [pygameImage('bird1.png'), pygameImage('bird2.png'), pygameImage('bird3.png')]
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.height = y
        self.vel = 0
        self.img = Bird.BIRD_IMG[0]
        self.img_show_duration = 0
        self.tick_count = 0

    def jump(self):
        self.height = self.y
        self.vel = -10
        self.tick_count = 0

    def move(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 0.5 * 3 *(self.tick_count**2)

        if d >= 16:
            d = 16

        self.y = int(self.y + d)


    def draw(self, win):
        win.blit(self.img, (self.x,self.y))

    def get_mask(self):
        return pygame.mask.from_surface(self.img)
class Pipe:
    PIPE_IMG = pygameImage('pipe.png')
    GAP = 200
    def __init__(self, x):
        self.x = x
        self.TOP = pygame.transform.flip(Pipe.PIPE_IMG, False, True)
        self.BOTTOM = Pipe.PIPE_IMG
        self.h = random.randint(100, 500)
        self.y1 = self.h - self.TOP.get_height()
        self.y2 = self.h + Pipe.GAP
        self.velocity = 10

        self.passed = False


    def move(self):
        self.x = self.x - self.velocity

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_pipe_mask = pygame.mask.from_surface(self.TOP)
        bottom_pipe_mask = pygame.mask.from_surface(self.BOTTOM)

        top_offset = (self.x - bird.x, self.y1 - bird.y)
        bottom_offset = (self.x - bird.x, self.y2 - bird.y)

        if bird_mask.overlap(top_pipe_mask,top_offset) or bird_mask.overlap(bottom_pipe_mask,bottom_offset):
            return True
        return False


    def draw(self,win):
        win.blit(self.TOP, (self.x,self.y1))
        win.blit(self.BOTTOM, (self.x,self.y2))

class Base:
    BASE_IMG = pygameImage('base.png')

    def __init__(self):
        self.x1 = 0
        self.x2 = WIN_WIDTH
        self.velocity = 10

    def move(self):
        self.x1 = self.x1 - self.velocity
        self.x2 = self.x2 - self.velocity
        if self.x1 + WIN_WIDTH < 0:
            self.x1 = 0
            self.x2 = WIN_WIDTH

    def draw(self,win):
        win.blit(Base.BASE_IMG,(self.x1,730))
        win.blit(Base.BASE_IMG,(self.x2,730))
def draw(win, birds, pipes, base, gen, score):
    gameDisplay.blit(BG, (0, 0))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    for pipe in pipes:
        pipe.draw(win)
    score_label = STAT_FONT.render("Gens: " + str(gen), 1, (255, 255, 255))
    win.blit(score_label, (10, 10))

    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH-150, 10))

def run():
    global Quit
    base = Base()
    bird = Bird(250,350)
    pipes = [Pipe(600)]


    while not Quit:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(event)
                Quit = True

        base.move()
        rm = []
        add_pipe = False
        for pipe in pipes:
            if pipe.x + pipe.TOP.get_width() < 0:
                rm.append(pipe)
            elif not pipe.passed and bird.x + bird.img.get_width() > pipe.x + pipe.TOP.get_width():
                pipe.passed = True
                add_pipe = True
            pipe.move()


        for r in rm:
            pipes.remove(r)

        if add_pipe:
            pipes.append(Pipe(600))

        draw(gameDisplay,bird,pipes,base)
        pygame.display.update()

    pygame.quit()
    quit()

def fitness(genomes,config):
    global Quit,gen
    gen += 1
    score = 0

    birds = []
    nets = []
    ge = []

    for _, g in genomes:
        nets.append(neat.nn.FeedForwardNetwork.create(g,config))
        g.fitness = 0
        ge.append(g)
        birds.append(Bird(230,350))

    base = Base()
    pipes = [Pipe(700)]

    while not Quit:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                Quit = True

        pipe_index = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].TOP.get_width():
                pipe_index = 1
        else:
            break

        for index, bird in enumerate(birds):
            bird.move()
            ge[index].fitness += 0.1
            output = nets[index].activate((bird.y, abs(pipes[pipe_index].h - bird.y),abs(pipes[pipe_index].y2-bird.y)))
            if output[0] > 0.5:
                bird.jump()

        rm = []
        add_pipe = False
        for pipe in pipes:
            for index, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[index].fitness -= 1
                    birds.pop(index)
                    nets.pop(index)
                    ge.pop(index)

                elif not pipe.passed and bird.x + bird.img.get_width() > pipe.x + pipe.TOP.get_width():
                    pipe.passed = True
                    score += 1
                    add_pipe = True

            if pipe.x + pipe.TOP.get_width() < 0:
                rm.append(pipe)

            pipe.move()


        for r in rm:
            pipes.remove(r)

        if add_pipe:
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(700))

        for index, bird in enumerate(birds):
            if bird.y + bird.img.get_height() > 730 or bird.y < 0:
                birds.pop(index)
                nets.pop(index)
                ge.pop(index)

        base.move()
        draw(gameDisplay,birds,pipes,base,gen,score)
        pygame.display.update()



if __name__ == '__main__':
    configPath = os.path.join(os.getcwd(),'config-feedforward.txt')

    # config = neat.config.Config(neat.DefaultGenome,neat.DefaultSpeciesSet,neat.DefaultStagnation,neat.DefaultReproduction,configPath)

    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                configPath)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(fitness, 50)
    # run()