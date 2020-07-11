import os
import os.path as p
import pygame
from random import randint
import copy

import pdb

level_list=[
    p.join("resources", "level_1.bmp"),
    p.join("resources", "level_2.bmp")]
current_level = 0

object_dict = {obj_id:None for obj_id in range(0, 300)}

class PygView(object):

    def __init__(self, width=640*2+1, height=480*2+1, fps=30):
        pygame.init()
        pygame.display.set_caption("ESC to quit")
        self.pix_width = width
        self.pix_height = height
        self.screen = pygame.display.set_mode((self.pix_width, self.pix_height), pygame.DOUBLEBUF)
        self.surface = pygame.Surface(self.screen.get_size()).convert()
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.playtime = 0.0
        self.font = pygame.font.SysFont("mono", 20, bold=True)
        
        self.load_level(level_list[current_level])
            
    def load_level(self, filepath):
        global object_dict
        object_dict = {obj_id:None for obj_id in range(0, 300)}
        current_id = 1
        level_surf = pygame.image.load(filepath)
        self.grid = Grid(self.surface, self.pix_width, self.pix_height)
        for x in range(level_surf.get_width()):
            for y in range(level_surf.get_height()):
                pixel = level_surf.get_at((x,y))
                if pixel == pygame.Color("#000000"):
                    Wall(
                        self.grid,
                        Position(x,y),
                        current_id,
                        self.surface)
                    current_id += 1
                elif pixel.r == 255 and pixel.b == 255 and pixel != pygame.Color("#FFFFFF"):
                    Player(
                        self.grid,
                        Position(x,y),
                        current_id,
                        self.surface,
                        active_at_start = pixel.b > 0)
                    if pixel.b > 0:
                        self.grid.current_player = current_id
                    current_id += 1
                elif pixel == pygame.Color("#FFFF00"):
                    Goal(
                        self.grid,
                        Position(x,y),
                        current_id,
                        self.surface)
                    current_id += 1
                elif pixel.g == 255 and pixel != pygame.Color("#FFFFFF"):
                    Reciever(
                        self.grid,
                        Position(x, y),
                        current_id,
                        self.surface,
                        None,
                        pixel.b, pixel.b,
                        Position(pixel.b//2, pixel.b//2))
                    current_id += 1
                    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:    
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.load_level(level_list[current_level])
                    elif event.key == pygame.K_p:
                        pdb.set_trace()
                    elif event.key == pygame.K_LSHIFT:
                        self.grid.shift_players()
                    else:
                        self.step(event)

            for updateable in object_dict.values():
                if "update" in dir(updateable):
                    updateable.update()
            pygame.display.flip()
            self.screen.blit(self.surface, (0,0))
            for drawable in object_dict.values():
                if "draw" in dir(drawable):
                    drawable.draw()

        pygame.quit()
        
    def step(self, event):
        # For every reciever in the field, send the signal corresponding to the pressed button
        for reciever in object_dict.values():
            if type(reciever)==Reciever:
                if reciever.is_active:
                    if event.key == pygame.K_w:
                        reciever.signal('up')
                    if event.key == pygame.K_s:
                        reciever.signal('down')
                    if event.key == pygame.K_a:
                        reciever.signal('left')
                    if event.key == pygame.K_d:
                        reciever.signal('right')
                        
        # Reset every player command_recieved state
        for thing in object_dict.values():
            if issubclass(type(thing),GridEntity):
                thing.has_moved_this_turn = False
            if type(thing) == Player:
                thing.command_recieved = False
                

class Position:
    """An x,y location in the grid. 0,0 is tl corner"""
    def __init__(self,x,y):
        self.x = x
        self.y = y


class Grid:
    """A grid for every object to move around on"""
    def __init__(self, parent_surface, canvas_x, canvas_y, resolution = 40):
        self.obj_id = 0
        self.pix_width = canvas_x
        self.pix_height = canvas_y
        self.res = resolution
        self.parent_surface = parent_surface
        self.width = canvas_x//resolution
        self.height = canvas_y//resolution
        self.init_grid(self.width, self.height)
        self.surface = pygame.Surface((canvas_x, canvas_y))
        global object_dict
        object_dict[self.obj_id] = self
        self.current_player = 0
        
    def init_grid(self,x,y):
        self.grid = [[0 for n in range(y)] for m in range(x)]
        
    def request_move(self, requester_id, direction):
        """Processes requests to move udlr on grid. Passes the request on to anything
        that might be bothers (other pushables in the way, that sort of thing).
        Returns 0 if move is successful, 1 if oob move attempted, 2 if obstacle hit"""
        requester = object_dict[requester_id]
        if requester.has_moved_this_turn:
            print(f"ID {requester_id} has moved already, skipping second move")
            return 5
        req_pos = copy.copy(requester.pos)
        new_pos = copy.copy(req_pos)
        if direction.startswith('l'):
            new_pos.x -= 1
        elif direction.startswith('r'):
            new_pos.x += 1
        elif direction.startswith('u'):
            new_pos.y -= 1
        elif direction.startswith('d'):
            new_pos.y += 1
            
        if new_pos.x < 0 or new_pos.x >= self.width or new_pos.y < 0 or new_pos.y >= self.height:
            print("ID {} out of bounds move attempted".format(requester_id))
            return 1

        obj_at_new_pos = object_dict[self.grid[new_pos.x][new_pos.y]]
        
        if type(obj_at_new_pos) == Goal:
            print("You won! Push backspace to move onto the next level.")
            global current_level
            current_level += 1
        if type(obj_at_new_pos) == Wall:
            print("ID {} hit wall ID {} at {},{}".format(requester_id, obj_at_new_pos.obj_id, new_pos.x, new_pos.y))
            return 2
        if issubclass(type(obj_at_new_pos), Pushable):
            is_blocked = obj_at_new_pos.move(direction)
            if is_blocked:
                print(f"ID {requester_id} blocked by immovable mover {obj_at_new_pos} at {new_pos.x}, {new_pos.y}")
                return 4
                
        requester.set_new_position(new_pos)
        requester.has_moved_this_turn = True
        return 0

        
    def shift_players(self):
        object_dict[self.current_player].active = False
        self.current_player += 1
        self.current_player = self.current_player % 300
        while type(object_dict[self.current_player]) is not Player:
            self.current_player += 1
            self.current_player = self.current_player % 300
        object_dict[self.current_player].active = True
        
    
    # Drawing methods    
    def draw_grid(self):
        # Draw background
        pygame.draw.rect(
            self.surface,
            pygame.Color(0,0,0),
            pygame.Rect(0,0,self.pix_width, self.pix_height))
        # Draw horizontal lines
        for y in range(0, self.pix_height, self.res):
            pygame.draw.line(
                self.surface,
                pygame.Color("#B687FF"),
                (0, y),
                (self.pix_width, y))
        #Draw vertial lines
        for x in range (0, self.pix_width, self.res):
            pygame.draw.line(
                self.surface,
                pygame.Color("#B687FF"),
                (x, 0),
                (x, self.pix_height))
        self.surface.convert()
        
    def get_screen_position(self,grid_pos):
        """Get tl position on screen from grid"""
        x = self.res * grid_pos.x
        y = self.res * grid_pos.y
        return Position(x,y)
        
    def draw(self):
        """Draws every sprite in the grid"""
        #draw the grid for debug
        self.draw_grid()
        self.parent_surface.blit(self.surface, (0, 0))
        
     
class GridEntity(object):
    """Contains methods for objects that exist on the grid. Should be abstract."""
    def __init__(self, grid, position, obj_id, parent_surface):
        global object_dict
        self.grid = grid
        self.obj_id = obj_id
        self.pos = position
        self.grid.grid[position.x][position.y] = self.obj_id
        self.parent_surface = parent_surface
        object_dict[self.obj_id] = self
        self.surface = pygame.Surface((self.grid.res, self.grid.res))
        self.gen_sprite()
        self.standing_in = None
        self.has_moved_this_turn = False
        
    def gen_sprite(self):
        '''Abstract method; should be overridden by children'''
        pass
        
    def move(self, direction):
        return self.grid.request_move(self.obj_id, direction)
        self.has_moved_this_turn = True
            
    def set_new_position(self, new_pos):
        self.grid.grid[new_pos.x][new_pos.y] = self.obj_id
        self.grid.grid[self.pos.x][self.pos.y] = 0
        self.pos = new_pos
        
    def draw(self):
        screen_pos = self.grid.get_screen_position(self.pos)
        self.parent_surface.blit(self.surface, (screen_pos.x, screen_pos.y))
 
        
class Wall(GridEntity):
    """Walls block all movement"""
    def __init__(self, grid, position, obj_id, parent_surface):
        GridEntity.__init__(self, grid, position, obj_id, parent_surface)
        
    def gen_sprite(self):
        pygame.draw.rect(
            self.surface,
            pygame.Color("#A2A2A2"),
            pygame.Rect(2, 2, self.grid.res -4, self.grid.res-4))
        self.surface.convert()
        
        
class Goal(Wall):
    def __init__(self, grid, position, obj_id, parent_surface):
        GridEntity.__init__(self, grid, position, obj_id, parent_surface)
        
    def gen_sprite(self):
        pygame.draw.rect(
            self.surface,
            pygame.Color("#FFFF00"),
            pygame.Rect(2, 2, self.grid.res -4, self.grid.res-4))
        self.surface.convert()   
        
        
class Trench(GridEntity):
    """Trenches block pushables, but players can stand in them"""
    # DUMMIED OUT FOR NOW
    def __init__(self, grid, position, obj_id, parent_surface):
        GridEntity.__init__(self, grid, position, obj_id, parent_surface)
        self.standing_in = False
    
    def gen_sprite(self):
        pygame.draw.rect(
            self.surface,
            pygame.Color("#682430"),
            pygame.Rect(2, 2, self.grid.res -4, self.grid.res-4))
        self.surface.convert()
        
      
class Pushable(GridEntity):
    def __init__(self, grid, position, obj_id, parent_surface):
        GridEntity.__init__(self, grid, position, obj_id, parent_surface)
        
    def gen_sprite(self):
        pygame.draw.rect(
            self.surface,
            pygame.Color("#00EAF6"),
            pygame.Rect(5, 5, self.grid.res -10, self.grid.res-10))
        self.surface.convert()  
        

class Player(Pushable):
    
    def __init__(self, grid, position, obj_id, parent_surface, active_at_start = False):
        GridEntity.__init__(self, grid, position, obj_id, parent_surface)
        self.command_recieved = False
        self.active = active_at_start
        
    def gen_sprite(self):
        self.surface = pygame.image.load(p.join("resources","myguy.bmp"))
        self.surface = pygame.transform.scale(self.surface, (self.grid.res, self.grid.res))
        self.surface.convert_alpha()
        self.is_selected_surface = pygame.Surface((self.grid.res, self.grid.res))
        pygame.draw.rect(
            self.is_selected_surface,
            pygame.Color("#FFFF00"),
            pygame.Rect(5, 5, self.grid.res -10, self.grid.res-10))
        self.is_selected_surface.set_alpha(25)
        
    def draw(self):
        if self.active:
            self.is_selected_surface.set_alpha(25)
        else:
            self.is_selected_surface.set_alpha(0)
        self.surface.blit(self.is_selected_surface, (0,0))
        GridEntity.draw(self)
                
                        
class Reciever(Pushable):
    def __init__(self, grid, position, obj_id, parent_surface,
                commands, field_width, field_height, pos_in_field):
        Pushable.__init__(self, grid, position, obj_id, parent_surface)
        self.field_surface = pygame.Surface(
            (self.grid.res * field_width, 
             self.grid.res * field_height))
        self.commands = commands
        field_ul_x = self.pos.x - pos_in_field.x
        field_ul_y = self.pos.y - pos_in_field.y
        self.field = pygame.Rect(field_ul_x, field_ul_y, field_width, field_height)
        self.pos_in_field = pos_in_field
        self.is_active = True
        
    def gen_sprite(self):
        # Draw a cross
        pygame.draw.line(
            self.surface,
            pygame.Color("#FFFFFF"),
            (6,6),
            (self.grid.res-6, self.grid.res-6))
        pygame.draw.line(
            self.surface,
            pygame.Color("#FFFFFF"),
            (6, self.grid.res - 6),
            (self.grid.res - 6, 6))
        self.surface.convert()
        
    def move(self, direction):
        blocked = Pushable.move(self, direction)
        if not blocked:
            # Drag field with it
            if direction.startswith('l'):
                self.field = self.field.move(-1,0)
            elif direction.startswith('r'):
                self.field = self.field.move(1,0)
            elif direction.startswith('u'):
                self.field = self.field.move(0,-1)
            elif direction.startswith('d'):
                self.field = self.field.move(0,1)
        return blocked
            
    def signal(self, command):
        # Sends a command to every player in this reciever's field
        for player in object_dict.values():
            if type(player)==Player:
                if self.field.collidepoint(player.pos.x, player.pos.y) \
                and player.active:
                    if command in ['up', 'down', 'left', 'right']:
                        player.move(command)
                        player.command_recieved = True
                    if command == "switch":
                        self.grid.shift_players()
    
    def draw_field(self):
        pygame.draw.rect(
            self.field_surface,
            pygame.Color("#00FF00"),
            pygame.Rect(0,0,self.grid.res * self.field.width, self.grid.res * self.field.height))
        self.field_surface.set_alpha(50)
        field_ul = Position(self.pos.x - self.pos_in_field.x, self.pos.y - self.pos_in_field.y)
        screen_pos = self.grid.get_screen_position(field_ul)
        self.parent_surface.blit(self.field_surface, (screen_pos.x, screen_pos.y))
        
    def draw(self):
        Pushable.draw(self)
        self.draw_field()

if __name__ == "__main__":
    PygView().run()
    
    
    
    
