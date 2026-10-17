/**
 * Formatting and Helper Utilities.
 */

export function formatDate(isoOrDateStr) {
  if (!isoOrDateStr) return '-';
  try {
    const parts = isoOrDateStr.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const d = new Date(year, month, day);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
    const d = new Date(isoOrDateStr);
    return isNaN(d.getTime()) ? isoOrDateStr : d.toLocaleDateString();
  } catch {
    return isoOrDateStr;
  }
}

export function formatTime(timeStr) {
  if (!timeStr) return '-';
  try {
    // If format is HH:MM:SS
    const parts = timeStr.split(':');
    if (parts.length >= 2) {
      let hours = parseInt(parts[0], 10);
      const minutes = parts[1];
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12; // the hour '0' should be '12'
      return `${hours}:${minutes} ${ampm}`;
    }
    return timeStr;
  } catch {
    return timeStr;
  }
}

export function getStatusBadgeClass(status) {
  switch (status?.toLowerCase()) {
    case 'present':
    case 'active':
    case 'marked':
      return 'badge-success';
    case 'absent':
    case 'inactive':
      return 'badge-danger';
    case 'late':
    case 'already_marked':
      return 'badge-warning';
    default:
      return 'badge-neutral';
  }
}
