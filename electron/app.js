const THREE = window.THREE || require('three')
const { GLTFLoader } = THREE
const { VRMLoaderPlugin, VRMUtils } = window.THREE_VRM || THREEVRM

// ── Сцена ──────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(400, 700)
renderer.setClearColor(0x000000, 0)
document.body.prepend(renderer.domElement)

const scene = new THREE.Scene()
const camera = new THREE.PerspectiveCamera(30, 400 / 700, 0.1, 20)
camera.position.set(0, 1.4, 3.5)
scene.add(new THREE.DirectionalLight(0xffffff, 1.2))
scene.add(new THREE.AmbientLight(0xffffff, 0.6))

// ── VRM ────────────────────────────────────────────
let vrm = null
const loader = new THREE.GLTFLoader ? new THREE.GLTFLoader() : null

// Перевір що є в консолі
console.log('THREE:', Object.keys(THREE).slice(0, 10))
console.log('THREEVRM:', typeof THREEVRM)