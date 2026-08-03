import asyncio
import websockets
import json

PORT = 8765
print(f"Web-Socket on port {PORT}")

connected_nodes = {}
match_telemetry = {"p1" : "400,600", "p2" : "800,600"}

async def route_security_packets(websocket):
    global match_telemetry

    if not 1 in connected_nodes:
        player_id = 1
    elif 2 not in connected_nodes:
        player_id = 2
    else:
        await websocket.close(reason = "Max cap reached")
        return


    await websocket.send(json.dumps({"player_id" : player_id}))

    connected_nodes[player_id] = websocket
    try : 
        async for packet in websocket:
            incoming_payload = json.loads(packet)

            coordinate_string = f"{incoming_payload.get('x',0)},{incoming_payload.get('y',0)}"


            if player_id == 1:
                match_telemetry["p1"] = coordinate_string
            else:
                match_telemetry["p2"] = coordinate_string

            brodcast_string = json.dumps(match_telemetry)
            transmission_tasks = [node.send(brodcast_string) for node in connected_nodes.values()]
            await asyncio.gather(*transmission_tasks)

    except websockets.exceptions.ConnectionClosed:
        print(f"Connection killed by {player_id}")

    finally:
        if player_id in connected_nodes:
            del connected_nodes[player_id]

async def main():

    async with websockets.serve(route_security_packets,"0.0.0.0",PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())