const AppError = require("../utils/AppError");

module.exports = function notFoundMiddleware(req, _res, next) {
    next(new AppError(`Route not found: ${req.method} ${req.originalUrl}`, 404, "ROUTE_NOT_FOUND"));
};
