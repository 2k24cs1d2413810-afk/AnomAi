const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const crypto = require("crypto");
const AnalysisHistory = require("../models/AnalysisHistory");
const AppError = require("../utils/AppError");
const { analyzeDataset, downloadCleanedDataset } = require("../services/ml.services");

const CLEANED_DIR = path.join(__dirname, "../storage/cleaned");
fs.mkdirSync(CLEANED_DIR, { recursive: true });

function safeFilename(name) {
    return String(name || "file").replace(/[^a-zA-Z0-9._-]/g, "_");
}

async function saveCleanedFile(result) {
    if (!result.cleaned_file?.filename) return null;

    const sourceFilename = result.cleaned_file.filename;
    const response = await downloadCleanedDataset(sourceFilename);
    const extension = path.extname(sourceFilename).toLowerCase() || ".bin";
    const storageName = `anomai_${crypto.randomUUID()}${extension}`;
    const destination = path.join(CLEANED_DIR, storageName);
    const writer = fs.createWriteStream(destination);

    await new Promise((resolve, reject) => {
        response.data.pipe(writer);
        response.data.on("error", reject);
        writer.on("finish", resolve);
        writer.on("error", reject);
    });

    return { filename: sourceFilename, storageName, format: result.cleaned_file.format };
}

async function uploadAndAnalyze(req, res) {
    if (!req.file) throw new AppError("No dataset file was uploaded.", 400, "FILE_REQUIRED");

    const startedAt = Date.now();
    try {
        const result = await analyzeDataset(req.file);
        const savedFile = await saveCleanedFile(result);

        if (result.cleaned_file && savedFile) {
            result.cleaned_file = {
                ...result.cleaned_file,
                download_url: `/api/download/${encodeURIComponent(savedFile.storageName)}`
            };
        }

        const history = await AnalysisHistory.create({
            user: req.user._id,
            originalFilename: req.file.originalname,
            format: result.api?.input_format || path.extname(req.file.originalname).replace(".", ""),
            dataset: {
                originalRows: result.dataset?.original_rows,
                cleanedRows: result.dataset?.cleaned_rows,
                originalColumns: result.dataset?.original_columns,
                cleanedColumns: result.dataset?.cleaned_columns,
                changesApplied: result.dataset?.changes_applied
            },
            profile: result.profile,
            statistics: result.statistics,
            anomalies: result.anomalies,
            quality: result.quality,
            remidiation: result.remidiation,
            cleanedFile: savedFile || undefined,
            processing: { status: "completed", durationMs: Date.now() - startedAt }
        });

        result.history = {
            id: history._id.toString(),
            createdAt: history.createdAt
        };

        res.status(200).json(result);
    } catch (error) {
        throw error;
    } finally {
        if (req.file?.path) {
            await fsp.rm(req.file.path, { force: true }).catch(() => {});
        }
    }
}

async function downloadHistoryFile(req, res) {
    const filename = safeFilename(req.params.filename);
    if (!filename.startsWith("anomai_")) throw new AppError("Invalid cleaned dataset filename.", 400, "INVALID_FILENAME");

    const filePath = path.join(CLEANED_DIR, filename);
    const resolvedDir = path.resolve(CLEANED_DIR);
    const resolvedFile = path.resolve(filePath);
    if (!resolvedFile.startsWith(resolvedDir + path.sep)) throw new AppError("Invalid file path.", 400, "INVALID_PATH");

    if (!fs.existsSync(resolvedFile)) throw new AppError("Cleaned dataset file not found.", 404, "CLEANED_FILE_NOT_FOUND");
    res.download(resolvedFile, safeFilename(filename));
}

module.exports = { uploadAndAnalyze, downloadHistoryFile };
