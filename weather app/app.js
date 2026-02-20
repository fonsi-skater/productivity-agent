const storageKeys = {
  contacts: "fms_contacts",
  tasks: "fms_tasks",
  inventory: "fms_inventory",
};

const defaultData = {
  contacts: [
    {
      id: "c1",
      name: "Ava Flores",
      email: "ava.flores@example.com",
      phone: "+1 555-0120",
      company: "Nimbus Labs",
      tags: "VIP, Speaker",
    },
    {
      id: "c2",
      name: "Daniel Mensah",
      email: "daniel.mensah@example.com",
      phone: "+1 555-0192",
      company: "Orchid Supply",
      tags: "Vendor",
    },
  ],
  tasks: [
    {
      id: "t1",
      title: "Prepare client onboarding deck",
      owner: "Liam",
      priority: "High",
      due: "2026-02-10",
      notes: "Focus on Q1 milestones",
      done: false,
    },
    {
      id: "t2",
      title: "Weekly inventory check",
      owner: "Sora",
      priority: "Medium",
      due: "2026-02-14",
      notes: "Warehouse A + mobile kit",
      done: true,
    },
  ],
  inventory: [
    {
      id: "i1",
      name: "Field Router",
      sku: "FR-204",
      quantity: 18,
      location: "Warehouse A",
      status: "In stock",
    },
    {
      id: "i2",
      name: "Solar Battery Pack",
      sku: "SB-994",
      quantity: 4,
      location: "Warehouse B",
      status: "Low stock",
    },
  ],
};

const state = {
  contacts: [],
  tasks: [],
  inventory: [],
  edit: {
    contacts: null,
    tasks: null,
    inventory: null,
  },
  search: {
    contacts: "",
    tasks: "",
    inventory: "",
  },
};

const elements = {
  contactsList: document.getElementById("list-contacts"),
  tasksList: document.getElementById("list-tasks"),
  inventoryList: document.getElementById("list-inventory"),
  counts: {
    contacts: document.getElementById("count-contacts"),
    tasks: document.getElementById("count-tasks"),
    inventory: document.getElementById("count-inventory"),
  },
  statusStrip: document.getElementById("status-strip"),
};

