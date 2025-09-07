// question-bank/api/index.js
import express from "express";
import multer from "multer";
import fs from "fs";
import path from "path";

const app = express();
const upload = multer();

// where raw files are saved (gitignored later)
const storageDir = path.join(process.cwd(), "storage");
if (!fs.existsSync(storageDir)) fs.mkdirSync(storageDir, { recursive: true });

app.get("/health", (_req, res) => res.json({ ok: true }));

// POST /upload → save file to ./storage and log it in index.json
app.post("/upload", upload.single("file"), (req, res) => {
  if (!req.file) return res.status(400).json({ ok:false, error:"missing file" });

  const course = String(req.body.course_code || "ST1131");
  const now = Date.now();
  const outPath = path.join(storageDir, `${now}_${req.file.originalname}`);
  fs.writeFileSync(outPath, req.file.buffer);

  const indexPath = path.join(storageDir, "index.json");
  const index = fs.existsSync(indexPath) ? JSON.parse(fs.readFileSync(indexPath, "utf8")) : [];
  index.unshift({ id: now, filename: req.file.originalname, course_code: course, stored_path: outPath, created_at: new Date().toISOString() });
  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2));

  res.json({ ok:true, id: now, stored_path: outPath });
});

// GET /questions/search → list latest uploads (simple MVP)
app.get("/questions/search", (_req, res) => {
  const indexPath = path.join(storageDir, "index.json");
  const items = fs.existsSync(indexPath) ? JSON.parse(fs.readFileSync(indexPath, "utf8")) : [];
  res.json({ items });
});

const PORT = 3000;
app.listen(PORT, () => console.log(`API on http://localhost:${PORT}`));
