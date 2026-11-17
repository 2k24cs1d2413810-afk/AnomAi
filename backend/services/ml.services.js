const axios = require("axios");
const fs = require("fs");
const FormData = require("form-data");
const AppError = require("../utils/AppError");

const ML_SERVICE_URL = () => process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

async function analyzeDataset(file) {
    const formData = new FormData();
    const stream = fs.createReadStream(file.path);
    formData.append("dataset", stream, {
        filename: file.originalname,
        contentType: file.mimetype || "application/octet-stream"
    });

    try {
        const response = await axios.post(`${ML_SERVICE_URL()}/analyze`, formData, {
            headers: formData.getHeaders(),
            maxContentLength: Infinity,
            maxBodyLength: Infinity,
            timeout: 120000
        });
        return response.data;
    } catch (error) {
        if (error.response) {
            const detail = error.response.data?.detail || error.response.data?.error || error.response.data;
            throw new AppError(
                error.response.data?.error || "Dataset analysis failed in the ML service.",
                error.response.status || 502,
                "ML_ANALYSIS_FAILED",
                detail
            );
        }
        if (error.code === "ECONNREFUSED" || error.code === "ETIMEDOUT" || error.code === "ECONNABORTED") {
            throw new AppError("AnomAI ML service is unavailable. Start FastAPI on port 8000 and try again.", 503, "ML_SERVICE_UNAVAILABLE");
        }
        throw new AppError("Unable to communicate with the ML service.", 502, "ML_SERVICE_ERROR", error.message);
    } finally {
        stream.destroy();
    }
}

async function downloadCleanedDataset(filename) {
    try {
        return await axios.get(`${ML_SERVICE_URL()}/download/${encodeURIComponent(filename)}`, {
            responseType: "stream",
            timeout: 120000
        });
    } catch (error) {
        if (error.response?.status === 404) {
            throw new AppError("Cleaned dataset file was not found.", 404, "CLEANED_FILE_NOT_FOUND");
        }
        throw new AppError("Unable to retrieve the cleaned dataset from the ML service.", 502, "ML_DOWNLOAD_FAILED");
    }
}

async function healthCheck() {
    try {
        const response = await axios.get(`${ML_SERVICE_URL()}/health`, { timeout: 5000 });
        return response.data;
    } catch (_error) {
        return { status: "unavailable", service: "AnomAI ML Service" };
    }
}

module.exports = { analyzeDataset, downloadCleanedDataset, healthCheck };
