/**
 * NASA 3D Performance Optimizer
 * Advanced performance optimization for Three.js 3D visualizations
 */

class NASA3DPerformanceOptimizer {
    constructor() {
        this.performanceMode = 'auto';
        this.frameRate = 60;
        this.lastFrameTime = 0;
        this.frameHistory = [];
        this.adaptiveQuality = true;
        this.renderStats = {
            triangles: 0,
            drawCalls: 0,
            textures: 0,
            geometries: 0
        };
        
        this.init();
    }

    init() {
        this.detectHardwareCapabilities();
        this.setupPerformanceMonitoring();
        this.createPerformanceUI();
        
        console.log('🚀 NASA 3D Performance Optimizer initialized');
    }

    detectHardwareCapabilities() {
        // Get WebGL context to analyze capabilities
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        
        if (!gl) {
            console.warn('WebGL not supported');
            this.performanceMode = 'low';
            return;
        }

        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'Unknown';
        const vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'Unknown';
        
        // Analyze system capabilities
        const memory = navigator.deviceMemory || 4;
        const cores = navigator.hardwareConcurrency || 4;
        const maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
        const maxVertexAttribs = gl.getParameter(gl.MAX_VERTEX_ATTRIBS);
        
        // Determine performance mode
        if (memory >= 8 && cores >= 8 && maxTextureSize >= 4096) {
            this.performanceMode = 'high';
            this.targetFPS = 60;
        } else if (memory >= 4 && cores >= 4 && maxTextureSize >= 2048) {
            this.performanceMode = 'medium';
            this.targetFPS = 45;
        } else {
            this.performanceMode = 'low';
            this.targetFPS = 30;
        }
        
        console.log('🖥️ Hardware Analysis:', {
            renderer,
            vendor,
            memory: `${memory}GB`,
            cores,
            maxTextureSize,
            performanceMode: this.performanceMode,
            targetFPS: this.targetFPS
        });
        
        // Store capabilities for runtime decisions
        this.capabilities = {
            renderer,
            vendor,
            memory,
            cores,
            maxTextureSize,
            maxVertexAttribs,
            supportsWebGL2: !!canvas.getContext('webgl2'),
            supportsInstancing: !!gl.getExtension('ANGLE_instanced_arrays'),
            supportsFloatTextures: !!gl.getExtension('OES_texture_float')
        };
    }

    optimizeRenderer(renderer) {
        // Apply performance optimizations based on hardware
        switch (this.performanceMode) {
            case 'high':
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                renderer.antialias = true;
                break;
                
            case 'medium':
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.BasicShadowMap;
                renderer.antialias = false;
                break;
                
            case 'low':
                renderer.setPixelRatio(1);
                renderer.shadowMap.enabled = false;
                renderer.antialias = false;
                break;
        }
        
        // Enable optimizations
        renderer.sortObjects = true;
        renderer.outputEncoding = THREE.sRGBEncoding;
        renderer.physicallyCorrectLights = false; // Disable for performance
        
        console.log(`🎯 Renderer optimized for ${this.performanceMode} performance mode`);
        
        return renderer;
    }

    optimizeGeometry(geometry) {
        // Optimize geometry based on performance mode
        if (this.performanceMode === 'low') {
            // Reduce geometry complexity
            if (geometry.isBufferGeometry) {
                const positionAttribute = geometry.getAttribute('position');
                if (positionAttribute && positionAttribute.count > 1000) {
                    // Decimate geometry for low-end devices
                    return this.decimateGeometry(geometry, 0.5);
                }
            }
        }
        
        // Merge buffers for better performance
        if (geometry.isBufferGeometry) {
            geometry.deleteAttribute('uv2'); // Remove unnecessary UV coordinates
            geometry.deleteAttribute('tangent'); // Remove tangents if not needed
        }
        
        return geometry;
    }

    decimateGeometry(geometry, factor) {
        // Simple decimation - reduce vertex count
        const positionAttribute = geometry.getAttribute('position');
        const originalCount = positionAttribute.count;
        const newCount = Math.floor(originalCount * factor);
        
        if (newCount < originalCount) {
            const newPositions = new Float32Array(newCount * 3);
            const step = Math.floor(originalCount / newCount);
            
            for (let i = 0; i < newCount; i++) {
                const sourceIndex = i * step;
                newPositions[i * 3] = positionAttribute.getX(sourceIndex);
                newPositions[i * 3 + 1] = positionAttribute.getY(sourceIndex);
                newPositions[i * 3 + 2] = positionAttribute.getZ(sourceIndex);
            }
            
            geometry.setAttribute('position', new THREE.BufferAttribute(newPositions, 3));
            console.log(`📉 Geometry decimated: ${originalCount} → ${newCount} vertices`);
        }
        
        return geometry;
    }

