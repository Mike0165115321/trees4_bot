const API_BASE = '/api';

async function fetch_settings() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        const sett = await response.json();
        document.getElementById("sett-h3").value = sett.health_3;
        document.getElementById("sett-h2").value = sett.health_2;
        document.getElementById("sett-h1").value = sett.health_1;
        document.getElementById("sett-headless").checked = sett.headless === 'true';
    } catch (error) {
        console.error("Failed to fetch settings:", error);
    }
}

async function fetch_accounts() {
    try {
        const response = await fetch(`${API_BASE}/accounts`);
        const accounts = await response.json();
        render_table(accounts);
        update_stats(accounts);
    } catch (error) {
        console.error("Failed to fetch accounts:", error);
    }
}

function render_table(accounts) {
    const pendingBody = document.querySelector("#pending-table tbody");
    const finishedBody = document.querySelector("#finished-table tbody");
    
    pendingBody.innerHTML = "";
    finishedBody.innerHTML = "";
    
    accounts.forEach(acc => {
        const tr = document.createElement("tr");
        if (acc.status === 'pending') {
            tr.innerHTML = `
                <td>${acc.phone}</td>
                <td>${acc.recorder}</td>
                <td>
                    <button onclick="delete_account(${acc.id})" class="btn btn-outline btn-small">ลบ</button>
                </td>
            `;
            pendingBody.appendChild(tr);
        } else {
            tr.innerHTML = `
                <td>${acc.phone}</td>
                <td><span class="badge ${acc.status}">${acc.status === 'done' ? 'สำเร็จแล้ว' : 'ผิดพลาด'}</span></td>
                <td style="font-size: 0.8rem; color: #666;">${acc.updated_at}</td>
                <td>
                    <button onclick="delete_account(${acc.id})" class="btn btn-outline btn-small">ลบ</button>
                </td>
            `;
            finishedBody.appendChild(tr);
        }
    });
}

function update_stats(accounts) {
    document.getElementById("stat-total").innerText = accounts.length;
    document.getElementById("stat-pending").innerText = accounts.filter(a => a.status === 'pending').length;
    document.getElementById("stat-done").innerText = accounts.filter(a => a.status === 'done').length;
    document.getElementById("stat-error").innerText = accounts.filter(a => a.status === 'error').length;
}

async function delete_account(id) {
    if (confirm("คุณแน่ใจหรือไม่ว่าต้องการลบบัญชีนี้ออกจากคิว?")) {
        await fetch(`${API_BASE}/accounts/${id}`, { method: 'DELETE' });
        fetch_accounts();
    }
}

async function update_bot_ui() {
    const response = await fetch(`${API_BASE}/bot/status`);
    const status = await response.json();
    
    const badge = document.getElementById("bot-status-badge");
    const btnStart = document.getElementById("btn-start");
    const btnStop = document.getElementById("btn-stop");
    
    if (status.is_running) {
        badge.classList.add("online");
        badge.querySelector(".text").innerText = "บอทกำลังทำงาน...";
        btnStart.style.display = "none";
        btnStop.style.display = "inline-block";
    } else {
        badge.classList.remove("online");
        badge.querySelector(".text").innerText = "บอทปิดอยู่";
        btnStart.style.display = "inline-block";
        btnStop.style.display = "none";
    }
}

// Event Listeners
document.getElementById("add-account-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
        phone: document.getElementById("inp-phone").value,
        password: document.getElementById("inp-password").value,
        recorder: document.getElementById("inp-recorder").value,
        surveyor: document.getElementById("inp-surveyor").value,
    };
    
    const response = await fetch(`${API_BASE}/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        document.getElementById("add-account-form").reset();
        fetch_accounts();
    } else {
        const error = await response.json();
        alert(error.detail);
    }
});

document.getElementById("settings-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
        health_3: parseInt(document.getElementById("sett-h3").value),
        health_2: parseInt(document.getElementById("sett-h2").value),
        health_1: parseInt(document.getElementById("sett-h1").value),
        headless: document.getElementById("sett-headless").checked
    };
    
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    alert("Settings saved successfully! 💾");
});

document.getElementById("btn-start").addEventListener("click", async () => {
    const response = await fetch(`${API_BASE}/bot/start`, { method: 'POST' });
    const result = await response.json();
    alert("ส่งคำสั่ง: " + (result.message === "Bot started successfully" ? "เริ่มบอทสำเร็จ!" : result.message));
    update_bot_ui();
});

document.getElementById("btn-stop").addEventListener("click", async () => {
    await fetch(`${API_BASE}/bot/stop`, { method: 'POST' });
    update_bot_ui();
});

document.getElementById("btn-reset").addEventListener("click", async () => {
    if (confirm("คุณต้องการล้างสถานะทุกคนกลับเป็น 'รอดำเนินการ' ใช่หรือไม่?")) {
        await fetch(`${API_BASE}/bot/reset`, { method: 'POST' });
        fetch_accounts();
    }
});

document.getElementById("btn-refresh").addEventListener("click", fetch_accounts);

// Sidebar Navigation
document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.preventDefault();
        const target = item.getAttribute("data-target");
        
        // Update Nav UI
        document.querySelectorAll(".nav-item").forEach(nav => nav.classList.remove("active"));
        item.classList.add("active");
        
        // Update Page UI
        document.querySelectorAll(".page").forEach(page => page.classList.remove("active"));
        document.getElementById(target).classList.add("active");
    });
});

// Initialization
fetch_accounts();
fetch_settings();
update_bot_ui();

// Auto Refresh
setInterval(fetch_accounts, 5000);
setInterval(update_bot_ui, 3000);
