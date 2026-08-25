/**
 * Selah — OBS Studio WebSocket v5 Protocol Client (RFC 6455)
 * 
 * Provides automated broadcast automation from Selah:
 * - Automatic Stream Audio Muting when transitioning to red-verdict songs
 * - Scene switching (Worship / Sermon / Lower Thirds overlay)
 * - Connection status monitoring
 */

class ObsWebSocketClient {
  constructor() {
    this.ws = null;
    this.identified = false;
    this.requestId = 1;
    this.url = 'ws://127.0.0.1:4455';
    this.password = '';
    this.listeners = new Set();
  }

  connect(url = 'ws://127.0.0.1:4455', password = '') {
    this.url = url;
    this.password = password;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[Selah OBS] WebSocket connected to', this.url);
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          // Op 0: Hello from OBS
          if (msg.op === 0) {
            // Op 1: Identify
            this.ws.send(JSON.stringify({
              op: 1,
              d: {
                rpcVersion: 1,
                eventSubscriptions: 33, // General + Inputs
                ...(this.password ? { authentication: this.password } : {})
              }
            }));
          } 
          // Op 2: Identified
          else if (msg.op === 2) {
            this.identified = true;
            console.log('[Selah OBS] Successfully authenticated & identified with OBS Studio!');
            this.notifyListeners('connected', true);
          }
        } catch (e) {
          console.error('[Selah OBS] Message parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.identified = false;
        this.notifyListeners('connected', false);
        console.log('[Selah OBS] Disconnected from OBS Studio.');
      };

      this.ws.onerror = (err) => {
        console.warn('[Selah OBS] WebSocket notice (OBS may not be running):', err);
      };
    } catch (err) {
      console.warn('[Selah OBS] Connection initialization notice:', err);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.identified = false;
    }
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notifyListeners(event, data) {
    this.listeners.forEach((l) => l(event, data));
  }

  /**
   * Set Mute state for Livestream Audio in OBS
   * @param {string} inputName - Name of audio source in OBS (e.g. 'Livestream Audio' / 'Mic/Aux')
   * @param {boolean} muted - true to mute, false to unmute
   */
  setStreamAudioMute(inputName = 'Livestream Audio', muted = true) {
    if (!this.identified || !this.ws) return;

    this.ws.send(JSON.stringify({
      op: 6, // Request
      d: {
        requestType: 'SetInputMute',
        requestId: `req_mute_${this.requestId++}`,
        requestData: {
          inputName: inputName,
          inputMuted: muted
        }
      }
    }));
    console.log(`[Selah OBS] Sent SetInputMute: ${inputName} -> ${muted ? 'MUTED' : 'UNMUTED'}`);
  }

  /**
   * Switch Program Scene in OBS
   * @param {string} sceneName - Target scene name (e.g. 'Worship Lyrics', 'Sermon Camera')
   */
  setCurrentProgramScene(sceneName) {
    if (!this.identified || !this.ws) return;

    this.ws.send(JSON.stringify({
      op: 6,
      d: {
        requestType: 'SetCurrentProgramScene',
        requestId: `req_scene_${this.requestId++}`,
        requestData: {
          sceneName: sceneName
        }
      }
    }));
  }
}

export const obsClient = new ObsWebSocketClient();
