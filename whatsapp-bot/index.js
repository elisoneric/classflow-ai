const express = require('express');
const { makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');

const app = express();
app.use(express.json());

let sock;
let isReady = false;

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: pino({ level: 'silent' })
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect } = update;
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('connection closed due to ', lastDisconnect.error, ', reconnecting ', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('WhatsApp Bot connected successfully!');
            isReady = true;
        }
    });

    sock.ev.on('creds.update', saveCreds);
}

// Endpoint to send a message to a group
app.post('/send_group', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: "WhatsApp bot not ready" });
    }

    const { course_code, message } = req.body;
    if (!message) {
        return res.status(400).json({ error: "Message is required" });
    }

    // In a real system, you'd map course_code to a specific group JID.
    // For MVP, we broadcast to a predefined group or just log.
    // Example Group JID: "1234567890@g.us"
    const groupJid = process.env.WHATSAPP_GROUP_JID;
    
    if (!groupJid) {
        console.log(`Simulating sending to ${course_code} group: ${message}`);
        return res.json({ success: true, simulated: true });
    }

    try {
        await sock.sendMessage(groupJid, { text: message });
        return res.json({ success: true });
    } catch (error) {
        console.error("Failed to send WhatsApp message:", error);
        return res.status(500).json({ error: "Failed to send message" });
    }
});

app.listen(3000, () => {
    console.log('WhatsApp Microservice listening on port 3000');
    connectToWhatsApp();
});
