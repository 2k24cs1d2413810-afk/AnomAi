const express = require("express");
const mongoose = require("mongoose");
const { healthCheck } = require("../services/ml.services");

const router = express.Router();

router.get("/", async (_req, res) => {
    const ml = await healthCheck();
    const mongo = mongoose.connection.readyState === 1;
    const healthy = mongo && ml.status === "healthy";
    res.status(healthy ? 200 : 503).json({
        success: healthy,
        service: "AnomAI Backend",
        database: mongo ? "connected" : "disconnected",
        mlService: ml.status,
        timestamp: new Date().toISOString()
    });
});

module.exports = router;
