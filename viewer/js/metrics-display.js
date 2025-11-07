// ProMirrorGolf - Metrics Display Handler

class MetricsDisplay {
    constructor() {
        this.userMetrics = null;
        this.proMetrics = null;
        this.recommendations = [];
        
        // Ideal ranges for each metric
        this.idealRanges = {
            hip_rotation: { min: 40, max: 50, unit: '°' },
            shoulder_rotation: { min: 85, max: 105, unit: '°' },
            x_factor: { min: 40, max: 55, unit: '°' },
            spine_angle_address: { min: 28, max: 38, unit: '°' },
            spine_angle_change: { min: -3, max: 3, unit: '°' },
            tempo_ratio: { min: 2.7, max: 3.3, unit: ':1' },
            weight_shift: { min: 60, max: 85, unit: '%' }
        };
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        this.metricsGrid = document.querySelector('.metrics-grid');
        this.recommendationsList = document.querySelector('.recommendation-list');
    }
    
    attachEventListeners() {
        // Listen for metric updates
        window.addEventListener('metricsUpdate', (e) => {
            this.updateMetrics(e.detail.userMetrics, e.detail.proMetrics);
        });
        
        // Listen for frame updates to show dynamic metrics
        window.addEventListener('frameUpdate', (e) => {
            this.updateDynamicMetrics(e.detail.frame);
        });
    }
    
    updateMetrics(userMetrics, proMetrics) {
        this.userMetrics = userMetrics;
        this.proMetrics = proMetrics;
        
        // Clear existing metrics
        this.metricsGrid.innerHTML = '';
        
        // Create metric cards for each measurement
        const metrics = [
            { key: 'hip_rotation', label: 'Hip Rotation' },
            { key: 'shoulder_rotation', label: 'Shoulder Rotation' },
            { key: 'x_factor', label: 'X-Factor' },
            { key: 'spine_angle_address', label: 'Spine Angle' },
            { key: 'tempo_ratio', label: 'Tempo Ratio' },
            { key: 'weight_shift', label: 'Weight Shift' }
        ];
        
        metrics.forEach(metric => {
            const card = this.createMetricCard(
                metric.key,
                metric.label,
                userMetrics[metric.key],
                proMetrics[metric.key]
            );
            this.metricsGrid.appendChild(card);
        });
        
        // Generate recommendations
        this.generateRecommendations();
        this.displayRecommendations();
    }
    
    createMetricCard(key, label, userValue, proValue) {
        const card = document.createElement('div');
        card.className = 'metric-card';
        
        const range = this.idealRanges[key];
        const status = this.getMetricStatus(userValue, range);
        const unit = range.unit;
        
        // Format values based on metric type
        let userDisplay = this.formatMetricValue(userValue, key);
        let proDisplay = this.formatMetricValue(proValue, key);
        
        // Calculate positions for visualization
        const { userPos, proPos, idealStart, idealWidth } = this.calculatePositions(
            userValue, proValue, range
        );
        
        card.innerHTML = `
            <div class="metric-header">
                <span class="metric-label">${label}</span>
                <span class="metric-status ${status.class}">${status.icon}</span>
            </div>
            <div class="metric-values">
                <span class="user-value">${userDisplay}</span>
                <span class="vs">vs</span>
                <span class="pro-value">${proDisplay}</span>
            </div>
            <div class="metric-bar">
                <div class="metric-range">
                    <div class="ideal-range" style="left: ${idealStart}%; width: ${idealWidth}%;"></div>
                    <div class="user-marker" style="left: ${userPos}%;"></div>
                    <div class="pro-marker" style="left: ${proPos}%;"></div>
                </div>
            </div>
        `;
        
        // Add tooltip on hover
        card.addEventListener('mouseenter', () => {
            this.showMetricTooltip(card, key, userValue, proValue);
        });
        
        return card;
    }
    
