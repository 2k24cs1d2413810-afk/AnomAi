const express = require("express");
const cors = require("cors");
const path = require("path");
const mongoose = require("mongoose");

const authRoutes = require("./routes/auth.routes");
const analysisRoutes = require("./routes/analysis");
const historyRoutes = require("./routes/history.routes");
const healthRoutes = require("./routes/health.routes");
const notFoundMiddleware = require("./middleware/notFound.middleware");
const errorMiddleware = require("./middleware/error.middleware");

const app = express();
const frontendPath = path.join(__dirname, "..", "frontend");

app.disable("x-powered-by");
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true, limit: "2mb" }));

app.get("/api/status", (_req, res) => {
    res.json({
        success: true,
        database: mongoose.connection.readyState === 1 ? "connected" : "disconnected"
    });
});

app.use("/api/health", healthRoutes);
app.use("/api/auth", authRoutes);
app.use("/api", analysisRoutes);
app.use("/api", historyRoutes);

app.use(express.static(frontendPath));

app.get("/anomai", (_req, res) => {
    res.sendFile(path.join(frontendPath, "index.html"));
});

app.get("/anomai/:userId/history", (_req, res) => {
    res.sendFile(path.join(frontendPath, "index.html"));
});

app.use(notFoundMiddleware);
app.use(errorMiddleware);

module.exports = app;
