function login(event) {
    event.preventDefault();
  
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
  
    // Fake validation logic for demo
    if (username === "admin" && password === "password") {
      alert("Login successful!");
      window.location.href = "view_inventory.html";
      // Redirect or proceed
    } else {
      alert("Invalid credentials.");
    }
  
    return false;
  }
  