require("dotenv").config();
const mongoose = require("mongoose");
const User = require("../models/User");
const AnalysisHistory = require("../models/AnalysisHistory");

(async () => {
    try {
        await mongoose.connect(process.env.MONGODB_URI, { serverSelectionTimeoutMS: 8000 });
        await User.createCollection();
        await AnalysisHistory.createCollection();
        await User.syncIndexes();
        await AnalysisHistory.syncIndexes();
        await mongoose.connection.db.command({ ping: 1 });
        console.log(`MongoDB ready: ${mongoose.connection.name}`);
        console.log("Collections ready: users, analysishistories");
        await mongoose.disconnect();
    } catch (error) {
        console.error("MongoDB setup failed:", error.message);
        process.exitCode = 1;
    }
})();
