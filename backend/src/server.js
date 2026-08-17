require("dotenv").config();
const express = require("express");
const cors = require("cors");
const crypto = require("crypto");
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
 const {
  title,
  language,
  periodicity,
  application_number,
} = req.body;

  if (!title || !language || !periodicity) {
    return res.status(400).json({
      error: "title, language and periodicity are required",
    });
  }
const currentApplicationNumber =
  application_number || `APP-${crypto.randomUUID()}`;
  try {
    const response = await fetch(`${process.env.AI_SERVICE_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
  title,
  language,
  periodicity,
  application_number: currentApplicationNumber,
}),
    });

    if (!response.ok) {
      const errorText = await response.text();

      console.error("AI service returned an error:", errorText);

      return res.status(502).json({
        error: "AI verification service failed",
      });
    }

    const result = await response.json();

    res.json({
  ...result,
  submitted_title: title,
  application_number: currentApplicationNumber,
});
  } catch (error) {
    console.error("Failed to connect to AI service:", error);

    res.status(502).json({
      error: "Unable to connect to AI verification service",
    });
  }
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});