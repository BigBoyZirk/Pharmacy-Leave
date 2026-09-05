function exclusiveEndToInclusive(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  date.setDate(date.getDate() - 1);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function formatRange(start, end) {
  return start === end ? start : `${start} to ${end}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const calendarEl = document.getElementById("staff-calendar");
  if (!calendarEl) return;

  let pendingStart = null;
  let pendingEnd = null;
  const modal = new bootstrap.Modal(document.getElementById("requestModal"));

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    firstDay: 1,
    selectable: true,
    selectMirror: true,
    height: "auto",
    
    // Touch support for mobile
    dragScroll: false,
    selectLongPressDelay: 100,
    eventLongPressDelay: 100,
    longPressDelay: 100,
    selectMinDistance: 5,
    
    events: "/api/my-leave",
    
    select(info) {
      pendingStart = info.startStr;
      pendingEnd = exclusiveEndToInclusive(info.endStr);
      document.getElementById("request-range").textContent = formatRange(pendingStart, pendingEnd);
      document.getElementById("staff-note").value = "";
      modal.show();
      calendar.unselect();
    },
  });
  
  calendar.render();

  // ==================== SUBMIT LEAVE REQUEST ====================
  document.getElementById("submit-request").addEventListener("click", async function() {
    // Disable button to prevent double-click
    this.disabled = true;
    this.textContent = "Submitting...";
    
    const note = document.getElementById("staff-note").value;
    
    try {
      const res = await fetch("/api/leave-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start: pendingStart, end: pendingEnd, note }),
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        alert(data.error || "Could not submit request.");
        this.disabled = false;
        this.textContent = "Submit request";
        return;
      }
      
      modal.hide();
      window.location.reload();
      
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred. Please try again.');
      this.disabled = false;
      this.textContent = "Submit request";
    }
  });

  // ==================== CANCEL LEAVE REQUEST ====================
  document.querySelectorAll(".cancel-leave").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Cancel this pending request?")) return;
      
      const res = await fetch(`/api/leave/${btn.dataset.id}/cancel`, { method: "POST" });
      const data = await res.json();
      
      if (!res.ok) {
        alert(data.error || "Could not cancel.");
        return;
      }
      window.location.reload();
    });
  });
});