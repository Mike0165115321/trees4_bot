const API_BASE = '/api';
let bot_current_phone = ''; // เบอร์ที่บอทกำลังทำงานอยู่
let selectionMode = false;
let selectedAccountPhones = new Set();
let currentDateFilter = 'today'; // ฟิลเตอร์วันที่ปัจจุบัน ('today', 'month', 'year', 'all')

const isToday = (dateStr) => {
    if (!dateStr) return false;
    const today = new Date().toISOString().split('T')[0];
    return dateStr.startsWith(today);
};


const getDisplayDate = (dateStr) => {
    if (!dateStr) return "";
    const [date] = dateStr.split(' ');
    const [y, m, d] = date.split('-');
    return `${d}/${m}/${y}`;
};

const isThisMonth = (dateStr) => {
    if (!dateStr) return false;
    const month = new Date().toISOString().substring(0, 7); // YYYY-MM
    return dateStr.startsWith(month);
};

const isThisYear = (dateStr) => {
    if (!dateStr) return false;
    const year = new Date().toISOString().substring(0, 4); // YYYY
    return dateStr.startsWith(year);
};

async function fetch_settings() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        const sett = await response.json();
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
    
    // จัดการหัวตาราง Checkbox
    document.querySelectorAll(".check-col").forEach(el => {
        el.style.display = selectionMode ? "table-cell" : "none";
    });

    pendingBody.innerHTML = "";
    finishedBody.innerHTML = "";
    
    // แบ่งข้อมูล
    const pendingList = accounts.filter(a => a.status === 'pending');
    let finishedList = accounts.filter(a => a.status !== 'pending' && a.status !== 'processing');

    // กรองข้อมูลตามวันที่
    if (currentDateFilter === 'today') {
        finishedList = finishedList.filter(a => isToday(a.updated_at));
    } else if (currentDateFilter === 'month') {
        finishedList = finishedList.filter(a => isThisMonth(a.updated_at));
    } else if (currentDateFilter === 'year') {
        finishedList = finishedList.filter(a => isThisYear(a.updated_at));
    }

    // เรียงลำดับ (ล่าสุดขึ้นก่อน)
    finishedList.sort((a, b) => b.updated_at.localeCompare(a.updated_at));

    // แสดงรายการ Pending
    let pendingIndex = 0;
    pendingList.forEach(acc => {
        pendingIndex++;
        const tr = document.createElement("tr");
        const isChecked = selectedAccountPhones.has(acc.phone);
        const checkHtml = selectionMode ? `
            <td class="check-col">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                    onchange="toggle_account_selection('${acc.phone}')" 
                    style="width: 18px; height: 18px; cursor: pointer;">
            </td>
        ` : '';

        const isActive = (acc.phone === bot_current_phone);
        if (isActive) tr.classList.add('active-row');

        tr.innerHTML = `
            ${checkHtml}
            <td class="col-phone">
                <span class="queue-number ${isActive ? 'active' : ''}">${pendingIndex}</span>
                <strong style="font-size: 1rem;">${acc.phone}</strong>
                ${isActive ? '<br><span style="color: var(--success); font-size: 0.7rem; font-weight: 500; margin-left: 34px;">● กำลังทำงาน</span>' : ''}
            </td>
            <td class="col-recorder" style="color: var(--text-dim);">${acc.recorder}</td>
            <td class="col-actions">
                <button onclick="move_to_top(${acc.id})" class="btn btn-outline btn-small" style="color: var(--warning);">ทำก่อน ⬆️</button>
                <button onclick="open_image_modal(${acc.id}, '${acc.phone}')" class="btn btn-outline btn-small">จัดการรูป 🖼️</button>
                <button onclick="open_speed_modal(${acc.id}, '${acc.phone}')" class="btn btn-outline btn-small">ความเร็ว ⏱️</button>
                <button onclick="delete_account(${acc.id})" class="btn btn-danger btn-small">ลบ</button>
            </td>
        `;
        pendingBody.appendChild(tr);
    });

    // แสดงรายการ Finished พร้อมหัวข้อวันที่ถ้าเป็น 'all'
    let lastDate = "";
    finishedList.forEach(acc => {
        const tr = document.createElement("tr");
        const isChecked = selectedAccountPhones.has(acc.phone);
        const checkHtml = selectionMode ? `
            <td class="check-col">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                    onchange="toggle_account_selection('${acc.phone}')" 
                    style="width: 18px; height: 18px; cursor: pointer;">
            </td>
        ` : '';

        // เพิ่มแถบหัวข้อวันที่
        if (currentDateFilter !== 'today') {
            const currentDate = acc.updated_at.split(' ')[0];
            if (currentDate !== lastDate) {
                const headerTr = document.createElement("tr");
                headerTr.innerHTML = `<td colspan="${selectionMode ? 6 : 5}" class="date-divider">📅 ${getDisplayDate(acc.updated_at)}</td>`;
                finishedBody.appendChild(headerTr);
                lastDate = currentDate;
            }
        }

        tr.innerHTML = `
            ${checkHtml}
            <td class="col-phone"><strong>${acc.phone}</strong></td>
            <td class="col-status"><span class="badge ${acc.status}">${acc.status === 'done' ? 'สำเร็จแล้ว' : 'ผิดพลาด'}</span></td>
            <td class="col-stats">
                <span style="color: var(--info); font-weight: 700; font-size: 1.1rem;">${acc.trees_filled || 0}</span> <small style="color: var(--text-dim)">ต้น</small> / 
                <span style="color: var(--purple); font-weight: 700; font-size: 1.1rem;">${acc.images_uploaded || 0}</span> <small style="color: var(--text-dim)">รูป</small>
            </td>
            <td class="col-time" style="font-size: 0.8rem; color: var(--text-dim); opacity: 0.7;">${acc.updated_at.split(' ')[1]}</td>
            <td class="col-actions">
                <button onclick="requeue_account(${acc.id})" class="btn btn-outline btn-small">กลับเข้าคิว 🔄</button>
                <button onclick="open_speed_modal(${acc.id}, '${acc.phone}')" class="btn btn-outline btn-small">ความเร็ว ⏱️</button>
                <button onclick="delete_account(${acc.id})" class="btn btn-danger btn-small">ลบ</button>
            </td>
        `;
        finishedBody.appendChild(tr);
    });
}

