// ProMirrorGolf - UI Controls Handler

class PlaybackControls {
    constructor() {
        this.isPlaying = false;
        this.currentFrame = 0;
        this.totalFrames = 300;
        this.playbackSpeed = 1.0;
        this.animationId = null;
        this.lastFrameTime = 0;
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        // Playback elements
        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.playIcon = this.playPauseBtn.querySelector('.play-icon');
        this.pauseIcon = this.playPauseBtn.querySelector('.pause-icon');
        this.scrubber = document.getElementById('timeline-scrubber');
        this.progress = document.getElementById('timeline-progress');
        this.frameCounter = document.getElementById('current-frame');
        
        // Speed buttons
        this.speedButtons = document.querySelectorAll('.speed-btn');
        
        // View buttons
        this.viewButtons = document.querySelectorAll('.view-btn');
        
        // Export button
        this.exportBtn = document.getElementById('export-btn');
        this.exportModal = document.getElementById('export-modal');
        
        // Overlay toggle
        this.overlayToggle = document.getElementById('overlay-toggle');
        
        // Pro/Club selectors
        this.proSelector = document.getElementById('pro-selector');
        this.clubSelector = document.getElementById('club-selector');
    }
    
    attachEventListeners() {
        // Play/Pause
        this.playPauseBtn.addEventListener('click', () => this.togglePlayback());
        
        // Scrubber
        this.scrubber.addEventListener('input', (e) => {
            this.currentFrame = parseInt(e.target.value);
            this.updateFrame();
        });
        
        // Speed controls
        this.speedButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setPlaybackSpeed(parseFloat(btn.dataset.speed));
                this.updateSpeedButtons(btn);
            });
        });
        
        // View controls
        this.viewButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const panel = btn.closest('.viewer-panel');
                const view = btn.dataset.view;
                this.changeView(panel.id, view);
                this.updateViewButtons(btn, panel);
            });
        });
        
        // Export
        this.exportBtn.addEventListener('click', () => this.openExportModal());
        
        // Export modal
        const modalClose = this.exportModal.querySelector('.modal-close');
        modalClose.addEventListener('click', () => this.closeExportModal());
        
        this.exportModal.addEventListener('click', (e) => {
            if (e.target === this.exportModal) {
                this.closeExportModal();
            }
        });
        
        const exportOptions = this.exportModal.querySelectorAll('.export-option');
        exportOptions.forEach(option => {
            option.addEventListener('click', () => {
                this.handleExport(option.dataset.format);
            });
        });
        
        // Overlay toggle
        this.overlayToggle.addEventListener('click', () => this.toggleOverlay());
        
        // Pro selector
        this.proSelector.addEventListener('change', (e) => {
            this.loadPro(e.target.value);
        });
        
        // Club selector
        this.clubSelector.addEventListener('change', (e) => {
            this.changeClub(e.target.value);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
    }
    
    togglePlayback() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    play() {
        this.isPlaying = true;
        this.playIcon.style.display = 'none';
        this.pauseIcon.style.display = 'block';
        this.lastFrameTime = performance.now();
        this.animate();
    }
    
    pause() {
        this.isPlaying = false;
        this.playIcon.style.display = 'block';
        this.pauseIcon.style.display = 'none';
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    animate() {
        if (!this.isPlaying) return;
        
        const currentTime = performance.now();
        const deltaTime = currentTime - this.lastFrameTime;
        const frameDuration = 1000 / (60 * this.playbackSpeed); // 60 fps base
        
        if (deltaTime >= frameDuration) {
            this.currentFrame++;
            if (this.currentFrame >= this.totalFrames) {
                this.currentFrame = 0;
            }
            this.updateFrame();
            this.lastFrameTime = currentTime;
        }
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    updateFrame() {
        // Update scrubber
        this.scrubber.value = this.currentFrame;
        
        // Update progress bar
        const progressPercent = (this.currentFrame / this.totalFrames) * 100;
        this.progress.style.width = `${progressPercent}%`;
        
        // Update frame counter
        this.frameCounter.textContent = this.currentFrame;
        
        // Trigger frame update event for renderers
        window.dispatchEvent(new CustomEvent('frameUpdate', { 
            detail: { frame: this.currentFrame } 
        }));
    }
    
    setPlaybackSpeed(speed) {
        this.playbackSpeed = speed;
    }
    
    updateSpeedButtons(activeBtn) {
        this.speedButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }
    
    changeView(panelId, view) {
        // Trigger view change event for renderers
        window.dispatchEvent(new CustomEvent('viewChange', { 
            detail: { panel: panelId, view: view } 
        }));
    }
    
    updateViewButtons(activeBtn, panel) {
        const buttons = panel.querySelectorAll('.view-btn');
        buttons.forEach(btn => {
            btn.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }
    
    toggleOverlay() {
        window.dispatchEvent(new CustomEvent('toggleOverlay'));
    }
    
    openExportModal() {
        this.exportModal.style.display = 'flex';
        this.pause(); // Pause playback when opening modal
    }
    
    closeExportModal() {
        this.exportModal.style.display = 'none';
    }
    
    handleExport(format) {
        console.log(`Exporting as ${format}...`);
        
        // Trigger export event
        window.dispatchEvent(new CustomEvent('export', { 
            detail: { format: format } 
        }));
        
        this.closeExportModal();
        
        // Show export progress (would be handled by backend)
        this.showExportProgress(format);
    }
    
    showExportProgress(format) {
        // Create temporary progress notification
        const notification = document.createElement('div');
        notification.className = 'export-notification';
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-dark);
            padding: 16px 20px;
            border-radius: 8px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
        `;
        
        notification.innerHTML = `
            <div class="loading" style="
                width: 16px;
                height: 16px;
                border: 2px solid var(--border-light);
                border-top-color: var(--accent-red);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
            <span>Exporting as ${format.toUpperCase()}...</span>
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds (simulating export completion)
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    loadPro(proId) {
        if (!proId) return;
        
        // Update header
        const proName = this.proSelector.options[this.proSelector.selectedIndex].text;
        document.getElementById('pro-name').textContent = proName;
        
        // Trigger pro load event
        window.dispatchEvent(new CustomEvent('loadPro', { 
            detail: { proId: proId } 
        }));
    }
    
    changeClub(club) {
        // Trigger club change event
        window.dispatchEvent(new CustomEvent('changeClub', { 
            detail: { club: club } 
        }));
    }
    
    handleKeyPress(e) {
        // Keyboard shortcuts
        switch(e.key) {
            case ' ':
                e.preventDefault();
                this.togglePlayback();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.currentFrame = Math.max(0, this.currentFrame - 1);
                this.updateFrame();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.currentFrame = Math.min(this.totalFrames - 1, this.currentFrame + 1);
                this.updateFrame();
                break;
            case '1':
                this.setPlaybackSpeed(0.25);
                this.updateSpeedButtons(this.speedButtons[0]);
                break;
            case '2':
                this.setPlaybackSpeed(1.0);
                this.updateSpeedButtons(this.speedButtons[1]);
                break;
            case '3':
                this.setPlaybackSpeed(2.0);
                this.updateSpeedButtons(this.speedButtons[2]);
                break;
            case 'o':
                this.toggleOverlay();
                break;
            case 'e':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.openExportModal();
                }
                break;
        }
    }
    
    // Helper method to reset playback
    reset() {
        this.pause();
        this.currentFrame = 0;
        this.updateFrame();
    }
    
    // Helper method to jump to specific swing phase
    jumpToPhase(phase) {
        const phaseFrames = {
            'address': 0,
            'backswing': 90,
            'top': 120,
            'downswing': 180,
            'impact': 210,
            'follow': 250
        };
        
        if (phase in phaseFrames) {
            this.currentFrame = phaseFrames[phase];
            this.updateFrame();
        }
    }
}

// Add spin animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .export-notification {
        animation: slideInRight 0.3s ease-out;
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Export for use in other modules
window.PlaybackControls = PlaybackControls;