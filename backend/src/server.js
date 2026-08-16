const express = require("express");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    service: "prgi-backend",
  });
});

app.post("/api/verify", async (req, res) => {
  const { title, language, periodicity } = req.body;

  if (!title || !language || !periodicity) {
    return res.status(400).json({
      error: "title, language and periodicity are required",
    });
  }

  // Temporary response.
  // This will be replaced with PostgreSQL + FastAPI.
  res.json({
    status: "LIKELY_REJECTED",
    verification_score: 18,
    violations: [
      {
        type: "SIMILARITY",
        message: "High similarity with an existing registered title.",
      },
    ],
    matches: [
      {
        title: "The Indian Express",
        score: 91,
        match_types: ["FUZZY", "PHONETIC"],
        language: "English",
        periodicity: "Daily",
      },
    ],
    explanation:
      "The proposed title has high lexical and phonetic similarity with an existing registered title.",
  });
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});