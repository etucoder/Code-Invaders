import asyncio
import json
from uuid import uuid4
import websockets
# TIME TO CHANGE THE WHOLE SERVER TO SUPPORT MORE THAN 2 PLAYERS!!!!!!!!!!!!!!!!!
print("Hello!")
PORT = 8765

PLAYER_STARTS = {
    1: "486,400", 
    2: "800,400"
    }

########### LOBBIES ############
lobbies = {}
connections = {}
# match_telemetry = {"p1": PLAYER_STARTS[1], "p2": PLAYER_STARTS[2],"p1_level" : 1,"p2_level" : 1,"p1_in_shop" : False, "p2_in_shop" : False,"all_bugs_dead_p1" : False,"all_bugs_dead_p2": False,'p1_choosing_cards' : False,'p2_choosing_cards' : False,'bugs_list' : []}
connection_lock = asyncio.Lock() 
 
lobby_id = str(uuid4()) #dwsadwsafeassdfsSadasddwdwasdsdwsfadssdfdswas##################################################################################################################### Turn UUID into String ###########################################

def create_lobby():
    lobby_id = str(uuid4())

    lobbies[lobby_id] = {
        "players" : {},
        "telemetry" : {
            "p1" : PLAYER_STARTS[1],
            "p2" : PLAYER_STARTS[2],

            "p1_level" : 1,
            "p2_level" : 1,

            "p1_in_shop" : False,
            "p2_in_shop" : False,

            "all_bugs_dead_p1" : False,
            "all_bugs_dead_p2" : False,

            "p1_choosing_cards" : False,
            "p2_choosing_cards" : False,

            "bugs_list" : [],
            "explosions" : []

        }
    }

    print(f"Created Lobby with ID {lobby_id}")

    return lobby_id


def find_open_lobby():

    for lobby_id,lobby in lobbies.items():
        if len(lobby["players"]) == 1:
            return lobby_id

    return create_lobby()

async def send_lobby_state(lobby_id):

    if lobby_id not in lobbies:
        return

    lobby = lobbies[lobby_id]

    message = json.dumps(lobby["telemetry"])

    recipients = tuple(lobby["players"].values())

    await asyncio.gather(
        *(player.send(message) for player in recipients), return_exceptions=True
    )

async def route_security_packets(websocket):
    global match_telemetry,lobby_id
    async with connection_lock:
        player_id = next((slot for slot in (1, 2) if slot not in connected_nodes), None)
        lobby_id = lobby_id
        if player_id is not None:
            connected_nodes[player_id] = websocket
            print(lobby_id)
        else:
            await websocket.close(reason="Maximum player count")
            return
    try:
        await websocket.send(json.dumps({"player_id": player_id,"lobby_id" : lobby_id}))
        
        async for packet in websocket:
            try:
                incoming_payload = json.loads(packet)
                
                if 'x' in incoming_payload and 'y' in incoming_payload:
                        x = int(incoming_payload["x"])
                        y = int(incoming_payload["y"])
                        match_telemetry[f"p{player_id}"] = f"{x},{y}"
                if incoming_payload.get("type") == "laser_fired":

                    target_id = 2 if player_id == 1 else 1
                    if target_id in connected_nodes:
                
                        await connected_nodes[target_id].send(json.dumps(incoming_payload))
                    continue 
                
                if 'level' in incoming_payload:
                    match_telemetry[f"p{player_id}_level"] = incoming_payload["level"]
                if 'is_in_shop' in incoming_payload:
                    match_telemetry[f"p{player_id}_in_shop"] = incoming_payload["is_in_shop"]
                if 'bugs_dead' in incoming_payload:
                    match_telemetry[f"all_bugs_dead_p{player_id}"] = incoming_payload["bugs_dead"]
                 
                if 'choosing_cards' in incoming_payload:
                    match_telemetry[f"p{player_id}_choosing_cards"] = incoming_payload["choosing_cards"]
                if 'bugs_list' in incoming_payload and player_id == 1:
                    match_telemetry['bugs_list'] = incoming_payload['bugs_list']
                if 'explosions' in incoming_payload and player_id == 1:
                    match_telemetry['explosions'] = incoming_payload['explosions']
                   
            
            except Exception as e:
                print(e)
                continue
   
            
            broadcast_string = json.dumps(match_telemetry)
            recipients = tuple(connected_nodes.values())
            await asyncio.gather(
                *(node.send(broadcast_string) for node in recipients),
                return_exceptions=True,
                )
    except websockets.exceptions.ConnectionClosed:
        print(f"Connection closed for player {player_id}")
    finally:
        async with connection_lock:
            if connected_nodes.get(player_id) is websocket:
                del connected_nodes[player_id]
                match_telemetry[f"p{player_id}"] = PLAYER_STARTS[player_id]
                match_telemetry[f"p{player_id}_level"] = 1
                match_telemetry[f"p{player_id}_in_shop"] = False
                match_telemetry[f"alll_bugs_dead_p{player_id}"] = False
                match_telemetry[f"p{player_id}_choosing_cards"] = False
                print(f"{player_id} full reset")

async def main():
    print(f"WebSocket server listening on port {PORT}")
    async with websockets.serve(
        route_security_packets, "0.0.0.0", PORT, ping_interval=20, ping_timeout=20
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)