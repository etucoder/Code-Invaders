import asyncio # For the itch.io page
import pygame
import random
import math
import websockets
import json
import threading
import time
import sys
from uuid import uuid4
print(f"Platform : {sys.platform}")
print("Started!")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()) # type: ignore
remote_level = 0
remote_shop_state = False
net_lock = threading.Lock() # Lock
websocket_client = None
player_id = None
network_connected = False
network_thread_launched = False
p1_coords = "400,600"
p2_coords = "800,600"
SERVER_URL = "ws://localhost:8765"
#
# SERVER_URL = "wss://code-invaders-server.onrender.com"
pygame.init()
pygame.font.init()
font = pygame.font.SysFont(None,96)
title_font = pygame.font.Font("PressStart2P.ttf", 72)
subtitle_font = pygame.font.Font("PressStart2P.ttf", 42)
card_font = pygame.font.SysFont(None,20)
ui_font = pygame.font.Font("VT323-Regular.ttf", 20)
small_font = ui_font = pygame.font.Font("VT323-Regular.ttf", 18)
WIDTH , HEIGHT = 1000 ,600
FPS =  60                
screen = pygame.display.set_mode((WIDTH,HEIGHT))
running = True
clock = pygame.time.Clock()
game_canvas_color = (0,0,0)
particles = []
game_state = 0  
multiplayer_mode = False
explosion_sound = pygame.mixer.Sound("explosion.ogg")
small_explosion_sound = pygame.mixer.Sound("small_explosion1.ogg")
small_explosion_sound.set_volume(0.07)
click_sound = pygame.mixer.Sound("shortclick.ogg")
laser_sound = pygame.mixer.Sound("laser.ogg")
laser_sound.set_volume(0.15)
shake_intensity  =0
game_canvas = pygame.Surface((WIDTH + 40,HEIGHT + 40),pygame.SRCALPHA)
#### Menu Stuff #####

data_coins = 0 
shop_showing = False
shop_items = []
max_overdrive = 100
network_positions = {'p1_x': 200,'p1_y':600,"p2_x":800,"p2_y":600}
level_start = {'p1_lv' : 0,'p2_lv' : 0, 'p1_inshop' : False, 'p2_inshop' : False,'p1_bugs_are_dead' : False,'p2_bugs_are_dead' : False,'p1_choosing_cards' : False, 'p2_choosing_cards' :  False}
outbound_events = []
incoming_remote_lasers = []
p1_choosing_cards = False
p2_choosing_cards =  False
im_choosing_cards = False
active_ws_connection = None
all_bugs_are_dead = False
other_bugs_are_dead = False
next_bug_id = 0
network_bugs = {}
explosions = []
explosions_to_draw = []

game_id = uuid4()


async def network_sync_loop(ship_reference,game_id = 0):
    global explosions_to_draw, all_bugs_are_dead,other_bugs_are_dead,active_ws_connection,p1_coords,level_start, p2_coords, network_connected, game_state, player_id,ship,ship2,network_positions,multiplayer_mode,net_lock,pro_ships_2,pro_ships
    try:
        print("Going to connect")
        async with websockets.connect(SERVER_URL,ping_interval=20,ping_timeout=20) as ws:

            active_ws_connection = ws
            
            handshake_data = await ws.recv()
            config_receipt = json.loads(handshake_data)
            print("CONNECTED")
            player_id = int(config_receipt["player_id"])

            multiplayer_mode = True
            network_connected = True
            if player_id == 1:
                ship.is_local = True
                ship2.is_local = False
            elif player_id == 2:
                ship2.is_local = True
                ship.is_local = False
            else:
                print(player_id)
    
            network_connected = True
            game_state =   1
            #### Receive the stuff 3/4 working #######
            async def receive_handler():
                global explosions_to_draw,bugs,network_positions,lasers,net_lock,incoming_remote_lasers,level_start,p1_choosing_cards,p2_choosing_cards
                try:
                    async for message in ws:
                        global_match_state = json.loads(message)
                        if global_match_state.get("type") == "laser_fired":
                            with net_lock:
                                incoming_remote_lasers.append({
                                    "x" : global_match_state["x"],
                                    "y" : global_match_state["y"],
                                    "d" : global_match_state["damage"],
                                    "p" : global_match_state["pierce"]
                                })
                            
                            continue
                        
            
                        with net_lock:
                            p1_x,p1_y = map(int, global_match_state.get("p1","486,400").split(","))
                            p2_x,p2_y = map(int, global_match_state.get("p2","486,400").split(","))
                           
                        with net_lock:
                            network_positions["p1_x"] = p1_x
                            network_positions["p1_y"] = p1_y
                            network_positions["p2_x"] = p2_x
                            network_positions["p2_y"] = p2_y

                        with net_lock:
                            level_start['p1_bugs_are_dead'] = global_match_state.get("all_bugs_dead_p1", False)
                            level_start['p2_bugs_are_dead'] = global_match_state.get("all_bugs_dead_p2", False)
                        with net_lock:
                            p1_lv = global_match_state.get('p1_level',1)
                            p2_lv = global_match_state.get('p2_level',1)
                            p1_shop = global_match_state.get('p1_in_shop',False)
                            p2_shop = global_match_state.get('p2_in_shop',False)
          
#f
                            level_start["p2_lv"] = p2_lv
                            level_start["p2_inshop"] = p2_shop
                            level_start["p1_lv"] = p1_lv
                            level_start["p1_inshop"] = p1_shop
                        with net_lock:
                            p1_choosing_cards = global_match_state.get('p1_choosing_cards', False)
                            p2_choosing_cards = global_match_state.get('p2_choosing_cards', False)
                        # Copies player 1 so sync works (right?)  dfeskkjhkjhgghfhgdfddwasddawdsddwasdadwasawadwasddwdadwadsddwasashddwaswasdsdwaskjhdwasddwasddwasdjkjhsdasjkdkjhkjhjawdsafrgtdwasdhdwasdasdaasddwasdfg
                            if player_id == 2:
                                received_ids = set()

                                try:
                                    for explosion_data in global_match_state["explosions"]:
                                        explosions_to_draw.append([explosion_data[0],explosion_data[1],explosion_data[2]])
                                        print("it worked!")
                                except Exception as e:
                                      print(f"[Explosion Error] {e} ")
                                for bug_data in global_match_state["bugs_list"]: # Gets the bug list from plahyer 1

                                    bug_id = bug_data[8]

                                    received_ids.add(bug_id)

                                    if bug_id not in network_bugs:
                                        
                                        new_bug = Bug(
                                            x = bug_data[0],
                                            y = bug_data[1],
                                            w = bug_data[2],
                                            h = bug_data[3],
                                            image_path= bug_data[4],
                                            damage = bug_data[5],
                                            hp = bug_data[6],
                                            speed = bug_data[7],
                                            id = bug_data[8],
                                            y_speed= bug_data[9]

                                        )

                                        network_bugs[bug_id] = new_bug
                                        bugs.add(new_bug)

                                    else:

                                        bug = network_bugs[bug_id]

                                        bug.rect.x = bug_data[0]
                                        bug.rect.y = bug_data[1]
                                        bug.hp = bug_data[6]

                                for bug_id in list(network_bugs.keys()):
                                    if bug_id not in received_ids:
                                        network_bugs[bug_id].kill()

                                        del network_bugs[bug_id]
                                

                except Exception as e:
                        print(f"[Receiving Error]: Exception {e} from player {player_id}")

            async def send_handler():
                global explosions,card_was_chosen,p1_choosing_cards,p2_choosing_cards,im_choosing_cards,network_connected,outbound_events,net_lock,all_bugs_are_dead
                while network_connected:
                    events_to_send = []
                    with net_lock:
                        if outbound_events:
                            events_to_send = list(outbound_events)
                            outbound_events.clear()
                    is_in_shop = False
                    if game_state == 4:
                        is_in_shop = True
                    else:
                        is_in_shop = False
                    if player_id == 1:
                        the_giant_list = []
                        #  Create Explosions List
                        explosions_list = []
                        for bug in bugs:
                            all_attributes = [bug.rect.x,bug.rect.y,bug.w,bug.h,bug.image_num,bug.damage,bug.hp,bug.speed,bug.id,bug.y_speed]
                            the_giant_list.append(all_attributes)
                        
                        for explosion in explosions:
                            explosions_list.append([explosion[0],explosion[1],explosion[2]])
                        local_payload = {'x' : ship.rect.x,'y' : ship.rect.y, 'level' : current_level,'is_in_shop':is_in_shop,'bugs_dead' : all_bugs_are_dead,'choosing_cards' : im_choosing_cards,'bugs_list' : the_giant_list,'explosions' : explosions_list}
                        explosions.clear()
                    elif player_id == 2:
                        local_payload = {'x' : ship2.rect.x, 'y' : ship2.rect.y, 'level' : current_level,'is_in_shop':is_in_shop,'bugs_dead' : all_bugs_are_dead,'choosing_cards' : im_choosing_cards}
                
                    else:

                        pass
                    await ws.send(json.dumps(local_payload))

                    for event_packet in events_to_send:
                            await ws.send(json.dumps(event_packet))
                    await asyncio.sleep(0.016)

            await asyncio.gather(receive_handler(),send_handler())
            

    except Exception as e:
        print(f"Connection failed/closed : Error {e}")
        network_connected = False





def launch_network_thread(ship_instance):

    global network_thread_launched
    if network_thread_launched:
        return


    net_thread = threading.Thread(target = lambda: asyncio.run(network_sync_loop(ship_instance),loop_factory=asyncio.SelectorEventLoop)
                                   ,daemon = True)
    net_thread.start()

    network_thread_launched = True
    



class ShopItem:
    def __init__(self,name,cost,description,stats,effect_type,x,y,w = 260,h = 130,image = None):
        self.name = name
        self.cost = cost
        self.description = description
        self.effect_type = effect_type
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w,h)
        self.purchased = False
        self.stats = stats
        self.image = image
        if self.image != None:
            self.image = pygame.image.load(self.image).convert_alpha()
            self.image = pygame.transform.scale(self.image,(72,72))
           
    def draw(self,mouse_pos):
        nb = (160,32,240)
        global scroll_y,scroll_y
        self.rect = pygame.Rect(self.x+ scroll_x, self.y+scroll_y, self.w,self.h)
        box_color = (15,25,35) if not self.purchased  else (5, 10, 15)
        if self.purchased == True:
            box_color = (5,10,15)
        else:
            if self.rect.collidepoint(mouse_pos):
                box_color = nb
            else:
                box_color = (15,25,35)
        border_color = (0,255,100) if not self.purchased else (100,100,100)

        pygame.draw.rect(game_canvas,box_color,self.rect)
        pygame.draw.rect(game_canvas, border_color, self.rect,2)

        name_surface = ui_font.render(self.name, True , (255,255,255) if not self.purchased else (100,100,100))
        cost_color = (255,200,0) if data_coins >= self.cost else (255,50,50)
        cost_surface = ui_font.render(f"Cost: {self.cost} CR", True, (0,255,0) if not self.purchased else (100,100,100))
        stat_surface = ui_font.render(self.stats, True, cost_color if not self.purchased else (100,100,100))
        description_surface = ui_font.render(self.description, True,(0,180,255) if not self.purchased else(100,100,100))

        game_canvas.blit(name_surface,(self.rect.x + 15,self.rect.y + 15))
        game_canvas.blit(cost_surface,(self.rect.x + 15, self.rect.y + 45))
        game_canvas.blit(description_surface,(self.rect.x + 15,self.rect.y + 80))
        game_canvas.blit(stat_surface,(self.rect.x + 15,self.rect.y + 150))
        if self.image != None:
            game_canvas.blit(self.image,(self.rect.right - self.image.width - 5,self.rect.top + self.image.width / 12 + 5))
    def buy(self, mouse_pos, mouse_pressed):
        global data_coins,max_overdrive,files,ship
        if (not self.purchased and mouse_pressed[0]
                and self.rect.collidepoint(mouse_pos) and data_coins >= self.cost):
            data_coins -= self.cost
            self.purchased = True

            if self.effect_type == "Heal-Files":
                if self.name == "Quick Fix": # Spray the code with pesticide and call it debugging.
                    for file in files:
                        file.hp += min(0.1 * file.max_hp,file.max_hp - file.hp)
                elif self.name == "Bug Patch": # Tape and paint the bugs until no one knows they're there...
                    for file in files:
                        file.hp += min(0.33 * file.max_hp,file.max_hp - file.hp)
                elif self.name == "Security Update":  # Change passcode from 1234 to 12345. We're leading in cybersecurity.
                    for file in files:
                        file.hp += min(0.66 * file.max_hp,file.max_hp - file.hp)
                elif self.name == "Full Refactor": # Oh, the library became insecure AFTER I wrote 10,000 lines of code. What a coincidence!
                    for file in files:
                        file.hp += file.max_hp - file.hp
            elif self.effect_type == "Cooldown-Decrease":
                if self.name == "Office Processor":   # No! You can't open 2 tabs at once!
                    ship.max_cooldown = 0.9 * ship.max_max_cooldown

                if self.name == "Gaming Processor": # They don't need to fire their weapons to win. They just need to wear a skin with more than one color to crash my laptop...
                    ship.max_cooldown = 0.8 * ship.max_max_cooldown

                if self.name == "Dev Processor": # Finally, I can run Vs Code and ChatGPT at the same time!
                    ship.max_cooldown = 0.65  * ship.max_max_cooldown

                if self.name == "Server Processor": # Time to set my render distance to max and fill the whole world with TNT
                    ship.max_cooldown = 0.5 * ship.max_max_cooldown

            elif self.effect_type == "Ship-Speed":
                if self.name == "Office Mouse": # At this point , the mouse is more dust then technology. Better off using telepathy to control the cursor...
                    ship.speed = 1.1 * ship.original_speed
                if self.name == "RGB Mouse": # More LEDs that buttons. "But it GLOWS..." So does uranium I don't use it for programming (Most of the time)
                    ship.speed = 1.25 * ship.original_speed
                if self.name == "High-End Gaming Mouse" : # Great tracking , it makes you better at gaming. Instead of dying 20 times for every 1 person I kill, I die 19...
                    ship.speed = 1.5 * ship.original_speed
                if self.name == "Industrial-Grade Mouse": # Developed after someone misclicked one to many times. Power consumption reduced from 50 cities to 45
                    ship.speed = 2.0 * ship.original_speed

            elif self.effect_type == "Damage":
                if self.name == "DDR2 Stick": ## It may hold more data my being used as a bat than actual RAM. Type any 2 letters to make it crash.
                    ship.damage = 1.1 * ship.max_damage
                if self.name == "Aluminum-Coated DDR3": # Oh, it didn't come with any heat shielding but some old aluminum foil fixed that...
                    ship.damage = 1.25 * ship.max_damage
                if self.name == "RGB DDR4": # You may have bought it more for the lights than the RAM, and you can't tell which is higher quality.
                    ship.damage = 1.5 * ship.max_damage
                if self.name == "256GB DDR5": # Costs your whole life savings just so you could load Minecraft a little faster...
                    ship.damage = 2.0 * ship.max_damage

            elif self.effect_type == "Overdrive-Duration":
                if self.name == "Ice Pack": # Actually pretty good at cooling but getting up every 15 minutes to replace it just so VSCode keeps runnings is kind of irritating.
                    max_overdrive = 110
                if self.name == "Aluminum Block" : # Grabbed this out of a calculator and put a cpu on it to fry an egg at work... You can taste some aluminum if you try enough.
                    max_overdrive = 125
                if self.name == "Aluminum Tower" : # A Nice tower with copper pipes running through them. We only bought it because of our server room being so hot it was classified as a "Fire Hazard"
                    max_overdrive = 150
                if self.name == "Pure Metal Dual-Tower": # Sure, it cools well, but someone put ONE stack of papers next to the cooling fan and now the whole building somehow has our paper.
                    max_overdrive = 200
                if self.name == "Liquid Nitrogen Cooling Pot": # When you never want to lag again, this is the perfect cooler. Also functions as Air Conditioning in the summmer my making the room 10 degrees colder.
                    max_overdrive = 325
                if self.name == "Cyrostat Dilution Refrigarator": # I'm sure Google won't mind us putting our servers in there next to the quantum computer. It's so cold that lag somehow makes the computer run faster?? All I know is I can't use the cooling racks for my yougurt anymore...
                    max_overdrive = 500

            elif self.effect_type == "File Max Hp":
                if self.name == "Layered Plastic Bag": # Finally found a use for all those plastic bags...
                    for file in files:
                        file.max_hp = file.max_max_hp + 1
                elif self.name == "Brittle Plastic Shell": # Made out of the same plastic as throw-away utensils. They have the same strength, but at least the utensils can hold food...
                    for file in files:
                        file.max_hp = file.max_max_hp + 2.5
                elif self.name == "Aluminum Alloy": # Our friend though he was really smart and spent $50 on aluminum foil and wrapped the laptop in in. I then explained that aluminum does not always come in a foil form...
                    for file in files:
                        file.max_hp = file.max_max_hp + 5
                elif self.name == "Carbon Fiber": # The same material space NASA uses for rockets. The difference is they go to space and their launch date is still somehow before ours?
                    for file in files:
                        file.max_hp = file.max_max_hp + 10
                elif self.name == "Titantium Safe" : # The cage probably costs more than the server.Deleting a code file with a sledgehammer deletes the sledgehammer. All this for the program files from 2008 because they somehow still hold the code together...
                    for file in files:
                        file.max_hp = file.max_max_hp + 25

            elif self.effect_type == "File Protection Turret":
                if self.name == "Foam Guns" : # Cost : 15 Gave a kid a nerf gun a box of ammo and told him to hit anyone who came into the server room. I don't think the CEO was too happy getting showered with foam balls...
                    # Creates a Foam Gun Turret (In progress) 
                    pass
                elif self.name == "Automated Foam Missile Launcher" : # Cost : 25 An Ultrasonic, Raspberry Pi 4,Battery, Foam, and Rubber Bands made a highly dangerous and lethal weapon if any ants stepped into the room...
                    # Creates a Foam Missile Turret (In Progress)
                    pass
                elif self.name == "Taser 4000 Pro": # Cost: 50 A Premium Taser bought because we thought more volts = faster charging. Let's just say our laptop didn't share our enthusiasm
                    # Creates a Taser 400 Pro
                    pass
                elif self.name == "Laser Blaster": # Cost: 150 Gives knockback and shock with a side of damage. However, it drains a car battery for every single shot...
                    # Creates a Laser Blaster
                    pass
                elif self.name == "Laser Shotgun": # Cost : 500 The Laser Blaster but better. The power scales exponentially, but I'm not paying the electricity bill...
                    # Creates a Laser Shotgun
                    pass
                elif self.name == "Flamethrower": # Cost : 2000 When you copy the YouTuber and it actually works... Burns anyone and anything near the server, including the server itself...
                    # Creates a Flamethrower
                    pass
                elif self.name == "Rocket Launcher": # Cost : 5000 Wheeeeeeeee BOOOOOOOOOM.... "Now no one will steal our source code!" "You mean the one with more bugs than lines of code?"
                    # Creates a Rocket Launcher
                    pass
                elif self.name == "Uranium Slingshot": # Cost : 12,500 A Robotic Arm Launches a marble-sized uranium ball toward anyone who isn't authorized. Wait , why is the FBI here? I wonder why...
                    # Creates a Uranium Slingshot
                    pass
                elif self.name == "Reactor Core": # Cost : 75,000 One wrong move and I'll vaporize you... And myself and the server and the city probably...
                    # Creates a Reactor Core
                    pass
                elif self.name == "Orbital Strike Cannon": # 250,000 Push of a button and flick of a lever, it's raining TNT , I'll see you never!
                    # Creates an Orbital Strike Cannon
                    pass
                elif self.name == "Antimatter Vaporizer":  # 1,000,000 Removes something from existense. Costs twice the global GDP for each shot.
                    # Creates an Antimatter Vaporizer
                    pass
                elif self.name == "Open-Source": # 2,500,000 Costs Data here but costs nothing in the real world. The best way to secure your project is to give it to people who will use,test,fix,and rebuild it.
                    # Creates an Open Source Turret
                    pass
            elif self.effect_type == "Data Collection":
                if self.name == "Manual Search": # After 12 Hours of google searches, I finally found my question on stack overflow AND THE ANSWER WAS DELETED!!!
                    ship.data_per_enemy = 2
                elif self.name == "Basic Data Grabber": # Can't Call it a Scraper because it only gets the title of the website... Better than nothing I guess...
                    ship.data_per_enemy = 4
                elif self.name == "Web Scrapper API": # A low-quality web scrapper for a high-percentage-of-my-income price
                    ship.data_per_enemy = 8
                elif self.name == "Raspberry Pi Data Farm": # The Boss bought them for team-building but the only thing they're building is dust. Set up all 40 together and you've got a nice data scraper, providing no one noticed that 40 Raspberry Pi's dissappeared...
                    ship.data_per_enemy = 16
                elif self.name == "Data Mining": # Spend your life savings on 12 GPUs and send them to the mines. Change your identity when the electricity bill comes in.
                    ship.data_per_enemy = 32
                elif self.name == "Automated Scam Emails": # Its so easy to fool people... WAIT I WON A MILLIONS DOLLARS? Yeah I'll give you 100 bucks and my Bank Account password for "Verification" 
                    ship.data_per_enemy = 64
                elif self.name == "Automated Scam Calls": # Yeah, the car warranty I can't afford has expired? Yeah so has this bazooka, but I'm ok with giving it a test! Why'd you leave?
                    ship.data_per_enemy = 128
                elif self.name == "Actual Website": # Sign Up or Log in to access the watching paint dry livestream with limited giveaways of waster time for everyone who watches!
                    ship.data_per_enemy = 256
                elif self.name == "Minecraft Server": # Note : Don't ask for data AFTER blowing them and their bas up with TNT...
                    ship.data_per_enemy = 512
                elif self.name == "Hackclub Slack Scanner": # Data is Data, even if it's about the next minecraft modpack...
                    ship.data_per_enemy = 1024
                elif self.name == "Database Company": # Data? I AM THE DATA!!!
                    ship.data_per_enemy = 2048
                elif self.name == "Search Engine" : # Why are so many people searching up "Who would win : Taco vs. Grilled Cheese"?
                    ship.data_per_enemy = 4096

            elif self.effect_type == "Data Coin Mult":
                if self.name == "Self Organizing": ### Label and Ship the data yourself to recieve a quality bonus. 
                    # What, you want me to make their last 10 searches visible on a public website with 10,000 line of CSS for a QUALITY MULT?
                    ship.data_mult = 1.5
                elif self.name == "Group Data Auditing": # Share the work. # Share the profits. # Share the depression.
                    ship.data_mult = 2
                elif self.name == "AI Model Training" : # Pays higher until you realize that it somehow mistakes a TV for a water bottle?
                    ship.data_mult = 3
                elif self.name == "Manual Group AI Training" : # Your group meetups involve dragging bounding boxes from one side of the screen to the other while eating the free snacks you provided.
                    ship.data_mult = 5
                elif self.name == "Data Polishing Offload" : # Pay someone else to write the labels on the data while you play games...
                    ship.data_mult = 7.5
                elif self.name == "Auto AI Training" : # An AI Training an AI. After 5 weeks of training, It can tell that a cat and a dog are different but cant say which is which
                    ship.data_mult = 10
                elif self.name == "Data Seller" : # Selling your data to companies and telling you we don't from 1982!
                    ship.data_mult = 25
                elif self.name == "Bakery" : # High quality cookies  =  High quality data
                    ship.data_mult = 50
                elif self.name == "Clone Machine" : # More people, More data... its simple, really.
                    ship.data_mult = 100
