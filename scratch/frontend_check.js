// Using built-in fetch (Node >=18)
const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function main() {
  try {
    console.log('Fetching alerts list (limit=5, offset=0)');
    const listResp = await fetch(`${API_BASE}/api/alerts?limit=5&offset=0`);
    const listData = await listResp.json();
    console.log('Total alerts from API:', listData.total);
    const firstAlert = listData.items[0];
    if (!firstAlert) {
      console.log('No alerts returned');
      return;
    }
    const alertId = firstAlert.id;
    console.log('Fetching alert detail for id', alertId);
    const detailResp1 = await fetch(`${API_BASE}/api/alerts/${alertId}`);
    const detail1 = await detailResp1.json();
    const originalStatus = detail1.triage?.status || detail1.triage_status || 'new';
    console.log('Original triage status:', originalStatus);
    const newStatus = originalStatus === 'new' ? 'investigating' : 'new';
    console.log('Patching triage status to', newStatus);
    const patchResp = await fetch(`${API_BASE}/api/alerts/${alertId}/triage`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const patched = await patchResp.json();
    console.log('Patch response status:', patched.status);
    // refetch detail
    const detailResp2 = await fetch(`${API_BASE}/api/alerts/${alertId}`);
    const detail2 = await detailResp2.json();
    console.log('Refetched triage status after patch:', detail2.triage?.status || detail2.triage_status);
    // verify persistence
    const persisted = (detail2.triage?.status || detail2.triage_status) === newStatus;
    console.log('Persistence verified:', persisted);
    // Cleanup: revert to original status
    if (persisted) {
      await fetch(`${API_BASE}/api/alerts/${alertId}/triage`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: originalStatus })
      });
      console.log('Reverted triage status to original');
    }
    // Pagination check: fetch second page and compare totals
    const page2Resp = await fetch(`${API_BASE}/api/alerts?limit=5&offset=5`);
    const page2 = await page2Resp.json();
    console.log('Second page total (should match first total):', page2.total);
    console.log('Pagination consistency:', page2.total === listData.total);
  } catch (err) {
    console.error('Error during checks:', err);
    process.exit(1);
  }
}

main();
