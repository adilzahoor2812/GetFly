const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const htmlPath = path.resolve(__dirname, 'drone_control_demo.html');
  const outputDir = path.resolve('/opt/cursor/artifacts');
  const fs = require('fs');
  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 430, height: 920 },
    recordVideo: {
      dir: outputDir,
      size: { width: 430, height: 920 },
    },
  });

  const page = await context.newPage();
  await page.goto(`file://${htmlPath}`);
  await page.waitForTimeout(9800);

  await context.close();
  await browser.close();

  const videos = fs.readdirSync(outputDir).filter(f => f.endsWith('.webm'));
  const latest = videos.sort().pop();
  const webmPath = path.join(outputDir, latest);
  const mp4Path = path.join(outputDir, 'drone_app_demo.mp4');

  const { execSync } = require('child_process');
  execSync(`ffmpeg -y -i "${webmPath}" -c:v libx264 -pix_fmt yuv420p -movflags +faststart "${mp4Path}"`, {
    stdio: 'inherit',
  });

  console.log('Video saved to:', mp4Path);
})();
