const express = require("express");
const cors = require("cors");
const morgan = require("morgan");
const axios = require("axios");
const swaggerJsdoc = require("swagger-jsdoc");
const swaggerUi = require("swagger-ui-express");
const winston = require("winston");

const app = express();
const PORT = process.env.PORT || 3000;
const JAVA_API_URL = process.env.JAVA_API_URL || "http://localhost:8080";
const PYTHON_PROCESSOR_URL =
  process.env.PYTHON_PROCESSOR_URL || "http://localhost:5000";

const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [new winston.transports.Console()],
});

app.use(cors());
app.use(express.json());
app.use(morgan("combined"));

const swaggerSpec = swaggerJsdoc({
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Sandbox Gateway API",
      version: "1.0.0",
      description:
        "API Gateway that routes requests to Java User API and Python Data Processor",
    },
    servers: [{ url: `http://localhost:${PORT}` }],
  },
  apis: [__filename],
});

app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
app.get("/api-docs-json", (_req, res) => res.json(swaggerSpec));

/**
 * @openapi
 * /health:
 *   get:
 *     summary: Gateway health check
 *     responses:
 *       200:
 *         description: Service health status
 */
app.get("/health", async (_req, res) => {
  const checks = { gateway: "healthy" };
  try {
    await axios.get(`${JAVA_API_URL}/actuator/health`, { timeout: 3000 });
    checks.javaApi = "healthy";
  } catch {
    checks.javaApi = "unreachable";
  }
  try {
    await axios.get(`${PYTHON_PROCESSOR_URL}/health`, { timeout: 3000 });
    checks.pythonProcessor = "healthy";
  } catch {
    checks.pythonProcessor = "unreachable";
  }
  res.json({ status: "healthy", service: "node-gateway", checks });
});

/**
 * @openapi
 * /api/users:
 *   get:
 *     summary: Get all users (proxied from Java API)
 *     responses:
 *       200:
 *         description: List of users
 */
app.get("/api/users", async (_req, res) => {
  try {
    const response = await axios.get(`${JAVA_API_URL}/api/users`, {
      timeout: 10000,
    });
    res.json(response.data);
  } catch (err) {
    logger.error("Failed to fetch users from Java API", { error: err.message });
    res
      .status(502)
      .json({ error: "Java API unavailable", detail: err.message });
  }
});

/**
 * @openapi
 * /api/process/users:
 *   post:
 *     summary: Process users (proxied to Python Processor)
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               action:
 *                 type: string
 *               department:
 *                 type: string
 *               format:
 *                 type: string
 *     responses:
 *       200:
 *         description: Processing result
 */
app.post("/api/process/users", async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_PROCESSOR_URL}/api/process/users`,
      req.body,
      { timeout: 10000 }
    );
    res.json(response.data);
  } catch (err) {
    logger.error("Failed to process users", { error: err.message });
    res
      .status(502)
      .json({ error: "Python Processor unavailable", detail: err.message });
  }
});

/**
 * @openapi
 * /api/reports/generate:
 *   post:
 *     summary: Generate report (proxied to Python Processor)
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               report_type:
 *                 type: string
 *               filters:
 *                 type: object
 *     responses:
 *       200:
 *         description: Generated report
 */
app.post("/api/reports/generate", async (req, res) => {
  try {
    const response = await axios.post(
      `${PYTHON_PROCESSOR_URL}/api/reports/generate`,
      req.body,
      { timeout: 10000 }
    );
    res.json(response.data);
  } catch (err) {
    logger.error("Failed to generate report", { error: err.message });
    res
      .status(502)
      .json({ error: "Python Processor unavailable", detail: err.message });
  }
});

if (require.main === module) {
  app.listen(PORT, () => {
    logger.info(`Gateway listening on port ${PORT}`);
    logger.info(`Swagger UI: http://localhost:${PORT}/api-docs`);
    logger.info(`Java API target: ${JAVA_API_URL}`);
    logger.info(`Python Processor target: ${PYTHON_PROCESSOR_URL}`);
  });
}

module.exports = app;
