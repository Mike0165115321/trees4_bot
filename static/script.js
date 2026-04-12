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
                    <button onclick="open_image_modal(${acc.id}, '${acc.phone}')" class="btn btn-outline btn-small" style="margin-right: 5px;">จัดการรูป 🖼️</button>
                    <button onclick="open_speed_modal(${acc.id}, '${acc.phone}')" class="btn btn-outline btn-small" style="margin-right: 5px;">ความเร็ว ⏱️</button>
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
                    <button onclick="open_speed_modal(${acc.id}, '${acc.phone}')" class="btn btn-outline btn-small" style="margin-right: 5px;">ความเร็ว ⏱️</button>
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
    const btnPause = document.getElementById("btn-pause");
    const btnResume = document.getElementById("btn-resume");
    
    if (status.is_running) {
        badge.classList.add("online");
        if (status.is_paused) {
            badge.querySelector(".text").innerText = "บอทพักชั่วคราว ⏸️";
            btnPause.style.display = "none";
            btnResume.style.display = "inline-block";
        } else {
            badge.querySelector(".text").innerText = "บอทกำลังทำงาน...";
            btnPause.style.display = "inline-block";
            btnResume.style.display = "none";
        }
        btnStart.style.display = "none";
        btnStop.style.display = "inline-block";
    } else {
        badge.classList.remove("online");
        badge.querySelector(".text").innerText = "บอทปิดอยู่";
        btnStart.style.display = "inline-block";
        btnStop.style.display = "none";
        btnPause.style.display = "none";
        btnResume.style.display = "none";
    }
}

// Event Listeners
document.getElementById("add-account-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append("phone", document.getElementById("inp-phone").value);
    formData.append("password", document.getElementById("inp-password").value);
    formData.append("recorder", document.getElementById("inp-recorder").value);
    formData.append("surveyor", document.getElementById("inp-surveyor").value);
    
    const fileInput = document.getElementById("inp-images");
    if (fileInput && fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append("images", fileInput.files[i]);
        }
    }
    
    const response = await fetch(`${API_BASE}/accounts`, {
        method: 'POST',
        body: formData
    });
    
    if (response.ok) {
        document.getElementById("add-account-form").reset();
        
        const fileInput = document.getElementById("inp-images");
        if (fileInput && fileInput.resetFiles) {
            fileInput.resetFiles();
        } else {
            const display = document.getElementById("file-name-display");
            if (display) {
                display.textContent = "ยังไม่ได้เลือกไฟล์";
                display.style.color = "var(--text-dim)";
            }
            const preview = document.getElementById("inp-images-preview");
            if (preview) preview.innerHTML = '';
        }
        
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

document.getElementById("btn-pause").addEventListener("click", async () => {
    await fetch(`${API_BASE}/bot/pause`, { method: 'POST' });
    update_bot_ui();
});

document.getElementById("btn-resume").addEventListener("click", async () => {
    await fetch(`${API_BASE}/bot/resume`, { method: 'POST' });
    update_bot_ui();
});

document.getElementById("btn-reset").addEventListener("click", async () => {
    if (confirm("คุณต้องการล้างสถานะทุกคนกลับเป็น 'รอดำเนินการ' ใช่หรือไม่?")) {
        await fetch(`${API_BASE}/bot/reset`, { method: 'POST' });
        fetch_accounts();
    }
});

document.getElementById("btn-refresh").addEventListener("click", fetch_accounts);

// Modal Logic
let currentModalAccountId = null;

async function open_image_modal(acc_id, phone) {
    currentModalAccountId = acc_id;
    document.getElementById("modal-phone").innerText = phone;
    document.getElementById("image-modal").classList.add("show");
    await load_modal_images();
}

document.getElementById("close-modal").addEventListener("click", () => {
    document.getElementById("image-modal").classList.remove("show");
    currentModalAccountId = null;
});

async function load_modal_images() {
    if (!currentModalAccountId) return;
    const response = await fetch(`${API_BASE}/accounts/${currentModalAccountId}/images`);
    const images = await response.json();
    const container = document.getElementById("existing-images");
    container.innerHTML = "";
    
    if (images.length === 0) {
        container.innerHTML = "<p style='color: var(--text-dim); font-size: 0.9rem;'>ยังไม่มีรูปภาพ</p>";
    } else {
        images.forEach(img => {
            const div = document.createElement("div");
            div.className = "img-preview-container";
            div.innerHTML = `
                <img src="/${img.file_path}" alt="Tree Image">
                <button class="delete-img-btn" onclick="delete_image(${img.id})">✕</button>
            `;
            container.appendChild(div);
        });
    }
}

async function delete_image(img_id) {
    if (confirm("ต้องการลบรูปภาพนี้หรือไม่?")) {
        await fetch(`${API_BASE}/images/${img_id}`, { method: 'DELETE' });
        await load_modal_images();
    }
}

document.getElementById("btn-upload-more").addEventListener("click", async () => {
    if (!currentModalAccountId) return;
    const fileInput = document.getElementById("modal-inp-images");
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("กรุณาเลือกรูปภาพอย่างน้อย 1 ใบ");
        return;
    }
    
    const formData = new FormData();
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append("images", fileInput.files[i]);
    }
    
    document.getElementById("btn-upload-more").innerText = "กำลังอัปโหลด...";
    const response = await fetch(`${API_BASE}/accounts/${currentModalAccountId}/images`, {
        method: 'POST',
        body: formData
    });
    
    document.getElementById("btn-upload-more").innerText = "อัปโหลด ⬆️";
    
    if (response.ok) {
        if (fileInput.resetFiles) {
            fileInput.resetFiles();
        } else {
            fileInput.value = "";
            const display = document.getElementById("modal-file-name-display");
            if (display) {
                display.textContent = "ยังไม่ได้เลือกไฟล์";
                display.style.color = "var(--text-dim)";
            }
            const preview = document.getElementById("modal-images-preview");
            if (preview) preview.innerHTML = '';
        }
        await load_modal_images();
    } else {
        alert("อัปโหลดไม่สำเร็จ");
    }
});

