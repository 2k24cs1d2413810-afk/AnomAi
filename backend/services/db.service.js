const mongoose = require("mongoose");
const User = require("../models/User");
const AnalysisHistory = require("../models/AnalysisHistory");

async function connectDatabase() {
    const uri = process.env.MONGODB_URI;
    if (!uri) throw new Error("MONGODB_URI is not configured.");

    mongoose.set("strictQuery", true);
    await mongoose.connect(uri, {
        serverSelectionTimeoutMS: 8000,
        maxPoolSize: 10,
        minPoolSize: 1
    });

    await mongoose.connection.db.command({ ping: 1 });
    await User.createCollection().catch(error => { if (error.codeName !== "NamespaceExists") throw error; });
    await AnalysisHistory.createCollection().catch(error => { if (error.codeName !== "NamespaceExists") throw error; });
    await User.syncIndexes();
    await AnalysisHistory.syncIndexes();
    console.log(`[AnomAI] MongoDB connected: ${mongoose.connection.name}`);
    console.log("[AnomAI] MongoDB collections ready: users, analysishistories");
}

async function disconnectDatabase() {
    if (mongoose.connection.readyState !== 0) {
        await mongoose.disconnect();
    }
}

module.exports = { connectDatabase, disconnectDatabase };