    formatMetricValue(value, key) {
        const range = this.idealRanges[key];
        
        if (key === 'tempo_ratio') {
            return `${value.toFixed(1)}:1`;
        } else if (key === 'weight_shift') {
            return `${Math.round(value)}%`;
        } else {
            return `${value.toFixed(1)}°`;
        }
    }
    
    getMetricStatus(value, range) {
        const tolerance = (range.max - range.min) * 0.1; // 10% tolerance
        
        if (value >= range.min && value <= range.max) {
            return { class: 'good', icon: '✓' };
        } else if (
            value >= range.min - tolerance && value <= range.max + tolerance
        ) {
            return { class: 'warning', icon: '!' };
        } else {
            return { class: 'error', icon: '✗' };
        }
    }
    
    calculatePositions(userValue, proValue, range) {
        // Expand visualization range for better display
        const vizMin = range.min - (range.max - range.min) * 0.5;
        const vizMax = range.max + (range.max - range.min) * 0.5;
        const vizRange = vizMax - vizMin;
        
        // Calculate positions as percentages
        const userPos = ((userValue - vizMin) / vizRange) * 100;
        const proPos = ((proValue - vizMin) / vizRange) * 100;
        const idealStart = ((range.min - vizMin) / vizRange) * 100;
        const idealWidth = ((range.max - range.min) / vizRange) * 100;
        
        return {
            userPos: Math.max(0, Math.min(100, userPos)),
            proPos: Math.max(0, Math.min(100, proPos)),
            idealStart: Math.max(0, idealStart),
            idealWidth: Math.min(100 - idealStart, idealWidth)
        };
    }
    
    generateRecommendations() {
        this.recommendations = [];
        
        // Analyze each metric and generate recommendations
        const metricAnalysis = [
            {
                key: 'spine_angle_address',
                label: 'Spine Angle at Address',
                importance: 3,
                getDrill: (diff) => {
                    if (diff < -5) {
                        return {
                            title: 'Increase Spine Angle at Address',
                            description: `Your spine angle is too upright. Bend more from the hips to achieve the ideal angle.`,
                            drill: 'Place a club across your hips and practice tilting forward while keeping your back straight.'
                        };
                    } else {
                        return {
                            title: 'Decrease Spine Angle at Address',
                            description: `Your spine angle is too bent over. Stand slightly more upright at address.`,
                            drill: 'Practice setting up with your back against a wall, then step forward maintaining that posture.'
                        };
                    }
                }
            },
            {
                key: 'shoulder_rotation',
                label: 'Shoulder Rotation',
                importance: 2,
                getDrill: (diff) => {
                    return {
                        title: 'Increase Shoulder Turn',
                        description: `Your shoulder rotation is limited, reducing power potential. Work on achieving a fuller turn.`,
                        drill: 'Practice backswings with your trail foot stepped back to encourage fuller rotation.'
                    };
                }
            },
            {
                key: 'weight_shift',
                label: 'Weight Transfer',
                importance: 2,
                getDrill: (diff) => {
                    return {
                        title: 'Improve Weight Transfer',
                        description: `Transfer more weight to your lead foot through impact for better power and consistency.`,
                        drill: 'Practice stepping through your swing, lifting your trail foot after impact.'
                    };
                }
            },
            {
                key: 'x_factor',
                label: 'X-Factor',
                importance: 1,
                getDrill: (diff) => {
                    return {
                        title: 'Increase X-Factor',
                        description: `Create more separation between your hips and shoulders for increased power.`,
                        drill: 'Practice the split-grip drill: hold the club with hands apart and focus on hip-shoulder separation.'
                    };
                }
            },
            {
                key: 'tempo_ratio',
                label: 'Tempo',
                importance: 1,
                getDrill: (diff) => {
                    if (diff < -0.5) {
                        return {
                            title: 'Slow Down Backswing',
                            description: `Your backswing is too quick relative to your downswing. Develop a smoother tempo.`,
                            drill: 'Count "1-2-3" on the backswing and "1" on the downswing to establish rhythm.'
                        };
                    } else {
                        return {
                            title: 'Speed Up Transition',
                            description: `Your downswing is too slow relative to your backswing. Create more acceleration.`,
                            drill: 'Practice the pump drill: make small pumping motions at the top to trigger a faster downswing.'
                        };
                    }
                }
            }
        ];
        
        // Calculate differences and sort by importance
        metricAnalysis.forEach(analysis => {
            const userValue = this.userMetrics[analysis.key];
            const proValue = this.proMetrics[analysis.key];
            const range = this.idealRanges[analysis.key];
            
            const diff = userValue - proValue;
            const status = this.getMetricStatus(userValue, range);
            
            if (status.class !== 'good') {
                this.recommendations.push({
                    ...analysis.getDrill(diff),
                    importance: analysis.importance,
                    status: status.class,
                    diff: Math.abs(diff)
                });
            }
        });
        
        // Sort by importance and difference
        this.recommendations.sort((a, b) => {
            if (a.status !== b.status) {
                return a.status === 'error' ? -1 : 1;
            }
            if (a.importance !== b.importance) {
                return b.importance - a.importance;
            }
            return b.diff - a.diff;
        });
        
        // Keep top 3 recommendations
        this.recommendations = this.recommendations.slice(0, 3);
    }
    
