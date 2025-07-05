import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: 'biki.AudioRecorderNode',
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === 'BikiAudioRecorderNode') {
            nodeData.input.required.audioUI = ['AUDIO_UI', {}];

            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const currentNode = this;
                let mediaRecorder;
                let audioChunks = [];
                let isRecording = false;
                let recordingTimer;

                // Hide the base64_data widget
                const base64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                if (base64Widget) {
                    base64Widget.type = "hidden";
                }

                // Create custom button and countdown display
                const startBtn = document.createElement("div");
                startBtn.textContent = 'START';
                startBtn.classList.add("comfy-biki-big-button");
                const countdownDisplay = document.createElement("div");
                countdownDisplay.classList.add("comfy-biki-value-small-display");

                this.addDOMWidget("button_widget", "Start/Stop Recording", startBtn);
                this.addDOMWidget("text_widget", "Countdown Display", countdownDisplay);

                // Toggle recording on click
                startBtn.onclick = () => {
                    if (isRecording) stopRecording(); else startRecording();
                };

                const startRecording = () => {
                    if (isRecording) return;
                    if (!navigator.mediaDevices?.getUserMedia) return console.error('No audio support');

                    audioChunks = [];
                    isRecording = true;

                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then(stream => {
                            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                            mediaRecorder.ondataavailable = e => e.data.size && audioChunks.push(e.data);
                            mediaRecorder.onstop = () => {
                                const blob = new Blob(audioChunks, { type: 'audio/webm' });
                                const reader = new FileReader();
                                reader.onloadend = () => {
                                    const base64data = reader.result.split(',')[1];
                                    const audioBase64 = currentNode.widgets.find(w => w.name === 'base64_data');
                                    audioBase64.value = base64data;
                                    const audioUI = currentNode.widgets.find(w => w.name === 'audioUI');
                                    audioUI.element.src = `data:audio/webm;base64,${base64data}`;
                                    audioUI.element.classList.remove("empty-audio-widget");
                                };
                                reader.readAsDataURL(blob);
                            };
                            mediaRecorder.start();

                            // Update UI
                            startBtn.textContent = 'STOP';
                            console.log('Recording...');

                            // Countdown
                            const maxDuration = (currentNode.widgets.find(w => w.name === 'record_duration_max')?.value) || 10;
                            let remaining = maxDuration;
                            countdownDisplay.textContent = `Will stop in ${remaining}s`;

                            recordingTimer = setInterval(() => {
                                remaining--;
                                if (remaining <= 0) {
                                    clearInterval(recordingTimer);
                                    stopRecording();
                                } else {
                                    countdownDisplay.textContent = `Will stop in ${remaining}s`;
                                }
                            }, 1000);
                        });
                };

                const stopRecording = () => {
                    if (mediaRecorder?.state === 'recording') mediaRecorder.stop();
                    isRecording = false;
                    clearInterval(recordingTimer);
                    countdownDisplay.textContent = '';
                    startBtn.textContent = 'START';
                    console.log('Stopped');
                };

                this.onRemoved = () => {
                    clearInterval(recordingTimer);
                };
                this.serialize_widgets = true;
            };
        }
    }
});

// Styles (unchanged)
const style = document.createElement("style");
style.textContent = `
    .comfy-biki-big-button {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 10px;
        width: 20px;
        height: 20px;
        background-color: #e82b0e;
        color: white;
        font-size: 20px;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
    }

    .comfy-biki-big-button:hover {
        background-color: #bfafac;
    }

    .comfy-biki-big-button:active {
        background-color: #4CAF50;
    }

    .comfy-biki-big-button::before {
        content: "🎤";
        margin-right: 4px;
    }

    .comfy-biki-value-small-display {
        margin-top: 20px;
        font-size: 14px;
        text-align: center;
    }
`;
document.head.appendChild(style);
