const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const path = require("path");

const app = express();

app.set("view engine", "html");
app.use(express.static(path.join(__dirname, "/")));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// Proxy requests to /upload-menu to the backend server
app.use(
    "/upload-menu",
    createProxyMiddleware({
        target: "http://192.168.1.67:8000", // Local backend server
        changeOrigin: true,
        secure: false, // Set to true if backend supports HTTPS
    })
);

app.get("/", (req, res) => {
    res.render("index");
});

app.listen(8080, "0.0.0.0", () => {
    console.log("Listening on http://localhost:8080");
});
