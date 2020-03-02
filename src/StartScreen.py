from lxml import etree
from src.constants import *
import pygame as pg

from src.Level import Level
from src.Equipment import Equipment
from src.Player import Player
from src.InfoBox import InfoBox

START_MENU_WIDTH = 600

# > Start menu
START_MENU_ID = 0
#   - Launch new game
NEW_GAME_ACTION_ID = 0
#   - Load game
LOAD_GAME_ACTION_ID = 1
#   - Access to options screen
OPTIONS_ACTION_ID = 2
#   - Exit game
EXIT_ACTION_ID = 3


class StartScreen:
    def __init__(self, screen):
        self.screen = screen

        # Start screen loop
        bg_image = pg.image.load('imgs/interface/main_menu_background.jpg').convert_alpha()
        self.background = pg.transform.scale(bg_image, screen.get_size())

        # Creating menu
        self.active_menu = StartScreen.create_menu()

        # Memorize if a game is currently being performed
        self.started_game = False
        self.level = None

    @staticmethod
    def create_menu():
        entries = [[{'name': 'New game', 'id': NEW_GAME_ACTION_ID}], [{'name': 'Load game', 'id': LOAD_GAME_ACTION_ID}],
                   [{'name': 'Options', 'id': OPTIONS_ACTION_ID}], [{'name': 'Exit game', 'id': EXIT_ACTION_ID}]]

        for row in entries:
            for entry in row:
                entry['type'] = 'button'

        return InfoBox("In the name of the Five Cats", START_MENU_ID,
                       "imgs/interface/PopUpMenu.png", entries, START_MENU_WIDTH)

    def display(self):
        self.screen.blit(self.background, (0, 0))
        self.active_menu.display(self.screen)

    def play(self, level):
        self.started_game = True
        self.level = level

    def update_screen_display(self):
        # Blit the current state of the level
        self.level.display(self.screen)

    def update_state(self):
        if self.level:
            self.level.update_state()
            self.screen.fill(GREY)
            self.update_screen_display()

    def level_is_ended(self):
        return self.level.is_ended()

    def init_player(self, name):
        # -- Reading of the XML file
        tree = etree.parse("data/characters.xml").getroot()
        player_t = tree.xpath(name)[0]
        player_class = player_t.find('class').text.strip()
        lvl = player_t.find('lvl')
        if lvl is None:
            # If lvl is not informed, default value is assumes to be 1
            lvl = 1
        else:
            lvl = int(lvl.text.strip())
        defense = int(player_t.find('initDef').text.strip())
        res = int(player_t.find('initRes').text.strip())
        hp = int(player_t.find('initHP').text.strip())
        strength = int(player_t.find('initStrength').text.strip())
        move = int(player_t.find('move').text.strip())
        sprite = 'imgs/dungeon_crawl/player/' + player_t.find('sprite').text.strip()
        compl_sprite = player_t.find('complementSprite')
        if compl_sprite is not None:
            compl_sprite = 'imgs/dungeon_crawl/player/' + compl_sprite.text.strip()

        equipment = player_t.find('equipment')
        equipments = []
        for eq in equipment.findall('*'):
            equipments.append(Level.parse_item_file(eq.text.strip()))

        # Creating player instance
        player = Player(name, sprite, hp, defense, res, move, strength, [player_class], equipments, lvl,
                        compl_sprite=compl_sprite)

        # Up stats according to current lvl
        player.stats_up(lvl - 1)
        # Restore hp due to lvl up
        player.healed()

        inventory = player_t.find('inventory')
        for it in inventory.findall('item'):
            item = Level.parse_item_file(it.text.strip())
            player.set_item(item)

        return player

    def load_level(self, level, team):
        return Level('maps/level_' + level + '/', team)

    def new_game(self):
        # Modify screen
        screen = pg.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

        # Init player's team (one character at beginning)

        team = [self.init_player("john"), self.init_player("archer")]

        # Init the first level
        level = self.load_level("test", team)

        self.play(level)

    def load_game(self):
        try:
            save = open("saves/main_save.xml", "r")

            # Test if there is a current saved game
            if save:
                tree_root = etree.parse("saves/main_save.xml").getroot()
                level_name = tree_root.find("level/name").text.strip()
                game_status = tree_root.find("level/phase").text.strip()
                turn_nb = 0
                if game_status != 'I':
                    turn_nb = int(tree_root.find("level/turn").text.strip())
                team = []
                for player in tree_root.findall("team/player"):
                    name = player.find("name").text.strip()
                    level = int(player.find("level").text.strip())
                    p_class = player.find("class").text.strip()
                    exp = int(player.find("exp").text.strip())
                    hp = int(player.find("hp").text.strip())
                    strength = int(player.find("strength").text.strip())
                    defense = int(player.find("defense").text.strip())
                    res = int(player.find("res").text.strip())
                    move = int(player.find("move").text.strip())
                    current_hp = int(player.find("currentHp").text.strip())
                    pos = (int(player.find("position/x").text.strip()),
                           int(player.find("position/y").text.strip()))
                    inv = []
                    for it in player.findall("inventory/item"):
                        it_name = it.find("name").text.strip()
                        item = Level.parse_item_file(it_name)
                        inv.append(item)

                    equipments = []
                    for eq in player.findall("equipments/equipment"):
                        eq_name = eq.find("name").text.strip()
                        eq = Level.parse_item_file(eq_name)
                        equipments.append(eq)

                    # -- Reading of the XML file for default character's values (i.e. sprites)
                    tree = etree.parse("data/characters.xml").getroot()
                    player_t = tree.xpath(name)[0]

                    sprite = 'imgs/dungeon_crawl/player/' + player_t.find('sprite').text.strip()
                    compl_sprite = player_t.find('complementSprite')
                    if compl_sprite is not None:
                        compl_sprite = 'imgs/dungeon_crawl/player/' + compl_sprite.text.strip()

                    p = Player(name, sprite, hp, defense, res, move, strength, [p_class], equipments, level,
                               compl_sprite=compl_sprite)
                    p.earn_xp(exp)
                    p.set_items(inv)
                    p.set_current_hp(current_hp)
                    p.set_pos(pos)

                    team.append(p)

                # Load level with current game status, foes states, and team
                level = Level(level_name, team, game_status, turn_nb, tree_root.find("level/entities"))
                self.play(level)
            else:
                print("Error : no saved game")

            save.close()
        except FileNotFoundError as err:
            print("Error while opening saved game :", err)

    @staticmethod
    def options_menu():
        print("Access to options menu !")

    @staticmethod
    def exit_game():
        pg.quit()
        raise SystemExit

    def main_menu_action(self, method_id, args):
        # Execute action
        if method_id == NEW_GAME_ACTION_ID:
            self.new_game()
        elif method_id == LOAD_GAME_ACTION_ID:
            self.load_game()
        elif method_id == OPTIONS_ACTION_ID:
            self.options_menu()
        elif method_id == EXIT_ACTION_ID:
            self.exit_game()
        else:
            print("Unknown action... : " + method_id)

    def execute_action(self, menu_type, action):
        if not action:
            return
        method_id = action[0]
        args = action[1]

        if menu_type == START_MENU_ID:
            self.main_menu_action(method_id, args)
        else:
            print("Unknown menu... : " + menu_type)

    def motion(self, pos):
        if self.level is None:
            self.active_menu.motion(pos)
        else:
            self.level.motion(pos)


    def click(self, button, pos):
        if self.level is None:
            if button == 1:
                self.execute_action(self.active_menu.get_type(), self.active_menu.click(pos))
                return self.started_game
        else:
            self.level.click(button, pos)

    def button_down(self, button, pos):
        if self.level is not None:
            self.level.button_down(button, pos)