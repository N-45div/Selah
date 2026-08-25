/**
 * Selah — Web MIDI & USB Foot Pedal Controller Service
 * 
 * Native browser listener for MIDI sustain pedals (CC #64),
 * NoteOn triggers, and USB presenter remote PageUp/PageDown keys.
 * Allows worship tech operators to advance slides hands-free
 * while mixing audio on the sound board.
 */

const MIDI_NOTE_NEXT = [36, 60];      // C1, Middle C -> Next Slide
const MIDI_NOTE_PREV = [38, 62];      // D1, D4 -> Previous Slide
const MIDI_NOTE_MUTE = [40, 64];      // E1, E4 -> Emergency Mute
const MIDI_NOTE_BLACKOUT = [41, 65];  // F1, F4 -> Screen Blackout
const MIDI_CC_SUSTAIN = 64;           // Sustain Pedal CC -> Next Slide
const MIDI_CC_SOFT = 65;              // Soft Pedal CC -> Previous Slide

/**
 * Initialize Web MIDI API controller.
 * @param {Object} callbacks
 * @param {Function} callbacks.onNextSlide
 * @param {Function} callbacks.onPrevSlide
 * @param {Function} callbacks.onEmergencyMute
 * @param {Function} callbacks.onBlackout
 * @returns {{ connected: boolean, cleanup: Function }}
 */
export function initMidiController({ onNextSlide, onPrevSlide, onEmergencyMute, onBlackout }) {
  const state = { connected: false, cleanup: () => {} };

  if (!navigator.requestMIDIAccess) {
    console.warn('[Selah MIDI] Web MIDI API is not supported in this browser.');
    return state;
  }

  navigator.requestMIDIAccess({ sysex: false })
    .then((midiAccess) => {
      console.log('[Selah MIDI] Access granted. Scanning for MIDI inputs...');

      const inputHandlers = [];

      function attachInputs() {
        for (let input of midiAccess.inputs.values()) {
          console.log(`[Selah MIDI] Found input: ${input.name} (${input.manufacturer})`);
          
          const handler = (message) => {
            const [statusByte, data1, data2] = message.data;
            const command = statusByte >> 4;

            // Note On (Type 9) with velocity > 0
            if (command === 9 && data2 > 0) {
              if (MIDI_NOTE_NEXT.includes(data1)) {
                onNextSlide?.();
              } else if (MIDI_NOTE_PREV.includes(data1)) {
                onPrevSlide?.();
              } else if (MIDI_NOTE_MUTE.includes(data1)) {
                onEmergencyMute?.();
              } else if (MIDI_NOTE_BLACKOUT.includes(data1)) {
                onBlackout?.();
              }
            }

            // Control Change (Type 11) — USB Foot Pedal Sustain
            if (command === 11) {
              if (data1 === MIDI_CC_SUSTAIN && data2 >= 64) {
                onNextSlide?.();
              } else if (data1 === MIDI_CC_SOFT && data2 >= 64) {
                onPrevSlide?.();
              }
            }
          };

          input.onmidimessage = handler;
          inputHandlers.push({ input, handler });
        }
      }

      attachInputs();
      state.connected = true;

      // Listen for newly connected MIDI devices (hot-plugging)
      midiAccess.onstatechange = (event) => {
        if (event.port.type === 'input' && event.port.state === 'connected') {
          console.log(`[Selah MIDI] New input connected: ${event.port.name}`);
          attachInputs();
        }
      };

      state.cleanup = () => {
        inputHandlers.forEach(({ input }) => {
          input.onmidimessage = null;
        });
        midiAccess.onstatechange = null;
      };
    })
    .catch((err) => {
      console.error('[Selah MIDI] Failed to access MIDI devices:', err);
    });

  return state;
}

/**
 * Initialize USB Foot Pedal / Wireless Presenter Remote keyboard listener.
 * Maps PageUp/PageDown and common presenter remote keys to slide navigation.
 * @param {Object} callbacks
 * @param {Function} callbacks.onNextSlide
 * @param {Function} callbacks.onPrevSlide
 * @returns {Function} cleanup - Call to remove event listener
 */
export function initFootPedalListener({ onNextSlide, onPrevSlide }) {
  const handler = (e) => {
    if (e.key === 'PageDown' || e.key === 'Next') {
      e.preventDefault();
      onNextSlide?.();
    } else if (e.key === 'PageUp' || e.key === 'Prior') {
      e.preventDefault();
      onPrevSlide?.();
    }
  };

  window.addEventListener('keydown', handler);
  console.log('[Selah Pedal] USB foot pedal / presenter remote listener active (PageUp/PageDown).');

  return () => {
    window.removeEventListener('keydown', handler);
  };
}
