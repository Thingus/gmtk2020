import pygame
import numpy

object_dict = {obj_id:None for obj_id in range(0, 300)} 

class PygView(object):

    def __init__(self, width=641, height=481, fps=30):
        pygame.init()
        pygame.display.set_caption("ESC to quit")
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.surface = pygame.Surface(self.screen.get_size()).convert()
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.playtime = 0.0
        self.font = pygame.font.SysFont("mono", 20, bold=True)

        grid = Grid(self.surface, width, height)

    def run(self):
        running = True
        while running:
            for updateable in object_dict.values():
                if "update" in dir(updateable):
                    updateable.update()
            pygame.display.flip()
            self.screen.blit(self.surface, (0,0))
            for drawable in object_dict.values():
                if "draw" in dir(drawable):
                    drawable.draw()
        pygame.quit()


class Grid:
    """A grid for every object to move around on"""
    def __init__(self, parent_surface, canvas_x, canvas_y, resolution = 20):
        self.id = 0
        self.width = canvas_x
        self.height = canvas_y
        self.res = resolution
        self.parent_surface = parent_surface
        grid = numpy.ndarray((canvas_x//resolution, canvas_y//resolution))
        self.surface = pygame.Surface((canvas_x, canvas_y))
        global object_dict
        object_dict[self.id] = self
        
    def draw_grid(self):
        # Draw background
        pygame.draw.rect(
            self.surface,
            pygame.Color(0,0,0),
            pygame.Rect(0,0,self.width, self.height))
        # Draw horizontal lines
        for y in range(0, self.height, self.res):
            pygame.draw.line(
                self.surface,
                pygame.Color("#B687FF"),
                (0, y),
                (self.width, y))
        #Draw vertial lines
        for x in range (0, self.width, self.res):
            pygame.draw.line(
                self.surface,
                pygame.Color("#B687FF"),
                (x, 0),
                (x, self.height))
        self.surface.convert()
    
    def draw(self):
        """Draws every sprite in the grid"""
        #draw the grid for debug
        self.draw_grid()
        self.parent_surface.blit(self.surface, (0, 0))
        
        
class Player(object):
    
    def __init__(self, grid, position):
        self.grid = grid
        #grid.set

if __name__ == "__main__":
    PygView().run()
