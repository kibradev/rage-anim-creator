// node web/scripts/shot.cjs <out.png> [ped] [mine-clip-text] [game]
// Opens the running UI (http://localhost:5173), optionally picks a ped and an authored clip, saves a screenshot.
const { chromium } = require('playwright')

;(async () => {
  const [out = 'shot.png', ped, mine, game] = process.argv.slice(2)
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] })
  const p = await b.newPage({ viewport: { width: 1400, height: 850 } })
  const errs = []
  p.on('pageerror', (e) => errs.push(e.message))
  await p.goto('http://localhost:5173')
  await p.waitForTimeout(3500)
  if (ped) {
    await p.locator('[role=combobox]').first().click()
    await p.getByRole('option', { name: ped }).click()
    await p.waitForTimeout(3500)
  }
  if (mine) {
    await p.getByText('Benim', { exact: false }).first().click()
    await p.waitForTimeout(500)
    await p.getByText(mine, { exact: false }).first().click()
    await p.waitForTimeout(2500)
  }
  if (game === 'game') {
    await p.getByText('Oyun verisi', { exact: false }).first().click()
    await p.waitForTimeout(2500)
  }
  await p.screenshot({ path: out })
  console.log('SHOT', out, 'errors', JSON.stringify(errs))
  await b.close()
})()
