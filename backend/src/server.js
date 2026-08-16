require("dotenv").config();
const express = require("express");
const cors = require("cors");
const pool = require("./db");

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Health check
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    service: "prgi-backend",
  });
});

// Database connection test
app.get("/api/db-test", async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT COUNT(*) FROM public.prgi_titles"
    );

    res.json({
      connected: true,
      records: Number(result.rows[0].count),
    });
  } catch (error) {
    console.error("Database connection failed:", error);

    res.status(500).json({
      connected: false,
      error: error.message,
    });
  }
});

// Verify title
app.post("/api/verify", async (req, res) => {
  const { title, language, periodicity } = req.body;

  if (!title || !language || !periodicity) {
    return res.status(400).json({
      error: "title, language and periodicity are required",
    });
  }

  try {
    const result = await pool.query(
      `
      SELECT
        id,
        title,
        registration_number,
        language,
        periodicity,
        publisher,
        owner,
        publication_state,
        publication_district
      FROM public.prgi_titles
      WHERE language = $1
      ORDER BY id
      LIMIT 100
      `,
      [language]
    );

    res.json({
      status: "CANDIDATES_FOUND",
      proposed_title: title,
      candidates_found: result.rows.length,
      matches: result.rows,
    });
  } catch (error) {
    console.error("Verification database query failed:", error);

    res.status(500).json({
      error: "Failed to query PRGI database",
    });
  }
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});