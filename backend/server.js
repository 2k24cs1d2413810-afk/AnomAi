require("dotenv").config();

const app = require("./app");
const { connectDatabase, disconnectDatabase } = require("./services/db.service");

const PORT = Number(process.env.PORT) || 8080;
let server;
let shuttingDown = false;

async function start() {
    if (!process.env.JWT_SECRET || process.env.JWT_SECRET.includes("CHANGE_THIS")) {
        throw new Error("Set a real JWT_SECRET in backend/.env before starting AnomAI.");
    }

    await connectDatabase();

    server = app.listen(PORT, () => {
        console.log(`[AnomAI] Backend: http://localhost:${PORT}/anomai`);
        console.log(`[AnomAI] API: http://localhost:${PORT}/api/health`);
    });

    server.on("error", (error) => {
        console.error("HTTP server error:", error);
    });
}

async function shutdown(signal) {
    if (shuttingDown) return;
    shuttingDown = true;
    console.log(`[AnomAI] ${signal} received. Shutting down gracefully...`);

    if (server) {
        await new Promise(resolve => server.close(resolve));
    }
    await disconnectDatabase();
    process.exit(0);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

process.on("unhandledRejection", (reason) => {
    console.error("Unhandled promise rejection:", reason);
});

process.on("uncaughtException", (error) => {
    console.error("Uncaught exception:", error);
    // Operational request errors are handled by Express. An uncaught exception
    // is logged rather than silently killing the process during local showcase.
});

start().catch(async (error) => {
    console.error("AnomAI startup failed:", error.message);
    await disconnectDatabase().catch(() => {});
    process.exit(1);
});
