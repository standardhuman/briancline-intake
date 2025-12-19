// Voice Recording Handler
class VoiceRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioBlob = null;
    this.audioUrl = null;
    this.isRecording = false;
    this.uploadedUrl = null;
    // Waveform visualization
    this.audioContext = null;
    this.analyser = null;
    this.animationId = null;
    this.startTime = null;
    this.timerInterval = null;
  }

  async init() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Determine best supported MIME type
      const mimeTypes = ['audio/webm', 'audio/mp4', 'audio/ogg'];
      this.mimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type)) || '';

      this.mediaRecorder = new MediaRecorder(stream, this.mimeType ? { mimeType: this.mimeType } : {});

      // Set up audio analysis for waveform
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      const source = this.audioContext.createMediaStreamSource(stream);
      source.connect(this.analyser);

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          this.audioChunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        // Use the actual MIME type from the recorder
        const actualType = this.mediaRecorder.mimeType || this.mimeType || 'audio/webm';
        this.audioBlob = new Blob(this.audioChunks, { type: actualType });
        this.audioUrl = URL.createObjectURL(this.audioBlob);
        this.updateUI();
      };

      return true;
    } catch (error) {
      console.error('Microphone access denied:', error);
      return false;
    }
  }

  start() {
    this.audioChunks = [];
    // Record in 100ms chunks to ensure data is captured
    this.mediaRecorder.start(100);
    this.isRecording = true;
    this.startTime = Date.now();
    this.updateUI();
    this.startWaveform();
    this.startTimer();
  }

  stop() {
    this.mediaRecorder.stop();
    this.isRecording = false;
    this.stopWaveform();
    this.stopTimer();
  }

  startWaveform() {
    const canvas = document.getElementById('waveform');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    // Set canvas resolution for sharp rendering
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const draw = () => {
      if (!this.isRecording) return;

      this.animationId = requestAnimationFrame(draw);
      this.analyser.getByteTimeDomainData(dataArray);

      // Clear with background
      ctx.fillStyle = '#f3f4f6';
      ctx.fillRect(0, 0, rect.width, rect.height);

      // Draw waveform
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#dc2626';
      ctx.beginPath();

      const sliceWidth = rect.width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * rect.height) / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }

      ctx.lineTo(rect.width, rect.height / 2);
      ctx.stroke();
    };

    draw();
  }

  stopWaveform() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  startTimer() {
    const timeEl = document.getElementById('recording-time');
    if (!timeEl) return;

    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const mins = Math.floor(elapsed / 60);
      const secs = elapsed % 60;
      timeEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    }, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  async upload() {
    if (!this.audioBlob) return null;

    // Get correct extension from MIME type
    const ext = this.audioBlob.type.includes('mp4') ? 'm4a' :
                this.audioBlob.type.includes('ogg') ? 'ogg' : 'webm';

    const formData = new FormData();
    formData.append('file', this.audioBlob, `recording.${ext}`);
    formData.append('type', 'audio');

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      this.uploadedUrl = data.url;
      return data.url;
    } catch (error) {
      console.error('Audio upload error:', error);
      return null;
    }
  }

  updateUI() {
    const recordBtn = document.getElementById('record-btn');
    const recordingStatus = document.getElementById('recording-status');
    const audioPreview = document.getElementById('audio-preview');
    const audioPlayer = document.getElementById('audio-player');

    if (this.isRecording) {
      recordBtn.innerHTML = `
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="12" height="12" rx="1"></rect>
        </svg>
        Stop Recording
      `;
      recordBtn.classList.add('bg-red-600', 'hover:bg-red-700');
      recordBtn.classList.remove('bg-gray-900', 'hover:bg-gray-800');
      recordingStatus.classList.remove('hidden');
    } else {
      recordBtn.innerHTML = `
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
        </svg>
        Start Recording
      `;
      recordBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
      recordBtn.classList.add('bg-gray-900', 'hover:bg-gray-800');
      recordingStatus.classList.add('hidden');

      if (this.audioUrl) {
        audioPreview.classList.remove('hidden');
        audioPlayer.src = this.audioUrl;
      }
    }
  }

  clear() {
    this.audioChunks = [];
    this.audioBlob = null;
    this.audioUrl = null;
    this.uploadedUrl = null;
    document.getElementById('audio-preview').classList.add('hidden');
    const timeEl = document.getElementById('recording-time');
    if (timeEl) timeEl.textContent = '0:00';
  }
}

