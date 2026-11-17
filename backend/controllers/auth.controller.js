const jwt = require("jsonwebtoken");
const User = require("../models/User");
const AppError = require("../utils/AppError");
const { hashPassword, verifyPassword } = require("../utils/password");

function signToken(user) {
    return jwt.sign(
        { sub: user._id.toString(), email: user.email },
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRES_IN || "7d" }
    );
}

function publicUser(user) {
    return { id: user._id.toString(), name: user.name, email: user.email };
}

async function register(req, res) {
    const name = String(req.body.name || "").trim();
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");

    if (name.length < 2) throw new AppError("Name must contain at least 2 characters.", 400, "INVALID_NAME");
    if (!/^\S+@\S+\.\S+$/.test(email)) throw new AppError("Enter a valid email address.", 400, "INVALID_EMAIL");
    if (password.length < 8) throw new AppError("Password must contain at least 8 characters.", 400, "WEAK_PASSWORD");

    const exists = await User.findOne({ email }).lean();
    if (exists) throw new AppError("An account with this email already exists.", 409, "EMAIL_EXISTS");

    const passwordHash = await hashPassword(password);
    const user = await User.create({ name, email, passwordHash });
    const token = signToken(user);

    res.status(201).json({ success: true, token, user: publicUser(user) });
}

async function login(req, res) {
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");

    if (!email || !password) throw new AppError("Email and password are required.", 400, "CREDENTIALS_REQUIRED");

    const user = await User.findOne({ email }).select("+passwordHash");
    if (!user || !(await verifyPassword(password, user.passwordHash))) {
        throw new AppError("Invalid email or password.", 401, "INVALID_CREDENTIALS");
    }

    res.json({ success: true, token: signToken(user), user: publicUser(user) });
}

async function me(req, res) {
    res.json({ success: true, user: publicUser(req.user) });
}

module.exports = { register, login, me };
