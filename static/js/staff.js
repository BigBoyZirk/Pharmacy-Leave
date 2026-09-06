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

  // ==================== HOURS PREVIEW ====================
  function updateHoursPreview() {
    const start = document.getElementById("start-time").value;
    const end = document.getElementById("end-time").value;
    const remaining = parseFloat(document.getElementById("remaining-data")?.dataset?.remaining || 0);
    
    if (start && end) {
      const startDate = new Date('1970-01-01T' + start + ':00');
      const endDate = new Date('1970-01-01T' + end + ':00');
      const hoursPerDay = (endDate - startDate) / 3600000;
      
      if (hoursPerDay > 0) {
        // Calculate total hours for the selected date range
        const startDateObj = new Date(pendingStart + 'T00:00:00');
        const endDateObj = new Date(pendingEnd + 'T00:00:00');
        const days = Math.floor((endDateObj - startDateObj) / (86400000)) + 1;
        const totalHours = days * hoursPerDay;
        
        document.getElementById('hours-preview').textContent = `Hours per day: ${hoursPerDay.toFixed(1)}`;
        document.getElementById('total-hours-preview').textContent = `Total: ${totalHours.toFixed(1)} hrs`;
        
        // Check if exceeds remaining hours
        const warningEl = document.getElementById('remaining-warning');
        if (remaining > 0 && totalHours > remaining) {
          warningEl.style.display = 'block';
          warningEl.textContent = `⚠️ This exceeds your remaining hours (${remaining.toFixed(1)} hrs)`;
        } else {
          warningEl.style.display = 'none';
        }
      }
    }
  }

  // ==================== CALENDAR ====================
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
      
      const startDate = new Date(info.startStr + 'T00:00:00');
      const endDate = new Date(info.endStr + 'T00:00:00');
      const days = Math.floor((endDate - startDate) / (86400000));
      
      document.getElementById("request-range").textContent = formatRange(pendingStart, pendingEnd);
      document.getElementById("days-count").textContent = `${days} day(s)`;
      document.getElementById("staff-note").value = "";
      
      // Reset time pickers
      document.getElementById("start-time").value = "09:00";
      document.getElementById("end-time").value = "17:00";
      
      // Update hours preview
      updateHoursPreview();
      
      modal.show();
      calendar.unselect();
    },
  });
  
  calendar.render();

  // ==================== HOURS PREVIEW EVENTS ====================
  document.getElementById('start-time').addEventListener('change', updateHoursPreview);
  document.getElementById('end-time').addEventListener('change', updateHoursPreview);

  // ==================== SUBMIT LEAVE REQUEST ====================
  document.getElementById("submit-request").addEventListener("click", async function() {
    // Disable button to prevent double-click
    this.disabled = true;
    this.textContent = "Submitting...";
    
    const note = document.getElementById("staff-note").value;
    const startTime = document.getElementById("start-time").value;
    const endTime = document.getElementById("end-time").value;
    
    // Validate times
    if (!startTime || !endTime) {
      alert("Please select start and end times.");
      this.disabled = false;
      this.textContent = "Submit request";
      return;
    }
    
    // Calculate hours
    const start = new Date('1970-01-01T' + startTime + ':00');
    const end = new Date('1970-01-01T' + endTime + ':00');
    const hours = (end - start) / 3600000;
    
    if (hours <= 0) {
      alert("End time must be after start time.");
      this.disabled = false;
      this.textContent = "Submit request";
      return;
    }
    
    // Get remaining hours from the page (or calculate it)
    const remainingEl = document.getElementById('remaining-data');
    const remaining = remainingEl ? parseFloat(remainingEl.dataset.remaining) : 0;
    
    // Calculate total hours for the date range
    const startDateObj = new Date(pendingStart + 'T00:00:00');
    const endDateObj = new Date(pendingEnd + 'T00:00:00');
    const days = Math.floor((endDateObj - startDateObj) / (86400000)) + 1;
    const totalHours = days * hours;
    
    // Check hard limit
    if (remaining > 0 && totalHours > remaining) {
      alert(`Limit reached. You have ${remaining.toFixed(1)} hours remaining, but this request needs ${totalHours.toFixed(1)} hours.`);
      this.disabled = false;
      this.textContent = "Submit request";
      return;
    }
    
    try {
      const res = await fetch("/api/leave-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start: pendingStart,
          end: pendingEnd,
          note: note,
          start_time: startTime,
          end_time: endTime,
          hours: hours
        }),
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

  // ==================== REMAINING HOURS DATA ====================
  // Add a hidden element to store remaining hours for JavaScript
  const remainingData = document.createElement('div');
  remainingData.id = 'remaining-data';
  remainingData.dataset.remaining = document.querySelector('.stat-chip strong')?.textContent || 0;
  remainingData.style.display = 'none';
  document.body.appendChild(remainingData);
});