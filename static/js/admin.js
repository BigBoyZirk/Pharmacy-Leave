function exclusiveEndToInclusive(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  date.setDate(date.getDate() - 1);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const calendarEl = document.getElementById("admin-calendar");
  if (!calendarEl) return;

  const editModal = new bootstrap.Modal(document.getElementById("editLeaveModal"));

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    firstDay: 1,
    height: "auto",
    events: "/api/admin/leave",
    eventClick(info) {
      const props = info.event.extendedProps;
      document.getElementById("edit-leave-id").value = info.event.id;
      document.getElementById("edit-leave-who").textContent =
        `${props.staffName} — ${props.status}`;
      document.getElementById("edit-start").value = info.event.startStr;
      document.getElementById("edit-end").value = exclusiveEndToInclusive(info.event.endStr);
      document.getElementById("edit-note").value = props.adminNote || "";
      editModal.show();
    },
  });
  calendar.render();

  document.querySelectorAll(".decide-leave").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const note = prompt("Optional note for the staff member:") || "";
      const res = await fetch(`/api/admin/leave/${btn.dataset.id}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision: btn.dataset.decision, note }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Could not update request.");
        return;
      }
      window.location.reload();
    });
  });

  document.getElementById("manual-leave-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const res = await fetch("/api/admin/leave/manual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: Number(document.getElementById("manual-user").value),
        start: document.getElementById("manual-start").value,
        end: document.getElementById("manual-end").value,
        note: document.getElementById("manual-note").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Could not add leave.");
      return;
    }
    window.location.reload();
  });

  async function updateLeave(action) {
    const note = document.getElementById("edit-note").value.trim();
    if (!note) {
      alert("Please add a note explaining the change.");
      return;
    }
    const res = await fetch(`/api/admin/leave/${document.getElementById("edit-leave-id").value}/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        start: document.getElementById("edit-start").value,
        end: document.getElementById("edit-end").value,
        note,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Could not update leave.");
      return;
    }
    window.location.reload();
  }

  document.getElementById("edit-leave-form").addEventListener("submit", (event) => {
    event.preventDefault();
    updateLeave("move");
  });

  document.getElementById("cancel-leave-admin").addEventListener("click", () => {
    updateLeave("cancel");
  });
});
