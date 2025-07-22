(() => {
  // ✅ WebGPU: добавим, если BrowserForge убрал


  // ✅ WebRTC leak mitigation (не ломая методы)
  const OrigRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
  if (OrigRTCPeerConnection && !OrigRTCPeerConnection.__patchedForLeak__) {
    const NewRTCPeerConnection = function (config) {
      if (config && config.iceServers) {
        config.iceServers = []; // убираем STUN-сервера
      }
      const pc = new OrigRTCPeerConnection(config);
      return pc;
    };
    NewRTCPeerConnection.prototype = OrigRTCPeerConnection.prototype;
    NewRTCPeerConnection.__patchedForLeak__ = true;
    window.RTCPeerConnection = NewRTCPeerConnection;
    window.webkitRTCPeerConnection = NewRTCPeerConnection;
  }
})();

