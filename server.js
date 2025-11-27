const express = require('express');
const http = require('http');
const expressWs = require('express-ws');
const pty = require('node-pty');
const os = require('os');

const app = express();
const server = http.createServer(app);
const wss = expressWs(app, server);

const shell = os.platform() === 'win32' ? 'powershell.exe' : 'bash';
const port = 3000;

app.ws('/shell', (ws, req) => {
    console.log('New WebSocket connection established.');

    const ptyProcess = pty.spawn(shell, [], {
        name: 'xterm-color',
        cols: 80,
        rows: 30,
        cwd: process.env.HOME,
        env: process.env
    });

    // Pipe data from PTY to WebSocket
    ptyProcess.on('data', function (data) {
        try {
            ws.send(data);
        } catch (e) {
            console.log('Error sending data to WebSocket:', e);
        }
    });

    // Pipe data from WebSocket to PTY
    ws.on('message', function (msg) {
        ptyProcess.write(msg);
    });

    // Handle connection close
    ws.on('close', () => {
        ptyProcess.kill();
        console.log('Connection closed.');
    });

    // Handle PTY exit
    ptyProcess.on('exit', (code, signal) => {
        console.log(`PTY process exited with code ${code}, signal ${signal}`);
        ws.close();
    });
});

server.listen(port, () => {
    console.log(`Lorel Axun server bridge listening on port ${port}`);
    console.log('Ready to receive WebSocket connections on ws://localhost:3000/shell');
});