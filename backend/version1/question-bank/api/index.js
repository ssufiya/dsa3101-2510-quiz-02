import express from "express";
import multer from "multer";
import fs from "fs";
import path from "path";

const app = express();
const upload = multer();
app.use(express.json());

const storageDir = path.join(process.cwd(), "storage");
if (!fs.existsSync(storageDir)) fs.mkdirSync(storageDir, { recursive: true });

const indexPath = path.join(storageDir, "index.json");
function readIndex() {
  return fs.existsSync(indexPath) ? JSON.parse(fs.readFileSync(indexPath, "utf8")) : [];
}
function writeIndex(items) {
  fs.writeFileSync(indexPath, JSON.stringify(items, null, 2));
}

app.get("/health", (_req, res) => res.json({ ok: true }));

// Upload → save file and create DRAFT record (status: 'needs_review')
app.post("/upload", upload.single("file"), (req, res) => {
  if (!req.file) return res.status(400).json({ ok:false, error:"missing file" });

  const course = String(req.body.course_code || "ST1131");
  const now = Date.now();
  const outPath = path.join(storageDir, `${now}_${req.file.originalname}`);
  fs.writeFileSync(outPath, req.file.buffer);

  const items = readIndex();
  items.unshift({
    id: now,
    filename: req.file.originalname,
    course_code: course,
    stored_path: outPath,
    status: "needs_review",              // <— NEW
    created_at: new Date().toISOString()
  });
  writeIndex(items);

  res.json({ ok:true, id: now, stored_path: outPath, status: "needs_review" });
});

// Review queue: list drafts
app.get("/review/list", (_req, res) => {
  const items = readIndex().filter(x => x.status === "needs_review");
  res.json({ items });
});

// Publish a draft (simple: change status)
app.post("/review/publish", (req, res) => {
  const id = Number(req.body?.id ?? req.query?.id);
  if (!id) return res.status(400).json({ ok:false, error:"missing id" });
  const items = readIndex();
  const it = items.find(x => x.id === id);
  if (!it) return res.status(404).json({ ok:false, error:"not found" });
  it.status = "published";
  writeIndex(items);
  res.json({ ok:true, id, status:"published" });
});

// Instructor view: only published items
app.get("/questions/published", (_req, res) => {
  const items = readIndex().filter(x => x.status === "published");
  res.json({ items });
});

// Legacy endpoint: show everything (for debugging)
app.get("/questions/search", (_req, res) => {
  res.json({ items: readIndex() });
});

const PORT = 3000;
app.listen(PORT, () => console.log(`API on http://localhost:${PORT}`));
