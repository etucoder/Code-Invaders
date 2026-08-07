import asyncio
import json

import websockets


print("Hello!")

PORT = 8765
PLAYER_STARTS = {1: "486,400", 2: "800,400"}
connected_nodes = {}
match_telemetry = {"p1": PLAYER_STARTS[1], "p2": PLAYER_STARTS[2],"p1_level" : 1,"p2_level" : 1,"p1_in_shop" : False, "p2_in_shop" : False,"all_bugs_dead_p1" : False,"all_bugs_dead_p2": False,'1' : False,'p2_choosing_cards' : False,'bugs_list' : []}
connection_lock = asyncio.Lock() 
 

async def route_security_packets(websocket):
    global match_telemetry
    async with connection_lock:
        player_id = next((slot for slot in (1, 2) if slot not in connected_nodes), None)
        if player_id is not None:
            connected_nodes[player_id] = websocket
        else:
            await websocket.close(reason="Maximum player count")
            return
    try:
        await websocket.send(json.dumps({"player_id": player_id}))
        
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
                    print('bd updateD')
                if 'choosing_cards' in incoming_payload:
                    match_telemetry[f"p{player_id}_choosing_cards"] = incoming_payload["choosing_cards"]
                if 'bugs_list' in incoming_payload:
                    match_telemetry['bugs_list'] = incoming_payload['bugs_list']
                print(match_telemetry)
            except Exception as e:
                print(e)
                continue
                #adawd
            
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
                match_telemetry[f"p{player_id}"] = PLAYER_STARTS[player_id] # asadwasdefd

async def main():
    print(f"WebSocket server listening on port {PORT}")
    async with websockets.serve(
        route_security_packets, "0.0.0.0", PORT, ping_interval=20, ping_timeout=20
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
#csfesfdsdfsdfsdfsd