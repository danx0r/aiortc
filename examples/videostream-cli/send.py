import argparse
import asyncio
import logging
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription
)
from aiortc.contrib.media import MediaPlayer
from aiortc.contrib.signaling import BYE, TcpSocketSignaling

async def run(pc, player, signaling):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)

    await signaling.connect()
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    print ("connected")
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("--play-from", required=True, help="Read the media from a file and sent it."),
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = TcpSocketSignaling("127.0.0.1", 5676)
    pc = RTCPeerConnection()

    # create media source
    player = MediaPlayer(args.play_from)

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        print ("awaiting connection")
        loop.run_until_complete(
            run(
                pc=pc,
                player=player,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