scroll_x, scroll_y = 0,50

heal_files_1 = ShopItem("Quick Fix",5,"Spray the code with pesticide\nand call it debugging.","Heals all files by 10%","Heal-Files",30+scroll_x,100+scroll_y, w = 280,h = 180)
heal_files_2 = ShopItem("Bug Patch",10,"Tape and paint the bugs until no\none knows they're there...","Heals all files by 33%","Heal-Files",30+scroll_x,300+scroll_y, w = 280,h = 180)
heal_files_3 = ShopItem("Security Update",20, "Change passcode from 1234 to 12345.\nWe're leading in cybersecurity.","Heals all files by 66%","Heal-Files",30+scroll_x,500+scroll_y,w = 280,h = 180)
heal_files_4 = ShopItem("Full Refactor",30, "Oh, the library became insecure\nAFTER I wrote 10,000 lines of code.\nWhat a coincidence!","Heals all files to full health","Heal-Files",30+scroll_x,700+scroll_y,w=280,h = 180)

name_surface = [subtitle_font.render("Heals", True , (0,255,0)),"Heals"]
cooldown_surface = [subtitle_font.render("Cooldown", True , (0,0,255)),"Cooldown"]
damage_surface = [subtitle_font.render("Damage", True , (255,0,0)),"Damage"]
speed_surface = [subtitle_font.render("Speed", True , (255,255,0)),"Speed"]
max_hp_surface= [subtitle_font.render("File Max\n Health", True , (255,165,0)),"File Max\n Health"]
overdrive_surface= [subtitle_font.render("Overdrive\n Duration", True , (128,0,128)),"Overdrive\nDuration"]
game_canvas.blit(name_surface[0],(heal_files_1.rect.centerx,heal_files_1.rect.top + 20))
titles = []
titles.append(name_surface)
titles.append(cooldown_surface)
titles.append(damage_surface)
titles.append(max_hp_surface)
titles.append(speed_surface)
titles.append(overdrive_surface)
# All upgrades in shop
cooldown_files_1 = ShopItem("Office Processor",25,"No! You can't open 2 tabs at once!","Cooldown reduced by 10%","Heal-Files",330+scroll_x,100+scroll_y, w = 300,h = 180,image = "officecore.png")
cooldown_files_2 = ShopItem("Gaming Processor",125,"They don't need to fire their weapons.\nThey just need to wear a skin with more\nthan one color to crash my laptop...","Cooldown reduced by 20%","Heal-Files",330+scroll_x,300+scroll_y, w = 300,h = 180,image = "gamingcore.png")
cooldown_files_3 = ShopItem("Dev Processor",750, "Finally, I can run Vs Code and ChatGPT\nat the same time!","Cooldown reduced by 35%","Heal-Files",330+scroll_x,500+scroll_y,w = 300,h = 180, image = "devcore.png")
cooldown_files_4 = ShopItem("Server Processor",3000, "Time to set my render distance to max\nand fill the whole world with TNT","Cooldown reduced by 50%","Heal-Files",330+scroll_x,700+scroll_y,w=300,h = 180,image = "servercpu.png")

speed_files_1 = ShopItem("Office Mouse",10,"At this point , the mouse is more dust\nthen technology. Better off using\ntelepathy to control the cursor...",r"Cursor is 10% faster","Heal-Files",660+scroll_x,100+scroll_y, w = 300,h = 180,image = "officemouse.png")
speed_files_2 = ShopItem("RGB Mouse",30,"More LEDs than mouse parts. 'But it\nGLOWS...' So does uranium I don't use it\nfor programming (Most of the time)",r"Cursor is 25% faster","Heal-Files",660+scroll_x,300+scroll_y, w = 300,h = 180,image = "rgb.png")
speed_files_3 = ShopItem("High-End Gaming Mouse",150, "Great tracking , it makes you better\nat gaming. Instead of dying 20 times\nfor every 1 person I kill, I die 19...",r"Cursor is 50% Faster","Heal-Files",660+scroll_x,500+scroll_y,w = 300,h = 180, image = "devmouse.png")
speed_files_4 = ShopItem("Industrial-Grade Mouse",750, "Developed after someone misclicked one\nto many times. Power consumption reduced\nfrom 50 cities to 45",r"Cursor is 100% Faster","Heal-Files",660+scroll_x,700+scroll_y,w=300,h = 180,image = "industrialmouse.png")

ram_files_1 = ShopItem("DDR2 Stick",25,"It may hold more data my being used as \nnotepad than actual RAM. Type any 2\nletters to make it crash.",r"Lasers do 10% more damage","Heal-Files",990+scroll_x,100+scroll_y, w = 300,h = 180,image = "ddr2.png")
ram_files_2 = ShopItem("Aluminum-Coated DDR3",125,"Oh, it didn't come with any heat\nshielding but some old\naluminum foil fixed that...",r"Lasers do 25% more damage","Heal-Files",990+scroll_x,300+scroll_y, w = 300,h = 180,image = "ddr3.png")
ram_files_3 = ShopItem("RGB DDR4",750, "You may have bought it more for the\nlights than the RAM, and you can't\ntellwhich is higher quality..",r"Lasers do 50% more damage","Heal-Files",990+scroll_x,500+scroll_y,w = 300,h = 180, image = "ddr4.png")
ram_files_4 = ShopItem("256GB DDR5",3000, "Costs your whole life savings just so\nyou could load Minecraft a little\nfaster...",r"Lasers do 100% more damage","Heal-Files",990+scroll_x,700+scroll_y,w=300,h = 180,image = "ddr5.png")


cooler_files_1 = ShopItem("Ice Pack",5,"Actually pretty good at cooling but\ngetting up every 15 minutes to replace it\njust so VSCode keeps running is kind\nof irritating.",r"Overdrive lasts 10% longer","Heal-Files",1320+scroll_x,100+scroll_y, w = 320,h = 180,image = "icepack.png")
cooler_files_2 = ShopItem("Aluminum Block",12,"Grabbed this out of a calculator and put a\ncpu on it to fry an egg at work...\nYou can taste some aluminum if you\ntry enough.",r"Overdrive lasts 25% longer","Heal-Files",1320+scroll_x,300+scroll_y, w = 320,h = 180,image = "aluminumblock.png")
cooler_files_3 = ShopItem("Aluminum Tower",125, "A Nice tower with copper pipes\nrunning through them. We only bought it\nbecause of our server room being so hot\nit was classified as a 'Fire Hazard'",r"Overdrive lasts 50% longer","Heal-Files",1320+scroll_x,500+scroll_y,w = 320,h = 180, image = "coolingtower1.png")
cooler_files_4 = ShopItem("Pure Metal Dual-Tower",800, "Sure, it cools well, but someone put ONE\nstack of papers next to the cooling fan and\nnow the whole building somehow has our\npaper.",r"Overdrive lasts 100% longer","Heal-Files",1320+scroll_x,700+scroll_y,w=320,h = 180,image = "coolingtower2.png")
cooler_files_5 = ShopItem("Liquid Nitrogen Cooling Pot",4500, "When you never want to lag again, this is\nthe perfect cooler. Also functions as\nAir Conditioning in the summmer\nmy making the room 10 degrees colder.",r"Overdrive lasts 325% Longer","Heal-Files",1320+scroll_x,900+scroll_y,w = 320,h = 180, image = "liquidnitrogencooler.png")
cooler_files_6 = ShopItem("Cyrostat Dilution Refrigarator",45000, "I'm sure Google won't mind us putting our\nservers in there next to the quantum\ncomputer.All I know is I can't use the\ncooling racks for my yougurt anymore...",r"Overdrive lasts 500% Longer" ,"Heal-Files",1320+scroll_x,1100+scroll_y,w=320,h = 180,image = "quantumcooler.png")

for item in (cooldown_files_1, cooldown_files_2, cooldown_files_3, cooldown_files_4):
    item.effect_type = "Cooldown-Decrease"
for item in (speed_files_1, speed_files_2, speed_files_3, speed_files_4):
    item.effect_type = "Ship-Speed"
for item in (ram_files_1, ram_files_2, ram_files_3, ram_files_4):
    item.effect_type = "Damage"
for item in (cooler_files_1, cooler_files_2, cooler_files_3, cooler_files_4, cooler_files_5, cooler_files_6):
    item.effect_type = "Overdrive-Duration"

six = 6

case_files_1 = ShopItem("Layered Plastic Bag",3,"Finally found a use for all those plastic\nbags...",r"Files get +1 max HP","Heal-Files",1670+scroll_x,100+scroll_y, w = 320,h = 180,image = "plasticbags.png")
case_files_2 = ShopItem("Brittle Plastic Shell",10,"Made out of the same plastic as throw-away\nutensils. They have the same strength,but\nat least the utensils can hold food...",r"Files get +2.5 Max HP","Heal-Files",1670+scroll_x,300+scroll_y, w = 320,h = 180,image = "plasticcase.png")
case_files_3 = ShopItem("Aluminum Alloy",50, "Comes with a complimentary premium aluminum\n(foil) case worth $100 (In sentimental\nvalue...)'",r"Files get +5 Max HP","Heal-Files",1670+scroll_x,500+scroll_y,w = 320,h = 180, image = "aluminum.png")
case_files_4 = ShopItem("Carbon Fiber",400, "The same material NASA uses for rockets.\nThe difference is they go to space and\ntheir launch date is still\nsomehow before ours?",r"Files get +10 Max HP","Heal-Files",1670+scroll_x,700+scroll_y,w=320,h = 180,image = "carbonfiber.png")
case_files_5 = ShopItem("Titantium Safe",2000, "Protects the program files from 2008 because\nthey somehow still hold the code together..",r"Files get +25 Max HP","Heal-Files",1670+scroll_x,900+scroll_y,w = 320,h = 180, image = "safe.png")

for item in (case_files_1, case_files_2, case_files_3, case_files_4, case_files_5):
    item.effect_type = "File Max Hp"

shop_items.append(heal_files_1)
shop_items.append(heal_files_2)
shop_items.append(heal_files_3)
shop_items.append(heal_files_4)
shop_items.append(cooldown_files_1)
shop_items.append(cooldown_files_2)
shop_items.append(cooldown_files_3)
shop_items.append(cooldown_files_4)
shop_items.append(ram_files_1)
shop_items.append(ram_files_2)
shop_items.append(ram_files_3)
shop_items.append(ram_files_4)
shop_items.append(speed_files_1)
shop_items.append(speed_files_2)
shop_items.append(speed_files_3)
shop_items.append(speed_files_4)

shop_items.append(cooler_files_1)
shop_items.append(cooler_files_2)
shop_items.append(cooler_files_3)
shop_items.append(cooler_files_4)
shop_items.append(cooler_files_5)
shop_items.append(cooler_files_6)

shop_items.append(case_files_1)
shop_items.append(case_files_2)
shop_items.append(case_files_3)
shop_items.append(case_files_4)
shop_items.append(case_files_5)
textboxes = []

