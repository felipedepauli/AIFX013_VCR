const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto('http://127.0.0.1:5000');
    await page.waitForSelector('.image-card');
    
    // Select first image Checkbox
    const cards = await page.$$('.image-card');
    await cards[0].$eval('.select-checkbox', el => el.click());
    
    // Shift-click third image card
    await page.keyboard.down('Shift');
    await cards[2].click();
    await page.keyboard.up('Shift');
    
    // Check how many are selected
    const selected = await page.$$('.image-card.selected');
    console.log(`Selected count: ${selected.length}`);
    await browser.close();
})();
