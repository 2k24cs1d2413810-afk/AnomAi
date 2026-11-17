const multer = require("multer");
const path = require("path");
const fs = require("fs");
const AppError = require("../utils/AppError");

const uploadDirectory = path.join(__dirname, "../uploads");
fs.mkdirSync(uploadDirectory, { recursive: true });

const ALLOWED_EXTENSIONS = [
    ".csv", ".tsv", ".txt", ".xlsx", ".xls", ".ods",
    ".json", ".jsonl", ".ndjson", ".xml", ".parquet"
];

const MAX_FILE_SIZE = Number(process.env.MAX_UPLOAD_MB || 25) * 1024 * 1024;

const storage = multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, uploadDirectory),
    filename: (_req, file, cb) => {
        const extension = path.extname(file.originalname).toLowerCase();
        cb(null, `${Date.now()}-${Math.round(Math.random() * 1e9)}${extension}`);
    }
});

const fileFilter = (_req, file, cb) => {
    const extension = path.extname(file.originalname).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return cb(new AppError(
            `Unsupported file format. Supported formats: ${ALLOWED_EXTENSIONS.join(", ")}.`,
            415,
            "UNSUPPORTED_FILE_FORMAT"
        ));
    }
    cb(null, true);
};

module.exports = multer({
    storage,
    limits: { fileSize: MAX_FILE_SIZE, files: 1 },
    fileFilter
});
