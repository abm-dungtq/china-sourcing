import { dispatch } from '../session/dispatch.js';
import { emit, info } from '../io/output.js';
import { CliError } from '../io/errors.js';
import { withRecovery } from '../session/recovery.js';
import { sleep } from '../session/wait.js';
import { clickConversationByName, clickImSendButton, findImInput, waitForConversationActivated, waitForMessageSent, } from '../session/im-locators.js';
import { readState } from '../session/state.js';
const IM_BASE = 'https://air.1688.com/app/ocms-fusion-components-1688/def_cbu_web_im/index.html';
export async function execute(ctx, args) {
    if (!args.message || !args.myLoginId || !args.searchNames?.length) {
        throw new CliError(2, 'BAD_INPUT', 'myLoginId, searchNames, and message are required.');
    }
    if (args.message.length > 500) {
        throw new CliError(2, 'BAD_INPUT', 'Message too long (max 500 chars).');
    }
    return withRecovery(ctx, { cmd: 'seller-chat', args }, () => executeRaw(ctx, args), { headed: args.headed === true, maxRetries: 0 });
}
export async function executeRaw(ctx, args) {
    const page = await ctx.newPage();
    try {
        // Build URL using 1688's "联系卖家" pattern:
        //   touid=cnalichn<loginId>  (cnalichn prefix is required)
        //   siteid=cnalichn
        //   status=1
        //   orderId / offerId        (server uses these to scope/create conversation)
        //   #/
        //
        // Without proper scope params, 1688 won't create the conversation
        // server-side and the chat shows "您尚未选择联系人".
        let url;
        if (args.sellerLoginId && (args.orderId || args.offerId)) {
            url =
                `${IM_BASE}?` +
                    `touid=cnalichn${encodeURIComponent(args.sellerLoginId)}` +
                    `&siteid=cnalichn` +
                    `&status=1` +
                    `&portalId=` +
                    `&gid=` +
                    `&offerId=${args.offerId ? encodeURIComponent(args.offerId) : ''}` +
                    `&itemsId=` +
                    `&orderId=${args.orderId ? encodeURIComponent(args.orderId) : ''}` +
                    `#/`;
            const scope = args.orderId
                ? `orderId=${args.orderId}`
                : `offerId=${args.offerId}`;
            info(`Opening 旺旺 (scoped: ${scope})...`);
        }
        else {
            url = `${IM_BASE}?fromid=cnalichn${encodeURIComponent(args.myLoginId)}`;
            info('Opening 旺旺 IM (sidebar mode)...');
        }
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        if (/login\.1688\.com|login\.taobao\.com/.test(page.url())) {
            throw new CliError(3, 'NOT_LOGGED_IN', 'Session expired. Run `1688 login`.');
        }
        const input = await findImInput(page);
        await sleep(3000);
        // If scoped URL (order/offer) was used, conversation should auto-activate.
        // Otherwise (sidebar mode), find + click the seller in sidebar.
        let matchedName = null;
        if (args.sellerLoginId && (args.orderId || args.offerId)) {
            // Scoped — wait for auto-activation
            matchedName = args.searchNames[0] ?? args.sellerLoginId;
        }
        else {
            info(`Searching sidebar for: ${args.searchNames.join(' / ')}`);
            matchedName = await clickConversationByName(page, args.searchNames);
            if (!matchedName) {
                throw new CliError(29, 'SELLER_NOT_IN_SIDEBAR', `Seller not found in 旺旺 conversation list (tried: ${args.searchNames
                    .filter(Boolean)
                    .join(', ')}). Use an orderId-based call so we can pass orderId to ` +
                    'auto-activate the conversation.');
            }
        }
        await waitForConversationActivated(page, matchedName, args);
        await sleep(1500);
        // 4. Type the message and send.
        info(`Typing message (${args.message.length} chars)...`);
        await input.click({ force: true });
        await input.fill('');
        await page.keyboard.type(args.message, { delay: 20 });
        await sleep(500);
        info('Sending...');
        await clickImSendButton(page);
        const sentAt = new Date().toISOString();
        await waitForMessageSent(page, args.message);
        let screenshotPath = null;
        if (args.screenshotPath) {
            await sleep(2500);
            await page.evaluate(() => {
                // Hide floating "发送链接" product overlay card if covering chat messages
                const btns = Array.from(document.querySelectorAll('button, span, div'));
                for (const el of btns) {
                    if (el.textContent?.trim() === '发送链接') {
                        let card = el.parentElement;
                        for (let i = 0; i < 4 && card; i++) {
                            if (card.innerText?.includes('价格') && card.innerText?.includes('发送链接')) {
                                card.style.display = 'none';
                                break;
                            }
                            card = card.parentElement;
                        }
                    }
                }
            }).catch(() => {});
            await sleep(300);
            await page.screenshot({ path: args.screenshotPath, fullPage: false });
            screenshotPath = args.screenshotPath;
            info(`Saved IM screenshot: ${screenshotPath}`);
        }
        return {
            ok: true,
            sentTo: matchedName,
            message: args.message,
            sentAt,
            screenshotPath,
        };
    }
    finally {
        await page.close().catch(() => { });
    }
}
export async function run(opts) {
    if (!opts.message) {
        throw new CliError(2, 'BAD_INPUT', 'Message is required.');
    }
    if (!opts.message.trim()) {
        throw new CliError(2, 'BAD_INPUT', 'Message cannot be empty.');
    }
    if (!opts.target) {
        throw new CliError(2, 'BAD_INPUT', 'Provide an orderId or seller name as target.');
    }
    const state = await readState(opts.profile);
    if (!state.nick) {
        throw new CliError(3, 'NOT_LOGGED_IN', 'Cannot determine your loginId. Run `1688 whoami` first.');
    }
    const myLoginId = state.nick;
    // For orderId target: look up seller; by default also send the order detail
    // URL as a first message (1688 IM auto-renders it as an order card).
    // --no-card skips the card (use for follow-up replies).
    // For loginId target: just send the text (sidebar mode).
    let baseArgs;
    let sendCard = false;
    let finalMessage = opts.message;
    if (/^\d+$/.test(opts.target)) {
        info(`Looking up seller for order ${opts.target}...`);
        const order = await dispatch('order-get', { orderId: opts.target, maxScanPages: 5, headed: opts.headed }, { headed: opts.headed, profile: opts.profile });
        if (!order.seller.loginId) {
            throw new CliError(12, 'SELLER_NOT_FOUND', `Order ${opts.target} has no seller loginId.`);
        }
        baseArgs = {
            searchNames: [order.seller.loginId, order.seller.name].filter(Boolean),
            sellerLoginId: order.seller.loginId,
            orderId: opts.target,
            myLoginId,
        };
        sendCard = !opts.noCard;
        // Optional: --prefix adds 【订单 XXX】 in text (redundant if card sent)
        if (opts.prefix && !finalMessage.includes(opts.target)) {
            finalMessage = `【订单 ${opts.target}】${finalMessage}`;
        }
        info(`Will message: ${order.seller.name ?? order.seller.loginId}`);
    }
    else {
        baseArgs = {
            searchNames: [opts.target],
            myLoginId,
        };
        info(`Will message: ${opts.target} (sidebar mode — requires existing chat)`);
    }
    // First, send the order URL as a separate message (auto-rendered as card).
    if (sendCard) {
        const orderUrl = `https://trade.1688.com/order/new_step_order_detail.htm?orderId=${opts.target}`;
        info(`Sending message 1/2: order link card`);
        await dispatch('seller-chat', { ...baseArgs, message: orderUrl, headed: opts.headed }, { headed: opts.headed, profile: opts.profile });
        await sleep(1500);
        info(`Sending message 2/2: question`);
    }
    const data = await dispatch('seller-chat', { ...baseArgs, message: finalMessage, headed: opts.headed }, { headed: opts.headed, profile: opts.profile });
    emit({
        human: () => {
            process.stdout.write(`✓ Message sent to ${data.sentTo}\n`);
            process.stdout.write(`  at: ${data.sentAt}\n`);
            process.stdout.write(`  >> ${data.message}\n`);
        },
        data,
    });
}
//# sourceMappingURL=seller-chat.js.map