messages = [["C:/Users/You","Hello, World!"], 
            ["C:/Users/You" , "Oh, finally got my IDE working... "],
            ["C:/Users/You" , "Now I can finally test my new debugging program!"],
            ["C:/Users/You","Let me just boot it up and..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Use the Arrow Keys/WASD to move the debugging cursor"],
            ["C:/Files/Programming/DebuggerSetup.exe", "Use the Spacebar/E to shoot down incoming errors."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Shoot down the errors before they reach your files."],
            ["C:/Files/Programming/DebuggerSetup.exe", "If an error reaches your file,it will deal\nsome damage to that file."],
            ["C:/Files/Programming/DebuggerSetup.exe", "If one of your files runs out of health and crashes..."],
            [r"C:/Files/Programming/DebuggerSetup.exe", r"You lose the program... FOREVER"],
            ["C:/Files/Programming/DebuggerSetup.exe", "If a error hits your cursor,your\ncursor will take damage."],
            ["C:/Files/Programming/DebuggerSetup.exe", "If your cursor takes enough damage...\n Well we don' really know what happens..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "All we know is that it dissappears."],
            ["C:/Files/Programming/DebuggerSetup.exe", "If all 3 cursors get destroyed\nyou lose the program... FOREVER."],
            ["C:/Files/Programming/DebuggerSetup.exe", "See the bright orange bar over there?"],
            ["C:/Files/Programming/DebuggerSetup.exe", "Press / or q to activate it."],
            ["C:/Files/Programming/DebuggerSetup.exe", "While activated, your cooldown will decrease\ndrastically."],
            ["C:/Files/Programming/DebuggerSetup.exe", "This allows you to defeat errors much easier."],
            ["C:/Files/Programming/DebuggerSetup.exe", "However, after use, you have to recharge\nthe bar to use it again."],
            ["C:/Files/Programming/DebuggerSetup.exe", "You can recharge the bar by destroying errors."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Use it wisely..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Keep..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "The..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Files..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Alive..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "They..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Control..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "The..."],
            ["C:/Files/Programming/DebuggerSetup.exe", "Installation Ended. You may know close this window."],
            ["?","?"],
            ["??","??"],
            [""]
            ]

class Textbox():
    def __init__(self,x,y,w,h,text_to_write,text_speed,speaker,speaker_color,text_color):
        global messages
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.messages = messages
        self.text_to_write = text_to_write 
        self.text_speed = text_speed
        self.current_text = ""
        self.char_index = 0
        self.speaker = speaker
        self.speaker_color = speaker_color
        self.text_color = text_color
        self.is_finished = False
        self.timer = 0
        self.box_rect = pygame.Rect(self.x,self.y,self.w,self.h)
        self.font = ui_font
        self.text_index = 0
    def update(self,mouse_pos,update = False):
        global keys
        if not self.is_finished:
            self.timer += 1
            if self.timer >= self.text_speed:
                self.timer = 0
                if self.char_index < len(self.text_to_write):
                    self.current_text += self.text_to_write[self.char_index]
                    self.char_index += 1
                else:
                    self.is_finished = True
        if True:
            if update and self.box_rect.collidepoint(mouse_pos):
         
                if self.text_index <= 29 :
                    self.char_index = 0
                    self.text_index += 1
                    self.current_text = ""
                    self.text_to_write = self.messages[self.text_index][1]
                    self.is_finished = False

    def draw(self,surface = game_canvas):
        pygame.draw.rect(surface, (10,15,20),self.box_rect)
        pygame.draw.rect(surface, (0,255,100),self.box_rect,3)

        speaker_surface = self.font.render(f"[{self.messages[self.text_index][0]}] : ", True,self.speaker_color)
        surface.blit(speaker_surface,(self.box_rect.x + 20,self.box_rect.y + 15))
        
        text_surface = self.font.render(self.current_text,True,self.text_color)
        surface.blit(text_surface,(self.box_rect.x + 20,self.box_rect.y + 55))


class MenuButton():
    def __init__(self,text,center_x,center_y,width,height,target_state,color = (30,30,35)):
        self.text = text
        self.width = width
        self.height = height
        self.target_state = target_state

        self.rect = pygame.Rect(0,0,width,height)
        self.rect.center = (center_x,center_y)
        self.idle_color = color
        self.hover_color = (0,180,255)
    def draw(self,game_canvas,font,mousepos):
        the_color = (0,0,0)
        if self.rect.collidepoint(mousepos):
            the_color = self.hover_color
        else:
            the_color = self.idle_color

        pygame.draw.rect(game_canvas,the_color,self.rect,border_radius=8)
        pygame.draw.rect(game_canvas,(255,255,255),self.rect,width=2,border_radius=8)

        text_surface = font.render(self.text,True,(255,255,255))
        text_rect = text_surface.get_rect(center = self.rect.center)
        game_canvas.blit(text_surface,text_rect)

    def check_clicks(self,mouse_pos , mouse_pressed ):
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False


##### Game Stuff #####f
# ########### SHIPPY ########## 
class Ship(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp = 10,speed = 6,knockback = 0,pierce = 0):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.weapon_type = "Regular"
        self.image_path = image_path
        self.pierce = pierce
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.damage = 3
        self.original_damage = damage
        self.max_damage = damage
        self.hp = hp
        self.speed = speed
        if self.weapon_type != "Shotgun" and self.weapon_type != "Mine" :
            self.cooldown = 8
        elif self.weapon_type == "Shotgun":
            self.cooldown = 45
        elif self.weapon_type == "Mine":
            self.cooldown = 60
        elif self.weapon_type == "Missile":
            self.cooldown = 100
        self.max_cooldown = self.cooldown
        self.max_max_cooldown = self.max_cooldown
        self.max_hp = hp
        self.knockback = knockback
        self.can_dash = True
        self.is_dashing = False
        self.dash_damage = 3
        self.dash_cooldown = 200
        self.invert_duration = 0
        self.overdrive_duration = 0
        self.max_overdrive_duration = 600
        self.freeze_duration = 0
        self.original_speed = self.speed
        self.is_local = None
        red_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,100)
        green_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,(100/self.max_hp) * self.hp)
    def move(self):
        if self.is_local == True:
            global keys,bugs,overdrive_charge
            if self.invert_duration <= 0:
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.rect.y -= self.speed
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.rect.y += self.speed
                elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.rect.x -= self.speed
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.rect.x += self.speed


            else:
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.rect.y += self.speed
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.rect.y -= self.speed
                elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.rect.x += self.speed
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.rect.x -= self.speed
                self.invert_duration -= 1


            if keys[pygame.K_RSHIFT] and self.can_dash and self.dash_cooldown <= 0:
                self.is_dashing = True
                self.dash_cooldown = 200
                dash_beam = pygame.Rect(self.rect.x,0,self.w,self.rect.y)
                for bug in bugs:
                    if bug.rect.colliderect(dash_beam):
                        bug.hp -= self.dash_damage
                self.rect.y = 0
            elif keys[pygame.K_RSHIFT] and self.dash_cooldown <= 150:
                self.rect.y = 500
            
                
                self.is_dashing = False
            if self.dash_cooldown > 0 and self.can_dash:
                self.dash_cooldown -= 1

            if self.rect.x >= WIDTH - self.w:
                self.rect.x = WIDTH - self.w
            elif self.rect.x <= 0:
                self.rect.x =  0

            if self.rect.y <=  0:
                self.rect.y = 0

            if self.rect.y >= HEIGHT - self.h:
                self.rect.y = HEIGHT - self.h
    def update(self):
        if not self.overdrive_duration > 0 or self.freeze_duration > 0:
            if self.weapon_type != "Shotgun" and self.weapon_type != "Mine" :
                self.max_max_cooldown = 1
            elif self.weapon_type == "Shotgun":
                self.max_max_cooldown = 45
            elif self.weapon_type == "Mine":
                self.max_max_cooldown = 45

            if self.weapon_type != "Shotgun" and self.weapon_type != "Mine" :
                self.max_cooldown = self.max_max_cooldown
            elif self.weapon_type == "Shotgun":
                self.max_cooldown = self.max_max_cooldown * 2
            elif self.weapon_type == "Mine":
                self.max_cooldown = self.max_max_cooldown * 4
        global lives_left
        
        if self.hp <= 0:
            lives_left -= 1
            self.hp = self.max_hp


        if self.freeze_duration > 0 and self.overdrive_duration <= 0:
            self.speed = 0.6 * (self.original_speed)
            self.max_cooldown = 2 * (self.max_max_cooldown)
            self.freeze_duration -= 1
        else:
            self.speed = self.original_speed
            if self.overdrive_duration <= 0:
                self.max_cooldown = self.max_max_cooldown
            else :
                self.max_cooldown = 0.25 * self.max_max_cooldown
    def shoot(self):
        global lasers,card_was_chosen,overdrive_charge,net_lock,outbound_events

        if (keys[pygame.K_SPACE] or keys[pygame.K_e]) and self.cooldown <= 0 and self.is_local:
            if self.weapon_type == "Regular":
                laser = Laser(self.rect.centerx,self.rect.top,5,5,damage=self.damage,knockback=self.knockback,pierce=self.pierce)
                lasers.append(laser)
                self.cooldown = self.max_cooldown
                laser_sound.play()
                payload  = {
                    "type" : "laser_fired",
                    "x" : self.rect.centerx,
                    "y": self.rect.top,
                    "weapon" : "Regular",
                    "damage" : self.damage ,
                    "pierce" : self.pierce
                }
                with net_lock:
                    outbound_events.append(payload)
            elif self.weapon_type == "Double":
                laser = Laser(self.rect.x+3,self.rect.y+10,5,5,damage=self.damage,knockback=self.knockback,pierce=self.pierce)
                laser1 = Laser(self.rect.x+18,self.rect.y+10,5,5,damage=self.damage,knockback=self.knockback,pierce=self.pierce)
                lasers.append(laser)
                lasers.append(laser1)
                self.cooldown = self.max_cooldown
                for i in range(2):
                    laser_sound.play()

            elif self.weapon_type == "Shotgun":
            
                coord_pairs = [(-3.00,-5.20),(-1.55,-5.80),(0.00,-6.00),(1.55,-5.80),(3.00,-5.20)]
               
                for vx,vy in coord_pairs:
                    bullet = Laser(self.rect.centerx,self.rect.centery,5 ,5,(0,255,0),9,self.damage * 1.5,vx = vx,vy = vy)
                    lasers.append(bullet)
                click_sound.play()
                self.cooldown = self.max_cooldown
            
        elif self.cooldown > 0 and card_was_chosen == True:
            self.cooldown -= 1
        else:
            pass
        global active_ws_connection
        


        
        if self.overdrive_duration > 0:
            self.max_cooldown = 0.25 * (self.max_max_cooldown)
            self.overdrive_duration -= 1
            overdrive_charge -= 100/self.max_overdrive_duration
    
        else:
            pass
    def multi_update(self):
        self.rect.x = self.rect.x
        self.rect.y = self.rect.y
        
items = [pygame.transform.scale(pygame.image.load("exception.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("indentationerror.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("indexerror.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("memoryerror.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("importerror.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("brokenpipe.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("typeerror.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("packetbug.png").convert_alpha(),(9,9)),
        pygame.transform.scale(pygame.image.load("nullpointererror.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("deprecatedmethod.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("deprecatedgiant.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("sqlinjector.png").convert_alpha(),(24,24)) ,
        pygame.transform.scale(pygame.image.load("racecondition.png").convert_alpha(),(24,24)),
        pygame.transform.scale(pygame.image.load("sleepthread.png").convert_alpha(),(24,24))]
names = ["exception.png","indentationerror.png","indexerror.png","memoryerror.png","importerror.png","brokenpipe.png","typeerror.png","packetbug.png","nullpointererror.png",
         "deprecatedmethod.png","deprecatedgiant.png","sqlinjector.png","racecondition.png","sleepthread.png"]
class Bug(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path,damage,hp ,speed,y_speed = 0.5,id = None ):
        super().__init__()
        self.x = x
        self.image_num = image_path
        self.y = y
        self.w = w
        self.h = h
        self.image_path = names[image_path]
        self.damage = damage
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.image = items[image_path]
        self.rect = self.image.get_rect(topleft = (x,y))
        self.movetox = 0
        self.movetoy = 0
        self.float_y = float(self.y)
        self.float_x = float(self.x)
        self.y_speed = y_speed
        self.og_y_speed = y_speed
        self.creation_cooldown = 100
        self.max_creation_cooldown = self.creation_cooldown
        self.cooldown = 75
        self.max_cooldown = 75
        self.null_cooldown = 400
        self.max_null_cooldown = self.null_cooldown
        self.xv = 0
        self.yv = 0
        self.teleport_cooldown = 0
        self.max_teleport_cooldown = 50
        self.id = id
        if self.image_path == "packetbug.png":
            self.orbit_angle = random.uniform(0,2*math.pi)
            self.target_radius = random.uniform(140,180)
        self.packetcooldown = 10
        self.sleep_freeze_cooldown = 300
        self.max_sleep_freeze_cooldown = self.sleep_freeze_cooldown
    def move(self,axis = "n",amount = 0):
        if axis == "x":
            self.movetox = amount
            if amount > 0:
                if self.speed > self.movetox:
                    self.rect.x += self.movetox
                    self.movetox -= self.movetox
                else:
                    self.rect.x += self.speed
                    self.movetox -= self.speed
            elif amount < 0:
                if self.speed < self.movetox:
                    self.rect.x -= self.movetox
                    self.movetox += self.movetox
                else:
                    self.rect.x -= self.speed
                    self.movetox += self.speed

        self.float_y += self.y_speed
        self.rect.y = int(self.float_y)
# Thoughts : How to spawn boss? Custom
    def check_for_collisions(self):
        global explosions,bugs,enemy_lasers,current_level,ship,overdrive_charge,lasers,mines,cur_frame,shake_intensity,max_overdrive
        memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
        if memory_error_alive == True:
            self.image.set_alpha(100)
            self.y_speed = 0.5 * self.og_y_speed
            self.max_creation_cooldown = 200
   
        else:
            self.max_creation_cooldown = 100
        for laser in lasers:
            memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
            if memory_error_alive == False or self.image_path == "memoryerror.png":
                self.y_speed = self.og_y_speed
                self.image.set_alpha(255)
                if self.rect.colliderect(laser):
                    if self.image_path != "sqlinjector.png":
                        self.hp -= laser.damage
                    if self.image_path == "sqlinjector.png":
                        self.hp -= laser.damage
                        laser.yv = laser.speed
                        laser.state = "Reflected"
                        self.float_y -= laser.knockback
                    
                    else:
                        for bug in bugs:
                            if self.x == bug.x:
                                bug.float_y -= laser.knockback
                        if laser in lasers:
                            if laser.pierce <= 0 or self.hp > 0 :
                                lasers.remove(laser)
                            elif self.hp <= 0:
                                laser.pierce -= 1
                    if self.hp <= 0:
                        global data_coins
                        if self.image_path == "exception.png":
                            data_coins += 1

                
            elif memory_error_alive == True:
                self.image.set_alpha(100)
                self.y_speed = 0.5 * self.og_y_speed
        if self.hp <= 0:
            global explosions
            color = (255,0,0)
            type_of_explosion = self.image_path
            explosion = [self.rect.x,self.rect.y,type_of_explosion] 
            print(explosion)
            explosions.append(explosion)
            self.kill()
            small_explosion_sound.play()
            if overdrive_charge < max_overdrive and ship.overdrive_duration <= 0:
                if self.image_path != "packetbug.png": 
                    overdrive_charge += 100
                else:
                    overdrive_charge += 0.25
            color = (0,255,0)
            if self.image_path == "exception.png":
                color = (0,255,0)
            elif self.image_path == "indentationerrorlow.png" or self.image_path == "indentationerror .png":
                color = (0,0,255)
            elif self.image_path == "indexerror.png":
                color = (255,165,0)
            elif self.image_path == "memoryerror.png":
                 color = (0,255,0)
                 for i in range(9):
                    particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8),random.choice([(0,255,0),(255,0,0),(255,255,0)])])
            elif self.image_path == "importerror.png":
                color = (165,42,42)
            elif self.image_path == "brokenpipe.png":
                color = (255,255,255)
            elif self.image_path == "typeerror.png":
                color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
            if self.image_path != "packetbug.png":
                for i in range(9):
                    particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8), color])
            else:
                for i in range(2):
                    particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8), color])
        
        for ship in pro_ships:
            if self.rect.colliderect(ship.rect):
                shake_intensity = 30
                if ship.is_dashing == False:
                    self.kill()
                    ship.hp -= self.damage
                    
                 
                else:
                    self.hp -= ship.dash_damage
        for file in files:
            if current_level != 20 and self.image_path != "packetbug.png":
                if self.rect.colliderect(file.rect):
                    self.hp = 0
                    file.hp -= self.damage
                    shake_intensity = 35
        global spacer
        if self.hp <= self.max_hp * 0.5 and self.image_path == "indentationerror.png":
            self.image_path = "indentationerrorlow.png"
            self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(self.w,self.h))
            self.rect = self.image.get_rect(topleft = (self.rect.x,self.rect.y))
        if self.image_path == "importerror.png":
            if self.creation_cooldown <= 0:
                child_bug = Bug(self.rect.x, self.rect.bottom,24,24,0,1,1,1)
                bugs.add(child_bug)
                self.creation_cooldown = self.max_creation_cooldown
            else:
                self.creation_cooldown -= 1

        if self.image_path == "brokenpipe.png" and self.cooldown <= 0:
            enemy_laser = EnemyLaser(self.rect.centerx - 2, self.float_y,9,9,damage=0.5,speed=6)
            enemy_lasers.append(enemy_laser)
            self.cooldown = self.max_cooldown
        elif self.image_path == "brokenpipe.png" and self.cooldown > 0:
            self.cooldown -= 1

        

        if self.image_path == "packetbug.png":
    
            if self.target_radius > 10:
                self.target_radius -= 0.36
            target_x = ship.rect.centerx + math.cos(self.orbit_angle) * self.target_radius
            target_y = ship.rect.centery + math.sin(self.orbit_angle) * self.target_radius

           
            dx = target_x - self.float_x
            dy = target_y - self.float_y
            distance = math.hypot(dx, dy)

        
            move_x = 0.0
            move_y = 0.0
            tracking_speed = 2 

            if distance > 2:
                move_x = (dx / distance) * tracking_speed
                move_y = (dy / distance) * tracking_speed
            else:
       
                self.orbit_angle += 0.02 

            for other_bug in bugs:
                if other_bug != self and other_bug.image_path == "packetbug.png":
                    sep_dx = self.rect.centerx - other_bug.rect.centerx
                    sep_dy = self.rect.centery - other_bug.rect.centery
                    sep_dist = math.hypot(sep_dx, sep_dy)
                    
                    if 0 < sep_dist < 24:
                        push_force = (24 - sep_dist) * 0.25
                        move_x += (sep_dx / sep_dist) * push_force
                        move_y += (sep_dy / sep_dist) * push_force


            self.float_x += move_x
            self.float_y += move_y
            self.rect.x = int(self.float_x)
            self.rect.y = int(self.float_y)



          
        if self.image_path == "nullpointererror.png":
            if self.null_cooldown <= 0:
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6)
                null_lasers.append(null_bullet)
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv=6,yv = 0)
                null_lasers.append(null_bullet)
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv=0,yv = -6)
                null_lasers.append(null_bullet)
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv= -6,yv = 0)
                null_lasers.append(null_bullet)

                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv = 6 , yv = 6)
                null_lasers.append(null_bullet)
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv= -6,yv = 0)
                null_lasers.append(null_bullet)
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv=6,yv = -6)
                null_lasers.append(null_bullet)
                null_bullet = NullLaser(self.rect.centerx,self.rect.centery,12,12,speed = 6,xv= -6,yv = -6)
                null_lasers.append(null_bullet)
                self.null_cooldown = self.max_null_cooldown
            else:
                self.null_cooldown -= 1

        
        if self.image_path == "deprecatedmethod.png" and self.hp <= 0:
                startx,starty = self.rect.x,self.rect.y
                for i in range(3):
                    for j in range(3):
                        bug = Bug(startx + i * 10,starty- colindex + j * 10 ,9,9,7,1,1,0.4,y_speed = 0)
                        bugs.add(bug)
                        bug.orbit_angle = random.uniform(0,2*math.pi)
                        bug.target_radius = random.uniform(140,180)
                bugs.remove(self)
        if self.image_path == "deprecatedgiant.png":
                if self.hp <= 0:
                    startx,starty = self.rect.x,self.rect.y
                    for i in range(10):
                        for j in range(10):
                            bug = Bug(startx + i * 10,starty- colindex + j * 10 ,9,9,7,1,1,0.4,y_speed = 0)
                            bugs.add(bug)
                            bug.orbit_angle = random.uniform(0,2*math.pi)
                            bug.target_radius = random.uniform(140,180)
                    bugs.remove(self)
                else:
                    if self.packetcooldown <= 0:
                        startx,starty = self.rect.x,self.rect.y
                        bug = Bug(startx,starty,9,9,7,1,1,0.4,y_speed = 0)
                        bugs.add(bug)
                        bug.orbit_angle = random.uniform(0,2*math.pi)
                        bug.target_radius = random.uniform(140,180)
                        self.packetcooldown = 10
                    else:
                        self.packetcooldown -= 1
        if self.image_path == "sqlinjector.png":
            for bug in bugs:
                if bug.rect.x == self.rect.x:
                    bug.y_speed = self.y_speed
        else:
            for bug in bugs:
                if not(bug.rect.x == self.rect.x and bug.image_path == "sqlinjector.png") and not(any(bug.image_path == "memoryerror.png" for bug in bugs)):
                    self.y_speed = self.og_y_speed


        if self.image_path == "racecondition.png" and self.teleport_cooldown <= 0:
       
            for laser in lasers:
                if laser.x >= self.rect.left and laser.x <= self.rect.right and laser.y >= self.rect.y:
                    self.rect.x = random.randint(self.rect.x - 100,self.rect.x + 100)
                    self.teleport_cooldown = self.max_teleport_cooldown
                    self.float_y -= 25
            for mine in mines:
                if mine.rect.x >= self.rect.left and mine.rect.x <= self.rect.right and mine.rect.y >= self.rect.y and mine.rect.y <= self.rect.y + 75:
                        self.rect.x = random.randint((self.rect.x -25 - 100),(self.rect.x +25 + 100))
      
                        self.teleport_cooldown = self.max_teleport_cooldown
                        self.float_y -= 25
        elif self.image_path == "racecondition.png":
            self.teleport_cooldown -= 1


        if self.image_path == "sleepthread.png":
            if self.sleep_freeze_cooldown <= 0:
                missile = FreezeMissile(self.rect.x,self.rect.y,10,10,1,1,0,0,4,2.5,200)
                enemy_missiles.append(missile)
                self.sleep_freeze_cooldown = self.max_sleep_freeze_cooldown
            else:
                self.sleep_freeze_cooldown -= 1
    def explode_into_pieces(self):
        for laser in lasers:
            if self.rect.colliderect(laser):
                if laser in lasers:
                    lasers.remove(laser)
                    self.hp -= laser.damage

        if self.hp <= 0:
            print("WWWhkjdwahkjhjhkjjhsddwaswddwasdwdwasdsdwdasaddwasddwasdhkjhkjhdwasdwasddwdwasddwasdwasdhkdawdala;lskdw;lslkldad;ldsasjhkWWWWWdwWWnkjhdwasdgjhghjhgkjdwashkjhdhWWWWWWdwasdwadlkljklkjlkjkjwasdadrdgddsdfsdsdwasdassawwdasadwaskjhjWADASDEFSFDF")
            for i in range(4):
                particle = [[self.rect.centerx, self.rect.centery] , [random.randint(-4,4),random.randint(-4,4)] , random.randint(3,8), (255,0,0)]
                particles.append(particle)
                


