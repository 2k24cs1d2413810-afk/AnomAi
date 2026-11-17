const jwt = require("jsonwebtoken");
const AppError = require("../utils/AppError");
const User = require("../models/User");

async function requireAuth(req, res, next) {
    const header = req.headers.authorization || "";
    const [scheme, token] = header.split(" ");

    if (scheme !== "Bearer" || !token) {
        return next(new AppError("Authentication required.", 401, "AUTH_REQUIRED"));
    }

    try {
        const payload = jwt.verify(token, process.env.JWT_SECRET);
        const user = await User.findById(payload.sub).select("_id name email").lean();

        if (!user) {
            return next(new AppError("User account no longer exists.", 401, "USER_NOT_FOUND"));
        }

        req.user = user;
        next();
    } catch (error) {
        return next(new AppError("Invalid or expired authentication token.", 401, "INVALID_TOKEN"));
    }
}

module.exports = requireAuth;
