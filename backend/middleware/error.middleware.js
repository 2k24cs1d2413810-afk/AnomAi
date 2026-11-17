const multer = require("multer");
const mongoose = require("mongoose");

module.exports = function errorMiddleware(error, req, res, _next) {
    console.error(`[AnomAI ERROR] ${req.method} ${req.originalUrl}`, error);

    let status = Number(error.statusCode) || 500;
    let code = error.code || "INTERNAL_ERROR";
    let message = error.message || "An unexpected server error occurred.";
    let details = error.details || undefined;

    if (error instanceof multer.MulterError) {
        status = error.code === "LIMIT_FILE_SIZE" ? 413 : 400;
        code = `UPLOAD_${error.code}`;
        message = error.code === "LIMIT_FILE_SIZE"
            ? `File is too large. Maximum allowed size is ${process.env.MAX_UPLOAD_MB || 25} MB.`
            : "The uploaded file could not be processed.";
    }

    if (error instanceof mongoose.Error.ValidationError) {
        status = 400;
        code = "VALIDATION_ERROR";
        message = Object.values(error.errors).map(e => e.message).join(" ");
    }

    if (error.code === 11000) {
        status = 409;
        code = "DUPLICATE_RESOURCE";
        message = "A resource with the same unique value already exists.";
    }

    const body = { success: false, error: message, code };
    if (details !== undefined) body.detail = details;

    if (process.env.NODE_ENV !== "production" && error.stack) {
        body.stack = error.stack;
    }

    res.status(status).json(body);
};
