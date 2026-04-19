const API = "http://127.0.0.1:5000";

// Load menu
async function loadMenu(type) {
  try {
    const res = await fetch(`${API}/menu?type=${type}`);
    const data = await res.json();

    const container = document.getElementById("menu");
    container.innerHTML = "";

    if (data.length === 0) {
      container.innerHTML = "<p>No items available</p>";
      return;
    }

    data.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.animationDelay = `${index * 0.1}s`;

      card.innerHTML = `<h3>${item.item_name}</h3>`;
      container.appendChild(card);
    });

  } catch (err) {
    console.error(err);
    alert("Error loading menu");
  }
}

// Complaint
function sendComplaint() {
  const text = document.getElementById("text").value;

  fetch(`${API}/complaint`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({complaint: text})
  });

  alert("Complaint submitted!");
}