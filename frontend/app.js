const eventsList = document.getElementById("events");
const statusDiv = document.getElementById("status");

function addEvent(event) {
    const li = document.createElement("li");
    li.className = "event " + (event.severity || "low");

    li.innerHTML = `
        <strong>${event.event_type}</strong><br/>
        ${event.source || ""}<br/>
        <small>${new Date().toLocaleTimeString()}</small>
    `;

    eventsList.prepend(li);
}

async function loadHistory() {

    const res = await fetch("http://localhost:8000/api/v1/events", {
        headers: {
            "Authorization": `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODM5NTM1NDAsInN1YiI6IjMyMmM3M2ZmLTk3MWQtNGI2NC1iYWRhLTJmYTFhZjg3ZDdjMCJ9.MNH0yvqhO6yyPXaoC36RWvWp8aa1lFMzTZnSNje55SE`
        }
    });
    const data = await res.json();

    data.reverse().forEach(addEvent);
}

function connectWebSocket() {
    const ws = new WebSocket("ws://localhost:8000/api/v1/events/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODM5NTM1NDAsInN1YiI6IjMyMmM3M2ZmLTk3MWQtNGI2NC1iYWRhLTJmYTFhZjg3ZDdjMCJ9.MNH0yvqhO6yyPXaoC36RWvWp8aa1lFMzTZnSNje55SE");

    ws.onopen = () => {
        statusDiv.innerText = "🟢 Connected";
    };

    ws.onclose = (event) => {
        console.log("WS closed:", event.code, event.reason);

        setTimeout(() => {
            connectWebSocket();
        }, 3000);
    };

    ws.onerror = () => {
        statusDiv.innerText = "⚠️ Error";
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            addEvent(data);
        } catch (e) {
            console.log("Invalid message:", event.data);
        }
    };
}

loadHistory();
connectWebSocket();