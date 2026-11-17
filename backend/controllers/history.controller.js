const mongoose = require("mongoose");
const AnalysisHistory = require("../models/AnalysisHistory");
const AppError = require("../utils/AppError");

function ensureOwner(req) {
    const requestedId = String(req.params.userId || "");
    if (!mongoose.isValidObjectId(requestedId) || requestedId !== req.user._id.toString()) {
        throw new AppError("You can only access your own analysis history.", 403, "HISTORY_ACCESS_DENIED");
    }
    return requestedId;
}

async function listHistory(req, res) {
    const userId = ensureOwner(req);
    const limit = Math.min(Math.max(Number(req.query.limit) || 20, 1), 100);
    const records = await AnalysisHistory.find({ user: userId })
        .sort({ createdAt: -1 })
        .limit(limit)
        .select("originalFilename format dataset quality remidiation.cleanedFile cleanedFile processing createdAt")
        .lean();

    res.json({ success: true, userId, count: records.length, history: records });
}

async function getHistoryItem(req, res) {
    const userId = ensureOwner(req);
    if (!mongoose.isValidObjectId(req.params.historyId)) {
        throw new AppError("Invalid history ID.", 400, "INVALID_HISTORY_ID");
    }

    const record = await AnalysisHistory.findOne({ _id: req.params.historyId, user: userId }).lean();
    if (!record) throw new AppError("Analysis history record not found.", 404, "HISTORY_NOT_FOUND");

    res.json({ success: true, history: record });
}

module.exports = { listHistory, getHistoryItem };
