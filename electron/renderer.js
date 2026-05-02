import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm'

// ── Сцена ──────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
renderer.setSize(400, 700)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.setClearColor(0x000000, 0)
document.body.prepend(renderer.domElement)

const scene = new THREE.Scene()
const camera = new THREE.PerspectiveCamera(30, 400 / 700, 0.1, 20)
camera.position.set(0, 0.8, 3.5)

const light = new THREE.DirectionalLight(0xffffff, 1.2)
light.position.set(1, 2, 2)
scene.add(light)
scene.add(new THREE.AmbientLight(0xffffff, 0.6))

// ── Завантаження VRM ───────────────────────────────────────────
let vrm = null
const loader = new GLTFLoader()
loader.register(parser => new VRMLoaderPlugin(parser))

loader.load('Mahiru_Angel.vrm', gltf => {
  vrm = gltf.userData.vrm
  VRMUtils.rotateVRM0(vrm)
  scene.add(vrm.scene)
  vrm.scene.position.set(0, -1.2, 0)

  const leftArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm')
  const rightArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm')
  if (leftArm) leftArm.rotation.z = -1.2
  if (rightArm) rightArm.rotation.z = 1.2

  console.log('leftArm:', leftArm)
  console.log('rightArm:', rightArm)
  console.log('VRM завантажено!')
})

// ── Емоції → blendshapes ───────────────────────────────────────
const EMOTION_MAP = {
  happy:     { happy: 1.0 },
  sad:       { sad: 1.0 },
  angry:     { angry: 1.0 },
  surprised: { surprised: 1.0 },
  relaxed:   { relaxed: 1.0 },
  neutral:   {},
}

function setEmotion(emotion) {
  if (!vrm?.expressionManager) return
  for (const name of ['happy','sad','angry','surprised','relaxed']) {
    vrm.expressionManager.setValue(name, 0)
  }
  const weights = EMOTION_MAP[emotion] || {}
  for (const [name, val] of Object.entries(weights)) {
    vrm.expressionManager.setValue(name, val)
  }
}

// ── Lip sync ──────────────────────────────────────────────────
let isSpeaking = false
let lipValue = 0

// ── WebSocket ──────────────────────────────────────────────────
const subtitle = document.getElementById('subtitle')
let subtitleTimer = null

function showSubtitle(text) {
  subtitle.textContent = text
  subtitle.classList.add('visible')
  clearTimeout(subtitleTimer)
  subtitleTimer = setTimeout(() => {
    subtitle.classList.remove('visible')
    setEmotion('neutral')  // ← додай цей рядок
  }, 4000)
}

const ws = new WebSocket('ws://localhost:8765')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'response') {
    setEmotion(data.emotion)
    showSubtitle(data.text)
  }
  if (data.type === 'state') {
    isSpeaking = data.value === 'speaking'
    if (data.value === 'idle') {
      lipValue = 0
      vrm?.expressionManager?.setValue('aa', 0)
    }
  }
}

ws.onopen = () => console.log('WebSocket підключено')
ws.onerror = () => console.log('WebSocket помилка — запусти python main.py')

// ── Анімація ───────────────────────────────────────────────────
const clock = new THREE.Clock()

function animate() {
  requestAnimationFrame(animate)
  const delta = clock.getDelta()
  const t = clock.getElapsedTime()

  if (vrm) {
    // Дихання
    vrm.scene.position.y = -1.2 + Math.sin(t * 1.2) * 0.005

    // Легке похитування рук
    const leftArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm')
    const rightArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm')
    if (leftArm) leftArm.rotation.z = -1.2 + Math.sin(t * 0.8) * 0.03
    if (rightArm) rightArm.rotation.z = 1.2 - Math.sin(t * 0.8) * 0.03

    // Lip sync
    if (isSpeaking) {
      lipValue = 0.4 + Math.sin(t * 12) * 0.35
      vrm.expressionManager?.setValue('aa', Math.max(0, lipValue))
    }

    // Моргання
    const blinkCycle = t % 4
    const blinkVal = blinkCycle < 0.1 ? blinkCycle / 0.1
                   : blinkCycle < 0.2 ? 1 - (blinkCycle - 0.1) / 0.1
                   : 0
    vrm.expressionManager?.setValue('blink', blinkVal)

    vrm.update(delta)
  }

  renderer.render(scene, camera)
}

animate()