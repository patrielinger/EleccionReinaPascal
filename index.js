const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname)));

// Crear carpetas si no existen
const candidatasDir = path.join(__dirname, 'candidatas');
const imgDir = path.join(candidatasDir, 'img');
if (!fs.existsSync(candidatasDir)) fs.mkdirSync(candidatasDir);
if (!fs.existsSync(imgDir)) fs.mkdirSync(imgDir);

// Configurar multer para subir imágenes
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, imgDir);
  },
  filename: (req, file, cb) => {
    const numero = req.body.numero;
    const ext = path.extname(file.originalname);
    cb(null, `${numero}${ext}`);
  }
});
const upload = multer({ storage });

// Archivos de datos
const candidatasFile = path.join(candidatasDir, 'candidatas.json');
const usuariosFile = path.join(candidatasDir, 'usuarios.json');
const votosFile = path.join(candidatasDir, 'votos.json');

// Funciones para cargar/guardar datos
function loadData(file, defaultValue = {}) {
  if (fs.existsSync(file)) {
    return JSON.parse(fs.readFileSync(file));
  }
  return defaultValue;
}

function saveData(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
}

// Cargar datos iniciales
let candidatas = loadData(candidatasFile, []);
let usuarios = loadData(usuariosFile, [{ username: 'admin', password: 'admin', role: 'admin' }]);
let votos = loadData(votosFile, {});

// Rutas
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = usuarios.find(u => u.username === username && u.password === password);
  if (user) {
    res.json({ success: true, role: user.role });
  } else {
    res.json({ success: false });
  }
});

app.get('/candidatas', (req, res) => {
  res.json(candidatas);
});

app.get('/ranking', (req, res) => {
  const ranking = { reina: {}, princesa: {}, dama: {} };
  for (const userVotes of Object.values(votos)) {
    for (const [candId, cat] of Object.entries(userVotes)) {
      if (!ranking[cat][candId]) ranking[cat][candId] = 0;
      ranking[cat][candId]++;
    }
  }
  res.json(ranking);
});

app.post('/votar', (req, res) => {
  const { id, categoria } = req.body;
  const username = req.body.username; // Asumir que se envía
  if (!votos[username]) votos[username] = {};
  votos[username][id] = categoria;
  saveData(votosFile, votos);
  res.json({ success: true });
});

app.post('/agregar-candidata', upload.single('foto'), (req, res) => {
  const { nombre, ano, descripcion, cancion, numero } = req.body;
  const candidata = { id: Date.now(), nombre, ano, descripcion, cancion, numero };
  candidatas.push(candidata);
  saveData(candidatasFile, candidatas);
  res.json({ success: true });
});

app.delete('/eliminar-candidata/:id', (req, res) => {
  const id = req.params.id;
  candidatas = candidatas.filter(c => c.id != id);
  // Limpiar votos
  for (const user in votos) {
    delete votos[user][id];
  }
  saveData(candidatasFile, candidatas);
  saveData(votosFile, votos);
  // Eliminar imagen si existe
  const files = fs.readdirSync(imgDir);
  const imgFile = files.find(f => f.startsWith(`${candidatas.find(c => c.id == id)?.numero || id}.`));
  if (imgFile) {
    fs.unlinkSync(path.join(imgDir, imgFile));
  }
  res.json({ success: true });
});

app.post('/agregar-usuario', (req, res) => {
  const { username, password } = req.body;
  usuarios.push({ username, password, role: 'user' });
  saveData(usuariosFile, usuarios);
  res.json({ success: true });
});

app.delete('/eliminar-usuario/:username', (req, res) => {
  const username = req.params.username;
  usuarios = usuarios.filter(u => u.username !== username);
  delete votos[username];
  saveData(usuariosFile, usuarios);
  saveData(votosFile, votos);
  res.json({ success: true });
});

app.get('/votos-usuario', (req, res) => {
    const username = req.query.username;
    const userVotes = votos[username] || {};
    res.json(userVotes);
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});