// --- Speed Modal Logic ---
async function open_speed_modal(acc_id, phone) {
    document.getElementById("speed-modal-phone").textContent = phone;
    document.getElementById("speed-modal-avg").innerHTML = 'โหลด...';
    document.getElementById("speed-modal-total").textContent = '0';
    document.getElementById("speed-modal-table-body").innerHTML = '';
    
    document.getElementById("speed-modal").style.display = "flex";
    
    try {
        const res = await fetch(`${API_BASE}/accounts/${acc_id}/speed`);
        const data = await res.json();
        
        document.getElementById("speed-modal-avg").innerHTML = `${data.avg_speed || 0} <span style="font-size: 1rem; color: var(--text-dim); font-weight: 400;">วินาที/ต้น</span>`;
        document.getElementById("speed-modal-total").textContent = data.total_trees;
        
        const tbody = document.getElementById("speed-modal-table-body");
        tbody.innerHTML = '';
        if (data.recent_speeds.length > 0) {
            data.recent_speeds.forEach((speed, idx) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td style="padding: 10px 15px; border-bottom: 1px solid var(--border); color: #fff;">คิวที่ ${data.total_trees - idx}</td>
                    <td style="padding: 10px 15px; text-align: right; border-bottom: 1px solid var(--border); color: ${speed > 8 ? 'var(--warning)' : 'var(--success)'}; font-weight: 600;">${speed}s</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="2" style="padding: 20px; text-align: center; color: var(--text-dim);">ยังไม่มีประวัติการทำงาน</td></tr>`;
        }
    } catch (e) {
        console.error(e);
        document.getElementById("speed-modal-avg").innerHTML = 'Error';
    }
}

async function fetch_global_speed() {
    try {
        const res = await fetch(`${API_BASE}/global_speed`);
        const data = await res.json();
        
        if (data && data.avg_sec > 0) {
            document.getElementById("global-speed-avg").textContent = data.avg_sec;
            document.getElementById("global-speed-min").textContent = data.per_min;
            document.getElementById("global-speed-hr").textContent = data.per_hour;
        } else {
            document.getElementById("global-speed-avg").textContent = "0.0";
            document.getElementById("global-speed-min").textContent = "0";
            document.getElementById("global-speed-hr").textContent = "0";
        }
    } catch (e) {
        console.error("Failed to fetch global speed", e);
    }
}

async function fetch_bot_logs() {
    try {
        const res = await fetch(`${API_BASE}/bot/logs`);
        const data = await res.json();
        const container = document.getElementById("bot-logs-container");
        
        let htmlStr = "";
        if (data && data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                // Filter out empty lines or purely decorative lines
                const trimmedLog = log.trim();
                if (!trimmedLog || trimmedLog.includes("===") || trimmedLog.includes("---") || trimmedLog.includes("═")) return;

                let typeClass = "info";
                if (log.includes("[OK]")) typeClass = "ok";
                else if (log.includes("[Warn]") || log.includes("(!)")) typeClass = "warn";
                else if (log.includes("[Error]") || log.includes("ล้มเหลว") || log.includes("Exception")) typeClass = "error";
                else if (log.includes("[Pause]") || log.includes("[Resume]")) typeClass = "pause";
                else if (log.includes("[Config]") || log.includes("Trees4All Bot")) typeClass = "config";
                
                const now = new Date();
                const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
                
                htmlStr += `<div class="log-entry ${typeClass}"><span class="log-time">${timeStr}</span> <span class="log-text">${log}</span></div>`;
            });
            
            // Only update DOM if the last log is different avoiding constant reflows
            const lastLog = data.logs[data.logs.length-1];
            if (container.dataset.lastLog !== lastLog || data.logs.length !== parseInt(container.dataset.logCount || '0')) {
                container.innerHTML = htmlStr;
                container.dataset.lastLog = lastLog;
                container.dataset.logCount = data.logs.length;
                container.scrollTop = container.scrollHeight;
            }
        }
    } catch (e) {
        // ignore
    }
}

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
fetch_global_speed();

// Auto Refresh
setInterval(fetch_accounts, 5000);
setInterval(update_bot_ui, 3000);
setInterval(fetch_global_speed, 5000);
setInterval(fetch_bot_logs, 2000);

// File Input Setup
function setupFileInput(inputId, displayId, previewContainerId) {
    const input = document.getElementById(inputId);
    const display = document.getElementById(displayId);
    const previewBox = document.getElementById(previewContainerId);
    if (!input || !display) return;
    
    let dt = new DataTransfer();
    
    input.resetFiles = function() {
        dt = new DataTransfer();
        input.value = "";
        renderPreviews();
    };

    input.addEventListener('change', function() {
        if (!this.files.length && dt.files.length === 0) return;
        
        // Append newly selected files to our DataTransfer
        for(let file of this.files) {
            dt.items.add(file);
        }
        input.files = dt.files;
        renderPreviews();
    });
    
    function renderPreviews() {
        if (previewBox) previewBox.innerHTML = '';
        
        if (input.files.length > 0) {
            if (input.files.length === 1) {
                display.textContent = input.files[0].name;
            } else {
                display.textContent = `เลือกแล้ว ${input.files.length} ไฟล์`;
            }
            display.style.color = 'var(--text-main)';
            
            if (previewBox) {
                Array.from(input.files).forEach((file, index) => {
                    if (file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const div = document.createElement('div');
                            div.className = "img-preview-container";
                            div.innerHTML = `
                                <img src="${e.target.result}">
                                <button type="button" class="delete-img-btn" data-index="${index}">✕</button>
                            `;
                            
                            div.querySelector('.delete-img-btn').addEventListener('click', function(evt) {
                                evt.preventDefault();
                                evt.stopPropagation();
                                const targetIndex = parseInt(this.getAttribute('data-index'));
                                
                                const newDt = new DataTransfer();
                                for(let i=0; i<dt.files.length; i++) {
                                    if (i !== targetIndex) {
                                        newDt.items.add(dt.files[i]);
                                    }
                                }
                                dt = newDt;
                                input.files = dt.files;
                                renderPreviews();
                            });
                            
                            previewBox.appendChild(div);
                        }
                        reader.readAsDataURL(file);
                    }
                });
            }
        } else {
            display.textContent = 'ยังไม่ได้เลือกไฟล์';
            display.style.color = 'var(--text-dim)';
        }
    }
}

setupFileInput('inp-images', 'file-name-display', 'inp-images-preview');
setupFileInput('modal-inp-images', 'modal-file-name-display', 'modal-images-preview');