function generateId(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random()
    .toString(36)
    .slice(2, 8)}`;
}

function loadData() {
  state.contacts =
    JSON.parse(localStorage.getItem(storageKeys.contacts)) ??
    defaultData.contacts;
  state.tasks =
    JSON.parse(localStorage.getItem(storageKeys.tasks)) ?? defaultData.tasks;
  state.inventory =
    JSON.parse(localStorage.getItem(storageKeys.inventory)) ??
    defaultData.inventory;
}

function saveData() {
  localStorage.setItem(storageKeys.contacts, JSON.stringify(state.contacts));
  localStorage.setItem(storageKeys.tasks, JSON.stringify(state.tasks));
  localStorage.setItem(storageKeys.inventory, JSON.stringify(state.inventory));
}

function updateStatus() {
  const pendingTasks = state.tasks.filter((task) => !task.done).length;
  const lowStock = state.inventory.filter((item) => item.status !== "In stock")
    .length;
  let message = "All systems go.";

  if (pendingTasks > 0 && lowStock > 0) {
    message = `${pendingTasks} tasks pending, ${lowStock} inventory alerts.`;
  } else if (pendingTasks > 0) {
    message = `${pendingTasks} tasks pending.`;
  } else if (lowStock > 0) {
    message = `${lowStock} inventory alerts.`;
  }

  elements.statusStrip.textContent = message;
}

function renderCounts() {
  elements.counts.contacts.textContent = state.contacts.length;
  elements.counts.tasks.textContent = state.tasks.length;
  elements.counts.inventory.textContent = state.inventory.length;
}

function renderContacts() {
  const query = state.search.contacts.toLowerCase();
  const filtered = state.contacts.filter((contact) =>
    `${contact.name} ${contact.email} ${contact.company} ${contact.tags}`
      .toLowerCase()
      .includes(query)
  );

  elements.contactsList.innerHTML = filtered.length
    ? filtered
        .map(
          (contact) => `
      <article class="card">
        <div>
          <h4>${contact.name}</h4>
          <span class="pill">${contact.tags || "General"}</span>
        </div>
        <div class="meta">
          <span>${contact.email}</span>
          <span>${contact.phone}</span>
          <span>${contact.company || "Independent"}</span>
        </div>
        <div class="card-actions">
          <button class="tiny primary" data-edit="contacts" data-id="${
            contact.id
          }">Edit</button>
          <button class="tiny ghost" data-delete="contacts" data-id="${
            contact.id
          }">Delete</button>
        </div>
      </article>
    `
        )
        .join("")
    : `<div class="empty">No contacts found.</div>`;
}

function renderTasks() {
  const query = state.search.tasks.toLowerCase();
  const filtered = state.tasks.filter((task) =>
    `${task.title} ${task.owner} ${task.notes} ${task.priority}`
      .toLowerCase()
      .includes(query)
  );

  elements.tasksList.innerHTML = filtered.length
    ? filtered
        .map((task) => {
          const pillClass =
            task.priority === "High"
              ? "pill danger"
              : task.priority === "Medium"
              ? "pill warn"
              : "pill";
          return `
        <article class="card">
          <div class="task-title">
            <input type="checkbox" data-toggle="${
              task.id
            }" ${task.done ? "checked" : ""} />
            <h4 class="${task.done ? "strike" : ""}">${task.title}</h4>
          </div>
          <div class="meta">
            <span>${task.owner}</span>
            <span>${task.due || "No due date"}</span>
            <span>${task.notes || "No notes"}</span>
          </div>
          <div class="card-actions">
            <span class="${pillClass}">${task.priority}</span>
            <button class="tiny primary" data-edit="tasks" data-id="${
              task.id
            }">Edit</button>
            <button class="tiny ghost" data-delete="tasks" data-id="${
              task.id
            }">Delete</button>
          </div>
        </article>
      `;
        })
        .join("")
    : `<div class="empty">No tasks found.</div>`;
}

function renderInventory() {
  const query = state.search.inventory.toLowerCase();
  const filtered = state.inventory.filter((item) =>
    `${item.name} ${item.sku} ${item.location} ${item.status}`
      .toLowerCase()
      .includes(query)
  );

  elements.inventoryList.innerHTML = filtered.length
    ? filtered
        .map((item) => {
          const statusClass =
            item.status === "Low stock"
              ? "pill warn"
              : item.status === "Backorder"
              ? "pill danger"
              : "pill";
          return `
        <article class="card">
          <div>
            <h4>${item.name}</h4>
            <span class="${statusClass}">${item.status}</span>
          </div>
          <div class="meta">
            <span>SKU ${item.sku}</span>
            <span>Qty ${item.quantity ?? 0}</span>
            <span>${item.location || "Unassigned"}</span>
          </div>
          <div class="card-actions">
            <button class="tiny primary" data-edit="inventory" data-id="${
              item.id
            }">Edit</button>
            <button class="tiny ghost" data-delete="inventory" data-id="${
              item.id
            }">Delete</button>
          </div>
        </article>
      `;
        })
        .join("")
    : `<div class="empty">No inventory items found.</div>`;
}

function resetForm(section) {
  const form = document.getElementById(`form-${section}`);
  form.reset();
  state.edit[section] = null;
  document.getElementById(getSubmitId(section)).textContent = `Add ${
    section === "inventory" ? "item" : section.slice(0, -1)
  }`;
}

function handleEdit(section, id) {
  state.edit[section] = id;
  const record = state[section].find((item) => item.id === id);
  if (!record) return;
  const form = document.getElementById(`form-${section}`);

  Object.entries(record).forEach(([key, value]) => {
    if (key === "id" || key === "done") return;
    const input = form.querySelector(`[name="${key}"]`);
    if (input) input.value = value ?? "";
  });

  document.getElementById(getSubmitId(section)).textContent = `Update ${
    section === "inventory" ? "item" : section.slice(0, -1)
  }`;
}

function handleDelete(section, id) {
  state[section] = state[section].filter((item) => item.id !== id);
  saveData();
  renderAll();
}

function renderAll() {
  renderCounts();
  updateStatus();
  renderContacts();
  renderTasks();
  renderInventory();
}

function getSubmitId(section) {
  if (section === "contacts") return "contact-submit";
  if (section === "tasks") return "task-submit";
  return "inventory-submit";
}

function setupForms() {
  const contactForm = document.getElementById("form-contacts");
  const taskForm = document.getElementById("form-tasks");
  const inventoryForm = document.getElementById("form-inventory");

  contactForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(contactForm);
    const payload = Object.fromEntries(formData.entries());

    if (state.edit.contacts) {
      state.contacts = state.contacts.map((contact) =>
        contact.id === state.edit.contacts
          ? { ...contact, ...payload }
          : contact
      );
    } else {
      state.contacts.unshift({ id: generateId("c"), ...payload });
    }

    saveData();
    resetForm("contacts");
    renderAll();
  });

  taskForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(taskForm);
    const payload = Object.fromEntries(formData.entries());

    if (state.edit.tasks) {
      state.tasks = state.tasks.map((task) =>
        task.id === state.edit.tasks
          ? { ...task, ...payload }
          : task
      );
    } else {
      state.tasks.unshift({
        id: generateId("t"),
        done: false,
        ...payload,
      });
    }

    saveData();
    resetForm("tasks");
    renderAll();
  });

  inventoryForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(inventoryForm);
    const payload = Object.fromEntries(formData.entries());
    const quantity = Number(payload.quantity || 0);

    if (state.edit.inventory) {
      state.inventory = state.inventory.map((item) =>
        item.id === state.edit.inventory
          ? { ...item, ...payload, quantity }
          : item
      );
    } else {
      state.inventory.unshift({
        id: generateId("i"),
        ...payload,
        quantity,
      });
    }

    saveData();
    resetForm("inventory");
    renderAll();
  });

  document.getElementById("contact-cancel").addEventListener("click", () => {
    resetForm("contacts");
  });
  document.getElementById("task-cancel").addEventListener("click", () => {
    resetForm("tasks");
  });
  document
    .getElementById("inventory-cancel")
    .addEventListener("click", () => {
      resetForm("inventory");
    });
}

function setupSearch() {
  document.getElementById("search-contacts").addEventListener("input", (e) => {
    state.search.contacts = e.target.value;
    renderContacts();
  });
  document.getElementById("search-tasks").addEventListener("input", (e) => {
    state.search.tasks = e.target.value;
    renderTasks();
  });
  document
    .getElementById("search-inventory")
    .addEventListener("input", (e) => {
      state.search.inventory = e.target.value;
      renderInventory();
    });
}

function setupListActions() {
  document.addEventListener("click", (event) => {
    const editTarget = event.target.closest("[data-edit]");
    if (editTarget) {
      handleEdit(editTarget.dataset.edit, editTarget.dataset.id);
      return;
    }

    const deleteTarget = event.target.closest("[data-delete]");
    if (deleteTarget) {
      handleDelete(deleteTarget.dataset.delete, deleteTarget.dataset.id);
      return;
    }
  });

  elements.tasksList.addEventListener("change", (event) => {
    const toggle = event.target.closest("[data-toggle]");
    if (!toggle) return;
    const taskId = toggle.dataset.toggle;
    state.tasks = state.tasks.map((task) =>
      task.id === taskId ? { ...task, done: toggle.checked } : task
    );
    saveData();
    renderAll();
  });
}

loadData();
setupForms();
setupSearch();
setupListActions();
renderAll();