    optimizeParticleSystem(particleCount, performanceMode = this.performanceMode) {
        // Adjust particle count based on performance
        const multipliers = {
            high: 1.0,
            medium: 0.7,
            low: 0.4
        };
        
        const optimizedCount = Math.floor(particleCount * multipliers[performanceMode]);
        
        console.log(`✨ Particle system optimized: ${particleCount} → ${optimizedCount} particles`);
        
        return {
            count: optimizedCount,
            useInstancing: this.capabilities.supportsInstancing && performanceMode !== 'low',
            useFloatTextures: this.capabilities.supportsFloatTextures && performanceMode === 'high'
        };
    }

    createLODSystem(objects) {
        // Level of Detail system for better performance
        const lodObjects = [];
        
        objects.forEach(obj => {
            const lod = new THREE.LOD();
            
            // High detail (close)
            lod.addLevel(obj, 0);
            
            // Medium detail (medium distance)
            if (this.performanceMode !== 'high') {
                const mediumDetail = this.createReducedDetailObject(obj, 0.6);
                lod.addLevel(mediumDetail, 50);
            }
            
            // Low detail (far distance)
            const lowDetail = this.createReducedDetailObject(obj, 0.3);
            lod.addLevel(lowDetail, 100);
            
            lodObjects.push(lod);
        });
        
        return lodObjects;
    }

    createReducedDetailObject(originalObject, reductionFactor) {
        // Create a simplified version of the object
        const reduced = originalObject.clone();
        
        if (reduced.geometry) {
            reduced.geometry = this.decimateGeometry(reduced.geometry.clone(), reductionFactor);
        }
        
        // Simplify materials
        if (reduced.material) {
            const simplifiedMaterial = reduced.material.clone();
            simplifiedMaterial.transparent = false; // Remove transparency for performance
            simplifiedMaterial.reflectivity = 0; // Remove reflections
            reduced.material = simplifiedMaterial;
        }
        
        return reduced;
    }

    setupPerformanceMonitoring() {
        let frameCount = 0;
        let lastTime = performance.now();
        
        const monitorPerformance = () => {
            const currentTime = performance.now();
            frameCount++;
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                this.updateFPS(fps);
                
                // Adaptive quality adjustment
                if (this.adaptiveQuality) {
                    this.adjustQuality(fps);
                }
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(monitorPerformance);
        };
        
        requestAnimationFrame(monitorPerformance);
    }

    updateFPS(fps) {
        this.frameRate = fps;
        this.frameHistory.push(fps);
        
        // Keep only last 60 frames
        if (this.frameHistory.length > 60) {
            this.frameHistory.shift();
        }
        
        // Update performance UI
        const fpsElement = document.getElementById('fps-counter');
        if (fpsElement) {
            fpsElement.textContent = `${fps} FPS`;
            fpsElement.className = fps >= this.targetFPS ? 'fps-good' : 
                                   fps >= this.targetFPS * 0.8 ? 'fps-ok' : 'fps-poor';
        }
    }

    adjustQuality(currentFPS) {
        // Automatically adjust quality based on performance
        const targetFPS = this.targetFPS;
        const tolerance = 5;
        
        if (currentFPS < targetFPS - tolerance && this.performanceMode !== 'low') {
            this.downgradeQuality();
        } else if (currentFPS > targetFPS + tolerance && this.performanceMode !== 'high') {
            this.upgradeQuality();
        }
    }

    downgradeQuality() {
        if (this.performanceMode === 'high') {
            this.performanceMode = 'medium';
            console.log('📉 Performance downgraded to medium');
        } else if (this.performanceMode === 'medium') {
            this.performanceMode = 'low';
            console.log('📉 Performance downgraded to low');
        }
        
        this.notifyQualityChange();
    }

    upgradeQuality() {
        if (this.performanceMode === 'low') {
            this.performanceMode = 'medium';
            console.log('📈 Performance upgraded to medium');
        } else if (this.performanceMode === 'medium') {
            this.performanceMode = 'high';
            console.log('📈 Performance upgraded to high');
        }
        
        this.notifyQualityChange();
    }

    notifyQualityChange() {
        if (window.nasaAnimationController) {
            nasaAnimationController.showNotification(
                `Quality adjusted to ${this.performanceMode} mode`,
                'info'
            );
        }
        
        // Trigger re-optimization of current scene
        this.triggerSceneOptimization();
    }

    triggerSceneOptimization() {
        // Notify 3D systems to re-optimize
        const event = new CustomEvent('nasaPerformanceUpdate', {
            detail: { performanceMode: this.performanceMode }
        });
        window.dispatchEvent(event);
    }

