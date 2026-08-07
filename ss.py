import asyncio
import json

import websockets


PORT = 8765
PLAYER_STARTS = {1: "486,400", 2: "800,400"}
connected_nodes = {}
match_telemetry = {"p1": PLAYER_STARTS[1], "p2": PLAYER_STARTS[2]}
connection_lock = asyncio.Lock()


async def route_security_packets(websocket):
    global match_telemetry

    # Reserve the slot before awaiting. Otherwise two clients that connect at
    # once can both observe player 1 as available and receive the same ID.
    async with connection_lock:
        player_id = next((slot for slot in (1, 2) if slot not in connected_nodes), None)
        if player_id is not None:
            connected_nodes[player_id] = websocket

    if player_id is None:
        await websocket.close(reason="Maximum player count reached")
        return

    try:
        await websocket.send(json.dumps({"player_id": player_id}))
        async for packet in websocket:
            incoming_payload = json.loads(packet)

            if incoming_payload.get("type") == "laser_fired":
                target_id = 2 if player_id == 1 else 1
                if target_id in connected_nodes:
                    await connected_nodes[target_id].send(json.dumps({
                        "type": "spawn_remote_laser",
                        "x": incoming_payload["x"],
                        "y": incoming_payload["y"],
                        "weapon": incoming_payload["weapon"]
                    }))
                continue

            match_telemetry[f"p{player_id}"] = f"{x},{y}"
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
            # Do not remove a newer connection that claimed this slot.
            if connected_nodes.get(player_id) is websocket:
                del connected_nodes[player_id]
                match_telemetry[f"p{player_id}"] = PLAYER_STARTS[player_id]


async def main():
    print(f"WebSocket server listening on port {PORT}")
    async with websockets.serve(
        route_security_packets, "0.0.0.0", PORT, ping_interval=20, ping_timeout=20
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
