import { writeFileSync } from 'node:fs';
import { dispatch } from '../session/dispatch.js';
import { emit, info, isJson } from '../io/output.js';
import { CliError } from '../io/errors.js';
import { withRecovery } from '../session/recovery.js';
import { clickConversationByName, findImInput, waitForConversationActivated, } from '../session/im-locators.js';
import { sleep } from '../session/wait.js';
import { readState } from '../session/state.js';
import { debugTmpPath } from '../util/temp.js';
const IM_BASE = 'https://air.1688.com/app/ocms-fusion-components-1688/def_cbu_web_im/index.html';
function formatBeijingTime(ms) {
    // 1688 is a Chinese platform — format in Asia/Shanghai (UTC+8).
    const d = new Date(ms + 8 * 3600_000);
    const pad = (n) => String(n).padStart(2, '0');
    return (`${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ` +
        `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`);
}
function parseOneWsMessage(m, myLoginId) {
    const msg = m.message;
    if (!msg)
        return null;
    if (m.recallFeature?.code)
        return null; // recalled — skip
    const ext = msg.extension ?? {};
    const content = msg.content ?? {};
    const senderNick = ext.sender_nick ?? '';
    const isMine = senderNick === `cnalichn${myLoginId}`;
    let sender = ext.senderNickName ?? senderNick.replace(/^cnalichn/, '');
    const colon = sender.indexOf(':');
    if (colon > -1)
        sender = sender.slice(0, colon);
    const createAt = Number(msg.createAt) || 0;
    const time = createAt ? formatBeijingTime(createAt) : null;
    const read = Number(m.readStatus ?? 0) === 2;
    let kind = 'text';
    let contentText = '';
    let card;
    const ct = content.contentType;
    if (ct === 1) {
        contentText = String(content.text?.content ?? '');
        const offerMatch = contentText.match(/https?:\/\/detail\.1688\.com\/offer\/(\d+)\.html/i);
        if (offerMatch) {
            kind = 'offerCard';
            card = { title: null, price: null, image: null, url: contentText };
        }
        else if (/order[Ii]d=\d+/.test(contentText) &&
            /1688\.com|alibaba\.com/i.test(contentText)) {
            kind = 'orderCard';
            card = { title: null, price: null, image: null, url: contentText };
        }
    }
    else if (ct === 101) {
        // Custom template — subtype determined by bizuniqueID prefix.
        contentText = String(content.custom?.summary ?? content.custom?.title ?? '');
        const biz = ext.bizuniqueID ?? '';
        if (biz.startsWith('cbu_offer_reply'))
            kind = 'autoReply';
        else if (biz.startsWith('cbu_im_msg_assessment'))
            kind = 'assessment';
        else
            kind = 'other';
    }
    else {
        contentText = `[contentType=${ct}]`;
        kind = 'other';
    }
    const messageId = msg.messageId !== undefined ? String(msg.messageId) : undefined;
    return {
        sender: sender.trim(),
        time,
        isMine,
        content: contentText,
        read,
        kind,
        ...(card ? { card } : {}),
        ...(messageId ? { messageId } : {}),
        _sortMs: createAt,
    };
}
function parseFromWsFrames(frames, myLoginId) {
    const midToMethod = new Map();
    const ourCids = new Set();
    for (const f of frames) {
        if (f.type === 'sent' && f.mid && f.method) {
            midToMethod.set(f.mid, f.method);
        }
        if (f.type === 'sent' &&
            f.method === '/r/MessageManager/listUserMessages') {
            try {
                const body = JSON.parse(f.payload).body;
                if (Array.isArray(body) && typeof body[0] === 'string') {
                    ourCids.add(body[0]);
                }
            }
            catch {
                /* ignore */
            }
        }
    }
    const seen = new Set();
    const out = [];
    for (const f of frames) {
        if (f.type !== 'recv')
            continue;
        const reqMethod = f.mid ? midToMethod.get(f.mid) : undefined;
        if (reqMethod !== '/r/MessageManager/listUserMessages')
            continue;
        let body;
        try {
            body = JSON.parse(f.payload).body;
        }
        catch {
            continue;
        }
        const models = body?.userMessageModels;
        if (!Array.isArray(models))
            continue;
        for (const m of models) {
            if (ourCids.size > 0 &&
                m.message?.cid &&
                !ourCids.has(m.message.cid)) {
                continue;
            }
            const msgId = String(m.message?.messageId ?? '');
            if (msgId && seen.has(msgId))
                continue;
            if (msgId)
                seen.add(msgId);
            const parsed = parseOneWsMessage(m, myLoginId);
            if (parsed)
                out.push(parsed);
        }
    }
    out.sort((a, b) => a._sortMs - b._sortMs);
    return out.map(({ _sortMs: _ms, ...rest }) => rest);
}
async function waitForWsMessages(frames, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        const midToMethod = new Map();
        for (const f of frames) {
            if (f.type === 'sent' && f.mid && f.method) {
                midToMethod.set(f.mid, f.method);
            }
        }
        const hit = frames.some((f) => f.type === 'recv' &&
            f.mid &&
            midToMethod.get(f.mid) === '/r/MessageManager/listUserMessages');
        if (hit)
            return true;
        await sleep(250);
    }
    return false;
}
export async function execute(ctx, args) {
    return withRecovery(ctx, { cmd: 'seller-messages', args }, () => executeRaw(ctx, args), { headed: args.headed === true, maxRetries: 1 });
}
export async function executeRaw(ctx, args) {
    const page = await ctx.newPage();
    // ALWAYS collect WebSocket frames (LWP protocol). Used as the primary data
    // source for messages — DOM extraction is only the fallback.
    const wsFrames = [];
    page.on('websocket', (ws) => {
        const record = (type, payloadRaw) => {
            const payload = typeof payloadRaw === 'string' ? payloadRaw : payloadRaw.toString();
            let method = '';
            let mid = null;
            try {
                const j = JSON.parse(payload);
                method = j?.lwp ?? '';
                mid = j?.headers?.mid ?? null;
            }
            catch {
                /* not JSON — skip */
            }
            wsFrames.push({
                type,
                method,
                mid,
                payloadLen: payload.length,
                payload,
            });
        };
        ws.on('framesent', (frame) => record('sent', frame.payload));
        ws.on('framereceived', (frame) => record('recv', frame.payload));
    });
    if (process.env.BB1688_PROBE === '1') {
        // Probe: dump frames to file for offline analysis.
        page.on('close', () => {
            const midToMethod = new Map();
            for (const f of wsFrames) {
                if (f.type === 'sent' && f.mid && f.method) {
                    midToMethod.set(f.mid, f.method);
                }
            }
            const enriched = wsFrames.map((f) => ({
                ...f,
                reqMethod: f.type === 'recv' && f.mid ? midToMethod.get(f.mid) ?? null : null,
            }));
            const interesting = enriched.filter((f) => {
                if (f.type === 'sent') {
                    return /Message|Conversation|SingleChat/i.test(f.method);
                }
                if (f.reqMethod &&
                    /Message|Conversation|SingleChat/i.test(f.reqMethod)) {
                    return true;
                }
                return /msgId|messageId|cardType|offerId|orderId|conversationCode|userConvs|listMessage/i.test(f.payload);
            });
            // Write full frames to file (truncation-free)
            try {
                const fullPath = debugTmpPath('1688-ws-frames.json');
                const interestingPath = debugTmpPath('1688-ws-interesting.json');
                writeFileSync(fullPath, JSON.stringify(enriched, null, 2));
                writeFileSync(interestingPath, JSON.stringify(interesting, null, 2));
            }
            catch (e) {
                process.stderr.write(`[ws-frames] write failed: ${String(e)}\n`);
            }
            process.stderr.write(`[ws-frames] total=${wsFrames.length} interesting=${interesting.length}\n` +
                `methods seen: ${[...new Set(wsFrames.map((f) => f.method).filter(Boolean))].join(', ')}\n` +
                `full dump → ${debugTmpPath('1688-ws-frames.json')} (${enriched.length} frames)\n` +
                `interesting dump → ${debugTmpPath('1688-ws-interesting.json')} (${interesting.length} frames)\n`);
        });
    }
    try {
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
        await findImInput(page);
        await sleep(3000);
        // If sidebar mode: find + click the seller
        let matched = null;
        if (!args.sellerLoginId || (!args.orderId && !args.offerId)) {
            matched = await clickConversationByName(page, args.searchNames);
            if (!matched) {
                throw new CliError(29, 'SELLER_NOT_IN_SIDEBAR', `Seller not in 旺旺 sidebar: ${args.searchNames.join(', ')}. ` +
                    'Use orderId instead to auto-activate via order context.');
            }
        }
        else {
            matched = args.searchNames[0] ?? args.sellerLoginId;
        }
        await waitForConversationActivated(page, matched, args);
        // Wait for IM page to fire `/r/MessageManager/listUserMessages` and the
        // server's recv frame to arrive. Falls through after timeout so we can
        // still fall back to DOM extraction.
        const gotWsMessages = await waitForWsMessages(wsFrames, 8000);
        if (gotWsMessages) {
            // Give a tiny grace window in case a second page-load batch is in flight.
            await sleep(800);
        }
        else {
            // No WS response captured — wait a bit more for DOM render.
            await sleep(2500);
        }
        // Try the WebSocket path first — server-truth data (messageId, createAt,
        // readStatus, URLs in plain text). If empty, fall back to DOM scraping.
        const wsMessages = parseFromWsFrames(wsFrames, args.myLoginId);
        const imFrameDoc = page
            .frames()
            .find((f) => /def_cbu_web_im_core/.test(f.url()));
        if (wsMessages.length > 0) {
            // WS data is clean but lacks visual card metadata (title/price/image).
            // The IM client hydrates URL messages into cards in DOM — pull that
            // enrichment so the human view shows product names instead of just IDs.
            if (imFrameDoc && wsMessages.some((m) => m.kind === 'offerCard')) {
                try {
                    const domCards = await imFrameDoc.evaluate(() => {
                        const out = [];
                        for (const item of Array.from(document.querySelectorAll('.message-item'))) {
                            const card = item.querySelector('.text-od-wrap, .od-wrap');
                            if (!card)
                                continue;
                            const timeEl = item.querySelector('.time');
                            const time = timeEl?.textContent?.trim() ?? null;
                            const titleEl = card.querySelector('.odName, .od-name, [class*="odName"]');
                            const priceEl = card.querySelector('.odPrice, .od-price, [class*="odPrice"]');
                            const imgEl = card.querySelector('img');
                            out.push({
                                time,
                                title: titleEl?.textContent?.trim().slice(0, 200) ?? null,
                                price: priceEl?.textContent
                                    ?.replace(/\s+/g, '')
                                    .replace('￥', '¥')
                                    .trim() ?? null,
                                image: imgEl?.getAttribute('src') ?? null,
                            });
                        }
                        return out;
                    });
                    // Pair by exact time match (YYYY-MM-DD HH:MM:SS). If duplicates
                    // (e.g. user re-sent same URL within the same second), consume
                    // each DOM card only once via shift().
                    const byTime = new Map();
                    for (const dc of domCards) {
                        if (!dc.time)
                            continue;
                        const list = byTime.get(dc.time) ?? [];
                        list.push(dc);
                        byTime.set(dc.time, list);
                    }
                    for (const msg of wsMessages) {
                        if (msg.kind !== 'offerCard' || !msg.card || !msg.time)
                            continue;
                        const bucket = byTime.get(msg.time);
                        const dc = bucket?.shift();
                        if (!dc)
                            continue;
                        msg.card.title = dc.title;
                        msg.card.price = dc.price;
                        msg.card.image = dc.image;
                    }
                }
                catch {
                    /* enrichment is best-effort */
                }
            }
            return {
                conversation: matched ?? '?',
                total: wsMessages.length,
                messages: wsMessages.slice(-Math.max(1, args.limit)),
            };
        }
        // Fallback: scrape from .message-item DOM nodes.
        const frame = imFrameDoc;
        if (!frame) {
            throw new CliError(22, 'CHAT_NOT_LOADED', 'IM iframe not available.');
        }
        // Probe mode: wait longer for response frames.
        if (process.env.BB1688_PROBE === '1') {
            await sleep(15000);
        }
        // Probe: dump (1) suspected card item HTML, (2) all mtop calls fired
        // during the IM load, (3) any WebSocket connections + global state.
        if (typeof globalThis !== 'undefined' && typeof process !== 'undefined' && process.env.BB1688_PROBE === '1') {
            // mtop trap was set up via addInitScript above? No — let's do it now
            // post-hoc by reading page state if available.
            const wsAndState = await page
                .evaluate(() => {
                const out = {
                    globalKeys: [],
                    imGlobals: {},
                    wsCount: 0,
                };
                // Top-level window keys that look IM/AMP/wangwang-related
                const filter = /amp|wangwang|ww|chat|im|conversation|message/i;
                for (const k of Object.keys(window)) {
                    if (filter.test(k)) {
                        out.globalKeys.push(k);
                        try {
                            const v = window[k];
                            if (v && typeof v === 'object') {
                                out.imGlobals[k] =
                                    'obj{' +
                                        Object.keys(v).slice(0, 8).join(',') +
                                        '}';
                            }
                            else if (typeof v === 'string' || typeof v === 'number') {
                                out.imGlobals[k] = String(v).slice(0, 60);
                            }
                        }
                        catch {
                            /* ignore */
                        }
                    }
                }
                return out;
            })
                .catch(() => ({
                globalKeys: [],
                imGlobals: {},
                wsCount: 0,
            }));
            process.stderr.write(`[im-state-probe]\n` + JSON.stringify(wsAndState, null, 2) + '\n');
        }
        if (typeof globalThis !== 'undefined' && typeof process !== 'undefined' && process.env.BB1688_PROBE === '1') {
            const probe = await frame.evaluate(() => {
                const items = Array.from(document.querySelectorAll('.message-item'));
                return items.slice(-6).map((item) => {
                    const text = (item.innerText ?? '').replace(/\s+/g, ' ').trim().slice(0, 80);
                    const html = item.outerHTML.slice(0, 800);
                    const classes = item.className?.toString?.() ?? '';
                    return { text, classes, html };
                });
            });
            process.stderr.write(`[card-probe]\n` + JSON.stringify(probe, null, 2) + '\n');
        }
        const raw = await frame.evaluate(() => {
            const items = Array.from(document.querySelectorAll('.message-item'));
            return items.map((item) => {
                const cls = item.className?.toString?.() ?? '';
                const isMine = / self(\s|$)/.test(' ' + cls);
                const full = (item.innerText ?? '').replace(/\s+/g, ' ').trim();
                const tsRe = /(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})/;
                const tsMatch = full.match(tsRe);
                const time = tsMatch ? tsMatch[1] : null;
                let sender = '';
                let content = full;
                if (tsMatch) {
                    sender = full.slice(0, tsMatch.index).trim();
                    content = full.slice(tsMatch.index + tsMatch[0].length).trim();
                }
                // Seller side shows "shop_name:operator_name" — keep just shop part.
                const colonIdx = sender.indexOf(':');
                const senderShort = colonIdx > -1 ? sender.slice(0, colonIdx) : sender;
                const read = /已读\s*$/.test(content);
                const cleanContent = content.replace(/\s*已读\s*$/, '').trim();
                // Detect card-like content. 1688 IM auto-renders detail / order URLs
                // into a card with image + title + price + link.
                let kind = 'text';
                let card;
                // 1688 IM auto-renders offer-detail URLs and order URLs into custom
                // card components. They have NO `<a href>` — detection is by class:
                //   - Offer card: div.text-od-wrap > img.headPic + div.infoWrap
                //                 (.odName + .odPrice inside)
                //   - Order card: similar wrapper with order-specific classes
                //   - Auto-reply / template: div.im-template-msg
                const offerCardEl = item.querySelector('.text-od-wrap, .od-wrap, .offer-card-wrap');
                const orderCardEl = item.querySelector('.text-od-order-wrap, .order-card-wrap, [class*="OrderCard"]');
                if (offerCardEl) {
                    kind = 'offerCard';
                    const titleEl = offerCardEl.querySelector('.odName, .od-name, [class*="odName"]');
                    const priceEl = offerCardEl.querySelector('.odPrice, .od-price, [class*="odPrice"]');
                    const cardImg = offerCardEl.querySelector('img');
                    card = {
                        title: titleEl?.textContent?.trim().slice(0, 200) ?? null,
                        price: priceEl?.textContent?.replace(/\s+/g, '').replace('￥', '¥').trim() ?? null,
                        image: cardImg?.getAttribute('src') ?? null,
                        // Offer cards don't expose URL in DOM — reconstruct from title
                        // hash isn't reliable. Leave null; agent can use cart-list or
                        // search to map title back to offerId if needed.
                        url: null,
                    };
                }
                else if (orderCardEl) {
                    kind = 'orderCard';
                    const cardImg = orderCardEl.querySelector('img');
                    card = {
                        title: cleanContent.slice(0, 200),
                        price: null,
                        image: cardImg?.getAttribute('src') ?? null,
                        url: null,
                    };
                }
                else if (item.querySelector('.im-template-msg')) {
                    // Smart-bot auto-reply / rich template message (the "智能客户专员"
                    // welcome reply, promotional banners, etc.).
                    kind = 'other';
                }
                else {
                    const contentImg = item.querySelector('.content img');
                    if (contentImg && cleanContent.length < 20) {
                        // Bare image in chat (no card wrapping, no card text).
                        kind = 'image';
                        card = {
                            title: null,
                            price: null,
                            image: contentImg.getAttribute('src') ?? null,
                            url: null,
                        };
                    }
                }
                return {
                    sender: senderShort.trim(),
                    time,
                    isMine,
                    content: cleanContent,
                    read,
                    kind,
                    card,
                };
            });
        });
        return {
            conversation: matched ?? '?',
            total: raw.length,
            messages: raw.slice(-Math.max(1, args.limit)),
        };
    }
    finally {
        await page.close().catch(() => { });
    }
}
export async function run(opts) {
    if (!opts.target && !opts.offer) {
        throw new CliError(2, 'BAD_INPUT', 'Provide <target> (orderId / seller name) or --offer <offerId>.');
    }
    const limit = Math.min(200, Math.max(1, parseInt(opts.limit ?? '20', 10)));
    const sinceMs = opts.since ? Date.parse(opts.since) : 0;
    const state = await readState(opts.profile);
    if (!state.nick) {
        throw new CliError(3, 'NOT_LOGGED_IN', 'Cannot determine your loginId. Run `1688 whoami`.');
    }
    let args;
    if (opts.offer) {
        // Pre-sale inquiry path: scope conversation by offerId.
        if (!/^\d+$/.test(opts.offer)) {
            throw new CliError(2, 'BAD_INPUT', `Invalid --offer: ${opts.offer}`);
        }
        let sellerLoginId = opts.target && !/^\d+$/.test(opts.target) ? opts.target : null;
        if (!sellerLoginId) {
            info(`Looking up seller for offer ${opts.offer}...`);
            const fe = await dispatch('detail-feglobals', { offerId: opts.offer }, { headed: opts.headed, profile: opts.profile });
            sellerLoginId = fe.offerLoginId;
        }
        if (!sellerLoginId) {
            throw new CliError(30, 'SELLER_UNKNOWN', `Cannot find seller for offer ${opts.offer}. Pass <sellerLoginId> --offer <offerId>.`);
        }
        args = {
            searchNames: [sellerLoginId],
            sellerLoginId,
            offerId: opts.offer,
            myLoginId: state.nick,
            limit,
            headed: opts.headed,
        };
    }
    else if (/^\d+$/.test(opts.target)) {
        info(`Looking up seller for order ${opts.target}...`);
        const order = await dispatch('order-get', { orderId: opts.target, maxScanPages: 5, headed: opts.headed }, { headed: opts.headed, profile: opts.profile });
        args = {
            searchNames: [order.seller.loginId, order.seller.name].filter(Boolean),
            sellerLoginId: order.seller.loginId ?? undefined,
            orderId: opts.target,
            myLoginId: state.nick,
            limit,
            headed: opts.headed,
        };
    }
    else {
        args = {
            searchNames: [opts.target],
            myLoginId: state.nick,
            limit,
            headed: opts.headed,
        };
    }
    const fetchOnce = async () => {
        const result = await dispatch('seller-messages', args, { headed: opts.headed, profile: opts.profile });
        if (sinceMs > 0) {
            const filtered = result.messages.filter((m) => {
                if (!m.time)
                    return false;
                const t = Date.parse(m.time.replace(' ', 'T') + '+08:00');
                return Number.isFinite(t) && t > sinceMs;
            });
            return { ...result, messages: filtered, total: filtered.length };
        }
        return result;
    };
    // Watch mode: prime dedup set with current history, then poll and emit
    // only newly-arrived messages. Ctrl+C to exit.
    if (opts.watch) {
        const intervalSec = Math.max(10, parseInt(opts.interval ?? '30', 10));
        const seen = new Set();
        info(`Watch mode: polling every ${intervalSec}s (Ctrl+C to stop)...`);
        let baseline;
        try {
            baseline = await fetchOnce();
        }
        catch (e) {
            throw new CliError(31, 'WATCH_BASELINE_FAILED', `Initial fetch failed: ${e.message}`);
        }
        for (const m of baseline.messages)
            seen.add(messageKey(m));
        info(`Baseline: ${baseline.conversation} — ${baseline.messages.length} messages in history`);
        // Poll loop
        // eslint-disable-next-line no-constant-condition
        while (true) {
            await sleep(intervalSec * 1000);
            let next;
            try {
                next = await fetchOnce();
            }
            catch (e) {
                process.stderr.write(`[watch] poll failed: ${e.message} — will retry next tick\n`);
                continue;
            }
            const newMsgs = next.messages.filter((m) => !seen.has(messageKey(m)));
            for (const m of newMsgs)
                seen.add(messageKey(m));
            if (newMsgs.length === 0)
                continue;
            if (isJson()) {
                for (const m of newMsgs) {
                    process.stdout.write(JSON.stringify({ conversation: next.conversation, message: m }) +
                        '\n');
                }
            }
            else {
                for (const m of newMsgs) {
                    process.stdout.write(formatOneMessage(m) + '\n');
                }
            }
        }
    }
    const data = await fetchOnce();
    emit({
        human: () => printMessages(data),
        data,
    });
}
function formatOneMessage(m) {
    const who = m.isMine ? '我' : m.sender || '对方';
    const tail = m.read && m.isMine ? '  [已读]' : '';
    const prefix = `  [${m.time ?? '?'}] ${who}:`;
    if (m.kind === 'offerCard' && m.card) {
        const offerMatch = m.card.url?.match(/detail\.1688\.com\/offer\/(\d+)\.html/i);
        const offerId = offerMatch?.[1];
        const title = m.card.title;
        const price = m.card.price;
        let body;
        if (title) {
            const priceStr = price ? ` ${price}` : '';
            const idStr = offerId ? `  #${offerId}` : '';
            body = `[商品] ${title}${priceStr}${idStr}`;
        }
        else if (offerId) {
            body = `[商品 ${offerId}]`;
        }
        else {
            body = `[商品卡] ${m.card.url ?? m.content}`;
        }
        return `${prefix} ${body}${tail}`;
    }
    if (m.kind === 'orderCard' && m.card) {
        const orderMatch = m.card.url?.match(/order[Ii]d=(\d+)/);
        const idTag = orderMatch ? `[订单 ${orderMatch[1]}]` : '[订单卡]';
        const extra = m.card.title ? `  ${m.card.title}` : '';
        return `${prefix} ${idTag}${extra}${tail}`;
    }
    if (m.kind === 'image' && m.card?.image) {
        return `${prefix} [图片] ${m.card.image}${tail}`;
    }
    if (m.kind === 'autoReply' ||
        m.kind === 'assessment' ||
        m.kind === 'other') {
        const tag = m.kind === 'autoReply'
            ? '[自动回复]'
            : m.kind === 'assessment'
                ? '[客服评价]'
                : '[模板]';
        const compact = m.content.replace(/\s+/g, ' ').trim();
        return `${prefix} ${tag} ${compact}${tail}`;
    }
    const compact = m.content.replace(/\s+/g, ' ').trim();
    return `${prefix} ${compact}${tail}`;
}
function printMessages(r) {
    process.stdout.write(`Conversation: ${r.conversation}\n`);
    if (r.messages.length === 0) {
        process.stdout.write('  (no messages)\n');
        return;
    }
    for (const m of r.messages) {
        process.stdout.write(formatOneMessage(m) + '\n');
    }
}
/** Stable dedup key for watch mode. Prefers messageId (WS path); falls back
 *  to a (time + sender + content-prefix) tuple for the rare DOM-fallback case. */
function messageKey(m) {
    if (m.messageId)
        return m.messageId;
    return `${m.time ?? '?'}|${m.sender}|${m.content.slice(0, 100)}`;
}
//# sourceMappingURL=seller-messages.js.map