class EnemyLaser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color = (0,0,255),speed = 9, damage = 1, knockback = 0,pierce = 0,xv=0,yv = 0):
        super().__init__(x, y, w, h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
        self.damage = damage
        self.knockback = knockback
        self.pierce = pierce
        self.xv = xv
        self.gd = 304
        self.yv = yv
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(game_canvas,self.color,laser)
    def update(self):
        global enemy_lasers,enemy_missiles
        if self.yv == 0 and self.xv == 0:
            self.y += self.speed
        else:
            self.x += self.xv
            self.y += self.yv

        if self.colliderect(ship.rect):
            if self in enemy_lasers:
                enemy_lasers.remove(self)
            ship.hp -= self.damage
        elif self.top > HEIGHT or self.bottom < 0 or self.left > WIDTH or self.right < 0:
            if self in enemy_lasers:
                enemy_lasers.remove(self)
       
############## Null lasers
class NullLaser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color = (128,0,128),speed = 3, damage = 3, knockback = 0 ,pierce = 0,xv = 0,yv = 0 ):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color 
        self.speed = speed
        self.damage = damage 
        self.knockback = 0
        self.pierce = 0
        self.invert_duration = 600
        self.xv = xv
        self.yv = yv
    def draw(self):
        global game_canvas
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(game_canvas,self.color,laser)
    def update(self):
        global null_lasers
        if self.xv == 0 and self.yv == 0:
            self.y += self.speed
        else:
            self.x += self.xv
            self.y += self.yv
        if self.colliderect(ship.rect):
            null_lasers.remove(self)
            ship.invert_duration += 100
        if self.left < 0 or self.right > WIDTH or self.top < 0 or self.bottom > HEIGHT:
            null_lasers.remove(self)


class MemoryError(Bug):
    def __init__(self, x, y, w, h, image_path, damage, hp, speed, y_speed=0.5):
        super().__init__(x, y, w, h, image_path, damage, hp, speed, y_speed)

class Mine(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,damage,xv,yv,speed,final_dest_x,final_dest_y):
        super().__init__()
        self.x = x
        self.float_x = float(x)
        self.y = y
        self.float_y = float(y)
        self.w = w
        self.image_path = "mine.png"
        self.h = h
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.color = (0,165,255)
        self.explosion_radius = 60
        self.damage = damage
        self.tx = final_dest_x
        self.ty = final_dest_y
        self.startx = x
        self.starty = y
        self.is_stuck = False
        self.slide_speed = 0.05
        self.state = "Normal"
    def update(self):
        global bugs,bosses,ship,pro_ships,coverbricks
        if not self.is_stuck:
            dx = self.tx - self.float_x
            dy = self.ty - self.float_y

            self.float_x += dx * self.slide_speed
            self.float_y += dy * self.slide_speed

            self.rect.x = int(self.float_x)
            self.rect.y = int(self.float_y)

            if math.hypot(self.float_x-self.tx,self.float_y - self.ty) < 1.5:
                self.rect.centerx = int(self.float_x)
                self.rect.centery = int(self.float_y)
                self.is_stuck = True
            for bug in bugs:
                if self.rect.colliderect(bug.rect):
                    if bug.image_path == "sqlinjector.png":
                        self.tx = self.startx
                        self.ty = self.starty
                        self.state = "Reversed"
                        self.image_path = "minetriggered.png"
                        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(self.w,self.h))
                        self.rect = self.image.get_rect(topleft = (self.x,self.y))
        if self.is_stuck:
            if self.state != "Reversed":
                for bug in bugs:
                    distance = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
                    if distance <= 35 or self.rect.colliderect(bug.rect) :
                        self.explode()
                        break
                for bug in bosses:
                    distance = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
                    if distance <= 35 or self.rect.colliderect(bug.rect) :
                        self.explode()
                        break
                for bug in coverbricks:
                    distance = math.hypot(bug.centerx - self.rect.centerx,bug.centery - self.rect.centery)
                    if distance <= 35 or self.rect.colliderect(bug) :
                        self.explode()
                        break
            
            else:
                distance = math.hypot(ship.rect.centerx - self.rect.centerx,ship.rect.centery - self.rect.centery)
                if distance <= 35 or self.rect.colliderect(ship.rect):
                    self.explode()
    

    def explode(self):
        global bugs,bosses,pro_ships,shake_intensity,explosion_sound
        shake_intensity = 15
        explosion_sound.play()
        if not self.state == "Reversed":
            for bug in bugs:
                dist = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
                if dist <= self.explosion_radius or self.rect.colliderect(bug.rect):
                    bug.hp -= self.damage

            for bug in bosses :
                dist = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
                if dist <= self.explosion_radius or self.rect.colliderect(bug.rect):
                    bug.hp -= self.damage

            for bug in coverbricks:
                dist = math.hypot(bug.centerx - self.rect.centerx,bug.centery - self.rect.centery)
                if dist <= self.explosion_radius or self.rect.colliderect(bug):
                    bug.hp -= self.damage

        else:
            for bug in pro_ships:
                dist = math.hypot(bug.rect.centerx - self.rect.centerx,bug.rect.centery - self.rect.centery)
                if dist <= self.explosion_radius or self.rect.colliderect(bug.rect):
                    bug.hp -= self.damage
        for i in range(20):
            particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-4,4),random.randint(-4,4)] , random.randint(3,8), (255,0,0)])
        self.kill()
                



        
class Laser(pygame.rect.Rect):
    def __init__(self,x,y,w,h,color=(255,0,255),speed = 9,damage = 1,knockback = 0,pierce = 0,vx = 0 ,vy = 0):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = speed
        self.damage = damage
        self.knockback = knockback
        self.pierce = pierce
        self.xv = vx
        self.yv = vy
        self.float_x = float(x)
        self.float_y = float(y)
        self.state = "Normal"
    def draw(self):
  
        pygame.draw.rect(game_canvas,self.color,self)
    def update(self):
        global enemy_lasers,ship,lasers
        if self.xv == 0 and self.yv == 0:
            self.y -= self.speed
        else:
            self.float_x += self.xv 
            self.float_y += self.yv
            self.x = int(self.float_x)
            self.y = int(self.float_y)
        if self.state == "Normal":
            for enlaser in enemy_lasers:
                if self.colliderect(enlaser):
                    lasers.remove(self)
                    try:
                        enemy_lasers.remove(enlaser)
                    except:
                        pass
        else:
 
            self.color = (255,0,0)
            self.x += self.xv
            self.y += self.yv
            if self.colliderect(ship):
                ship.hp -= self.damage
                lasers.remove(self)
        for bug in bugs:
            if self.colliderect(bug.rect):
                if self.pierce <= 0 or bug.hp > 0 : #ASdsadasddsasf
                    if self in lasers:
                        lasers.remove(self)
                    bug.hp -= self.damage
                elif bug.hp <= 0:
                    self.pierce -= 1
                  
    

        if self.top <= 0 :
            lasers.remove(self)
            coord_pairs = [(-4.24,4.24),(-3.00,5.20),(-1.55,5.80),(0.00,6.00),(1.55,5.80),(3.00,5.20),(4.24,4.24)]

        # addwwadwasdwdwsasdsdsdwasdwdddwadswaadssdwdwasdadwasdgffjwdsdasddddwasddwasdfdwasdfesdfddwasddwwasdasddwasdwswasddwsdwasdwasddsfghfdwadsdwsaddwdwfgrfedwasddwasdsfedwaddwasdwawdddhjkdsdwdasddwasddwdwasdaddwasddwadwasdsdddwasdddddddddddddddddddddddddddwasdwadwassdwasddadsgdfgdwddsfsedwsasdasdfdwasfedddwdwadgthtghgjdwasddwsysddwsdadwasdwasdwasdsdasdwsddwadsasdasddwasddwdwasdasddwddwasdsdwasdwdwsdasddsdwadwsdsadsdwaswdwasdadasdwdwasdwsdasdwdwasasdwsdwasddsdwasddwadwasdwasddasdwasdwadwasdwassdasdddwaswasddwddwasdwsdwasddssdddasdwdwasdasdwasddwasdwdwasdgddwadwasdwassddsddwasdddfhfghfghffddwasddsddwasdwasdsddwasdwasddwasddsawdasassdwfsdfdfdwdwasdadwsdsdwdawsddwadwasddsddwasddwsdasddwasdsddasdwdwasddsdsdsasdasdwaddasddwasdwasdsdsasddwasdfsddsaasddwadwassdsawasdsdwasdwasdwasddwasddwadwasddwasddf
class FileTower(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h,image_path,hp):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h 
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.hp = hp
        self.max_hp = hp
        self.max_max_hp = hp
        red_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,100)
        green_rect = pygame.rect.Rect(self.rect.centerx,self.rect.centery + 25,5,(100/self.max_hp) * self.hp)
        self.heal = 0
    def update(self):
        global files_destroyed,enemy_lasers
        if self.hp <= 0:
            self.kill()
            files_destroyed = True
        red_rect = pygame.rect.Rect(self.rect.x + 10,self.rect.top - 25,50,5)
        green_rect = pygame.rect.Rect(self.rect.x + 10,self.rect.top - 25,(50/self.max_hp) * self.hp,5)
        pygame.draw.rect(game_canvas,(255,0,0),red_rect)
        pygame.draw.rect(game_canvas,(0,255,0),green_rect)
        for laser in enemy_lasers:
            if self.rect.colliderect(laser):
                self.hp -= laser.damage
                enemy_lasers.remove(laser)
        if self.hp < self.max_hp:
            self.hp += self.heal
class SymbolSprite(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h,image_path):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))


class UpgradeCard(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, typeofcard, upgradeitem, amounttoadd, lineupnum,upgrade_name = "Laser"):
        super().__init__() 
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.typeofcard = typeofcard
        self.upgradeitem = upgradeitem
        self.amounttoadd = amounttoadd
        self.x_values = [100, 400, 700]
        self.lineupnum = lineupnum
        self.upgrade_name = upgrade_name
        self.the_color = (255,255,255)
        
    def draw(self):
        
        self.x = self.x_values[self.lineupnum]
        card_rect = pygame.Rect(self.x, self.y, self.w, self.h)
        

        pygame.draw.rect(game_canvas, (142, 142, 142), card_rect)


        symbol = self.typeofcard
        if symbol == "Triangle":
            symbol = SymbolSprite(self.x, self.y, 70, 70, "redtriangle.png")
            self.the_color = (255,0,0)
        elif symbol == "Square":
            symbol = SymbolSprite(self.x, self.y, 70, 70, "orangesquare.png")
            self.the_color = (255,165,0)
        elif symbol == "Circle":
            symbol = SymbolSprite(self.x, self.y, 50, 50, "yellowcircle.png")
            self.the_color = (255,255,0)
        elif symbol == "Pentagon":
            symbol = SymbolSprite(self.x, self.y, 50, 50, "greenpentagon.png")
            self.the_color = (0,255,0)
        elif symbol == "Hexagon":
            symbol = SymbolSprite(self.x, self.y, 50, 50, "bluehexagon.png")
            self.the_color = (0,0,255)

        symbol.rect.center = (card_rect.centerx, card_rect.top + 60)
        symbols.add(symbol)

        type_text = card_font.render(f"Item Upgrading : {self.upgrade_name}", True, self.the_color)
        stat_text = card_font.render(f"Stat Upgrading : {self.upgradeitem}", True, self.the_color)
        description = card_font.render(f"Upgrade {self.upgradeitem} by {self.amounttoadd}", True, self.the_color)
 
        text_rect = description.get_rect()
        stat_rect = stat_text.get_rect()
        type_rect = type_text.get_rect()
        
      
        text_rect.center = (card_rect.centerx, card_rect.bottom - 30) 
        stat_rect.center = (card_rect.centerx, card_rect.bottom - 65) 
        type_rect.center = (card_rect.centerx, card_rect.bottom - 100) 

    
        game_canvas.blit(description, text_rect)
        game_canvas.blit(stat_text, stat_rect)
        game_canvas.blit(type_text, type_rect)
    def effect(self,pressed_key):
        ################## ALL CARD UPGRADES ############################
        if (self.lineupnum == 0 and  pressed_key == pygame.K_1) or (self.lineupnum == 1 and  pressed_key == pygame.K_2) or (self.lineupnum == 2 and pressed_key == pygame.K_3):
            if self.upgradeitem == "Cooldown":
                ship.max_cooldown += self.amounttoadd
                ship.max_max_cooldown += self.amounttoadd
    
                return True
            elif self.upgradeitem == "Ship Atk":
                ship.damage += self.amounttoadd
                ship.original_damage = ship.damage
                return True
            elif self.upgradeitem == "Ship Speed":
                ship.speed += self.amounttoadd
                return True
            elif self.upgradeitem == "Tower Health":
                for file in files.sprites():
                    file.hp += self.amounttoadd
                    file.max_hp += self.amounttoadd
                return True
            elif self.upgradeitem == "Knockback":
                ship.knockback += self.amounttoadd
                return True
     
            elif self.upgradeitem == "Pierce":
                ship.pierce += self.amounttoadd
                if card_options.__contains__(pierce_1):
                    card_options.remove(pierce_1)
                return True
            elif self.upgradeitem == "Dash":
                ship.can_dash = True
                ship.dash_damage += self.amounttoadd
                if card_options.__contains__(dash_1):
                    card_options.remove(dash_1)
                return True
            elif self.upgradeitem == "Heal":
                for file in files.sprites():
                    file.heal += self.amounttoadd
                if card_options.__contains__(heal_1):
                    card_options.remove(heal_1)
                return True
            elif self.upgradeitem == "Double":
                    ship.weapon_type = "Double"
                    try:
                        card_options.remove(shotgun_1)
                        card_options.remove(mines_1)
                        card_options.remove(double_1)
                    except:
                        pass
                    return True
            elif self.upgradeitem == "Shotgun":
                    ship.weapon_type = "Shotgun"
                    try:
                        card_options.remove(shotgun_1)
                        card_options.remove(mines_1)
                        card_options.remove(double_1)
                    except:
                        pass

                    return True
            elif self.upgradeitem == "Mines":
                    ship.weapon_type = "Mine"
                    try:
                        card_options.remove(shotgun_1)
                        card_options.remove(mines_1)
                        card_options.remove(double_1)
                    except:
                        pass
                    return True
       
        return False



