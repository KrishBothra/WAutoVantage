# Work Tracker

## Sim
- [x] Create python sandbox to design the sim
- [x] Add gravity physics
- [x] Add Collision physics
- [x] Generate frames

## Client
- [x] Setup simple webApp using js
- [x] Send a webRTC request over webtransport

## Server
- [x] Establish handshake by confirming connection with client 
- [x] Attempt streaming blank frames to test communication
- [x] Spawn Simulation Thread
- [x] Consume frames 
- [x] Encode in h.264
- [x] Send over webRTC

## Client
- [x] Get frames from server
- [x] Display frame and find ball location
- [x] Return location via WebTransport

## Server
- [x] Receive detected location 
- [x] Compute error and transmit to client via WebTransport

## Client
- [x] Receive the transmitted err data and display

## Shutdown
- [x] Handle graceful shutdown of server

## Testing
- [x] Unit tests for simulation worker
- [x] Use unittest
- [x] Pass all tests
- [x] Document code  

## Deployment
- [x] Dockerize server
- [x] Deploy using kubernetes
- [x] Document deploying and decisions
- [x] Add clear comments
- [x] Share screen capture

