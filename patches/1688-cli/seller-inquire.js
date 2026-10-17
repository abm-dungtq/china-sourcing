import { dispatch } from '../session/dispatch.js';
import { emit, info } from '../io/output.js';
import { CliError } from '../io/errors.js';
import { readState } from '../session/state.js';
import { sleep } from '../session/wait.js';
const PRODUCT_URL = (id) => `https://detail.1688.com/offer/${id}.html`;
export async function run(opts) {
    if (!opts.offerId || !/^\d+$/.test(opts.offerId)) {
        throw new CliError(2, 'BAD_INPUT', 'Valid offerId required.');
    }
    if (!opts.message?.trim()) {
        throw new CliError(2, 'BAD_INPUT', 'Message cannot be empty.');
    }
    const state = await readState(opts.profile);
    if (!state.nick) {
        throw new CliError(3, 'NOT_LOGGED_IN', 'Cannot determine your loginId. Run `1688 whoami` first.');
    }
    // 1. Resolve seller loginId
    let sellerLoginId = opts.to ?? null;
    let sellerName = null;
    if (!sellerLoginId) {
        sellerLoginId = await tryFindSeller(opts.offerId, opts);
        if (!sellerLoginId) {
            throw new CliError(30, 'SELLER_UNKNOWN', `Cannot find seller for offer ${opts.offerId}. ` +
                'Pass --to <sellerLoginId> explicitly, OR add the item to cart first ' +
                `(1688 cart add ${opts.offerId} --sku ... --qty 1) so 1688 can ` +
                'identify the seller.');
        }
    }
    info(`Seller: ${sellerLoginId}${sellerName ? ` (${sellerName})` : ''}`);
    // 2. Send TWO messages — URL first (so 1688 IM can auto-render product card
    //    if it supports that for standalone links), then the question text.
    //    Pass sellerLoginId + offerId so seller-chat uses offer-scoped URL that
    //    creates the conversation server-side (works for never-chatted sellers).
    const productUrl = PRODUCT_URL(opts.offerId);
    const searchNames = [sellerLoginId, sellerName].filter(Boolean);
    const chatBaseArgs = {
        searchNames,
        sellerLoginId,
        offerId: opts.offerId,
        myLoginId: state.nick,
    };
    info(`Sending message 1/2: product link`);
    await dispatch('seller-chat', { ...chatBaseArgs, message: productUrl }, { headed: opts.headed, profile: opts.profile });
    // Small pause so the 2 sends look natural (and avoid hammering)
    await sleep(1500);
    info(`Sending message 2/2: question`);
    const screenshotPath = process.env.BB1688_SCREENSHOT_PATH || null;
    const data = await dispatch('seller-chat', { ...chatBaseArgs, message: opts.message, screenshotPath }, { headed: opts.headed, profile: opts.profile });
    emit({
        human: () => {
            process.stdout.write(`✓ Inquiry sent to ${data.sentTo}\n`);
            process.stdout.write(`  msg 1 (link):     ${productUrl}\n`);
            process.stdout.write(`  msg 2 (question): ${opts.message}\n`);
            process.stdout.write(`  at: ${data.sentAt}\n`);
            if (data.screenshotPath) {
                process.stdout.write(`  screenshot:       ${data.screenshotPath}\n`);
            }
        },
        data: { ok: true, sentTo: data.sentTo, productUrl, question: opts.message, sentAt: data.sentAt, screenshotPath: data.screenshotPath ?? null },
    });
}
/**
 * Find seller's loginId for an offerId. Strategy:
 *  1) Read window.FE_GLOBALS.offerLoginId from the product detail page (works
 *     for ALL offers — best path)
 *  2) Fallback: cart match (if for some reason the page lookup fails)
 */
async function tryFindSeller(offerId, opts) {
    // Primary: scrape window.FE_GLOBALS.offerLoginId from detail page
    info(`Reading seller loginId from detail page...`);
    try {
        const loginId = await dispatch('detail-feglobals', { offerId }, { headed: opts.headed, profile: opts.profile });
        if (loginId.offerLoginId) {
            info(`Found from FE_GLOBALS: seller=${loginId.offerLoginId}`);
            return loginId.offerLoginId;
        }
    }
    catch {
        /* fall through */
    }
    // Fallback: check cart
    info(`Looking up offer ${offerId} in cart...`);
    try {
        const cart = await dispatch('cart-list', { headed: opts.headed }, { headed: opts.headed, profile: opts.profile });
        const item = cart.items.find((i) => i.offerId === offerId);
        if (item?.seller.loginId) {
            info(`Found in cart: seller=${item.seller.loginId}`);
            return item.seller.loginId;
        }
    }
    catch {
        /* ignore */
    }
    return null;
}
// Standalone executor: scrape FE_GLOBALS from offer detail page
export async function scrapeFeGlobals(ctx, args) {
    const page = await ctx.newPage();
    try {
        await page.goto(`https://detail.1688.com/offer/${args.offerId}.html`, { waitUntil: 'domcontentloaded', timeout: 25000 });
        // The script tag containing FE_GLOBALS is in the initial HTML, so we don't
        // need to wait for JS to run — but a small delay helps if redirects happen.
        await sleep(1500);
        const result = await page.evaluate(() => {
            const w = window;
            return { offerLoginId: w.FE_GLOBALS?.offerLoginId ?? null };
        });
        return result;
    }
    finally {
        await page.close().catch(() => { });
    }
}
//# sourceMappingURL=seller-inquire.js.map