// File Upload Handler
class FileUploader {
  constructor() {
    this.files = [];
    this.uploadedUrls = [];
  }

  addFiles(newFiles) {
    for (const file of newFiles) {
      if (file.type.startsWith('image/') && this.files.length < 10) {
        this.files.push(file);
      }
    }
    this.updateUI();
  }

  removeFile(index) {
    this.files.splice(index, 1);
    this.uploadedUrls.splice(index, 1);
    this.updateUI();
  }

  async uploadAll() {
    this.uploadedUrls = [];

    for (const file of this.files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', 'image');

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          this.uploadedUrls.push(data.url);
        }
      } catch (error) {
        console.error('File upload error:', error);
      }
    }

    return this.uploadedUrls;
  }

  updateUI() {
    const preview = document.getElementById('file-preview');
    const fileCount = document.getElementById('file-count');

    if (this.files.length === 0) {
      preview.classList.add('hidden');
      preview.innerHTML = '';
      return;
    }

    preview.classList.remove('hidden');
    fileCount.textContent = `${this.files.length} file${this.files.length > 1 ? 's' : ''} selected`;

    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-3 gap-2 mt-3';

    this.files.forEach((file, index) => {
      const item = document.createElement('div');
      item.className = 'relative group';

      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.className = 'w-full h-20 object-cover rounded-lg';

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity';
      removeBtn.innerHTML = '×';
      removeBtn.onclick = () => this.removeFile(index);

      item.appendChild(img);
      item.appendChild(removeBtn);
      grid.appendChild(item);
    });

    preview.innerHTML = '';
    const countEl = document.createElement('p');
    countEl.id = 'file-count';
    countEl.className = 'text-sm text-gray-600';
    countEl.textContent = `${this.files.length} file${this.files.length > 1 ? 's' : ''} selected`;
    preview.appendChild(countEl);
    preview.appendChild(grid);
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
  const recorder = new VoiceRecorder();
  const uploader = new FileUploader();

  // Voice recording setup
  const recordBtn = document.getElementById('record-btn');
  const clearRecordingBtn = document.getElementById('clear-recording');

  if (recordBtn) {
    recordBtn.addEventListener('click', async () => {
      if (!recorder.mediaRecorder) {
        const success = await recorder.init();
        if (!success) {
          alert('Could not access microphone. Please allow microphone access and try again.');
          return;
        }
      }

      if (recorder.isRecording) {
        recorder.stop();
      } else {
        recorder.start();
      }
    });
  }

  if (clearRecordingBtn) {
    clearRecordingBtn.addEventListener('click', () => {
      recorder.clear();
    });
  }

  // File upload setup
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('border-gray-900', 'bg-gray-50');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-gray-900', 'bg-gray-50');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-gray-900', 'bg-gray-50');
      uploader.addFiles(e.dataTransfer.files);
    });

    dropZone.addEventListener('click', () => {
      fileInput.click();
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      uploader.addFiles(fileInput.files);
    });
  }

  // Form submission
  const form = document.getElementById('intake-form');
  const submitBtn = form?.querySelector('button[type="submit"]');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      submitBtn.disabled = true;
      submitBtn.textContent = 'Uploading files...';

      // Upload audio if recorded
      let audioUrl = null;
      if (recorder.audioBlob) {
        audioUrl = await recorder.upload();
      }

      // Upload images
      let imageUrls = [];
      if (uploader.files.length > 0) {
        submitBtn.textContent = 'Uploading images...';
        imageUrls = await uploader.uploadAll();
      }

      submitBtn.textContent = 'Sending...';

      // Add file URLs to form data
      const formData = new FormData(form);
      if (audioUrl) {
        formData.append('audio-url', audioUrl);
      }
      if (imageUrls.length > 0) {
        formData.append('image-urls', imageUrls.join(','));
      }

      // Submit form
      try {
        const response = await fetch('/api/submit', {
          method: 'POST',
          body: formData,
        });

        if (response.redirected) {
          window.location.href = response.url;
        } else if (response.ok) {
          window.location.href = '/thank-you.html';
        } else {
          throw new Error('Submission failed');
        }
      } catch (error) {
        console.error('Form submission error:', error);
        alert('Something went wrong. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Project Inquiry';
      }
    });
  }
});
