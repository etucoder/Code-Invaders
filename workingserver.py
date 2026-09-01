import asyncio
import json
from uuid import uuid4
import websockets
# TIME TO CHANGE THE WHOLE SERVER TO SUPPORT MORE THAN 2 PLAYERS!!!!!!!!!!!!!!!!!
# IT WORKS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
print("Hello!")
PORT = 8765

PLAYER_STARTS = {
    1: "486,400", 
    2: "800,400"
    }

########### LOBBIES ############
lobbies = {}
connections = {}
connection_lock = asyncio.Lock() 
 
lobby_id = str(uuid4()) 
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
            "p2_choosing_cards" : True,

            "p1_dead" : False,
            "p2_dead" : False,

            "bugs_list" : [],
            "explosions" : [],
            "bosses_list" : [],
            "enemy_lasers" : []

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
    lobby_id = None
    player_id = None

    async with connection_lock:
        lobby_id = find_open_lobby()

        lobby = lobbies[lobby_id]

        if 1 not in lobby["players"]:
            player_id = 1
        elif 2 not in lobby["players"]:
            player_id = 2

        else:
            await websocket.close(reason = "Lobby Full! This should never happen! Try again and report to dev if possible." )
            return

        lobby["players"][player_id] = websocket #aaaaaaaaaaaaahaaaaaaaaaaaahaaaaaahaaaaaaaaaah

        connections[websocket] = (lobby_id,player_id)

        print(
            f"Player {player_id} joined lobby {lobby_id}"
            f"({len(lobby['players'])} / 2)"
        )

    try:
        await websocket.send(
            json.dumps({
                "player_id" : player_id,
                "lobby_id" : lobby_id
            })
        )

        async for packet in websocket:

            try:

                incoming_payload = json.loads(packet)

                lobby = lobbies.get(lobby_id)

                if lobby is None:
                    break

                telemetry = lobby["telemetry"]

                if "x" in incoming_payload and "y" in incoming_payload:

                    x = int(incoming_payload["x"])
                    y = int(incoming_payload["y"])

                    telemetry[f"p{player_id}"] = f"{x},{y}"

                if incoming_payload.get("type") == "laser_fired" : 

                    other_player_id = 2 if  player_id == 1 else 1

                    target = lobby["players"].get(other_player_id)

                    if target is not None:

                        await target.send(
                            json.dumps(incoming_payload)
                        )       

                        continue

                if "level" in incoming_payload:
                    telemetry[f"p{player_id}_level"] = (
                        incoming_payload["level"]
                    )

                if "is_in_shop" in incoming_payload:
                    telemetry[f"p{player_id}_in_shop"] = (
                        incoming_payload["is_in_shop"]
                    )

                if "bugs_dead" in incoming_payload:
                    telemetry[f"all_bugs_dead_p{player_id}"] = ( 
                        incoming_payload["bugs_dead"]
                        )

                if "choosing_cards" in incoming_payload:
                    telemetry[f"p{player_id}_choosing_cards"] = (
                        incoming_payload["choosing_cards"]
                    )
                # Player 1 Specific so P2 can Copy
                if "bugs_list" in incoming_payload and player_id == 1:
                    telemetry["bugs_list"] = (
                        incoming_payload["bugs_list"]
                    )

                if "explosions" in incoming_payload and player_id == 1:
                    telemetry["explosions"] = (
                        incoming_payload["explosions"]
                    ) 

                if "bosses_list" in incoming_payload and player_id == 1:
                    telemetry["bosses_list"] = (
                        incoming_payload["bosses_list"]
                    )

                if "enemy_lasers" in incoming_payload and player_id == 1:
                                    telemetry["enemy_lasers"] = (
                                        incoming_payload["enemy_lasers"]
                                    )

                if "im_dead" in incoming_payload :
                    telemetry[f"p{player_id}_dead"] = (
                        incoming_payload["im_dead"]
                    )
                await send_lobby_state(lobby_id)
            except Exception as e:
                print(f"[Small Lobby Error] : {e}")

    except Exception as e:
        print(f"[Lobby Error] : {e}")


    finally:
        async with connection_lock:
            if websocket in connections:
                del connections[websocket]

            if lobby_id in lobbies:
                lobby = lobbies[lobby_id]

                if lobby["players"].get(player_id) is websocket:
                    del lobby["players"][player_id]

                print(f"Player {player_id} left lobby {lobby_id}")

            if len(lobby["players"]) == 0:
                del lobbies[lobby_id]

                print(f"Deleted Empty/Inactive Lobby {lobby_id}")

            else:
                telemetry = lobby["telemetry"]

                telemetry[f"p{player_id}"] = (PLAYER_STARTS[player_id])
                telemetry[f"p{player_id}_level"] = 1
                telemetry[f"p{player_id}_in_shop"] = False

                telemetry[f"all_bugs_dead_p{player_id}"] = False
                telemetry[f"p{player_id}_choosing_cards"] = False

                await send_lobby_state(lobby_id)

async def main():
    print(f"Websocket Server launched & listening on port {PORT}")

    async with websockets.serve(
        route_security_packets,
        "0.0.0.0",
        PORT,
        ping_interval = 50,
        ping_timeout = 50
    ):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=asyncio.SelectorEventLoop
    )
    print("Main Server Running")            