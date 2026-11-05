'use strict';

// Copy outside the skill folder, inspect the actual page, then replace these
// example selectors and assertions with the authorized product flow.
// The recorder has already navigated to the explicit --url before this runs.
module.exports = async function ({page, mark}) {
  await page.getByRole('heading', {name: 'Example product', exact: true}).waitFor();
  await mark('ready');

  await page.getByRole('button', {name: 'Open details', exact: true}).click();
  await page.getByRole('region', {name: 'Details', exact: true}).waitFor();
  await mark('details-visible');

  await page.getByRole('button', {name: 'Choose view B', exact: true}).click();
  if (await page.getByRole('status').innerText() !== 'View B') throw new Error('View selection did not update');
  await mark('view-b-selected');

  // Let the application's own persistence restore the selection. A per-load
  // init script that rewrites sessionStorage/localStorage would invalidate this.
  await page.reload({waitUntil: 'domcontentloaded'});
  if (await page.getByRole('status').innerText() !== 'View B') throw new Error('View selection did not survive refresh');
  await mark('view-b-restored');

  // For an authorized fullscreen scene, click the real fullscreen control and
  // await document.fullscreenElement before mark('fullscreen'). Inspect the
  // recorded viewport/screen observations; do not resize or fake fullscreen to
  // turn a clipped recording into an apparent success.
};
