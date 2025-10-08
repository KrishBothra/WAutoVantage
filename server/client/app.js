const connect_btn = document.getElementById('connect_btn');
const remote_video = document.getElementById('remote_video');
const status_display = document.getElementById('status_display');

async function init() {
  console.log('Connect button clicked');
  const origin = window.location.protocol + '//' + window.location.host;
  const url = `${origin}/wt`;

  connect_btn.disabled = true;

  let transport;
  try {

    transport = new WebTransport(url);
    await transport.ready;
    console.log('wt session is ready');
    status_display.textContent = 'Connected';
    
    const pc = new RTCPeerConnection();
    pc.ontrack = (event) => {
      if (event.track.kind === 'video') {
        remote_video.srcObject = event.streams[0];
        remote_video.onplaying = () => {
          function animationLoop() {
            const center = processFrame();
            if (center) {
              const message = {
                type: "detected-center",
                x: center.x,
                y: center.y
              };
              writer.write(encoder.encode(JSON.stringify(message)));
            }
            requestAnimationFrame(animationLoop);
          }
          animationLoop();
        }        
      }
    }

    const offer = await pc.createOffer({ offerToReceiveVideo: true });
    await pc.setLocalDescription(offer);

    const sdpOfferString = offer.sdp;

    const { readable, writable } = await transport.createBidirectionalStream();  

    const writer = writable.getWriter();
    const reader = readable.getReader();
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    const message = {
      type: "sdp-offer",
      sdp: sdpOfferString
    };

    console.log('spd-offer',JSON.stringify(message))
    transport.closed
      .then(() => {status_display.textContent = 'Session closed by server';})
      .catch((err) => {status_display.textContent = 'Server disconnected';});

    await writer.write((encoder.encode(JSON.stringify(message))));
    console.log('sent sdp offer to server');

    (async () => {
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          status_display.textContent = 'stream closed';
          break;
        }
    
        // accumulate and split at end of line tag
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('eol');
        buffer = parts.pop();  // leftover message that is part of next json
    
        for (const line of parts) {
          if (!line) continue;
    
          const message = JSON.parse(line);
          status_display.textContent = "Received reply";
          if (message.type === "sdp-answer") {
            console.log('Received sdp answer', message.sdp);
            const remoteDesc = new RTCSessionDescription({
              type: "answer",
              sdp: message.sdp
            });
            await pc.setRemoteDescription(remoteDesc);
            status_display.textContent = "Hand shake completed; connection established";
          }

          if (message.type === "l2-error") {
            status_display.textContent = `Reported L2 Error: ${message.val.toFixed(2)}`;
          }
        }
      }
    })();

  } 
  
  catch (e) {
    console.error('webTransport failed:', e);
    status_display.textContent = `Error: ${e.message}`;
  }

}


function processFrame() {
  const video = document.getElementById('remote_video');
  const canvas = document.getElementById('hidden_canvas');
  const ctx = canvas.getContext('2d', { willReadFrequently: true });

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const frameData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const pixels = frameData.data;
  let weightedSumX = 0;
  let weightedSumY = 0;
  let totalWeight = 0;

  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const index = (y * canvas.width + x) * 4;
      const r = pixels[index];
      if (r > 5) {
        weightedSumX += x * r;
        weightedSumY += y * r;
        totalWeight += r;
      }
    }
  }

  let center = null;
  if (totalWeight > 0) {
    const centerX = weightedSumX / totalWeight;
    const centerY = weightedSumY / totalWeight;
    center = { x: centerX.toFixed(3), y: centerY.toFixed(3) };
  } else {
    console.log("no ball detecte.");
  }
  return center;

}


connect_btn.addEventListener('click', init);
