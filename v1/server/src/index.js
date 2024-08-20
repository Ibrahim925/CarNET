const WebSocket = require("ws");
const readlineSync = require("readline-sync");

const wss = new WebSocket.Server({ port: 9000 });

wss.on("connection", (ws) => {
	console.log("A client connected");

	ws.on("message", (message) => {
		message = JSON.parse(message);
		console.log("Message received from client:", message);

		if (message["event"] === "object_detected") {
			// Prompt user for action
			const action = readlineSync
				.question("Accept or deny the action (accept/deny): ")
				.trim();

			// Validate input
			const validAction =
				action === "accept" || action === "deny" ? action : "deny";

			// Send response back to client
			ws.send(JSON.stringify({ action: validAction }));
		}
	});

	ws.on("close", () => {
		console.log("Client disconnected");
	});
});

console.log("WebSocket server is running on ws://localhost:9000");
