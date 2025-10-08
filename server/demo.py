import os
import json
import asyncio
import numpy as np
from av import VideoFrame
import fractions
import queue
from carviz import CarVisualizer
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCRtpSender

from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.types import Receive, Scope, Send

# sim parameters(defaults) that can be updated by http3_server's parsed args
sim_config = {
    "width": 640,
    "height": 480,
    "fps": 60,
    "grav": 980,
    "vel": (1000.0, 1000.0),
    "cor": 0.98
}

ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.environ.get("STATIC_ROOT", os.path.join(ROOT, "client"))
STATIC_URL = "/"

# global decleration to aid graceful shutdown of peer connections and sim thread
pcs = set()
sim = None

class CarVizVideoTrack(MediaStreamTrack):
    """
    Creates media stream track by fetching frames from the bouncing ball sim's output queue
    """
    kind = "video"

    def __init__(self, sim):
        super().__init__()
        self.sim = sim
        self.frame_count = 0

    async def recv(self):
        """
        Fetches next frame from sim queue on each call and converts to webRTC rgb24 VideoFrame
        """
        self.frame_count += 1
        while True:
            try:
                frame = self.sim.queue.get_nowait()
                break
            except queue.Empty:
                await asyncio.sleep(0.001)  # Small wait if no frame ready

        # Convert to WebRTC VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, self.sim.fps)
        return video_frame

def force_codec(pc, sender, forced_codec):
    """
    Enforces video codec chosen to encode stream during sdp negotiation 
    """
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    matching_codecs = [c for c in codecs if c.mimeType == forced_codec]
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(matching_codecs)

async def homepage(request):
    """
    Simple homepage.
    """
    return FileResponse(os.path.join(STATIC_ROOT, "index.html"))

async def wt(scope: Scope, receive: Receive, send: Send) -> None:
    """
    WebTransport endpoint for webRTC sdp negotiation and two-way data transfer.
    """
    global sim
    global pcs
    print("starting wt connection")
    
    # Wait for wt connection and accept it 
    message = await receive()
    assert message["type"] == "webtransport.connect"
    await send({"type": "webtransport.accept"}) 
    print("wt connected")
    # start buffer for storing long wt stream data; create new peer connection
    buffer = b""  
    pc = RTCPeerConnection() 
    pcs.add(pc) 
    stream_id = None

    while True:
        message = await receive()
        if message["type"] == "webtransport.stream.receive":
            buffer += message["data"]
            if stream_id is None:
                stream_id = message["stream"] # store stream id for communication
            try:
                obj = json.loads(buffer.decode()) # try json decode (works if full json received)
                
                # Handle sdp offer; spawn worker thread; create video track and set codec
                if obj.get("type") == "sdp-offer":
                    print("received sdp offer ")                   
                    sim = CarVisualizer(
                        width=sim_config["width"],
                        height=sim_config["height"],
                        fps=sim_config["fps"],
                        gravity=sim_config["grav"],
                        velocity=sim_config["vel"],
                        restitution=sim_config["cor"],
                    )
                    sim.start() 
                    track = CarVizVideoTrack(sim)
                    sender = pc.addTrack(track)
                    force_codec(pc, sender, "video/H264")

                    await pc.setRemoteDescription(RTCSessionDescription(sdp=obj["sdp"], type="offer"))
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)

                    answer_message = {
                        "type": "sdp-answer",
                        "sdp": pc.localDescription.sdp
                    }

                    payload = json.dumps(answer_message).encode()+ b"eol"

                    await send({
                        "data": payload,
                        "stream": message["stream"],
                        "type": "webtransport.stream.send",
                    })
                    print("replied with sdp answer")
                
                if obj.get("type") == "detected-center":
                    # compute L2 norm between reported and live ball center, and send it back to client over the same wt stream
                    if sim is not None and sim.current_center is not None:
                        current_center = sim.current_center
                        # print(current_center)
                        # print(type(obj["x"]),",",type(obj["x"]))
                        diff_x = current_center[0] - float(obj["x"])
                        diff_y = current_center[1] - float(obj["y"])
                        l2err = (diff_x**2+diff_y**2)**0.5
                    else:
                        l2err = 0.0
                        print("no center available, sim not started")

                    loc_err_message = {
                        "type": "l2-error",
                        "val": l2err
                    }

                    payload = json.dumps(loc_err_message).encode() + b"eol"

                    await send({
                        "type": "webtransport.stream.send",
                        "stream": message["stream"],
                        "data": payload,
                    })
                    # print("sent l2 err to client", loc_err_message)


                buffer = b"" # clear buffer for new message

            except json.JSONDecodeError:
                pass # complete json message not received yet, continue buffering


async def on_shutdown():
    """
    Handles shutdown of demo app module on SIGINT or SIGTERM
    """
    global sim, pcs

    # Stop worker thread if runnning
    if sim and sim.running:
        sim.stop()
        print("simulator thread stopped")

    # Close all peer connections
    if pcs:
        coros = [pc.close() for pc in pcs]
        await asyncio.gather(*coros)
        pcs.clear()
        print("peer connections closed")
        await asyncio.sleep(0.5) # small wait to close collected coroutines
    print("Demo shutdown complete")


starlette = Starlette(
    routes=[
        Route("/", homepage),
        Mount(STATIC_URL, StaticFiles(directory=STATIC_ROOT, html=True)),
    ],
)

async def app(scope: Scope, receive: Receive, send: Send) -> None:
    """
    ASGI app entrypoint. Routes webTransport and other http requests.
    """
    if scope["type"] == "webtransport" and scope["path"] == "/wt":
        await wt(scope, receive, send) # handle webTransport session at /wt
    else:
        await starlette(scope, receive, send)

app.on_shutdown = on_shutdown 