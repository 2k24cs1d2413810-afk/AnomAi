const crypto = require("crypto");

function hashPassword(password) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(16).toString("hex");
        crypto.scrypt(password, salt, 64, (error, derivedKey) => {
            if (error) return reject(error);
            resolve(`${salt}:${derivedKey.toString("hex")}`);
        });
    });
}

function verifyPassword(password, storedHash) {
    return new Promise((resolve, reject) => {
        const [salt, key] = String(storedHash).split(":");
        if (!salt || !key) return resolve(false);
        crypto.scrypt(password, salt, 64, (error, derivedKey) => {
            if (error) return reject(error);
            const stored = Buffer.from(key, "hex");
            const supplied = derivedKey;
            resolve(stored.length === supplied.length && crypto.timingSafeEqual(stored, supplied));
        });
    });
}

module.exports = { hashPassword, verifyPassword };
