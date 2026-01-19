/**
 * Formats AI response messages to improve readability
 * - Adds proper segmentation between days
 * - Converts activities to bullet points
 * - Improves overall formatting
 */

export function formatMessage(text: string): string {
  if (!text) return text;

  // Split by lines and process
  const lines = text.split('\n');
  const formattedLines: string[] = [];
  let currentDay: string | null = null;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();
    
    // Skip empty lines at the start
    if (!line && formattedLines.length === 0) continue;
    
    // Remove dashes used as list markers (e.g., "- Visit X" -> "Visit X")
    // This ensures we only use bullet points, not dashes
    line = line.replace(/^-\s+/, '');

    // Detect day headers (Day 1, Day 2, etc.) - can be at start or with colon
    const dayMatch = line.match(/^(Day\s+\d+)[:.]?\s*(.*)$/i);
    if (dayMatch) {
      // Add spacing before new day (except first day)
      if (currentDay !== null) {
        formattedLines.push('');
      }
      currentDay = dayMatch[1];
      formattedLines.push(`**${currentDay}**`);
      // If there's additional text after Day X, add it on next line
      if (dayMatch[2]) {
        formattedLines.push(dayMatch[2]);
      }
      continue;
    }

    // Detect time periods (Morning, Afternoon, Evening) - can be standalone or with colon
    const periodMatch = line.match(/^(Morning|Afternoon|Evening|Night)[:.]?\s*(.*)$/i);
    if (periodMatch) {
      formattedLines.push(`*${periodMatch[1]}*`);
      if (periodMatch[2]) {
        // Process activities in this period - split by common separators
        const activities = periodMatch[2]
          .split(/(?:and|,)\s+(?=(?:Visit|Explore|Enjoy|See|Tour|Go to|Check out))/i)
          .map(a => a.trim())
          .filter(a => a);
        
        activities.forEach(activity => {
          if (activity) {
            formattedLines.push(`  • ${activity}`);
          }
        });
      }
      continue;
    }

    // Detect activities with time ranges (e.g., "Visit X (9:00 AM - 11:00 AM)")
    // Also handles "Visit X from 9:00 AM to 11:00 AM" format
    const activityWithTimeMatch = line.match(/^(Visit|Explore|Enjoy|See|Tour|Go to|Check out)\s+(.+?)\s*(?:\(([^)]+)\)|from\s+([^to]+)\s+to\s+([^,]+))/i);
    if (activityWithTimeMatch) {
      const activity = activityWithTimeMatch[2].trim();
      const timeRange = activityWithTimeMatch[3] || 
                       (activityWithTimeMatch[4] && activityWithTimeMatch[5] 
                         ? `${activityWithTimeMatch[4].trim()} - ${activityWithTimeMatch[5].trim()}`
                         : '');
      formattedLines.push(`  • ${activity}${timeRange ? ` (${timeRange})` : ''}`);
      continue;
    }

    // Detect activities that are part of a list (starting with common verbs)
    if (line.match(/^(Visit|Explore|Enjoy|See|Tour|Go to|Check out)\s+/i)) {
      formattedLines.push(`  • ${line}`);
      continue;
    }

    // Detect numbered lists and convert to bullets
    const numberedMatch = line.match(/^\d+[.)]\s*(.+)$/);
    if (numberedMatch) {
      formattedLines.push(`  • ${numberedMatch[1]}`);
      continue;
    }

    // Detect lines that look like activities but don't start with verbs
    // (e.g., "City Palace (9:00 AM - 11:00 AM)")
    const simpleActivityMatch = line.match(/^(.+?)\s*\(([^)]+)\)$/);
    if (simpleActivityMatch && currentDay !== null) {
      const activity = simpleActivityMatch[1].trim();
      const timeRange = simpleActivityMatch[2].trim();
      // Only format as bullet if it looks like an activity (has time range)
      if (timeRange.match(/\d+:\d+\s*(AM|PM)/i)) {
        formattedLines.push(`  • ${activity} (${timeRange})`);
        continue;
      }
    }

    // Keep other lines as-is (descriptions, summaries, etc.)
    if (line) {
      formattedLines.push(line);
    }
  }

  // Join lines and clean up
  let formatted = formattedLines.join('\n');
  
  // Remove any remaining dashes used as list markers (lines starting with "- ")
  // This ensures we only use bullet points, not dashes
  formatted = formatted.replace(/^- /gm, '');
  
  // Clean up multiple empty lines (max 2 consecutive)
  formatted = formatted.replace(/\n{3,}/g, '\n\n');
  
  // Clean up leading/trailing whitespace
  formatted = formatted.trim();

  return formatted;
}

