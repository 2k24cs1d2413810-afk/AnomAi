const express = require("express");
const auth = require("../middleware/auth.middleware");
const upload = require("../middleware/upload.middleware");
const asyncHandler = require("../utils/asyncHandler");
const controller = require("../controllers/analysis.controller");

const router = express.Router();

router.post(
    "/upload",
    auth,
    upload.single("dataset"),
    asyncHandler(controller.uploadAndAnalyze)
);

router.get(
    "/download/:filename",
    auth,
    asyncHandler(controller.downloadHistoryFile)
);

module.exports = router;
