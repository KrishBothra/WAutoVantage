# Decisions, Learnings and Challenges

## Server

- Used `aiortc` and `aioquic` for WebRTC and WebTransport, respectively, due to their compatibility and Python support.
- Leveraged OpenCV for frame generation.
- Adopted existing examples from aiortc/aioquic to build the HTTP3 and WebRTC pipelines.

## Web App

- Used JavaScript to build a simple video-enabled client interface.
- Leveraged previous experience with WebGL to set up a test-ready webpage.

## Simulation

- Designed a bouncing ball simulation with gravity and coefficient of restitution.
- Assumed real-world scale: 1 pixel = 1 cm, VGA frame simulating a 6.4m x 4.8m room.
- Ball modeled as a size 7 basketball (~12 cm radius).
- Collision detection implemented using boundary checks.
- Configurable frame rate via dynamic sleep based on frame generation time.
- Used a Python queue (size 10) for frame buffering between threads.

## WebTransport

- Initially tried to build from scratch using Chrome's sample repository.
- Switched to using `http3_server.py` and `demo.py` from `aioquic/examples` for a working baseline.
- Used bidirectional streams instead of datagrams for larger and reliable messages like SDP.
- Implemented stream buffering to avoid truncated JSON messages.
- Generated WebTransport fingerprint and browser flags via Chrome sample guide.

## WebRTC

- Used `MediaStreamTrack` in `aiortc` to create and send video stream.
- Forced codec to H264 using provided utility to avoid compression artifacts.
- Verified codec settings using `chrome://webrtc-internals`.

## Compute ball center center on Client

- Captured video frame to hidden canvas for pixel access.
- Calculated centroid using weighted average on red channel after thresholding.
- Accounted for potential encoding artifacts in centroid calculation.

## Subsequent Communication

- Used bidirectional WebTransport streams for error and location data.
- Handled message routing by checking message types.

## Error

- Enabled configurable velocity and gravity to simulate ideal error tracking conditions.
- Disabled gravity and used perfectly elastic collisions for consistent velocity magnitude.

## Tests

- Unit tests covered physics logic, frame generation, and thread management.
- Validated video stream frame properties.

## Kubernetes

- Initial deployment using `LoadBalancer` and `minikube` failed due to QUIC compatibility issues.
- Switched to `NodePort` with `hostNetwork: true` for reliable QUIC communication.
- Resolved issues with hardcoded client URLs by using dynamic hostname detection.
- Encountered Docker cache issues requiring full reset of local environments.
- Successfully deployed, though observed intermittent freezing likely due to QUIC limitations in Kubernetes environments.
