const { app, BrowserWindow } = require('electron')
const path = require('path')

let win

app.whenReady().then(() => {
  win = new BrowserWindow({
    width: 400,
    height: 700,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  })

  win.loadFile('index.html')
  win.webContents.openDevTools({ mode: 'detach' })
  win.setIgnoreMouseEvents(false)

  // Позиція — правий нижній кут
  const { screen } = require('electron')
  const display = screen.getPrimaryDisplay()
  const { width, height } = display.workAreaSize
  win.setPosition(width - 420, height - 720)
})

app.on('window-all-closed', () => app.quit())