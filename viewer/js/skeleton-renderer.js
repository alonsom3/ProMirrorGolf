// Three.js skeleton renderer
javascript
class SkeletonRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        
        this.joints = [];
        this.bones = [];
        
        this.init();
    }
    
    init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setClearColor(0x0f0f0f, 1);
        this.container.appendChild(this.renderer.domElement);
        
        this.camera.position.z = 5;
        
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(5, 10, 5);
        this.scene.add(directionalLight);
        
        this.addGroundPlane();
        
        this.animate();
    }
    
    addGroundPlane() {
        const geometry = new THREE.PlaneGeometry(10, 10);
        const material = new THREE.MeshBasicMaterial({ 
            color: 0x1a1a1a, 
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.3
        });
        const plane = new THREE.Mesh(geometry, material);
        plane.rotation.x = Math.PI / 2;
        plane.position.y = -2;
        this.scene.add(plane);
    }
    
    loadPoseData(poseData, color = 0xff4444) {
        this.clearSkeleton();
        
        const landmarks = poseData.landmarks;
        
        for (let i = 0; i < 33; i++) {
            if (landmarks[i]) {
                const joint = this.createJoint(
                    landmarks[i].x * 5 - 2.5,
                    -landmarks[i].y * 5 + 2.5,
                    landmarks[i].z * 2,
                    color
                );
                this.joints.push(joint);
                this.scene.add(joint);
            }
        }
        
        this.createBones(landmarks, color);
    }
    
    createJoint(x, y, z, color) {
        const geometry = new THREE.SphereGeometry(0.05, 16, 16);
        const material = new THREE.MeshStandardMaterial({ 
            color: color,
            emissive: color,
            emissiveIntensity: 0.3
        });
        const sphere = new THREE.Mesh(geometry, material);
        sphere.position.set(x, y, z);
        return sphere;
    }
    
    createBones(landmarks, color) {
        const connections = [
            [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
            [11, 23], [12, 24], [23, 24], [23, 25], [25, 27],
            [24, 26], [26, 28]
        ];
        
        connections.forEach(([start, end]) => {
            if (landmarks[start] && landmarks[end]) {
                const bone = this.createBone(
                    landmarks[start],
                    landmarks[end],
                    color
                );
                this.bones.push(bone);
                this.scene.add(bone);
            }
        });
    }
    
    createBone(start, end, color) {
        const startVec = new THREE.Vector3(
            start.x * 5 - 2.5,
            -start.y * 5 + 2.5,
            start.z * 2
        );
        const endVec = new THREE.Vector3(
            end.x * 5 - 2.5,
            -end.y * 5 + 2.5,
            end.z * 2
        );
        
        const direction = new THREE.Vector3().subVectors(endVec, startVec);
        const length = direction.length();
        
        const geometry = new THREE.CylinderGeometry(0.02, 0.02, length, 8);
        const material = new THREE.MeshStandardMaterial({ color: 0x3a3a3a });
        const cylinder = new THREE.Mesh(geometry, material);
        
        cylinder.position.copy(startVec).add(direction.multiplyScalar(0.5));
        cylinder.quaternion.setFromUnitVectors(
            new THREE.Vector3(0, 1, 0),
            direction.normalize()
        );
        
        return cylinder;
    }
    
    clearSkeleton() {
        this.joints.forEach(joint => this.scene.remove(joint));
        this.bones.forEach(bone => this.scene.remove(bone));
        this.joints = [];
        this.bones = [];
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }
    
    resize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
}