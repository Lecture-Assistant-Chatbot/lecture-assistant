import CONFIG from "./config";

export async function sendMessageToBackend(prompt) {
  const url = `${CONFIG.API_BASE_URL}/api/v1/query`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error("Error fetching backend response:", error);
    return "Sorry, I couldn’t reach the server.";
  }
}
