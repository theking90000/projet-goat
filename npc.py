import pyglet
import numpy as np
from worldsprite import WorldSprite
from player import Bullet
from inventory import Weapon, WEAPON_MODELS
import astar


NPC_IMAGES = (pyglet.image.load("img/mec.png"),)
NPC_CARS = (pyglet.image.load("img/van.png"),)


class NpcWalker:
    def __init__(self, x, y, health, npctype, weapon, incar, batch):
        self.x = x
        self.y = y
        self.npctype = npctype
        self.sprite = WorldSprite(batch=batch, img=NPC_IMAGES[0], x=0, y=0)
        self.objective = self.get_objective() # INTEGRER COORDONNÉES D'UNE VILLE SUR LA MAP
        self.stress = 0
        self.speed_objective = 90
        self.health = health
        self.weapon = weapon
        self.incar = incar
        self.last_shot = 0
        self.time_since_load = 0
        self.batch = batch

    def get_objective(self):
        return (20000, -6000)

    def check_bullet_hit(self, bullet):
        if self.x < bullet.pos_x < self.x+32:
            if self.y < bullet.pos_y < self.y+32:
                self.health -= bullet.damage
                self.stress += 1

    def grid_cos_to_pixel(self, grid_x, grid_y, cam_x, cam_y):
        return (256*grid_x) + cam_x - (14*256), (256*grid_y) + cam_y - (15*256)

    def pixel_to_grid_cos(self, x, y, cam_x, cam_y):
        return int((x//256) - (cam_x//256)) + 14, int((y//256) - (cam_y//256)) + 15

    def find_grid_side_from_dir(self, x, y, cam_x, cam_y, dir_x, dir_y):
        pos_x, pos_y = x+dir_x, y+dir_y
        while 1:
            pos_x += dir_x
            pos_y += dir_y
            grid_x, grid_y = self.pixel_to_grid_cos(pos_x, pos_y, cam_x, cam_y)
            if 0 <= grid_x < 30 and 0 <= grid_y < 30:
                continue
            else:
                return self.pixel_to_grid_cos(pos_x-dir_x, pos_y-dir_y, cam_x, cam_y)
        return None

    def get_mov_from_dir(self, dir_x, dir_y, delta_t):
        mov_x, mov_y = dir_x, dir_y
        match(self.npctype):
            case 0:
                self.speed_objective = 90
                if self.stress > 1:
                    self.speed_objective = 180
                mov_x *= self.speed_objective*delta_t
                mov_y *= self.speed_objective*delta_t
            case 2:
                self.speed_objective = 90
                if self.stress > 1:
                    self.speed_objective = 180
                mov_x *= self.speed_objective*delta_t
                mov_y *= self.speed_objective*delta_t
        return mov_x, mov_y

    def get_mov_to_point(self, x2, y2, obstacle_map, cam_x, cam_y, delta_t):
        dir_x, dir_y = x2-self.x, y2-self.y
        dir_inten = np.sqrt(dir_x**2+dir_y**2)
        dir_x, dir_y = dir_x/dir_inten, dir_y/dir_inten
        mov_x, mov_y = self.get_mov_from_dir(dir_x, dir_y, delta_t)
        grid_x, grid_y = self.pixel_to_grid_cos(self.x+mov_x, self.y+mov_y, cam_x, cam_y)
        #print(grid_x, grid_y)
        if not obstacle_map[grid_x][grid_y]:
            return mov_x, mov_y
        grid_x2, grid_y2 = self.find_grid_side_from_dir(self.x, self.y, cam_x, cam_y, dir_x, dir_y)
        cell0, cell1 = astar.get_last_two_cells(astar.find_path(obstacle_map, grid_x, grid_y, grid_x2, grid_y2))
        dest_x1, dest_y1 = self.pixel_to_grid_cos(cell0.x, cell0.y, cam_x, cam_y)
        dest_x2, dest_y2 = self.pixel_to_grid_cos(cell1.x, cell1.y, cam_x, cam_y)
        dir_x, dir_y = dest_x2-dest_x1, dest_y2
        dir_inten = np.sqrt(dir_x**2+dir_y**2)
        dir_x, dir_y = dir_x/dir_inten, dir_y/dir_inten
        mov_x, mov_y = self.get_mov_from_dir(dir_x, dir_y, delta_t)
        return mov_x, mov_y

    def update_sprite(self, cam_x, cam_y):
        self.sprite.set_relative_pos(self.x, self.y, cam_x, cam_y)
    
    def get_distance_to_player(self, player_x, player_y):
        dist_x = self.x-player_x
        dist_y = self.y-player_y
        return np.sqrt(dist_x**2 + dist_y**2)

    def weapon_update(self, player_x, player_y, delta_t):
        self.last_shot += delta_t
        self.time_since_load += delta_t
        if self.weapon == None:
            return None
        if self.weapon.loaded <= 0:
            if self.time_since_load > self.weapon.loadtime:
                self.weapon.loaded = self.weapon.capacity
                if self.weapon.loaded > 0:
                    self.time_since_load = 0
            return None
        if self.time_since_load < self.weapon.loadtime:
            return None
        if self.last_shot > 1/self.weapon.rate:
            self.last_shot = 0
            self.weapon.loaded -= 1
            dir_x, dir_y = player_x-self.x, player_y-self.y
            dir_inten = np.sqrt(dir_x**2+dir_y**2)
            dir_x, dir_y = dir_x/dir_inten, dir_y/dir_inten
            return Bullet(self.x, self.y, dir_x, dir_y, self.weapon.reach, self.weapon.damage, self.weapon.accuracy, self.batch)
        return None

    def update(self, player_x, player_y, cam_x, cam_y, obstacle_map, delta_t):
        match(self.npctype):
            case 0:
                self.mov_x, self.mov_y = self.get_mov_to_point(self.objective[0], self.objective[1], obstacle_map, cam_x, cam_y, delta_t)
                self.x += self.mov_x
                self.y += self.mov_y
            case 2:
                if self.health < 25:
                    self.objective = self.get_objective()
                else:
                    if self.get_distance_to_player(player_x, player_y) > 200:
                        self.objective = (player_x, player_y)
                    else:
                        self.objective = self.get_objective()
                self.mov_x, self.mov_y = self.get_mov_to_point(self.objective[0], self.objective[1], obstacle_map, cam_x, cam_y, delta_t)
                self.x += self.mov_x
                self.y += self.mov_y
        self.update_sprite(cam_x, cam_y)
        return self.weapon_update(player_x, player_y, delta_t)


class NpcCar:
    def __init__(self, x, y, occupant, batch):
        self.x = x
        self.y = y
        self.npctype = npctype
        self.occupant = occupant
        self.sprite = WorldSprite(batch=batch, img=NPC_CARS[0], x=0, y=0)

    def update_sprite(self, cam_x, cam_y):
        self.sprite.set_relative_pos(self.x, self.y, cam_x, cam_y)

    def update(self, cam_x, cam_y, obstacle_map):
        if occupant != None:
            match(self.occupant.npctype):
                case 0:
                    pass
        self.update_sprite(cam_x, cam_y)


class NpcManager:
    def __init__(self, batch):
        self.batch = batch
        self.npcs = [NpcWalker(0, 0, 100, 2, Weapon(WEAPON_MODELS[0], 0, 0, 0, 0, 0), False, self.batch)]
        self.npcs_cars = []
    
    def update(self, bullet_manager, player_x, player_y, cam_x, cam_y, obstacle_map, bullet_list_player, bullet_list_ennemy, delta_t):
        new_npcs = []
        for npc in self.npcs:
            grid_x, grid_y = npc.pixel_to_grid_cos(npc.x, npc.y, cam_x, cam_y)
            if not 1 <= grid_x < 29 or not 1 <= grid_y < 29:
                continue
            new_npcs.append(npc)
            for bullet in bullet_list_player:
                npc.check_bullet_hit(bullet)
            for bullet in bullet_list_ennemy:
                npc.check_bullet_hit(bullet)
            bullet = npc.update(player_x, player_y, cam_x, cam_y, obstacle_map, delta_t)
            if bullet != None:
                bullet_manager.add_bullet(bullet, False)
        self.npcs = new_npcs