    createPerformanceUI() {
        const ui = document.createElement('div');
        ui.id = 'nasa-performance-ui';
        ui.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            z-index: 1000;
            display: none;
        `;
        
        ui.innerHTML = `
            <div>Performance Monitor</div>
            <div id="fps-counter" class="fps-good">60 FPS</div>
            <div>Mode: <span id="perf-mode">${this.performanceMode}</span></div>
            <div>Triangles: <span id="triangle-count">0</span></div>
            <div>Draw Calls: <span id="draw-calls">0</span></div>
        `;
        
        document.body.appendChild(ui);
        
        // Add CSS for FPS indicators
        const style = document.createElement('style');
        style.textContent = `
            .fps-good { color: #00ff00; }
            .fps-ok { color: #ffff00; }
            .fps-poor { color: #ff0000; }
        `;
        document.head.appendChild(style);
        
        // Toggle visibility with keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                ui.style.display = ui.style.display === 'none' ? 'block' : 'none';
            }
        });
    }

    updateRenderStats(renderer) {
        if (renderer.info) {
            this.renderStats = {
                triangles: renderer.info.render.triangles,
                drawCalls: renderer.info.render.calls,
                textures: renderer.info.memory.textures,
                geometries: renderer.info.memory.geometries
            };
            
            // Update UI
            const triangleElement = document.getElementById('triangle-count');
            const drawCallElement = document.getElementById('draw-calls');
            const perfModeElement = document.getElementById('perf-mode');
            
            if (triangleElement) triangleElement.textContent = this.renderStats.triangles.toLocaleString();
            if (drawCallElement) drawCallElement.textContent = this.renderStats.drawCalls;
            if (perfModeElement) perfModeElement.textContent = this.performanceMode;
        }
    }

    optimizeTextures(textureArray, maxSize = null) {
        if (!maxSize) {
            maxSize = this.performanceMode === 'high' ? 2048 : 
                     this.performanceMode === 'medium' ? 1024 : 512;
        }
        
        return textureArray.map(texture => {
            if (texture.image && (texture.image.width > maxSize || texture.image.height > maxSize)) {
                // Resize texture
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                const scale = Math.min(maxSize / texture.image.width, maxSize / texture.image.height);
                canvas.width = texture.image.width * scale;
                canvas.height = texture.image.height * scale;
                
                ctx.drawImage(texture.image, 0, 0, canvas.width, canvas.height);
                
                const optimizedTexture = texture.clone();
                optimizedTexture.image = canvas;
                optimizedTexture.needsUpdate = true;
                
                return optimizedTexture;
            }
            
            return texture;
        });
    }

    createInstancedMesh(geometry, material, count) {
        // Use instanced rendering for better performance with many similar objects
        if (!this.capabilities.supportsInstancing || this.performanceMode === 'low') {
            return null; // Fall back to regular meshes
        }
        
        const instancedMesh = new THREE.InstancedMesh(geometry, material, count);
        
        // Set up instance matrices
        const matrix = new THREE.Matrix4();
        for (let i = 0; i < count; i++) {
            matrix.setPosition(
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100
            );
            instancedMesh.setMatrixAt(i, matrix);
        }
        
        instancedMesh.instanceMatrix.needsUpdate = true;
        
        console.log(`🔄 Created instanced mesh with ${count} instances`);
        
        return instancedMesh;
    }

    enableOcclusionCulling(scene, camera) {
        // Frustum culling optimization
        const frustum = new THREE.Frustum();
        const matrix = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
        
        scene.traverse(object => {
            if (object.isMesh && object.geometry) {
                frustum.setFromProjectionMatrix(matrix);
                
                if (!object.geometry.boundingSphere) {
                    object.geometry.computeBoundingSphere();
                }
                
                object.visible = frustum.intersectsSphere(object.geometry.boundingSphere);
            }
        });
    }

    getPerformanceReport() {
        const avgFPS = this.frameHistory.reduce((a, b) => a + b, 0) / this.frameHistory.length;
        
        return {
            performanceMode: this.performanceMode,
            currentFPS: this.frameRate,
            averageFPS: Math.round(avgFPS),
            targetFPS: this.targetFPS,
            renderStats: this.renderStats,
            capabilities: this.capabilities,
            recommendations: this.getPerformanceRecommendations()
        };
    }

    getPerformanceRecommendations() {
        const recommendations = [];
        
        if (this.frameRate < this.targetFPS * 0.8) {
            recommendations.push('Consider reducing particle count');
            recommendations.push('Disable shadows for better performance');
            recommendations.push('Use lower resolution textures');
        }
        
        if (this.renderStats.drawCalls > 100) {
            recommendations.push('Merge geometries to reduce draw calls');
            recommendations.push('Use instanced rendering for repetitive objects');
        }
        
        if (this.renderStats.triangles > 100000) {
            recommendations.push('Implement LOD system');
            recommendations.push('Use geometry decimation');
        }
        
        return recommendations;
    }
}

// Initialize performance optimizer
let nasa3DPerformanceOptimizer;

document.addEventListener('DOMContentLoaded', () => {
    nasa3DPerformanceOptimizer = new NASA3DPerformanceOptimizer();
});

// Export for global access
window.NASA3DPerformanceOptimizer = NASA3DPerformanceOptimizer;