class RecursionBoss(pygame.sprite.Sprite):
    def __init__(self, x,y,w,h,image_path,damage,hp,id):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = 800
        self.id = id
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.damage = damage

        self.max_hp = 800
        self.create_child_cooldown = 300
        self.max_create_chile_cooldown = self.create_child_cooldown
        self.laser_cooldown = 125
        self.max_laser_cooldwon = self.laser_cooldown
        self.stage = "Base"
        self.direction = "None"
        self.speed = 2.4
        self.float_x = self.x
        self.float_y = self.y
        self.phase = "Movement"
        self.frame_shoot_delay = 5
        self.burst_count = 0
        self.max_burst_count = 4
        self.beam_count = 0
        self.max_beam_count = 20
        self.shoot_style = 2
        self.started_shooting = False
        self.giant_beam_count = 0 
        self.max_giant_beam_count = 3
        self.shots_fired = 0
    def update(self):
        global bugs
        if self.stage == "Moving":
            self.shoot_style = random.choice((1,2,3))
            if self.direction == "None":
                self.direction = random.choice(("Left","Right"))
            if self.direction == "Left":
                self.float_x -= self.speed
                self.rect.x = int(self.float_x)
                if self.rect.left <= 0:
                    self.direction = "Right"
            if self.direction == "Right":
                self.float_x += self.speed
                self.rect.x = int(self.float_x)
                if self.rect.right >= WIDTH:
                    self.direction = "Left"
            
            self.rect.y = int(self.float_y) 
        if self.hp <= 0:
            self.kill()
            bugs.empty()
            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (0,255,0)])
            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (0,0,255)])
            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (255,0,0)])

            for i in range(90):
                particles.append([[self.rect.centerx, self.rect.centery] , [random.randint(-10,10),random.randint(-10,10)] , random.randint(4,20), (128,0,128)])


        red_rect = pygame.rect.Rect(self.rect.centerx  - self.w // 2 + 50,self.rect.top - 25,150,5)
        green_rect = pygame.rect.Rect(self.rect.centerx  - self.w // 2 + 50,self.rect.top - 25,(150/self.max_hp) * self.hp,5)
        pygame.draw.rect(game_canvas,(255,0,0),red_rect)
        pygame.draw.rect(game_canvas,(0,255,0),green_rect)


    def check_for_collisions(self):
            global bugs,enemy_lasers
            memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
            if memory_error_alive == True:
                self.image.set_alpha(100)
                self.y_speed = 0
                self.max_creation_cooldown = 200
            else:
                self.max_creation_cooldown = 100
            for laser in lasers:
                memory_error_alive = any(bug.image_path == "memoryerror.png" for bug in bugs)
                if memory_error_alive == False or self.image_path == "memoryerror.png":
                    self.image.set_alpha(255)
                    if self.rect.colliderect(laser):
                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (0,255,0)])
                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (0,0,255)])
                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (255,0,0)])

                        for i in range(2):
                            particles.append([[laser.centerx, laser.centery] , [random.randint(-2,2),random.randint(-2,2)] , random.randint(4,8), (128,0,128)])
                        self.hp -= laser.damage
                        self.float_y -= laser.knockback
                        for bug in bugs:
                            if self.x == bug.x:
                                bug.float_y -= laser.knockback
                        if laser in lasers:
                            if laser.pierce <= 0 or self.hp > 0 :
                                lasers.remove(laser)
                            elif self.hp <= 0:
                                laser.pierce -= 1
                elif memory_error_alive == True:
                    self.image.set_alpha(100)
                    self.y_speed = 0
    def shoot(self):
        coord_pairs = [(-4.24,4.24),(-3.00,5.20),(-1.55,5.80),(0.00,6.00),(1.55,5.80),(3.00,5.20),(4.24,4.24)]
        self.speed = 0
        if self.hp <= 200:
            self.max_cooldown = 62.5
        if self.laser_cooldown <= 0:
            
            self.stage = "Shooting"
            if self.shoot_style == 1:
                for vx,vy in coord_pairs:
                    bullet = BossLaser(self.rect.x+147,self.rect.centery,vx ,vy,1,(255,0,0),speed=6)
                    boss_lasers.append(bullet)

                self.burst_count += 1

                if self.burst_count < self.max_burst_count:
                    self.laser_cooldown = self.frame_shoot_delay
                    if self.burst_count == 1:
                        if self.hp <= 499:
                            if self.hp <= 499 and self.shots_fired >= 3:
                                self.shots_fired = 0
                                for i in range(5):
                                    the_choice = random.choice(("exception.png",
                                                    "indentationerror.png",
                                                    "indexerror.png",
                                                    "memoryerror.png",
                                                    "importerror.png",
                                                    "brokenpipe.png","typeerror.png"))
                                    
                                    if the_choice == "exception.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,0,1,1,1)
                                                                        
                                    elif the_choice == "indentationerror.png":
                                            bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,1,1.5,3,0.8)

                                    elif the_choice == "indexerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,2,1,1,1,y_speed = 1.2)
                                    elif the_choice == "memoryerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,3,3,10,0.4,y_speed = 0.2)
                                    elif the_choice == "importerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,4,3,15,0.25,y_speed = 0.2)

                                    elif the_choice == "brokenpipe.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,5,3,1,0.4,y_speed = 0.5)

                                    elif the_choice == "typeerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,6,random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5))
                                    bugs.add(bug)

                else:
                    self.burst_count = 0
                    self.laser_cooldown = self.max_laser_cooldwon
                    self.stage = "Moving"
                    self.shots_fired += 1
            elif self.shoot_style == 2:
                self.stage = "Shooting"
                bullet1 = BossLaser(self.rect.centerx - 22,self.rect.centery,0,8,1,(255,255,0),9)
                bullet2 = BossLaser(self.rect.centerx + 22,self.rect.centery,0,8,1,(255,255,0),9)
                boss_lasers.append(bullet1)
                boss_lasers.append(bullet2)

                self.beam_count += 1

                if self.beam_count < self.max_beam_count:
                    self.laser_cooldown = 1
                    if self.beam_count == 1:
                        if self.hp <= 499  and self.shots_fired >= 3:
                            for i in range(5):
                                the_choice = random.choice(("exception.png",
                                                "indentationerror.png",
                                                "indexerror.png",
                                                "memoryerror.png",
                                                "importerror.png",
                                                "brokenpipe.png","typeerror.png"))
                                
                                if the_choice == "exception.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,0,1,1,1)
                                                                    
                                elif the_choice == "indentationerror.png":
                                        bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,1,1.5,3,0.8)

                                elif the_choice == "indexerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,2,1,1,1,y_speed = 1.2)
                                elif the_choice == "memoryerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,3,3,10,0.4,y_speed = 0.2)
                                elif the_choice == "importerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,4,3,15,0.25,y_speed = 0.2)

                                elif the_choice == "brokenpipe.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,5,3,1,0.4,y_speed = 0.5)

                                elif the_choice == "typeerror.png":
                                    bug = Bug(self.rect.centerx + i * 35,self.rect.bottom,24,24,6,random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5))
                                bugs.add(bug)
                    
                else:
                    self.beam_count = 0
                    self.laser_cooldown = self.max_laser_cooldwon
                    self.stage = "Moving"
                    self.shots_fired += 1
            elif self.shoot_style == 3:
                bullet1 = BossLaser(random.randint(self.rect.x,self.rect.right-24),self.rect.centery,0,8,10,(255,255,0),9,w=48,h=48)
                boss_lasers.append(bullet1)

                self.giant_beam_count += 1

                if self.giant_beam_count < self.max_giant_beam_count:
                    self.laser_cooldown = 30
                else:
                    self.laser_cooldown = self.max_laser_cooldwon
                    self.giant_beam_count = 0
                    self.stage = "Moving"
                    self.shots_fired += 1

        
        elif self.laser_cooldown > 0:
            self.laser_cooldown -= 1


        

        self.speed = 2.4



    
        

class BossLaser(pygame.rect.Rect):
    def __init__(self,x,y,xv,yv,damage,color,speed,w=6,h=6):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.w = w
        self.h = h
        self.damage = damage
        self.color = color
        self.speed = speed
        self.float_x = x
        self.float_y = y
        self.knockback = 0
        self.pierce = 0 
    def update(self):
        global boss_lasers,ship,lasers
        self.float_x += self.xv
        self.float_y += self.yv

        self.x = int(self.float_x)
        self.y = int(self.float_y)

        if (self.top < 0 or       
        self.bottom > HEIGHT or     
        self.left > 1280 or  
        self.right < 0):       
        
            try:
                boss_lasers.remove(self)
                
            except:
                try:
                    lasers.remove(self)
                except:
                    pass

        if self.colliderect(ship.rect) and (self.color == (255,0,0) or self.color == (255,255,0) or self.color == (0,255,0)):
            try:
                boss_lasers.remove(self)
                ship.hp -= self.damage
            except:
                try:
                    lasers.remove(self)
                except:
                    pass

    
    def draw(self):
        laser = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(game_canvas,self.color,laser)


stars = pygame.sprite.Group()
class Star(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        size = random.randint(10,30)
        self.images = [pygame.transform.scale(pygame.image.load("star.png").convert_alpha(),(size,size)),pygame.transform.scale(pygame.image.load("otherstar.png").convert_alpha(),(size,size)),pygame.transform.scale(pygame.image.load("otherotherstar.png").convert_alpha(),(size,size))]
        self.image = self.images[random.randint(0,len(self.images)-1)]
        self.rect = self.image.get_rect(topleft = (x,y))
        self.draw_self = True
        self.blink_cooldown = random.randint(10,50)
        self.blink_time = random.randint(5,12)
        self.max_blink_cooldown = self.blink_cooldown
        self.max_blink_time = self.blink_time
    def update(self):
        if self.blink_cooldown > 0:
            self.draw_self = True
            self.blink_cooldown -= 1

        elif self.blink_cooldown <= 0:
            self.draw_self = False
            self.blink_time - self.max_blink_time

        if self.blink_time > 0 and self.blink_cooldown <= 0:
            self.blink_time -= 1
            self.draw_self = False
        elif self.blink_time <= 0 and self.draw_self == True:
            self.blink_cooldown = self.max_blink_cooldown
star = Star(100,100,30,30)
stars.add(star)
class Shockwave:
    def __init__(self,x,y,max_radius = 120,dmg = 2):
        self.x = int(x)
        self.y = int(y)
        self.radius = 5
        self.max_radius = max_radius
        self.speed = 8
        self.alpha = 255
        self.dmg = dmg
    def update(self):
        global pro_ships,shockwaves,bosses
        self.radius += self.speed
        self.alpha = int(255-(self.radius / self.max_radius))
        for ship in pro_ships:
            dist = math.hypot(ship.rect.centerx - self.x,ship.rect.centery-self.y)
            if dist <= self.radius:
                ship.hp -= (self.dmg / 600)
        for ship in bugs:
                dist = math.hypot(ship.rect.centerx - self.x,ship.rect.centery-self.y)
                if dist <= self.radius:
                    ship.hp -= (self.dmg / 400)
        for ship in bosses:
            dist = math.hypot(ship.rect.centerx - self.x,ship.rect.centery-self.y)
            if dist <= self.radius:
                ship.hp -= (self.dmg / 600)
        if self.radius > self.max_radius:
            if self in shockwaves:
                shockwaves.remove(self)

    def draw(self):
        global game_canvas
        if self.alpha > 0:
            temp_surf = pygame.Surface((self.radius * 2 + 10,self.radius * 2 + 10),pygame.SRCALPHA)

            ring_color = (0,0,255,self.alpha)
            pygame.draw.circle(temp_surf,ring_color,(self.radius + 5,self.radius + 5),self.radius,12)
            game_canvas.blit(temp_surf,(self.x - self.radius - 5,self.y - self.radius - 5))
            



global_trail_surf = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)




class FreezeMissile(pygame.rect.Rect):
    def __init__(self,x,y,w,h,target_x,target_y,xv,yv,move_speed,turn_speed,freeze_duration):
        super().__init__(x,y,w,h)
        self.x = x
        self.float_x = float(x)
        self.y = y
        self.float_y = float(y)
        self.target_x = target_x
        self.target_y = target_y
        self.xv = xv
        self.yv = yv
        self.move_speed = 5
        self.turn_speed = turn_speed
        self.freeze_duration = freeze_duration
        self.color = (0,0,255)
        self.history = []
        self.max_trail_len = 12
        self.current_angle = 0 

    def update(self):
        global ship,game_canvas,pro_ships,lasers,global_trail_surf
        dx = ship.rect.centerx - self.centerx
        dy = ship.rect.centery - self.centery
        target_angle= math.atan2(dy,dx)

        angle_difference = target_angle - self.current_angle
        angle_difference = (angle_difference + math.pi) % (2 * math.pi) - math.pi

        max_turn_rate = 0.035

        if abs(angle_difference) <= max_turn_rate:
            self.current_angle = target_angle
        else:
            if angle_difference > 0:
                self.current_angle += max_turn_rate
            else:
                self.current_angle -= max_turn_rate

        dist = math.hypot(dx,dy)
        if dist > 0:
            self.float_x += math.cos(self.current_angle) * self.move_speed
            self.float_y += math.sin(self.current_angle) * self.move_speed
        self.x = int(self.float_x)
        self.y = int(self.float_y) 
        self.history.append((int(self.x),int(self.y)))
        if len(self.history) > self.max_trail_len:
            self.history.pop(0)

        trail_surface = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        for i,pos in enumerate(self.history):
            factor = i / len(self.history)

            alpha = int(factor * 180)
            trail_color = (self.color[0],self.color[1],self.color[2],alpha)
            trail_size = int(self.w * (0.4 + 0.6 * factor))
            mis = pygame.Rect(pos[0],pos[1],trail_size,trail_size)
            pygame.draw.rect(global_trail_surf,trail_color,mis)

     

        
        missile = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(game_canvas,self.color,missile)
        
        for freeze_mis in enemy_missiles:
                if freeze_mis != self:
                    if self.colliderect(freeze_mis):
                        enemy_missiles.remove(freeze_mis)
                        self.w += 12
                        self.h += 12
                        self.freeze_duration += self.w * 12

        for ship in pro_ships:
            if self.colliderect(ship.rect):
                ship.freeze_duration += self.freeze_duration
                self.explode()

        for laser in lasers:
            if self.colliderect(laser):
                self.explode()
                if laser in lasers:
                    lasers.remove(laser)

        if self.left <= 0 or self.right >= WIDTH or self.top <= 0 or self.bottom >= HEIGHT:
            self.explode()
    def explode(self):
        for i in range(25):
            particles.append([[self.centerx, self.centery] , [random.randint(-6,6),random.randint(-6,6)] , random.randint(4,12), (0,0,255)])
            shockwave = Shockwave(self.centerx,self.centery,min(self.w * 12,250),2)
            shockwaves.append(shockwave)
            if enemy_missiles.__contains__(self):
                enemy_missiles.remove(self)


