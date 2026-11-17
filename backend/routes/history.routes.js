const express = require("express");
const auth = require("../middleware/auth.middleware");
const asyncHandler = require("../utils/asyncHandler");
const controller = require("../controllers/history.controller");

const router = express.Router();
router.get("/users/:userId/history", auth, asyncHandler(controller.listHistory));
router.get("/users/:userId/history/:historyId", auth, asyncHandler(controller.getHistoryItem));
module.exports = router;
