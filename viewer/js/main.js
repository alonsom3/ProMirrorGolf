// ProMirrorGolf - Main Application Controller

class ProMirrorGolfApp {
    constructor() {
        this.serverUrl = 'http://localhost:8080';
        this.userSwingData = null;
        this.proDatabase = null;
        this.currentProData = null;
        this.skeletonRenderers = {};
        this.isOverlayMode = false;
        
        this.initialize();
    }
    
    async initialize() {
        console.log('ProMirrorGolf initializing...');
        
        // Initialize UI controllers
        this.controls = new PlaybackControls();
        this.metricsDisplay = new MetricsDisplay();
        
        // Initialize 3D renderers
        this.initializeRenderers();
        
        // Set up event listeners
        this.attachEventListeners();
        
        // Load data
        await this.loadInitialData();
        
        // Start checking for new swings
        this.startSwingPolling();
        
        console.log('ProMirrorGolf ready!');
    }
    
    initializeRenderers() {
        // Initialize skeleton renderers for both panels
        const userCanvas = document.getElementById('user-canvas');
        const proCanvas = document.getElementById('pro-canvas');
        
        if (typeof SkeletonRenderer !== 'undefined') {
            this.skeletonRenderers.user = new SkeletonRenderer(userCanvas, 'user');
            this.skeletonRenderers.pro = new SkeletonRenderer(proCanvas, 'pro');
        } else {
            console.warn('SkeletonRenderer not loaded, using placeholder');
            this.createPlaceholderCanvases();
        }
    }
    
    createPlaceholderCanvases() {
        // Create placeholder canvases for testing without Three.js renderer
        const createPlaceholder = (container, label) => {
            const canvas = document.createElement('canvas');
            canvas.width = container.offsetWidth;
            canvas.height = container.offsetHeight;
            container.appendChild(canvas);
            
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#141414';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#FF4444';
            ctx.font = '20px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`${label} 3D View`, canvas.width/2, canvas.height/2);
            
            return canvas;
        };
        
        createPlaceholder(document.getElementById('user-canvas'), 'User');
        createPlaceholder(document.getElementById('pro-canvas'), 'Pro');
    }
    