class Bluegame_canvasOfDeath(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,image_path):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = 600
        self.float_x = float(x)
        self.float_y = float(y)
        self.image_path = image_path
        self.image = pygame.transform.scale(pygame.image.load(self.image_path).convert_alpha(),(w,h))
        self.rect = self.image.get_rect(topleft = (x,y))
        self.x_speed = 1.6
        self.speed = self.x_speed
        self.y_speed = 0.1
        self.image_path = image_path
        self.create_child_cooldown = 500
        self.max_create_child_cooldown = self.create_child_cooldown
        self.missile_cooldown = 750
        self.max_missile_cooldown = self.missile_cooldown
        self.stage = 1
        self.direction = random.choice(("Left","Right"))
        self.packet_cooldown = 3
        self.max_hp = self.hp
        self.missile_payload = 5
        self.missiles_launched = 0
        self.spawn_packets = 20
        self.spawned_packets = 0
        self.created_cover = False
        self.cover_layers = 4
        self.layer_thickness = 6
        self.blockhp = 3
    def update(self):
        global items,coverbricks
        curx , cury = 0,0
        if not self.created_cover:
            for i in range(self.layer_thickness):
                for i in range(40):
                    cover = CoverBrick(self.rect.left+curx,self.rect.bottom+cury,self.w/40,self.w/40,self.blockhp,(255,0,0),xshift=curx,yshift=cury)
                    coverbricks.append(cover)
                    curx += self.w/40
                cury += self.w/40 
                curx = 0
            curx , cury = 0,0
            for i in range(30):
                for i in range(self.layer_thickness):
                    cover = CoverBrick((self.rect.left-(self.w/40*self.layer_thickness))+curx,self.rect.top+cury-10,self.w/40,self.w/40,self.blockhp,(255,0,0),xshift=curx,yshift=cury)
                    coverbricks.append(cover)
                    curx += self.w/40
                cury += self.w/40
                curx = self.rect.left-self.w/40*self.layer_thickness + 6

            curx , cury = 0,0
            for i in range(30):
                for i in range(self.layer_thickness):
                    cover = CoverBrick((self.rect.left-(self.w/40*self.layer_thickness))+curx,self.rect.top+cury-10,self.w/40,self.w/40,self.blockhp,(255,0,0),xshift=curx,yshift=cury)
                    coverbricks.append(cover)
                    curx += self.w/40
                cury += self.w/40
                curx = self.rect.right
            curx , cury = 0,0
            for i in range(self.layer_thickness):
                for i in range(55):
                    cover = CoverBrick(self.rect.x+curx,self.rect.top-cury,self.w/40,self.w/40,self.blockhp,(255,0,0),xshift=curx,yshift=cury)
                    coverbricks.append(cover)
                    curx += self.w/40
                cury += self.w/40 
                curx = -34
            self.created_cover = True
        if self.stage <= 5:
            if self.direction == "None":
                self.direction = random.choice(("Left","Right"))
            if self.direction == "Left":
                self.float_x -= self.speed
                self.rect.x = int(self.float_x)
                if self.rect.left <= 0:
                    self.direction = "Right"
            if self.direction == "Right":
                self.float_x += self.speed
                self.rect.x = int(self.float_x)
                if self.rect.right >= WIDTH:
                    self.direction = "Left"
                    
            self.rect.y = int(self.float_y) 

        if self.stage == 1 or self.stage == 2:
            if self.missile_cooldown <= 0:
                if self.missiles_launched < self.missile_payload:
                    missile = FreezeMissile(self.rect.centerx,self.rect.centery,12,12,ship.x,ship.y,0,0,3,0.0036,100)
                    enemy_missiles.append(missile)
                    self.missile_cooldown = 25
                    self.missiles_launched += 1
                else:
                    self.missile_cooldown = 750
                    self.missiles_launched = 0

            else:
                self.missile_cooldown -= 1

        for laser in lasers:
            if self.rect.colliderect(laser):
                self.hp -= laser.damage
                if laser in lasers:
                    lasers.remove(laser)
        if self.packet_cooldown <= 0 and self.stage == 2:

            if self.spawned_packets <= self.spawn_packets: 
                packet = Bug(self.rect.centerx,self.rect.bottom ,9,9,7,1,1,0.4,y_speed = 0)
                bugs.add(packet)
                self.packet_cooldown = 5
                self.spawned_packets += 1
            else:
                self.packet_cooldown = 1000
                self.spawned_packets = 0
        else:
            self.packet_cooldown -= 1

        if self.hp <= 0.9 * self.max_hp:
            self.stage = 2
        if self.hp <= 0:
            self.kill()
            coverbricks.clear()
            return
        red_rect = pygame.rect.Rect(self.rect.centerx  - self.w // 2 + 50,self.rect.top - 40,150,5)
        green_rect = pygame.rect.Rect(self.rect.centerx  - self.w // 2 + 50,self.rect.top - 40,(150/self.max_hp) * self.hp,5)
        pygame.draw.rect(game_canvas,(255,0,0),red_rect)
        pygame.draw.rect(game_canvas,(0,255,0),green_rect)

class CoverBrick(pygame.rect.Rect):
    def __init__(self,x,y,w,h,hp,color,xshift ,yshift):
        super().__init__(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = hp
        self.color = color
        self.max_hp = hp
        self.xshift = xshift
        self.yshift = yshift
        self.startx = startx
    def draw(self):
        global game_canvas,bosses
        brick = pygame.rect.Rect(self.x,self.y,self.w,self.h)
        pygame.draw.rect(game_canvas,self.color,brick)
        
    def update(self):
        global lasers,ship,bosses
        for boss in bosses:
            self.x = boss.rect.x + self.xshift
        for laser in lasers:
            if self.colliderect(laser):
                self.hp -= laser.damage
                if laser in lasers:
                    lasers.remove(laser)
        for mine in mines:
            if self.colliderect(mine.rect):
                mine.tx = random.randint(0,WIDTH-20)
                mine.ty = random.randint(120,500)
        if self.hp <= 0:
            if self in coverbricks:
                coverbricks.remove(self)
                packet = Bug(self.centerx,self.bottom ,9,9,7,0.25,1,0.4,y_speed = 0)
                bugs.add(packet)




pro_ships = pygame.sprite.Group()
pro_ships_2= pygame.sprite.Group()
coverbricks = []
ship = Ship(400,600,27,33,"ship1.png",1,10)   
ship2 = Ship(800,600,27,33,"ship2.png",1,10)
ship.is_local = True
ship2.is_local = False
pro_ships_2.add(ship2)
shockwaves = []
enemy_missiles = []    
null_lasers = []
boss_lasers = []
enemy_lasers = []
keys = pygame.key.get_pressed()
mines = pygame.sprite.Group()
files = pygame.sprite.Group()
symbols = pygame.sprite.Group()
main = FileTower(WIDTH//2 - 40 , HEIGHT - 130,80,120,"main.png",12)
server = FileTower(WIDTH//2 - 140 , HEIGHT - 130,80,120,"server.png",8)
client = FileTower(WIDTH//2 + 60 , HEIGHT - 130,80,120,"client.png",8)
image_folder = FileTower(WIDTH//2 + 160 , HEIGHT - 120,120,110,"game_sprites.png",8)
spritesheets = FileTower(WIDTH//2 - 280 , HEIGHT - 120,120,110,"spritesheets.png",8)
devlog = FileTower(WIDTH//2 - 380 , HEIGHT - 130,80,120,"devlog.png",8)
error_log = FileTower(WIDTH//2 + 300 , HEIGHT - 130,100,120,"error_log.png",8)
readme = FileTower(WIDTH//2 - 480 , HEIGHT - 130,80,120,"readme.png",8)
gitignore = FileTower(WIDTH//2 + 410 , HEIGHT - 130,80,120,"gitignore.png",8)
cards = []
cooldown_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Square","Cooldown",-((ship.max_cooldown / 15) * 0.5) ,0)
################ ALL CARDS ####################################
atk_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Square","Ship Atk",+0.5,1)
ship_speed_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Triangle","Ship Speed",+1,2,upgrade_name="Ship")
tower_hp_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Circle","Tower Health",+2.5,2,upgrade_name="File Towers")
pierce_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Pentagon","Pierce",+1,2,upgrade_name="Laser")
dash_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Triangle","Dash",+3,2,upgrade_name="Ship")
heal_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Circle","Heal",+0.00083,2,upgrade_name="File Tower")
double_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Hexagon","Double",+1,2,upgrade_name="Weapons")
shotgun_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Hexagon","Shotgun",+1,2,upgrade_name="Weapons")
mines_1 = UpgradeCard(0,HEIGHT//2 - 180,200,300,"Hexagon","Mines",+1,2,upgrade_name="Weapons")
###################################################################
card_options = [cooldown_1,atk_1,ship_speed_1,tower_hp_1]
files_destroyed = False
files.add(readme)
files.add(devlog)
files.add(spritesheets)
files.add(server)
files.add(main)
files.add(client)
files.add(image_folder)
files.add(error_log)
files.add(gitignore)

ship.rect.x = WIDTH // 2 - (ship.w//2)
ship.rect.y = 400
pro_ships.add(ship)
lasers = []

mouse_pos = ()
mouse_pressed = False

########################ALL LEVELS######################333333
current_level = 1
level1 = [["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"],["e","e","e","e","e"]]
level2 = [["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"],["e","e","e","e","e","e","e"]]
level3 = [["i","i","i","i","i","i"],["e","e","e","e","e","e",],["i","i","i","i","i","i"],["e","e","e","e","e","e",]]
level4 = [["e","e","e","e","e","e"],["e","e","e","e","e","e",],["i","i","i","i","i","i"],["i","i","i","i","i","i",],["i","i","i","i","i","i",]]
level5 = [["i","i","i","i","i","i"],["e","e","e","e","e","e",],["e","e","e","e","e","e",],["x","x","x","x","x","x"]]
level6 = [["i","i","i","i","i","i"],["x","x","x","x","x","x",],["e","e","e","e","e","e",],["x","x","x","x","x","x"]]
level7 = [["i","i","i","i","i","i","i","i","i","i","i"],["i","i","i","i","i","i","i","i","i","i"]]
level9 = [["e","e","x","x","e","e","","","","e","e","x","x","e","e"],["i","i","i","i","i","i","","","","i","i","i","i","i","i"]]
level8 = [["i","e","x","i","e","x","i","e","x","i","e","x"],["i","e","x","i","e","x","i","e","x","i","e","x"],["i","e","x","i","e","x","i","e","x","i","e","x"]]
level10 = [["e","e","e","m","m","e","e","e"],["x",'i',"x",'i',"x",'i',"x",'i'],['e','e','e','e','e','e','e','e']]
level11 = [["m","e","e","e","e","e","e","m"],["x",'m',"x",'i',"x",'i',"x",'m'],['e','e','e','m','m','e','e','e']]
level12 = [["x","x","x"],["m","m","m"],["x","x","x"],["x","x","x"],["x","x","x"],["x","x","x"],["x","x","x"],]
level13 = [['x','x','x','x','x'],['x','x','x','x','x'],['p','p','p','p','p']]
level14 = [['p','p','p','p','p'],['e','e','e','e','e'],['e','e','e','e','e'],[""],[""],["i","i","i","i","i"]]
level15 = [["x","x","x","x","x","x","x","x"],["x","x","x","x","x","x","x","x"],["x","x","x","x","x","x","x","x"],["x","x","x","x","x","x","x","x"]]
level16 = [['b','b','b','b','b','b','b'],['i','i','i','i','i','i','i']]
level17 = [["","m","m","m",""],["b","b","b","b","b"],["b","b","b","b","b"]]
level18 = [["b","b","b","b","b"],["b","b","b","b","b"],["b","b","b","b","b"],["b","b","b","b","b"]]
level19 = [["b","b","b","b","b"],["b","b","b","b","b"],["t","t","t","t","t"]]
level20 = [["BOSS"]]
"""
Key so I can create levels easily
e = Regular
i = indentationError (small tank)
x = indexError (fast rusher)
m = MemoryError (tank & protector)
p = ImportError (Tank & Spawner)
b = BrokenPipeError (Fragile Shooter)
t = TypeError (RNG enemy)
s = Swarm (A bunch of small , tracking , ship-damaging bugs)
n = NullPointerError (Highly Tanky enemy that flips controls)
"""

level21 = [["x","b","x","b","x"],["t","t","t","t","t"],["t","t","t","t","t"],["t","t","t","t","t"]]
level22 = [["b","b","x","b","b"],["t","x","x","x","t"],["t","t","t","t","t"],["p","p","p","p","p"]]
level23 = [["s","s","s"],["s","s","s"],["s","s","s"]]
level24 = [["b","b","b","b","b"],["p","s","p"],["p","s","p"]]
level25 = [["b","b","b","b","b"],["p","p","p","p","p"],["x","x","s","x","x"]]
level26 = [["n","n","n","n","n"],["n","n","n","n","n"],["x","x","x","x","x"],["b","b","b","b","b"]]
level27 = [["n","n","n","n","n","n","n"],["t","t","t","t","t","t","t"]]
level28 = [["n","n","n","n","n","n","n"],["e","s","e","s","e","s","e"]]
level29 =[["b","b","b","b","b","b"],["d","d","d","d","d","d"]]
level30 =[["d","d","dg","d","d"]]
level31 = [["n","d","n","d","n"],["d","n","d","n","d"],["n","d","n","d","n"],["d","n","d","n","d"]]
level32 = [["q","q","q","q","q"]]
level33 = [["b","b","b","b","b"],["q","q","q","q","q"]]
level34 = [["r","r","r","r","r"]]
level35 =[["r","r","r","r","r"],['q','q','d','q','q']]
level36 = [["l","l","l","l"],["q","q","q","q"]]
level37 = [["l","l","m","l","l"],["r","r","r","r","r"]]
level38 = [["x","r","x","r","x","r","x"],["b","b","b","b","b","b","b"],["q","q","q","q","q","q","q"]]
level39 = [["l","l","l","l","l"],["s","n","r","n","s"],["q","q","q","q","q"]]
level40 = [["BSOD"]]
level_list = [level1,level2,level3,level4,level5,level6,level7,level8,level9,level10,level11,level12,level13,level14,level15,level16,level17,level18,level19,level20,level21,level22,level23,level24,level25,level26,level27,level28,level29,level30,level31,level32,level33,level34,level35,level36,level37,level38,level39,level40]
level = level_list[current_level-1]
###########################################################################################################33

for i in range(15):
    star = Star(random.randint(40,WIDTH-40),random.randint(60,HEIGHT - 60),1,1)
    stars.add(star)

text_test = Textbox(575,330,400,100,"Hello, World!",1,"No one",(0,255,0),(60,255,60))



textboxes.append(text_test)
startx = (WIDTH // 2) - 75
starty = 0
rowindex = 0
colindex = 0
spacer = 30
startx = (WIDTH // 2) - ((len(level[0]) / 2) * spacer)
card_was_chosen = True
cards_were_shuffled = False
bugsnum = 0
bugs = pygame.sprite.Group()

bosses = pygame.sprite.Group()
add_pierce_possible = True
dash_possible = 2
heal_possible = True

############# More start menu stuff ###############

menu_buttons = [
    MenuButton("Start Programming (Play Game)",WIDTH//2-175,320,320,55,1),
    MenuButton("Read README.md (Tutorial)", WIDTH // 2 , 410, 320,55, 2),
    MenuButton("View Error Log (See Enemy Stats)", WIDTH // 2 , 500,320,55,3),
    MenuButton("Peer Programming (Multiplayer)",WIDTH//2+175,320,320,55,5)
]

back_button = MenuButton("Return to IDE (Start Menu)" ,WIDTH//2 + 290 , 205,320,55,0)



lives_left = 3

current_enemy = 0

full_title = "CODE INVADERS"
current_typed = ""
typed_frame = 0
type_letter = 0
typer_speed = 10




ship_image = pygame.image.load("ship.png").convert_alpha()
ship_image = pygame.transform.scale(ship_image,(27,33))
talking = False
overdrive_charge = 100
cur_frame = 0
flip_to = 0
transparency = 128
other_player_lv = 0
other_player_in_shop = False
all_bugs_are_dead = False


other_bugs_are_dead = False
all_bugs = []

upgrades_obtained = 0
async def main():
    #adwsddwdwadwasdwdclkjlkj,mnjhgdgvcbvcbvcbvcbvcbvbvcvbcbvcbvcbvghgfhgfbvcjkjhkjhkjhkjhggdssdfcgvhbjlkjm,nskjlkigjhgzxcszxddfeddwaslkjlilijlijljlilkjdslkjlkjkjhghjhgjjjjhgjhgjjjhgjjjjjghhgkjhukjjhffesdwasrertfesdfdsdferttretrfesdfete4et4etdawsdwasfesdfwasddwasdwdadwdasddawvdxvcxvdadwasdxasdwafseffesfsffehfthtadwsadwdwdwasddwasddwdwasfesdffesdfesdfeasddwafefesdsdgrdffesdfesdfwfesfesfhgdfgrgrdgrgrdfesasddwadwdwfesdgrdgfadsssaxcvdxcdwaswfefsdfdwasesfesddlkjldwasdwadwadswasdwasdakjldwaddwakdwasdwadwadwadjlkadsjlkkiuyuyudwadwaddwasyiuyuiuywase2qwe2klkqe2qe2fesdfesfesfesddwasdwadwaskjkjkjhkjkjhkjhjkjhwasdwasfesdsddwsdwasdcszcszcszxcsdzszcsxcszxcxsgdrfgrfddfrggrfddfrggrfddfrdrgfdrgffgrdadwasdwadwasdwasdwasdwadsadwsadwdwdasdadwdwasdwadwasdwasasdwasdwasdasddwafegrgthydwasdwasdwasczdwadsdddwafessdfeferjuhjhgjyghfesdfesfdwddwassdwasdwasddwasdwdwasdwasdwasdwasddwadsdwadsaddwadwaddwasdwasdsadwxdwase2qe2fsefesfdsdffsfesdffesfefsdfdsdffddwadwadwadaddwasasddwaadwwdawdwasdasddwasdadwadwdwwdwaddwadwasdddwsdwasdaasddwasdwadwasdwasdfesdffesdfesadwsadwadssdawsdwaddwadwadwasdsddwadwadwadwasddwasdwasddwawsdwfesfesfesfefesfesfdwadwadwdasdwadwasddsadsadwaddwasdadddwawdwadwadwaadwadwdsafedwasdwdwadwadwadaadadwsadaddadwddadwadwadwadwadwadwaddwadadwaddwaddwdadwadwaddadwsdadwsawdwadwaddwasdwadwadwadwasddwasddwadwaadwadwdwadsddwasdwaddwadwadwadwadadwadwadfesdfdyrtyryry5yawffmfes;lk;kffsljfdkfledfelfesfesfesffesfeffefsfeswasdasdwadddwasdwadwadwawafesfesfedwadwdwasddwadwaswasdwafesfesfefesffesfesffesfesfefesdfsefdfesfesfesefsefsfdwasdwasfesfesfesfesfsefsdfjygjhgjhgjhghjhdwadwadwasdwasdwdwadwadfejgjygjjygjdadwadwadwaadwdwdwaddwasdwfsfedsddwasdwasdkgkgkfkdjfjkfkdfdwafesdfesdferwedwasdwasr3w3rer3wer3dwasdwsfawdsdwadwaadwasdadwadwdwadsdadeawdwasdddwdwdwdwadsdwadaddwadwadwadasdwadwsadwsdwadwaddsasfesddwasdwadwasdadadsawadwadwasdwasddwasdwssdwasdadadwsdadwasadwadwasdsadwadwadsdwasdwaswsdwq3sdfedssdffdsdwadwadwaddwadgjgjygjyghjjhgjhgjghdwaswdwsdwasasadwddwas
    global explosions_to_draw,upgrades_obtained,i_actually_chose_a_card,next_bug_id,all_bugs,p1_choosing_cards,p2_choosing_cards,im_choosing_cards, level_start,all_bugs_are_dead,other_bugs_are_dead,remote_shop_state,remote_level,other_player_in_shop,other_player_lv,level_start,network_connected,multiplayer_mode,player_id,pro_ships_2,ship2,titles,scroll_x,scroll_y,shop_items,stars,flip_to,transparency,shake_intensity,talking,mouse_pressed,textboxes,coverbricks,global_trail_surf,shockwaves,enemy_missiles,cur_frame,overdrive_charge,null_lasers,shotgun_1,double_1,mines_1,lives_left,ship_image,boss_lasers,keys,current_enemy,full_title,current_typed,typed_frame,type_letter,typer_speed,menu_buttons,back_button,game_state,mouse_pressed,mouse_pos,heal_1,heal_possible,server,enemy_lasers,particles,dash_possible,add_pierce_possible,ship,pierce_1,files_destroyed,bugsnum,cards_were_shuffled,card_options,card_was_chosen,symbols,current_level,keys,running,files,pro_ships,lasers,level_list,level,startx,starty,rowindex,colindex,spacer,bugs


    
    if current_level == 20:
        lives_left = 3
    while running:
        if player_id == 1:
            other_player_lv = level_start["p2_lv"]
            other_player_in_shop = level_start["p2_inshop"]
        elif player_id == 2:
            other_player_lv = level_start["p1_lv"]
            other_player_in_shop = level_start["p1_inshop"] 
        if game_state == 5 and multiplayer_mode == False:
            multiplayer_mode = True
            launch_network_thread(ship)
            print("P2 LAUNCHED")


        mouseclicked = False
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if game_state == 3:
                    if event.key == pygame.K_RIGHT:
                        current_enemy += 1
                        if current_enemy > 5:
                            current_enemy = 0
                        
                    elif event.key == pygame.K_LEFT:
                        current_enemy -= 1
                        if current_enemy < -6:
                            current_enemy = 5
                for card in cards:
                    if card.effect(event.key):
                        card_was_chosen = True
                        upgrades_obtained += 1
                        if player_id == 2:
                            cards_were_shuffled = False 
                        im_choosing_cards = False
                        print(f"{player_id} Chose a card! {card_was_chosen}, {event.key}")
                        cards.clear()
                        symbols.empty()
            

                       
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button:
                if game_state == 0:
                    mouse_pressed = pygame.mouse.get_pressed()
                    for btn in menu_buttons:
                        if btn.check_clicks(mouse_pos,mouse_pressed):
                            game_state = btn.target_state
                elif game_state == 2 or game_state == 3:
                     if back_button.check_clicks(mouse_pos,mouse_pressed):
                        game_state = back_button.target_state
                mouseclicked = True
        game_canvas.fill(game_canvas_color)
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        if game_state == 4:
            if keys[pygame.K_e]:
                game_state = 1
            if keys[pygame.K_DOWN]:
                scroll_y -= 4
            elif keys[pygame.K_UP]:
                scroll_y += 4
            if keys[pygame.K_LEFT]:
                scroll_x += 4
            elif keys[pygame.K_RIGHT]:
                scroll_x -= 4
            global heal_files_1,ram_files_1,cooldown_files_1,speed_files_1,case_files_1,cooler_files_1
            for title in titles:
                if title[1] == "Heals":
                    game_canvas.blit(title[0],(heal_files_1.rect.centerx - 100,heal_files_1.rect.top - 50))
                if title[1] == "Cooldown":
                    game_canvas.blit(title[0],(cooldown_files_1.rect.centerx - 172,heal_files_1.rect.top - 50))
                if title[1] == "Damage":
                    game_canvas.blit(title[0],(ram_files_1.rect.centerx - 120,ram_files_1.rect.top - 50))
                if title[1] == "Speed":
                    game_canvas.blit(title[0],(speed_files_1.rect.centerx - 120,ram_files_1.rect.top - 50))
                if title[1] == "File Max\n Health":
                    game_canvas.blit(title[0],(case_files_1.rect.centerx - 160,ram_files_1.rect.top - 100))
                if title[1] == "Overdrive\nDuration":
                    game_canvas.blit(title[0],(cooler_files_1.rect.centerx - 210,cooler_files_1.rect.top - 100))
            for item in shop_items:
                item.draw(mouse_pos)
                item.buy(mouse_pos, mouse_pressed)
        if game_state == 0:
            if type_letter < len(full_title):
                typed_frame += 1

                if typed_frame >= typer_speed:
                    current_typed += full_title[type_letter]
                    type_letter += 1
                    typed_frame = 0

            title_surface = title_font.render(current_typed,True,(0,255,80))
            game_canvas.blit(title_surface,title_surface.get_rect(center = (WIDTH // 2 ,180)))
            for btn in menu_buttons:
                btn.draw(game_canvas,ui_font,mouse_pos)

        elif game_state == 2:
            tutorial_title = subtitle_font.render("README.md (How to play)",True,(0,180,255))
            game_canvas.blit(tutorial_title,tutorial_title.get_rect(center = (WIDTH//2, 100)))
            pygame.draw.rect(game_canvas, (20, 20, 25), (70, 160, 900, 420), border_radius=24)
            pygame.draw.rect(game_canvas, (0, 255, 0), (70, 160, 900, 420), width=8, border_radius=12)

            tutorial_text = [
                "Controls : WASD or Arrow Keys to Control Ship Movement",
                "Controls : Spacebar, Q, or E to fire lasers",
                "Controls : Press Right Shift to Dash (Once Unlocked)",
                "Goal : Protect your code files at the bottom from the endless waves of bugs (like in real programming...)!\n If they reach 0 HP , the game is over!",
                "Upgrades : After you clear a wave of bugs, you get to choose one of 2-3 upgrade cards to upgrade your stats.\n Press 1 to pick card 1, press 2 to pick card 2, and 3 to pick card 3",
                "Upgrades : Some upgrades can only be unlocked after using others (ex. Pierce need ATK+ and Cooldown+)",
                "Waves : There are 16 Waves (So Far). Beat all of them to finally finish your program :)",
                "IRL : If you like the game , play the real version... by learning Python! (Or just play the game again...)"
            ]

            for i, line in enumerate(tutorial_text):
                txt = small_font.render(line,True,(240,240,240))
                game_canvas.blit(txt,(100,200 + i * 45))
            back_button.draw(game_canvas, ui_font, mouse_pos)
            if back_button.check_clicks(mouse_pos,mouse_pressed):
                game_state = back_button.target_state

        elif game_state == 3:
            error_log_title = subtitle_font.render("SYSTEM ERROR LOG \n(Enemy Index)",True,(0,255,100))
            game_canvas.blit(error_log_title,error_log_title.get_rect(center = (WIDTH//2 , 60)))
            continue_text = ui_font.render("Use Left and Right Arrows to scroll through enemies.",True,(0,255,100))
            error_list = [ 

                "Exception : The basic enemy. HP : 1, ATK : 1, Speed : 0.5",
                "IndentationError : A stronger enemy. HP : 3, ATK : 1.5, Speed : 0.5",
                "IndexError : A fast, rusher enemy. HP : 1 , ATK : 1, Speed : 1",
                "MemoryError : A Highly Tanky spotlight enemy. You have to defeat this error to be able to attack any other one.\n HP : 10 , ATK : 3 , Speed : 0.5",
                "ImportError : A Highly Tanky Spawner error. It spawns Exceptions every few seconds. HP : 15 , ATK : 5, Speed : 0.5",
                "BrokenPipeError : A fragile shooter error. It shoots projectiles straight toward you and your files. HP : 1 , ATK : 0.5 , Speed : 0.5"

            ]

            image_list = [
                "exception.png",
                "indentationerror.png",
                "indexerror.png",
                "memoryerror.png",
                "importerror.png",
                "brokenpipe.png"
            ]


            text = ui_font.render(error_list[int(current_enemy)],True,(255,255,255))
            image = pygame.image.load(image_list[int(current_enemy)]).convert_alpha()
            image = pygame.transform.scale(image,(96,96))
            game_canvas.blit(text,text.get_rect(center = (WIDTH//2 , 400)))
            game_canvas.blit(image,(WIDTH//2 - (image.width //2),200))
            game_canvas.blit(continue_text,continue_text.get_rect(center = (WIDTH//2 , 350)))
            if back_button.check_clicks(mouse_pos,mouse_pressed):
                game_state = back_button.target_state
       
            back_button.draw(game_canvas, ui_font, mouse_pos)
        elif game_state == 1:
            game_canvas.fill(game_canvas_color)
            #print(f"{player_id},{other_player_in_shop},{other_bugs_are_dead},{other_player_lv},{p2_choosing_cards},{other_player_in_shop}")
            cur_frame += 1
            if cur_frame > 20:
                cur_frame = 0

            
            for i in range(lives_left):
                game_canvas.blit(ship_image,(i*30+25,25))
            if (not card_options.__contains__(pierce_1)) and ship.damage > 1 and ship.cooldown < 15 and add_pierce_possible:
                card_options.append(pierce_1)
                add_pierce_possible = False
            if ship.speed >= 8 and dash_possible > 0:
                    card_options.append(dash_1)
                    card_options.append(dash_1)
                    dash_possible = 0
            if server.max_hp > 5 and heal_possible == True:
                card_options.append(heal_1)
                card_options.append(heal_1)
                heal_possible = False
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()

            bugs.draw(game_canvas)
  
            transparent_surface = pygame.Surface((WIDTH + 40, HEIGHT + 40),pygame.SRCALPHA)
            if ship.hp <= 3:
                flip_speed = 3
                if transparency >= 128:
                    flip_to = 0
                if transparency <= 0:
                    flip_to = 128

                if flip_to == 128:
                    if flip_to + transparency >= 128:
                        transparency += flip_speed
                    else:
                        transparency = 128
                    
                if flip_to == 0:
                    if flip_speed <= transparency:
                        transparency -= flip_speed
                    else:
                        transparency = 0
             
                pygame.draw.rect(transparent_surface, (255, 40, 40,transparency), (20, 20, 20,HEIGHT))
                pygame.draw.rect(transparent_surface, (255, 40, 40,transparency), (WIDTH, 20, 20,HEIGHT))
                pygame.draw.rect(transparent_surface, (255, 40, 40,transparency), (20, 20,WIDTH,20))
                pygame.draw.rect(transparent_surface, (255, 40, 40,transparency), (20, HEIGHT,WIDTH,20))

            game_canvas.blit(transparent_surface,(0,0))

            add_to_x = 0
            ############## OVERDRIVE CHARGE BAR ######################
            overdrive_background = pygame.rect.Rect(186+add_to_x,401,150,10)
            overdrive_bar = pygame.rect.Rect(186+add_to_x,401,overdrive_charge * 1.5,10)
            if overdrive_charge >= 100 and cur_frame >= 5 and cur_frame <= 7 :
                    pygame.draw.rect(game_canvas, (255, 255, 255), (186+add_to_x - 2, 401 - 2, 150 + 4, 10 + 4), width=8)
            pygame.draw.rect(game_canvas,(0,0,255),overdrive_background)
            pygame.draw.rect(game_canvas,(255,165,0),overdrive_bar)
            tutorial_title = ui_font.render(f"Overdrive bar : {round(overdrive_charge,2)}% ",True,(0,180,255))
            game_canvas.blit(tutorial_title,tutorial_title.get_rect(center = (106+add_to_x, 405)))
            ########### HEALTH BAR ##############
            ship_health_n = 0
            if player_id == 1 or not multiplayer_mode : 
                ship_health_n = ship.hp
            elif player_id == 2:
                ship_health_n = ship2.hp
            ship_health_background = pygame.rect.Rect(183+add_to_x,370,150,10)
            ship_health = pygame.rect.Rect(183+add_to_x,370,ship_health_n * 15,10)
            pygame.draw.rect(game_canvas,(255,0,0),ship_health_background)
            pygame.draw.rect(game_canvas,(0,255,0),ship_health)
            tutorial_title = ui_font.render(f"Ship Health: {round(ship_health_n,1)} / 10",True,(0,180,255))
            game_canvas.blit(tutorial_title,tutorial_title.get_rect(center = (103+add_to_x, 374)))
            ###################### Cooldown Bar ##########################
            ship_cooldown = 0
            ship_cooldown = ship.cooldown if not player_id == 2 else ship2.cooldown
            ship_max_cooldown = ship.max_cooldown if not player_id == 2 else ship2.max_cooldown
            ship_health_background = pygame.rect.Rect(200+add_to_x,340,ship_max_cooldown,10)
            ship_health = pygame.rect.Rect(200+add_to_x,340,ship_cooldown,10)
            if ship.cooldown <= 0 and cur_frame >= 5 and cur_frame <= 10 :
                pygame.draw.rect(game_canvas, (255, 255, 255), (200 - 2, 340 - 2, ship.max_cooldown + 4, 10 + 4), width=4)
            pygame.draw.rect(game_canvas,(197,180,227),ship_health_background)
            pygame.draw.rect(game_canvas,(128,0,128),ship_health)
            tutorial_title = ui_font.render(f"Weapon Cooldown: {round(ship_cooldown,1)} / {round(ship_max_cooldown)}",True,(0,180,255))
            game_canvas.blit(tutorial_title,tutorial_title.get_rect(center = (110+add_to_x, 343)))
            ############################################################
            ####################### INVERT BAR ##################
            ship_invert_background = pygame.rect.Rect(242+add_to_x,310,ship.invert_duration + 15,10)
            pygame.draw.rect(game_canvas,(0,0,255),ship_invert_background)
            tutorial_title = ui_font.render(f"Controls Inverted for : {round(ship.invert_duration,0)} / {round(ship.max_cooldown)}",True,(0,180,255))
            if overdrive_charge >= 100:
                overdrive_charge = overdrive_charge
                if keys[pygame.K_q] or keys[pygame.K_SLASH]:
                    ship.overdrive_duration = ship.max_overdrive_duration
            game_canvas.blit(tutorial_title,tutorial_title.get_rect(center = (132+add_to_x, 314)))

            if not current_level == 20:
                files.draw(game_canvas)

            mouse_state = pygame.mouse.get_pressed()
            if mouse_state[0] and ship.weapon_type == "Mine":
                    if ship.cooldown <= 0 and card_was_chosen:
                        mine = Mine(ship.rect.x,ship.rect.y,8,8,6,0,0,ship.damage * 3,mouse_pos[0],mouse_pos[1])
                        mines.add(mine)
                        ship.cooldown = ship.max_cooldown  
                        
            if not talking:      
                if not files_destroyed:
                    for coverbrick in coverbricks:
                        coverbrick.draw()
                        coverbrick.update()
                    for null_laser in null_lasers:
                        null_laser.draw()
                        null_laser.update()
                    mines.draw(game_canvas)
                    mines.update()
                    for enms in enemy_missiles:
                        enms.update()
                    for file in files:
                        if current_level != 20 and current_level != 40:
                            file.update()
                    for laser in lasers:
                        laser.draw()
                        laser.update()
            
                        if ship.weapon_type == "Shotgun":
                            if laser.y < ship.rect.y - 150:
                                try:
                                    lasers.remove(laser)
                                except:
                                    pass
                
        

                    if card_was_chosen:
                        ship.move()
                        ship.shoot()
                        ship.update()

                        ship2.move()
                        ship2.shoot()
                        ship2.update()
                 

                if not multiplayer_mode or network_connected:
                    global incoming_remote_lasers,remote_level,remote_shop_state
                    lasers_to_spawn = []
                    with net_lock: # Update Level stuff asdwdasdadwasdjkddwasxfdgrdfgcvbfesdfdgrdfbveddfesdfwasdwasdwadwasdwaswasdgfgrwadwasdsjjkjhhkjhkfesdfffesddwasdwasdwadwasdwdwasdjhdwashkjhkjjhdwsadafesdfdswdasdadwsdwawswsdwdwasdwasdwadwawasdwasdwdwasdwasdwasdashfthfhtgfsedfesfesdfdasdwasdwasdwasddwadwadsadsasdasded
                        remote_level = level_start.get('p2_lv',1) if player_id == 1 else level_start.get("p1_lv",1)
                        remote_shop_state = level_start.get("p2_inshop",False) if player_id == 1 else level_start.get("p1_inshop",False)
                        if player_id == 2 and remote_level >= 1:
                            current_level = remote_level

                    try:
                        
                        if player_id == 1 or multiplayer_mode == False:
                            if player_id == 1:
                                ship2.rect.x = network_positions["p2_x"]
                                ship2.rect.y = network_positions["p2_y"]

                            pro_ships.draw(game_canvas)
                            if multiplayer_mode:
                                pro_ships_2.draw(game_canvas)
             
                       
                        elif player_id == 2:
                            
                            ship.rect.x = network_positions["p1_x"]
                            ship.rect.y = network_positions["p1_y"]
                            pro_ships_2.draw(game_canvas)
                            pro_ships.draw(game_canvas)
            
           
                        with net_lock:
                            if incoming_remote_lasers:
                                    lasers_to_spawn = list(incoming_remote_lasers)
                                    incoming_remote_lasers.clear()
                          
    
                            for laser_data in lasers_to_spawn:
                                remote_laser = Laser(laser_data["x"],laser_data["y"],5,5,damage=laser_data["d"],pierce = laser_data["p"])
                                lasers.append(remote_laser)
                    
                    except Exception as e:
                            print(f"Oh no : {e}")

                    else:
                        pass
                    stars.draw(game_canvas)
                    for star in stars:
                        
                        star.update()
                    previous_bugsnum = bugsnum
                    if card_was_chosen == True:
                        bugsnum = 0
                    for bug in bugs:
                    
                        if player_id == 1:
                            if bug.image_path != "recursionboss.png":
                                bug.move()
                                bug.check_for_collisions()
                        
                        bugsnum += 1
                    for card in cards:
                        card.draw()
                    for enlaser in enemy_lasers:
                        enlaser.draw()
                        enlaser.update()
                    
                    symbols.draw(game_canvas)



              

                    if player_id == 1:
                        
                        other_bugs_are_dead = level_start['p2_bugs_are_dead']
                    elif player_id == 2:
                        other_bugs_are_dead = level_start['p1_bugs_are_dead']
                    
                    if bugsnum == 0 and bosses.__len__() == 0:
                        all_bugs_are_dead = True
                        if player_id == 1:
                            level_start['p1_bugs_are_dead'] = True
                           
                        elif player_id == 2:
                            level_start['p2_bugs_are_dead'] = True
                
                #######################(HEY IT WORKS!!!)###### DANGER DO NOT CROSS: Errors: p2_card_chosen causes levels not to be drawn but... I DONT KNOW WHY ###########################
                    # print(bugsnum)
                    if bugsnum <= 0 and bosses.__len__() <= 0:
                        
                        bugs.empty()
                        lasers.clear()
                        enemy_lasers.clear()
                        all_bugs.clear()
                        # print("Cleared!")
                        if card_was_chosen == True  and previous_bugsnum > 0:
                            print("Cards chosen!")
                            if multiplayer_mode == False:
                                game_state = 4
                        # Tries to fix the cards (Fails most of the time help) (Hey it kind of works now...)
                        if (previous_bugsnum > 0) and not cards_were_shuffled and card_was_chosen:
                            card_options_current = card_options[:]
                            if current_level != 20:
                                card1= random.choice(card_options_current)
                                card_options_current.remove(card1)
                                card2= random.choice(card_options_current)
                                card_options_current.remove(card2)
                                card3= random.choice(card_options_current)
                                card_options_current.remove(card3)
                            else:
                                card1= shotgun_1
                                card2= double_1
                                card3= mines_1
                            card1.lineupnum = 0
                            card2.lineupnum = 1
                            card3.lineupnum = 2
                            cards.append(card1)
                            cards.append(card2)
                            cards.append(card3)
                            im_choosing_cards = True    
                            print("Cards Loaded!")
                            cards_were_shuffled = True
                            card_was_chosen = False
                     
                            print(card_was_chosen)
                        
                        elif previous_bugsnum > 0 and card_was_chosen == True and cards_were_shuffled == True:
                            cards.clear()
                            symbols.empty()
                            im_choosing_cards = False

                            print(f"Cards chosen and destroyed! {card_was_chosen}, {cards_were_shuffled}, {(previous_bugsnum > 0 or player_id == 2)} ")
                            # dkdwfesdffesfes dfafesfefefesdfesfesfesfdliljkljllijsfsdwadwdwadsdwaddwaddaalijldslijlijlijllijlijkllllijdwdwadwddwasadaadwasdwagrfsfedfefedsdwsadwadgdwasdwaddwfwdadwdwdwadwasdwawadwadwadawdddadadwdadwaddadaadwfsfasddwadwadwdwadadwsttuyuijhjdadwadwasdwasdkhjkjlkjiljlijlijlijlijlkjilijjhkjhkjkjhkhkjhmnvbghvnbvghgcgbvlj,mljiuykjhkjhkjhkdaddwasdgkjhgjhdgdwadwaddwadadsfgdgdfrgkuhkh;lk;lkpoijlkijokjoijlkjhuigytughuythkjhkjhkjhkjhdadwadsdwadwadwadwa;lkhkjdwaadadawsadadsassdwadwasdfsdadwskjhjhgjhghsdwfsgrdfxbuittyuw3rkiutgyjhgyii9pohkhukhkhkhkhkkhkjhjiuyiuyiuyiuyjdawkjhkuhkhuhjkjhjhgjhgjhguytthjdwasdwashmbmmbmnmmbmjbjmjbjbmjbdwasasdwsasmbnmnbjgyjgjgjgjgyjgjygjygkjhjhdwasdwdfsafdesfsdfcdawdsasdwasdassfasoiuoiuoigjkhkjhkjhkjhhkkjhkhkjhkhmnbbnjhkjhihkhdadadwasdsadwsadikjdwadwadwdwadwadwadwadsahkihkihkhimnbmnmnbmnbmnbdwdjhgjhuytuythgfwdadwfesdfesdfesfesfesfdfesdkhkkjhjhgnbvnbvnbvnbadwdwasdwdwasddwasdsasdwasdwadwadadwadadwadadwadsadwasdasdasddwadwadddwasdsaswadwasdwadwadwadwsasdwsdsarwfsdawdsadwsddawdawsdwdasdadwsaadwdwadwasdadwadwasdwassdwasddwasddaddwasqASDADdsfeghtuaddwasdaddwawadwadwdwadwasdadwasddadadwsfsfesfesfesfesfsfesdfsdfwasdwasdwsadwadwadwasffsdffesfesdfesdfesdsdasdadwasaadwdwashkhkjfdwasdhkdwadkdwadwadsdwadwadwaddwadwadwadwajhdakawadsadwsdadwadwadwdwasdsgrdfdhhhdsadwhjeqoqwuewoewquueeewqeqewqdwsddwasdaddwadwadwadwasdwadwdwadwasdwadwadwadwdwdwadwasddwsddwasddawsdwadwadwafxvasdafkdwaddwadwaddwasddwadwasdawasdwasdwasddwadwasdsawadwadwadwadwasdwajhkjhkjkjhkjkjkddwasddwasdwasdwasdwadadjjjhelpitdoesnt work dlfkesffsfesddfssfsffesdwadwadadookkhkhjhkjhhhiuiyuiiuhhhiuhiuhdksfjefkgjdsfgdsfefjkhfesdfkjhfgcvfdsfkejshfkejghksfjhtksdjfhsekfjhgvbbdkgjkslkfjertrwerlsfc lfsdferfdrtwerdrtlertertelrker erltjelrlterkjrtelrkj dfgbwkejrhbsdfkjwer uytuyt
                        else:
                            pass
                            # print(f"TRIPLE FAIL FAIL {player_id}, {cards_were_shuffled},{(previous_bugsnum > 0 or player_id == 2)}")
                            # im_choosing_cards = True
                   
                        
                        if (player_id == 1 or multiplayer_mode == False) and current_level < len(level_list) and card_was_chosen and p2_choosing_cards == False:
                            current_level += 1
                            print(f"|||=-----------===---===---------------------- Cards: {card_was_chosen}------------- LEVEL UP! LeveL : {current_level} -----------------")
                            print("|||=-----------===---===----------------------------  NEW LEVEL  -----------------------------")
                    
                            print(f"Debug this: P ID {player_id} , Level :{current_level}, Was card chosen :{card_was_chosen},Were cards shuffled : {cards_were_shuffled}"
                            )
                
                            cards_were_shuffled = False
                        # else:     
                        #     # This should never run!
                        #     # Why does it run?
                        #     # I DONT KNOW OK, BRAIN!!
                        #     # Fix youself... please bugs, I beg you.........PLEASE....HELP.................
                        #     print(f"Problem! BIG PROBLEM! : Id : {player_id}, Was the card chosen? : {card_was_chosen},{current_level},{bugsnum}! HELP!")                                                      
                        #     #print(card_was_chosen,cards_were_shuffled, current_level, bugsnum)
                       
                            level = level_list[current_level-1]
                            startx = (WIDTH // 2) - ((len(level[0]) / 2) * spacer)
                            colindex = 0
                            # Draws the enemies based  
                            for row in level:
                                for exception in row:
                                    # Draws the basic exception enemy 
                                    if exception == "e":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,0,1,1,1,y_speed=0.05,id = next_bug_id)
                                    # Draws the mini-tank indentation error enem
                                    elif exception == "i":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,1,1.5,3,0.8,id = next_bug_id)
                                    # Draws the fast, rusher exception error
                                    elif exception == "x":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,2,1,1,1,y_speed = 1.2,id = next_bug_id)
                                    # Draws the tanky supporting memory error
                                    elif exception == "m":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,3,3,7,0.4,y_speed = 0.2,id = next_bug_id)
                                    # Draws the giant tank spawner import error
                                    elif exception == "p":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,4,3,15,0.25,y_speed = 0.2,id = next_bug_id)
                                    # Spawns the shooting brokenpipe error
                                    elif exception == "b":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,5,3,1,0.4,y_speed = 0.5,id = next_bug_id)
                                    # Spawns the typeerror enemy
                                    elif exception == "t":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,6,random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5),id = next_bug_id)
                                    elif exception == "n":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,8,0,24,0.5,id = next_bug_id)
                                    # Spawns the recursion boss
                                    elif exception == "BOSS":
                                        bug = RecursionBoss(WIDTH//2 - 150,50,240,120,"recursionboss.png",1,100,id = next_bug_id)
                                        bosses.add(bug)
                                    # Spawns a deprecated error
                                    elif exception == "d":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,24,24,9,1.5,12,0.5,0.35,id = next_bug_id)
                                    # Spawns a deprecated giant
                                    elif exception == "dg":
                                        bug = Bug(startx  + rowindex * spacer,starty - colindex,48,48,10,1.5,48,0.5,0.05,id = next_bug_id)
                                        spacer += 1
                                        rowindex += 1
                                    elif exception == "q":
                                        bug = Bug(startx + rowindex * spacer , starty - colindex,24,24,11,2,10,0.5,y_speed = 0.25,id = next_bug_id)
                                    elif exception == "r":
                                        bug = Bug(startx + rowindex * spacer, starty - colindex,24,24,12,1.5,5,1.75,1.5,id = next_bug_id)
                                    elif exception == "l":
                                        bug = Bug(startx + rowindex * spacer, starty - colindex,24,24,13,3,5,1.75,0.3,id = next_bug_id)
                                    if exception not in ("", "s", "BOSS", "BSOD"):
                                        bugs.add(bug)
                                     
                                    if exception == "s":
                                        for i in range(3):
                                            for j in range(3):
                                                bug = Bug((startx  + rowindex * spacer ) + i * 10,(starty - colindex) + j * 10 ,9,9,7,1,1,0.4,y_speed = 0,id = next_bug_id)
                                                bugs.add(bug)
                                                next_bug_id += 1
                                    
                                    elif exception == "BSOD":
                                        boss = Bluegame_canvasOfDeath(0,50,200,100,"bluescreenofdeath.png")
                                        bosses.add(boss)
                                    
                                    rowindex += 1
                                    next_bug_id += 1
                                colindex -= spacer
                                rowindex = 0
                            for bug in bugs:
                                all_bugs.append(bug)
                        elif current_level >= len(level_list) and bosses.__len__() == 0:
                            win  = title_font.render(f"YOU WIN \n(for now)",True , (0,255,0))
                            game_canvas.blit(win,(WIDTH//2 - 300,HEIGHT//2  - 100)) 
                            pass
                            print(f"DOUBLE FAIL :{player_id,card_was_chosen,bugsnum,cards_were_shuffled,p2_choosing_cards}")
            
            if player_id == 1 and not im_choosing_cards and p2_choosing_cards:
                txt = subtitle_font.render("Waiting on p2 to \nchoose cards........",True,(0,125,255))
                game_canvas.blit(txt, txt.get_rect(center = (WIDTH//2 , 100)) )
                print("Weeee")
            elif player_id == 2 and not im_choosing_cards and p1_choosing_cards:
                txt = subtitle_font.render("Waiting on p1 to \n choose cards........", True,(255,125,0))
                game_canvas.blit(txt,txt.get_rect(center = ( WIDTH//2 , 100) ))
                print("Whooooooo")

            # Draw bosses
            bosses.draw(game_canvas)
            # Update boss lasers
            for laser in boss_lasers:
                laser.draw()
                laser.update()
            # Update Bosses
            for boss in bosses:
                if boss.image_path == "recursionboss.png":
                    boss.update()
                    boss.check_for_collisions()
                    boss.shoot()
                else:
                    boss.update()
            # Draw and update particles
            for explosion_list in explosions_to_draw:
                image_path = explosion_list[2]
                x = explosion_list[0]
                y = explosion_list[1]
                color = (0,255,0)
                if image_path == "exception.png":
                    color = (0,255,0)
                elif image_path == "indentationerrorlow.png" or image_path == "indentationerror .png":
                    color = (0,0,255)
                elif image_path == "indexerror.png":
                    color = (255,165,0)
                elif image_path == "memoryerror.png":
                        color = (0,255,0)
                        for i in range(9):
                            particles.append([[x, y] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8),random.choice([(0,255,0),(255,0,0),(255,255,0)])])
                elif image_path == "importerror.png":
                    color = (165,42,42)
                elif image_path == "brokenpipe.png":
                    color = (255,255,255)
                elif image_path == "typeerror.png":
                    color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
                if image_path != "packetbug.png":
                    for i in range(9):
                        particles.append([[x, y] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8), color])
                else:
                    for i in range(2):
                        particles.append([[x, y] , [random.randint(-3,3),random.randint(-3,3)] , random.randint(4,8), color])
                explosions_to_draw.remove(explosion_list)

            for particle in particles[:]:
                particle[0][0] += particle[1][0] 
                particle[0][1] += particle[1][1] 
                particle[2] -= 0.1 
                rect_particle = pygame.rect.Rect(particle[0][0],particle[0][1],particle[2],particle[2])
                try:
                    color = particle[3]
                    pygame.draw.rect(game_canvas,particle[3],rect_particle)
                except:
                    pygame.draw.rect(game_canvas,(0,200,100),rect_particle)

                if particle[2] <= 0:
                    particles.remove(particle) 
            # Draw and update shockwaves
            for shockwave in shockwaves:
                shockwave.draw()
                shockwave.update()
            # Check if it is single player, then show text if it is
            if multiplayer_mode == False:
                for textbox in textboxes:
                    # Are we out of textboxes?
                    if textbox.text_index <= 29:
                        textbox.draw()
                        if mouseclicked:
                            textbox.update(mouse_pos,True)
                        else:
                            textbox.update(mouse_pos,False)
                        talking = True
                    else:
                        talking = False
               
            # Draws the trails for missiles
            game_canvas.blit(global_trail_surf,(0,0))
            global_trail_surf.fill((0,0,0,0))
            if files_destroyed or lives_left <= 0:
                # If the game runs out of levels then display the win screen
                win  = title_font.render(f"YOU LOSE...",True , (255,0,0))
                game_canvas.blit(win,win.get_rect(center = (WIDTH//2 , 200)))
                current_level = 0
                ship = Ship(100,100,27,33,"ship.png",1,1)



        # Shakes the screen, then decreases intensity
        if shake_intensity > 0:
            offset_x = random.randint(-shake_intensity,shake_intensity)
            offset_y = random.randint(-shake_intensity,shake_intensity)

            shake_intensity -= 1
        # Sets shake to 0
        else:
            offset_x,offset_y = 0,0

        # Blits the shaking screen to the static screen
        screen.blit(game_canvas,(-20+offset_x,-20+offset_y))
        pygame.display.flip()
        await asyncio.sleep(0.001)
asyncio.run(main())


#douiiidwasdwdwaedwadwasdwasdwadwasdsdwasdwadwdwasddwadwaadwasddwasddwdwadwadwadsdwasddwasddwasdwasddwasdwasddwadwsdwasdwuydwdwasdsdwadddadsbvcbfcvbfdgrdgffefesffesfesfesdfesfesdfesfesdfesffesddwasdwasdwadwasde2e2qwdwasdwsdwaddwadwasddwasddwasddwadwasdwasdwaddwasyuidwaddwasdfesfesfesfesffesdfdwadwasdwadwadwawsdwasffesdfedsdfeddwasdwadwsdwadwasdwadesdfesddwasukjhmnbnmkhje2qwedwasddwadwadwsasddwadwasddwasdhkjhkjhjkhjkjhkhkjh,m,,mn,ngjgmnbbmmnbnmmnmjhgjhjhgjgjhgkkhjkkjhkhjhkjhkjmnbnmnbnbkjhujhkjhkgfesdioioiuhkjhkjhkjhkjhjhkjhkjhkjhkjhjhjkjhjhkjhkjkkjhkjhioiuiiuiuoiuoooiuoiuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuoiuijuoiuoiuiyiuyyiuiuyiuiuyiuyiuyuyuuykkjhjjhgjhgjjhgjhgkjhkjhjjhjkjhkjhkhkjhoiuoiuoiuoiuooiuoiukjkjhjhljljlljlkjkhkjhkjhkkjhkjcvfthgfdrgfdkjhjkjoiuoiooiuoiuoiuooiuoiuoiuoiuokjhkjkjkjhjlkjkjjhjgjjhgjhgkjjhhljkmnbnmlkjklkhkjhjmnbhgyjkjhjhkjhjkjhkjhjhkjkmnbkjhmnbhghgkjjhgjhjhgjhghhgfdjhnhkhkjkjhkkjhkjkjhjkjhjhghkjhkjhkjhjkkjhjjhgdwdwhkjhkjhkhkikjhjkjhkjhkjhkjhfjhgnbvnbvnbvhhjhygjhgkjhkjjlkjkjlkjkuhkuhdwasdwasfesddwadwaddwasddwasdwadzvfdfesfesdfdhtfghgrhdgrfkjhkjkjhjhaadwadwdwadwaddwadsdwdwasgrdwdwasfxvxvdcxvdcvdcxdwasdfsfesfesddwdwadwadwadwawdwdwasdwadsdwadwadwadwadwafsfesdfaddwasdwfesdeadswdwadwadwdwadwadwdgrhfggrsfesgcbcbgdgrdggrdfetyytrtydwadadwaddwadwadwfsfesffesdfeefesfdffesfefesfesfesdwajgjhkjhjhgjhjhjhgjhgjhghgjhgkjjhgnhkjhkhkjhkjhkjjhjmnbgjiuytuyuytmmbbhggnbvcbfhgfhfhgffhgfhggghgfvnbbvnvjgjhgjhghkjkjhkkjhjgjhgjhgjjhgjjhkkhmnbbmvnbhvnhvnbvnbvjhgjjhgjhgjjgjhgjhgddwddwadwasddwadwadwasdswasdaddwasdwadaddddwasddwasdwdwadasdwdwadwaasdwswasddwadwasddwasdwwasddwasdwadfesdwasdsddwdwasadzxczxcwasdgrgfddwadwasdwasdsddwasddasdwasdwadwdwadzfdwasdwadwasddwasdsdsadexcdwasdadwdwadwadwadwacdwasdadwasdwdwadsdssdsvxvcxvdxckjhkjkjhkjkjhkdwfsffffjhkhkkjhkjhkkjhjkjhkjhjhwadsddwdddddddddzv xzdcszcszxcdddddddddccbmnbmnccbnnwddadwasdfxcvfxvsdfxcdvczxscxzcsxwgtfesfesfdwafesfdaddddwasddwadwawadvnbvndwaasdsdgjhdwadsdwadwgjhgjhgmmnliulkjnljklkjbnmjkjhkhnmliukjhdwaddwadjyghjgvcwetretretretrertergjhgkjhvnbvhgfcvbvcwaddwadhfggugdwaddwadwadwasfhgyuydhdwddwdwasdwasdzcxdwadwasdwadwadwadwadwaswadwdwadwadwadwasdsdsddwasddwakjdwadwadsadwadwdwdadwadwadwdwasddwadssadwsdwafxczxsdwasddwasddwddadwadawadhkjhjhwadwadsdsasdwaddwdddwasdwddwdwddwadwaddwadwdwasddfesdwadsdwadsdwadsccszcszxcadswddwasddwasasddwadwasdnvnbvnngjhgjdwasdhghdwcbdwasdwaddwadsvcbadwadwasdwasdhfdawdadddwasdfkjhkjhsfdwdczfdxdwawasdwasdwadwwasdsdlkjlkcvdadwadwdxvcvddvbbmnbmnbvb mjsadwasdwaffdwaswadwdwdwdwaddwadwagtdwadzcsdwasjkdwadwasdwddwadwasaugjykhujnnbjkhuiydjugydrgdfdagdgrfasdwasddwadwdwdwasdasdwasddwaadzcdwadwadwadwadwadwadddwasddadwasddwadwasdwadwasddwasdwasdwaszxcfesdffefesfdwadwadfsfdwasddzcxsdcxzdwasdadwadwasdwdwasdkuyhhkuhjfsdfghjnvbvwesrtyufsfesffesddwasddwasdddjghjdsdsdwasddwasdwadwafeddwasdsdwadwasdwadwadwasddwafesfdsdfsdfddgijghnbtrfdwesdqwaserwfdyjhuikjkjwadwadwdawaaavbndwdwadwasddwadwadwasddwasdaszvxcjuygdwasdzcsdwafedwasdwadwadwasdwadwdwdwaddxcvxcvxvdxvdxvchhfnbvbnvbngurtfhfgdwzxzcsxcsvfesvxcvvnhm,jjhkuhgfhdfghbvngrdwasdwasdzcszxdwasdyjghbdwaddzclkjsuhygbvvnvbnghtjkidwadwasddwadczcsxdwaddzczhbmnhjgyhjgxvdcvdxcvdxcbdgrfsdfgjuihjdwdwadwasddwadwasddwadwxfhghnvbnasddwadsdwdwadwadwafzxczscgryfghdwadsadwaasddwadwadwadwasdddwasdwadwasdwasddwasytuhgikhdfwadsadwasdwawadwadsadwadwadwaddwaadwadwadwdwadwajerdgfwhkjhdwasdasddgfyghjgbndwadxcvbnmnbvcsdjgjhdwasdghghkkjhkjfghaddwaddwadwasddwadwasddwadwadwwadwadsdawdaszxvxcdwadwadwadwdwadssqSQsddwkhk