    displayRecommendations() {
        this.recommendationsList.innerHTML = '';
        
        this.recommendations.forEach((rec, index) => {
            const item = document.createElement('div');
            item.className = `recommendation-item ${rec.status}`;
            
            item.innerHTML = `
                <div class="rec-number">${index + 1}</div>
                <div class="rec-content">
                    <h4>${rec.title}</h4>
                    <p>${rec.description}</p>
                    <div class="drill-suggestion">
                        <strong>Drill:</strong> ${rec.drill}
                    </div>
                </div>
            `;
            
            this.recommendationsList.appendChild(item);
        });
    }
    
    updateDynamicMetrics(frame) {
        // Update metrics that change during the swing
        // This would show real-time angle changes if we had frame-by-frame data
        
        // For now, we can highlight the current swing phase
        const phase = this.getSwingPhase(frame);
        this.highlightRelevantMetrics(phase);
    }
    
    getSwingPhase(frame) {
        if (frame < 30) return 'address';
        if (frame < 120) return 'backswing';
        if (frame < 130) return 'top';
        if (frame < 210) return 'downswing';
        if (frame < 220) return 'impact';
        return 'follow';
    }
    
    highlightRelevantMetrics(phase) {
        // Highlight metrics relevant to current phase
        const phaseMetrics = {
            'address': ['spine_angle_address'],
            'backswing': ['shoulder_rotation', 'hip_rotation'],
            'top': ['x_factor', 'shoulder_rotation'],
            'downswing': ['tempo_ratio', 'weight_shift'],
            'impact': ['weight_shift', 'spine_angle_address'],
            'follow': ['weight_shift']
        };
        
        // Reset all highlights
        const cards = this.metricsGrid.querySelectorAll('.metric-card');
        cards.forEach(card => card.style.opacity = '0.6');
        
        // Highlight relevant metrics
        if (phaseMetrics[phase]) {
            // Would need to track which card corresponds to which metric
            // For demonstration, this shows the concept
        }
    }
    
    showMetricTooltip(card, key, userValue, proValue) {
        // Could implement hover tooltips with more detailed information
        // For now, the card shows all necessary information
    }
    
    // Public method to load sample data for testing
    loadSampleData() {
        const sampleUser = {
            hip_rotation: 45.2,
            shoulder_rotation: 78.5,
            x_factor: 43.1,
            spine_angle_address: 25.3,
            tempo_ratio: 3.0,
            weight_shift: 72
        };
        
        const samplePro = {
            hip_rotation: 48.3,
            shoulder_rotation: 96.2,
            x_factor: 47.9,
            spine_angle_address: 33.2,
            tempo_ratio: 3.1,
            weight_shift: 85
        };
        
        this.updateMetrics(sampleUser, samplePro);
    }
}

// Export for use in other modules
window.MetricsDisplay = MetricsDisplay;