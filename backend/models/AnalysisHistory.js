const mongoose = require("mongoose");

const analysisHistorySchema = new mongoose.Schema(
    {
        user: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true, index: true },
        originalFilename: { type: String, required: true },
        format: { type: String, required: true },
        dataset: {
            originalRows: Number,
            cleanedRows: Number,
            originalColumns: Number,
            cleanedColumns: Number,
            changesApplied: Number
        },
        profile: { type: mongoose.Schema.Types.Mixed, default: {} },
        statistics: { type: mongoose.Schema.Types.Mixed, default: {} },
        anomalies: { type: mongoose.Schema.Types.Mixed, default: {} },
        quality: { type: mongoose.Schema.Types.Mixed, default: {} },
        remidiation: { type: mongoose.Schema.Types.Mixed, default: {} },
        cleanedFile: {
            filename: String,
            format: String,
            storageName: String
        },
        processing: {
            status: { type: String, enum: ["completed", "failed"], default: "completed" },
            durationMs: Number
        }
    },
    { timestamps: true }
);

analysisHistorySchema.index({ user: 1, createdAt: -1 });

module.exports = mongoose.model("AnalysisHistory", analysisHistorySchema);
