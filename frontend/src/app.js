const healthEl = document.querySelector("#health");
const announcementsEl = document.querySelector("#announcements");
const employeesEl = document.querySelector("#employees");
const ticketsEl = document.querySelector("#tickets");
const ticketForm = document.querySelector("#ticket-form");
const ticketMessageEl = document.querySelector("#ticket-message");
const announcementCountEl = document.querySelector("#announcement-count");
const employeeCountEl = document.querySelector("#employee-count");
const openTicketCountEl = document.querySelector("#open-ticket-count");
const highPriorityCountEl = document.querySelector("#high-priority-count");

let portalData = {
  announcements: [],
  employees: [],
  tickets: [],
};

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return response.json();
}

async function sendJson(path, data) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }

  return response.json();
}

function formatDate(value) {
  return new Intl.DateTimeFormat("ja-JP", {
    dateStyle: "medium",
  }).format(new Date(value));
}

function renderSummary() {
  announcementCountEl.textContent = portalData.announcements.length;
  employeeCountEl.textContent = portalData.employees.length;
  openTicketCountEl.textContent = portalData.tickets.filter((ticket) => ticket.status === "未対応").length;
  highPriorityCountEl.textContent = portalData.tickets.filter((ticket) => ticket.priority === "高").length;
}

function renderAnnouncements(items) {
  announcementsEl.innerHTML = items
    .map(
      (item) => `
        <article class="announcement">
          <div class="announcement-topline">
            <span>${item.category}</span>
            <time>${formatDate(item.published_at)}</time>
          </div>
          <h3>${item.title}</h3>
          <p>${item.body}</p>
        </article>
      `
    )
    .join("");
}

function initials(name) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2);
}

function renderEmployees(items) {
  employeesEl.innerHTML = items
    .map(
      (employee) => `
        <article class="employee">
          <div class="avatar">${initials(employee.name)}</div>
          <div>
            <strong>${employee.name}</strong>
            <span>${employee.department} / ${employee.role}</span>
            <a href="mailto:${employee.email}">${employee.email}</a>
          </div>
        </article>
      `
    )
    .join("");
}

function statusClass(status) {
  if (status === "完了") return "done";
  if (status === "対応中") return "progress";
  return "open";
}

function priorityClass(priority) {
  if (priority === "高") return "high";
  if (priority === "低") return "low";
  return "medium";
}

function renderTickets(items) {
  ticketsEl.innerHTML = items
    .map(
      (ticket) => `
        <tr>
          <td>${ticket.title}</td>
          <td>${ticket.owner}</td>
          <td><span class="badge ${statusClass(ticket.status)}">${ticket.status}</span></td>
          <td><span class="priority ${priorityClass(ticket.priority)}">${ticket.priority}</span></td>
        </tr>
      `
    )
    .join("");
}

async function loadTickets() {
  portalData.tickets = await fetchJson("/api/tickets");
  renderTickets(portalData.tickets);
  renderSummary();
}

ticketForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  ticketMessageEl.textContent = "";

  const submitButton = ticketForm.querySelector("button");
  const formData = new FormData(ticketForm);
  const ticket = {
    title: formData.get("title"),
    owner: formData.get("owner"),
    priority: formData.get("priority"),
  };

  try {
    submitButton.disabled = true;
    submitButton.textContent = "追加中";
    await sendJson("/api/tickets", ticket);
    ticketForm.reset();
    ticketForm.elements.priority.value = "中";
    ticketMessageEl.textContent = "チケットを追加しました。";
    ticketMessageEl.className = "form-message success";
    await loadTickets();
  } catch (error) {
    console.error(error);
    ticketMessageEl.textContent = "チケットを追加できませんでした。";
    ticketMessageEl.className = "form-message error";
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "追加";
  }
});

async function loadPortal() {
  try {
    const health = await fetchJson("/api/health");
    healthEl.textContent = `API ${health.status} / DB ${health.database}`;
    healthEl.classList.add("ok");
    healthEl.classList.remove("error");

    const [announcements, employees, tickets] = await Promise.all([
      fetchJson("/api/announcements"),
      fetchJson("/api/employees"),
      fetchJson("/api/tickets"),
    ]);

    portalData = { announcements, employees, tickets };
    renderSummary();
    renderAnnouncements(announcements);
    renderEmployees(employees);
    renderTickets(tickets);
  } catch (error) {
    console.error(error);
    healthEl.textContent = "API 接続エラー";
    healthEl.classList.add("error");
    healthEl.classList.remove("ok");
  }
}

loadPortal();