function toggle_account_selection(phone) {
    if (selectedAccountPhones.has(phone)) {
        selectedAccountPhones.delete(phone);
    } else {
        selectedAccountPhones.add(phone);
    }
    update_selection_ui();
}

function update_selection_ui() {
    const count = selectedAccountPhones.size;
    document.getElementById("selected-count").innerText = count;
    const btnCheck = document.getElementById("btn-start-check-selected");
    
    if (count > 0) {
        btnCheck.disabled = false;
        btnCheck.style.opacity = "1";
    } else {
        btnCheck.disabled = true;
        btnCheck.style.opacity = "0.5";
    }
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

async function requeue_account(id) {
    if (confirm("ต้องการนำบัญชีนี้กลับเข้าคิว (pending) ใหม่หรือไม่?")) {
        await fetch(`${API_BASE}/accounts/${id}/requeue`, { method: 'POST' });
        fetch_accounts();
    }
}

async function move_to_top(id) {
    await fetch(`${API_BASE}/accounts/${id}/move_to_top`, { method: 'POST' });
    fetch_accounts();
}

async function update_bot_ui() {
    const response = await fetch(`${API_BASE}/bot/status`);
    const status = await response.json();
    bot_current_phone = status.current_phone || '';
    
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
    formData.append("health_3", document.getElementById("inp-h3").value);
    formData.append("health_2", document.getElementById("inp-h2").value);
    formData.append("health_1", document.getElementById("inp-h1").value);
    
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

// Auto-save headless setting on change
document.getElementById("sett-headless").addEventListener("change", async (e) => {
    const data = {
        headless: e.target.checked
    };
    
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    // Optional: add a small notification or toast here if needed
});

// Filter Tabs Listeners
document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", () => {
        // อัปเดต UI Tab
        document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        
        // อัปเดต Filter และเรนเดอร์ตารางใหม่
        currentDateFilter = tab.getAttribute("data-filter");
        fetch_accounts();
    });
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

document.getElementById("btn-retry").addEventListener("click", async () => {
    if (confirm("ต้องการนำบัญชีที่สถานะ 'ผิดพลาด' กลับไปรันใหม่อีกครั้งใช่หรือไม่? (บัญชีที่สำเร็จแล้วจะไม่ถูกเปลี่ยน)")) {
        await fetch(`${API_BASE}/bot/retry`, { method: 'POST' });
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
setInterval(fetch_accounts, selectionMode ? 10000 : 5000); // ช้าลงหน่อยถ้ากำลังเลือกอยู่
setInterval(update_bot_ui, 3000);
setInterval(fetch_global_speed, 5000);
setInterval(fetch_bot_logs, 2000);

// Selection Mode Listeners
document.getElementById("btn-toggle-selection").addEventListener("click", () => {
    selectionMode = true;
    document.getElementById("selection-action-bar").style.display = "flex";
    document.getElementById("btn-toggle-selection").style.display = "none";
    fetch_accounts();
    update_selection_ui();
});

document.getElementById("btn-cancel-selection").addEventListener("click", () => {
    selectionMode = false;
    selectedAccountPhones.clear();
    document.getElementById("selection-action-bar").style.display = "none";
    document.getElementById("btn-toggle-selection").style.display = "inline-block";
    fetch_accounts();
});

document.getElementById("btn-start-check-selected").addEventListener("click", async () => {
    if (selectedAccountPhones.size === 0) return;
    
    if (confirm(`คันยืนยันที่จะให้บอทเริ่มเช็คยอดต้นไม้ ${selectedAccountPhones.size} บัญชีที่เลือกใช่หรือไม่?`)) {
        const formData = new FormData();
        Array.from(selectedAccountPhones).forEach(phone => {
            formData.append("phones", phone);
        });
        
        const response = await fetch(`${API_BASE}/bot/check`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        alert(result.message);
        
        // จบโหมดเลือก
        selectionMode = false;
        selectedAccountPhones.clear();
        document.getElementById("selection-action-bar").style.display = "none";
        document.getElementById("btn-toggle-selection").style.display = "inline-block";
        fetch_accounts();
        update_bot_ui();
    }
});

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