    attachEventListeners() {
        // Frame updates
        window.addEventListener('frameUpdate', (e) => {
            this.updateFrame(e.detail.frame);
        });
        
        // View changes
        window.addEventListener('viewChange', (e) => {
            this.changeView(e.detail.panel, e.detail.view);
        });
        
        // Overlay toggle
        window.addEventListener('toggleOverlay', () => {
            this.toggleOverlayMode();
        });
        
        // Pro selection
        window.addEventListener('loadPro', (e) => {
            this.loadProData(e.detail.proId);
        });
        
        // Club change
        window.addEventListener('changeClub', (e) => {
            this.changeClub(e.detail.club);
        });
        
        // Export
        window.addEventListener('export', (e) => {
            this.handleExport(e.detail.format);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }
    
    async loadInitialData() {
        try {
            // Check for latest user swing from server
            const hasNewSwing = await this.checkForNewSwing();
            
            if (hasNewSwing) {
                await this.loadUserSwing();
            } else {
                // Load sample data for demonstration
                this.loadSampleSwing();
            }
            
            // Load pro database
            await this.loadProDatabase();
            
            // Load metrics for display
            this.updateMetricsDisplay();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            // Load sample data as fallback
            this.loadSampleData();
        }
    }
    
    async checkForNewSwing() {
        try {
            const response = await fetch(`${this.serverUrl}/api/latest-swing`);
            if (response.ok) {
                const data = await response.json();
                return data.hasNewSwing;
            }
        } catch (error) {
            console.log('Server not available, using sample data');
        }
        return false;
    }
    
    async loadUserSwing() {
        try {
            const response = await fetch(`${this.serverUrl}/api/user-swing`);
            if (response.ok) {
                this.userSwingData = await response.json();
                this.updateUserRenderer();
            }
        } catch (error) {
            console.error('Error loading user swing:', error);
        }
    }
    
    loadSampleSwing() {
        // Create sample swing data for demonstration
        this.userSwingData = this.generateSampleSwingData('user');
        this.updateUserRenderer();
    }
    
    async loadProDatabase() {
        try {
            const response = await fetch(`${this.serverUrl}/api/pros`);
            if (response.ok) {
                this.proDatabase = await response.json();
            } else {
                throw new Error('Pro database not available');
            }
        } catch (error) {
            console.log('Loading sample pro database');
            this.proDatabase = this.generateSampleProDatabase();
        }
        
        this.populateProSelector();
    }
    
    generateSampleProDatabase() {
        // Generate sample pro data for demonstration
        const pros = [
            { id: 'rory_mcilroy_driver', name: 'Rory McIlroy', club: 'Driver' },
            { id: 'tiger_woods_driver', name: 'Tiger Woods', club: 'Driver' },
            { id: 'dustin_johnson_driver', name: 'Dustin Johnson', club: 'Driver' },
            { id: 'jon_rahm_driver', name: 'Jon Rahm', club: 'Driver' },
            { id: 'justin_thomas_driver', name: 'Justin Thomas', club: 'Driver' },
            { id: 'rory_mcilroy_7iron', name: 'Rory McIlroy', club: '7-Iron' },
            { id: 'tiger_woods_7iron', name: 'Tiger Woods', club: '7-Iron' },
            { id: 'dustin_johnson_7iron', name: 'Dustin Johnson', club: '7-Iron' }
        ];
        
        return pros.map(pro => ({
            pro_id: pro.id,
            golfer_name: pro.name,
            club_type: pro.club,
            metrics: {
                hip_rotation: 45 + Math.random() * 10,
                shoulder_rotation: 90 + Math.random() * 20,
                x_factor: 45 + Math.random() * 10,
                spine_angle_address: 30 + Math.random() * 8,
                tempo_ratio: 2.8 + Math.random() * 0.6,
                weight_shift: 75 + Math.random() * 15
            },
            pose_sequence: this.generateSamplePoseSequence()
        }));
    }
    
    generateSampleSwingData(type) {
        return {
            swing_id: `${type}_${Date.now()}`,
            timestamp: new Date().toISOString(),
            metrics: {
                hip_rotation: type === 'user' ? 45.2 : 48.3,
                shoulder_rotation: type === 'user' ? 78.5 : 96.2,
                x_factor: type === 'user' ? 43.1 : 47.9,
                spine_angle_address: type === 'user' ? 25.3 : 33.2,
                tempo_ratio: type === 'user' ? 3.0 : 3.1,
                weight_shift: type === 'user' ? 72 : 85
            },
            pose_sequence: this.generateSamplePoseSequence()
        };
    }
    
    generateSamplePoseSequence() {
        // Generate 300 frames of sample pose data
        const frames = [];
        for (let i = 0; i < 300; i++) {
            const frame = {
                frame: i,
                landmarks: {}
            };
            
            // Generate 33 MediaPipe landmarks
            for (let j = 0; j < 33; j++) {
                frame.landmarks[j] = {
                    x: 0.5 + Math.sin(i * 0.05 + j) * 0.2,
                    y: 0.3 + Math.cos(i * 0.05 + j) * 0.1,
                    z: 0.1 + Math.sin(i * 0.03 + j) * 0.05,
                    visibility: 0.95 + Math.random() * 0.05
                };
            }
            
            frames.push(frame);
        }
        return frames;
    }
    
    populateProSelector() {
        const selector = document.getElementById('pro-selector');
        selector.innerHTML = '<option value="">Select Pro...</option>';
        
        // Group by golfer
        const golfers = {};
        this.proDatabase.forEach(pro => {
            if (!golfers[pro.golfer_name]) {
                golfers[pro.golfer_name] = [];
            }
            golfers[pro.golfer_name].push(pro);
        });
        
        // Create options
        Object.keys(golfers).forEach(name => {
            const group = document.createElement('optgroup');
            group.label = name;
            
            golfers[name].forEach(pro => {
                const option = document.createElement('option');
                option.value = pro.pro_id;
                option.textContent = `${name} - ${pro.club_type}`;
                group.appendChild(option);
            });
            
            selector.appendChild(group);
        });
        
        // Auto-select first pro
        if (this.proDatabase.length > 0) {
            selector.value = this.proDatabase[0].pro_id;
            this.loadProData(this.proDatabase[0].pro_id);
        }
    }
    
    loadProData(proId) {
        const proData = this.proDatabase.find(p => p.pro_id === proId);
        if (proData) {
            this.currentProData = proData;
            this.updateProRenderer();
            this.updateMetricsDisplay();
        }
    }
    
    changeClub(club) {
        // Filter pros by club type and update selector
        console.log(`Changing to ${club}`);
        // Implementation would filter the pro list
    }
    
    updateUserRenderer() {
        if (this.skeletonRenderers.user && this.userSwingData) {
            this.skeletonRenderers.user.loadSwingData(this.userSwingData);
        }
    }
    
    updateProRenderer() {
        if (this.skeletonRenderers.pro && this.currentProData) {
            this.skeletonRenderers.pro.loadSwingData(this.currentProData);
        }
    }
    
    updateMetricsDisplay() {
        if (this.userSwingData && this.currentProData) {
            window.dispatchEvent(new CustomEvent('metricsUpdate', {
                detail: {
                    userMetrics: this.userSwingData.metrics,
                    proMetrics: this.currentProData.metrics
                }
            }));
        } else if (this.userSwingData) {
            // Load sample metrics for demonstration
            this.metricsDisplay.loadSampleData();
        }
    }
    
    updateFrame(frame) {
        // Update renderers with current frame
        if (this.skeletonRenderers.user) {
            this.skeletonRenderers.user.setFrame(frame);
        }
        if (this.skeletonRenderers.pro) {
            this.skeletonRenderers.pro.setFrame(frame);
        }
    }
    
    changeView(panelId, view) {
        const renderer = panelId === 'user-viewer' ? 
            this.skeletonRenderers.user : this.skeletonRenderers.pro;
            
        if (renderer) {
            renderer.changeView(view);
        }
    }
    
    toggleOverlayMode() {
        this.isOverlayMode = !this.isOverlayMode;
        
        if (this.isOverlayMode) {
            // Switch to overlay mode
            document.querySelector('.viewer-container').classList.add('overlay-mode');
            this.mergeRenderers();
        } else {
            // Switch back to side-by-side
            document.querySelector('.viewer-container').classList.remove('overlay-mode');
            this.separateRenderers();
        }
    }
    
    mergeRenderers() {
        // Combine both skeletons in one view
        console.log('Switching to overlay mode');
        // Implementation would merge the two Three.js scenes
    }
    
    separateRenderers() {
        // Separate skeletons back to individual views
        console.log('Switching to side-by-side mode');
        // Implementation would separate the Three.js scenes
    }
    
    async handleExport(format) {
        console.log(`Exporting as ${format}`);
        
        const exportData = {
            format: format,
            userSwing: this.userSwingData,
            proSwing: this.currentProData,
            timestamp: new Date().toISOString()
        };
        
        try {
            const response = await fetch(`${this.serverUrl}/api/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(exportData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.downloadExport(result.url, format);
            }
        } catch (error) {
            console.error('Export error:', error);
            // Fallback to client-side export
            this.clientSideExport(format);
        }
    }
    
    clientSideExport(format) {
        // Handle export on client side if server unavailable
        if (format === 'html') {
            this.exportAsHTML();
        } else if (format === 'pdf') {
            console.log('PDF export requires server');
        } else if (format === 'mp4') {
            console.log('Video export requires server');
        }
    }
    
    exportAsHTML() {
        // Create standalone HTML file with embedded data
        const htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>ProMirrorGolf Analysis - ${new Date().toLocaleDateString()}</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        background: #0A0A0A; 
                        color: #E0E0E0; 
                        padding: 20px;
                    }
                    h1 { color: #FF4444; }
                    .metrics { 
                        display: grid; 
                        grid-template-columns: repeat(3, 1fr); 
                        gap: 20px; 
                        margin: 20px 0;
                    }
                    .metric {
                        background: #141414;
                        padding: 15px;
                        border-radius: 8px;
                        border: 1px solid #2A2A2A;
                    }
                    .metric-label { font-size: 12px; color: #888; }
                    .metric-value { font-size: 24px; font-weight: bold; }
                </style>
            </head>
            <body>
                <h1>ProMirrorGolf Swing Analysis</h1>
                <p>Date: ${new Date().toLocaleDateString()}</p>
                <p>Comparing to: ${this.currentProData?.golfer_name || 'Pro'}</p>
                
                <div class="metrics">
                    ${this.generateMetricsHTML()}
                </div>
                
                <script>
                    const swingData = ${JSON.stringify({
                        user: this.userSwingData,
                        pro: this.currentProData
                    })};
                    console.log('Swing data embedded:', swingData);
                </script>
            </body>
            </html>
        `;
        
        this.downloadFile(htmlContent, 'swing-analysis.html', 'text/html');
    }
    
    generateMetricsHTML() {
        if (!this.userSwingData) return '';
        
        const metrics = this.userSwingData.metrics;
        return Object.keys(metrics).map(key => `
            <div class="metric">
                <div class="metric-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
                <div class="metric-value">${metrics[key].toFixed(1)}</div>
            </div>
        `).join('');
    }
    
    downloadFile(content, filename, type) {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    downloadExport(url, format) {
        // Download file from server
        const a = document.createElement('a');
        a.href = url;
        a.download = `swing-analysis.${format}`;
        a.click();
    }
    
    handleResize() {
        // Update renderer sizes
        if (this.skeletonRenderers.user) {
            this.skeletonRenderers.user.resize();
        }
        if (this.skeletonRenderers.pro) {
            this.skeletonRenderers.pro.resize();
        }
    }
    
    startSwingPolling() {
        // Poll for new swings every 5 seconds
        setInterval(async () => {
            const hasNewSwing = await this.checkForNewSwing();
            if (hasNewSwing) {
                await this.loadUserSwing();
                this.updateMetricsDisplay();
                
                // Show notification
                this.showNewSwingNotification();
            }
        }, 5000);
    }
    
    showNewSwingNotification() {
        const notification = document.createElement('div');
        notification.className = 'swing-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-red);
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        `;
        notification.textContent = 'New swing detected and loaded!';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    loadSampleData() {
        // Load complete sample data for testing
        console.log('Loading sample data for demonstration');
        
        this.userSwingData = this.generateSampleSwingData('user');
        this.proDatabase = this.generateSampleProDatabase();
        
        this.populateProSelector();
        this.updateUserRenderer();
        
        if (this.proDatabase.length > 0) {
            this.currentProData = this.proDatabase[0];
            this.updateProRenderer();
        }
        
        this.metricsDisplay.loadSampleData();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProMirrorGolfApp();
});

// Add slide animations
const animationStyles = document.createElement('style');
animationStyles.textContent = `
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
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .overlay-mode .viewer-panel:first-child {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 1;
        opacity: 0.5;
    }
    
    .overlay-mode .viewer-panel:last-child {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 2;
    }
`;
document.head.appendChild(animationStyles);

console.log('ProMirrorGolf v1.0.0 - Ready');